from watch.models import TelegramLog
import json
import requests
import time


def split_message_by_line(data, line):
    lines = data.split('\n')
    messages = []
    current_message = ""
    for line_content in lines:
        if len(current_message) + len(line_content) + 1 > 4096:  # +1 for the newline character
            messages.append(current_message)
            current_message = ""
        current_message += line_content + '\n'
    if current_message:
        messages.append(current_message)
    return messages

def telegram(data, logger):
    # Fetch tokens
    
    tel_config = TelegramLog.objects.get()
    if not logger: return
    apiURL = f'https://api.telegram.org/bot{tel_config.bot_token}/sendMessage'
    json_data = {
        'chat_id': tel_config.chat_id,
        'text': data,
        'parse_mode': 'HTML'
    }
    messages = [data] if len(data) < 4096 else split_message_by_line(data, 30)
    
    for message in messages:
        json_data["text"] = message
        retry_send(apiURL, json_data)

def retry_send(apiURL, json_data, initial_wait=3):
    wait_time = initial_wait
    while True:
        response = requests.post(apiURL, json=json_data)
        if response.status_code == 429:
            print(f"Error: TooManyRequests\nSleep: {wait_time} Second(s).")
            time.sleep(wait_time)
            wait_time += 2
        elif response.status_code == 200:
            break
        else:
            print(f"ERROR: telegram error with {response.status_code} status code.\n{response.text}")
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as err:
                print(f'[-] Error: {err}')
            return
