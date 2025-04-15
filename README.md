# EyeofSauron

A simple Django application that monitors Hackerone programs and sends alerts to a Telegram channel when new programs and new scopes are detected.

## Setup Instructions

### 1. Create a Telegram Bot

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Use the `/newbot` command to create a new bot
3. Follow the instructions and obtain your `bot_token`

### 2. Get Your Channel/Group ID

1. Add [@myidbot](https://t.me/myidbot) to your Telegram channel or group
2. Run the `/getgroupid` command in the channel
3. Save the Group ID for configuration

### 3. Clone and Set Up the Project

```bash
# Clone the repository
git clone git@github.com:VoorivexTeam/EyeofSauron.git
cd EyeofSauron

# Set up virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Configure the Django Application

```bash
# Set up the database
python3 manage.py makemigrations
python3 manage.py migrate

# Create an admin user
python3 manage.py createsuperuser
```

### 5. Running the Application & Configuration

Run the following commands in separate terminal (recommand in tmux):

```bash
# Start the Django server
python3 manage.py runserver 0.0.0.0:8000 --insecure

# For background tasks processing
python3 manage.py process_tasks

```

### 6. Set Up Keys and Initial Database and Programs

You can configure the bot token and channel ID in the application settings through the admin interface

Run the initial fetch to generate your database (It takes about 10 minutes):

```bash
curl http://localhost:8000/watch/?platform=hackerone&debug=true
```

### 7. Set Up a Cron Job for Regular Updates

To edit your crontab:

```bash
crontab -e
```

Add this to your crontab to check for new programs every 10 minutes:

```bash
*/10 * * * * echo "$(date) - $(/usr/bin/curl -s "http://localhost:8000/watch/?debug=false&logger=true")" >> /var/log/curl_job.log 2>&1
```

