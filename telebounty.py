import requests
import time
import logging
import os
import json
from threading import Event, Thread
from datetime import datetime

# Load configuration from a file
CONFIG_FILE = 'config.json'
SCOPE_FILE = 'scope.txt'  # Local file with URLs to monitor
GIST_URL = None  # If you want to monitor a Gist instead, set the Gist URL in the config

def load_config():
    """ Load the configuration file with API and chat details """
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

config = load_config()
API_TOKEN = config['API_TOKEN']
CHAT_ID = config['CHAT_ID']
CHECK_INTERVAL = config['CHECK_INTERVAL']  # in seconds
SUMMARY_INTERVAL = config['SUMMARY_INTERVAL']  # in cycles, how often to send summary
GIST_URL = config.get('GIST_URL', None)  # Optional Gist URL from config

# Initialize variables
previous_urls = []
pause_event = Event()
cycle_count = 0
log_file = 'bounty_monitor.log'

# Setup logging
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(message)s')

def send_telegram_message(message):
    """ Sends a message to the specified Telegram chat with a timestamp """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    full_message = f"[{timestamp}] {message}"
    url = f'https://api.telegram.org/bot{API_TOKEN}/sendMessage'
    data = {'chat_id': CHAT_ID, 'text': full_message}
    try:
        requests.post(url, data=data)
        logging.info(f"Message sent: {full_message}")
    except Exception as e:
        logging.error(f"Error sending message: {e}")

def fetch_scope_content():
    """ Fetches the latest content from the local scope file or a Gist """
    if GIST_URL:
        try:
            response = requests.get(GIST_URL)
            response.raise_for_status()
            return response.text.splitlines()
        except requests.RequestException as e:
            logging.error(f"Error fetching Gist: {e}")
            send_telegram_message(f"Error fetching Gist: {e}")
            return None
    else:
        try:
            with open(SCOPE_FILE, 'r') as file:
                lines = file.read().splitlines()
                if not lines:
                    send_telegram_message("Warning: The scope file is empty.")
                    logging.warning("The scope file is empty.")
                return lines
        except Exception as e:
            logging.error(f"Error reading scope file: {e}")
            send_telegram_message(f"Error reading scope file: {e}")
            return None

def monitor_urls():
    """ Monitors the scope file for URL changes (additions/deletions) """
    global previous_urls, cycle_count
    while not pause_event.is_set():
        current_urls = fetch_scope_content()

        if current_urls is None:
            time.sleep(CHECK_INTERVAL)
            continue  # Retry on next iteration if error occurs

        current_urls_set = set(current_urls)
        previous_urls_set = set(previous_urls)

        new_urls = current_urls_set - previous_urls_set
        deleted_urls = previous_urls_set - current_urls_set

        if new_urls:
            new_message = "New URLs added:\n" + "\n".join(new_urls)
            send_telegram_message(new_message)
            logging.info(f"New URLs detected: {new_urls}")
            previous_urls = current_urls

        if deleted_urls:
            deleted_message = "URLs deleted:\n" + "\n".join(deleted_urls)
            send_telegram_message(deleted_message)
            logging.info(f"Deleted URLs detected: {deleted_urls}")
            previous_urls = current_urls

        cycle_count += 1

        if cycle_count % SUMMARY_INTERVAL == 0:
            send_summary_report()

        time.sleep(CHECK_INTERVAL)

def send_summary_report():
    """ Sends a summary report of URL monitoring """
    summary_message = f"Monitoring summary:\n- Total cycles: {cycle_count}\n- Last known URLs count: {len(previous_urls)}"
    send_telegram_message(summary_message)
    logging.info("Summary report sent.")

def handle_telegram_commands():
    """ Handles incoming Telegram commands from the user """
    global CHECK_INTERVAL
    while True:
        url = f'https://api.telegram.org/bot{API_TOKEN}/getUpdates'
        response = requests.get(url)
        updates = response.json()

        if 'result' in updates:
            for update in updates['result']:
                if 'message' in update:
                    chat_id = update['message']['chat']['id']
                    if str(chat_id) == CHAT_ID:
                        text = update['message'].get('text', '').lower()

                        if text == '/pause':
                            pause_event.set()
                            send_telegram_message("Monitoring paused.")
                            logging.info("Monitoring paused.")
                        elif text == '/resume':
                            pause_event.clear()
                            send_telegram_message("Monitoring resumed.")
                            logging.info("Monitoring resumed.")
                            monitor_urls()  # Restart monitoring
                        elif text.startswith('/set_interval'):
                            try:
                                new_interval = int(text.split(' ')[1])
                                CHECK_INTERVAL = new_interval
                                send_telegram_message(f"Check interval set to {CHECK_INTERVAL} seconds.")
                                logging.info(f"Check interval updated to {CHECK_INTERVAL} seconds.")
                            except (IndexError, ValueError):
                                send_telegram_message("Usage: /set_interval <seconds>")
                        elif text.startswith('/add_url'):
                            new_url = text.split(' ')[1]
                            if new_url:
                                with open(SCOPE_FILE, 'a') as f:
                                    f.write(f"\n{new_url}")
                                send_telegram_message(f"URL {new_url} added to scope.")
                                logging.info(f"URL {new_url} added to scope.")
                        elif text.startswith('/remove_url'):
                            url_to_remove = text.split(' ')[1]
                            with open(SCOPE_FILE, 'r') as f:
                                lines = f.readlines()
                            with open(SCOPE_FILE, 'w') as f:
                                for line in lines:
                                    if line.strip("\n") != url_to_remove:
                                        f.write(line)
                            send_telegram_message(f"URL {url_to_remove} removed from scope.")
                            logging.info(f"URL {url_to_remove} removed from scope.")
                        elif text == '/check':
                            current_urls = fetch_scope_content()
                            send_telegram_message(f"Manual check completed. Total URLs: {len(current_urls)}")
                            logging.info("Manual check completed.")
                        elif text == '/status':
                            send_telegram_message(f"Current check interval: {CHECK_INTERVAL} seconds.\nSummary interval: {SUMMARY_INTERVAL} cycles.\nTotal URLs: {len(previous_urls)}")
                            logging.info("Status requested.")

        time.sleep(5)

# Main execution
if __name__ == "__main__":
    logging.info("Bug bounty monitor started.")
    send_telegram_message("Bug bounty monitoring started.")
    
    # Start monitoring and handle commands in parallel
    monitor_thread = Thread(target=monitor_urls)
    monitor_thread.start()
    
    command_thread = Thread(target=handle_telegram_commands)
    command_thread.start()
