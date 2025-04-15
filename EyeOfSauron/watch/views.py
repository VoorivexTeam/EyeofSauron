from django.shortcuts import render
from watch.models import Program, Target, TelegramLog, HackeroneAPI
from django.http import HttpResponse
from background_task import background
from background_task.models import Task
import time
import requests
import concurrent.futures
import base64
from watch.notifiy import telegram
from datetime import datetime


# Constants
HACKERONE_API_URL = "https://api.hackerone.com/v1/hackers/programs"
HACKERONE_VERBOSE_NAME = "Update Hackerone Programs."
logger = False
STATE_CHANGE_MESSAGES = {
    ('open', 'paused'): 'Change Program From Open To Paused',
    ('paused', 'open'): 'Change Program From Paused To Open',
}

def CheckPrograms(program_name, submission, submission_state, platform, bugbounty):

    # print(f"[+] Checking: {program_name}, {submission_state}, {bugbounty}")
    queryset = Program.objects.filter(name=program_name, platform=platform)
    log_data = ''
    program_pk = None

    if queryset.exists():
        program = queryset.first()
        changes_made = False

        # Update bug bounty program type if it has changed
        if program.bbp != bugbounty:
            program.bbp = bugbounty
            change_type = 'Change Program From BBP To VDP' if not bugbounty else 'Change Program From VDP To BBP'
            changes_made = True

        # Update submission state if it has changed
        elif program.state != submission_state:
            change_type = STATE_CHANGE_MESSAGES.get((program.state, submission_state), 'State Change')
            program.state = submission_state
            changes_made = True

        # Save changes if any were made
        if changes_made:
            program.save()
        else:
            return program.pk  # No changes needed, return the primary key

    else:
        # Create a new program if it doesn't exist
        program = Program.objects.create(
            name=program_name,
            submission=submission,
            state=submission_state,
            platform=platform,
            bbp=bugbounty
        )
        change_type = 'New BBP Program' if bugbounty else 'New VDP Program'

    # Prepare log data
    program_pk = program.pk
    log_data += f'💥 <b>{change_type}</b> 💥\n\n'
    log_data += f'🔰 Program: {program.name}\n'
    log_data += f'💰 Bounty: {program.bbp}\n'
    log_data += f'🚀 Platform: {program.platform}\n'
    log_data += f'🔗 <a href="{program.submission}">Submission</a>\n'

    # Uncomment the following line to enable Telegram logging
    if bugbounty and submission_state == 'open':
        telegram(log_data, logger)

    return program_pk


def CheckTargets(target_title, target_type, is_scope, program_id):
    """
    Check and update target details or create a new target if it doesn't exist.
    """
    # print(f"[+] Checking target: {target_title} for program ID: {program_id}")
    if "█" in target_title:  # Skip invalid target titles
        return

    try:
        program = Program.objects.get(id=program_id)
    except Program.DoesNotExist:
        print(f"Program with ID {program_id} does not exist.")
        return
    target_queryset = Target.objects.filter(program=program, title=target_title)
    data = ''
    type_data = ''

    if target_queryset.exists():
        target = target_queryset.first()

        # Check if the scope has changed
        if target.scope != is_scope:
            type_data = '⬆️ Out Scope Now ⬆️' if target.scope and not is_scope else '⬇️ In Scope Now ⬇️'
            target.scope = is_scope
            target.save()

            # Construct notification data
            data += f'<b>{type_data}</b>\n\n'
            data += construct_target_data(target, program)
    else:
        # Create a new target if it doesn't exist
        target = Target.objects.create(
            title=target_title,
            type=target_type,
            scope=is_scope,
            program=program
        )
        type_data = 'New In Scope Target' if is_scope else 'New OutScope Target'

        # Construct notification data
        data += f'💥 <b>{type_data}</b> 💥\n\n'
        data += construct_target_data(target, program)

    # Log and send notification if applicable
    if data.strip():  # Ensure data is not empty
        if program.bbp and target.scope and program.state == 'open':
            telegram(data, logger)


def construct_target_data(target, program):
    """
    Helper function to construct target data for notifications.
    """
    return (
        f'🎯 Target: <b>{target.title}</b>\n'
        f'🔰 Program: <b><a href="{program.submission}">{program.name}</a></b>\n'
        f'🌐 Type: <b>{target.type}</b>\n'
        f'🍧 Scope: <b>{target.scope}</b>\n'
        f'💰 Bounty: <b>{program.bbp}</b>\n'
        f'🚀 Platform: <b>{program.platform}</b>\n'
    )


@background(schedule=0)
def hackerone(verbose_name=HACKERONE_VERBOSE_NAME):
    start_time = time.time()
    try:
        h1 = HackeroneAPI.objects.get()
        h1_token_encoded = base64.b64encode(f"{h1.username}:{h1.api_key}".encode())
        h1_token = h1_token_encoded.decode()
    except Exception as e:
        print(f"Error fetching HackerOne API credentials: {e}")
        return

    headers = {
        'Accept': 'application/json',
        'Authorization': f'Basic {h1_token}'
    }
    all_programs = []
    for page_number in range(1, 20):
        program_url = f"{HACKERONE_API_URL}?page[number]={page_number}&page[size]=100"
        response = requests.get(program_url, headers=headers)
        
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(f'[-] Error: {err}')
            continue

        data = response.json().get('data', [])
        if not data:
            break
        all_programs.extend(data)
        print(f"[{datetime.now().strftime('%Y/%m/%d %H:%M:%S')}] | [prod] Fetched {len(data)} programs from page {page_number}")

    # Process all programs and their targets
    for program in all_programs:
        handle = program['attributes']['handle']
        program_name = program['attributes']['name']
        submission = f'https://hackerone.com/{handle}'
        submission_state = program['attributes']['submission_state']
        platform = 'hackerone'
        bugbounty = program['attributes']['offers_bounties']
        if program_name == 'Agoric':
            bugbounty = True

        targets_url = f"{HACKERONE_API_URL}/{handle}"
        resp = requests.get(targets_url, headers=headers)
        try:
            resp.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(f'[-] Error: {err}')
            continue

        PK = CheckPrograms(program_name, submission, submission_state, platform, bugbounty)
        targets = resp.json()['relationships']['structured_scopes']['data']
        for target in targets:
            target_title = target['attributes']['asset_identifier']
            asset_type = target['attributes']['asset_type']
            isscope = target['attributes']['eligible_for_submission']

            target_type = map_asset_type(asset_type)
            CheckTargets(target_title, target_type, isscope, PK)

    elapsed_time_minutes = (time.time() - start_time) / 60
    print(f"[{datetime.now().strftime('%Y/%m/%d %H:%M:%S')}] | [prof] - Task Time Running: {elapsed_time_minutes:.2f} M\n")
    return 'Hackerone Programs Updated. ✅'


def map_asset_type(asset_type):
    """
    Map asset type to a more readable format.
    """
    asset_type_mapping = {
        'URL': 'website',
        'HARDWARE': 'hardware',
        'CIDR': 'cidr',
        'OTHER': 'other',
        'OTHER_IPA': 'other',
        'APPLE_STORE_APP_ID': 'ios',
        'TESTFLIGHT': 'ios',
        'DOWNLOADABLE_EXECUTABLES': 'exe',
        'WINDOWS_APP_STORE_APP_ID': 'exe',
        'GOOGLE_PLAY_APP_ID': 'android',
        'OTHER_APK': 'android',
        'SOURCE_CODE': 'source_code',
    }
    return asset_type_mapping.get(asset_type, 'unknown')




def Update(request):
    global logger
    debug = request.GET.get('debug', '').lower() == 'true'
    logger = request.GET.get('logger', '').lower() == 'true'
    print(f"logger: {logger}")
    print(f"debug: {debug}")
    
    if debug:
        print(f"[{datetime.now().strftime('%Y/%m/%d %H:%M:%S')}] | [debug] - Initiating HackerOne Programs Update Task... ✅")
        hackerone.now(verbose_name=HACKERONE_VERBOSE_NAME)
        return HttpResponse(
            "[debug]: ✅ The Update Task has been successfully initiated. Please wait while the process completes.",
            status=200
        )
    else:
        tasks = Task.objects.filter(verbose_name=HACKERONE_VERBOSE_NAME)
        if not tasks.exists():
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] | [prod] - Initiating HackerOne Programs Update Task... ✅")
            hackerone(verbose_name=HACKERONE_VERBOSE_NAME)
            return HttpResponse(
                "✅ The Update Task has been successfully initiated. Please wait while the process completes.",
                status=200
            )
        else:
            return HttpResponse(
                "⚠️ A task is already running for this operation. Please wait for it to complete before initiating a new one.",
                status=400
            )

