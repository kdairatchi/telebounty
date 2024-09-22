# telebounty
# Bug Bounty Monitor

This tool monitors a list of URLs from a `scope.txt` file or a GitHub Gist and sends notifications via Telegram when URLs are added or removed. You can also control the script via Telegram commands.

## Features

- Monitor URLs from `scope.txt` or a GitHub Gist.
- Notifications for added or removed URLs.
- Configurable check intervals via Telegram commands.
- Pause and resume monitoring via Telegram commands.

## Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/kdairatchi/telebounty.git
   cd telebounty
pip install requests


	3.	Create a Telegram bot using BotFather and get the API token.
	4.	Update config.json with your Telegram bot API token and chat ID.
	5.	Add URLs to scope.txt (or set the Gist URL in config.json if using a Gist).
	6.	Run the script:

python main.py



Commands

	•	/pause: Pauses monitoring.
	•	/resume: Resumes monitoring.
	•	/set_interval <seconds>: Changes the URL check interval.
	•	/check: Manually triggers a URL check.
	•	/status: Displays the current check interval, summary interval, and total URLs.
