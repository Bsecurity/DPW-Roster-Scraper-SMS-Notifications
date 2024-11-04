# config.py

"""
Configuration File for DPW Roster Scraper SMS Notifications

This file contains all the configuration variables required for the DPW Microster Scraper
script that sends SMS notifications via the ClickSend API.

Ensure that this file is kept secure and **never** exposed publicly, especially if it contains
sensitive information like usernames, passwords, or API credentials.

Best Practices:
- Add `config.py` to your `.gitignore` file to prevent it from being committed to version control.
- Consider using environment variables or a separate secure method for managing sensitive data.
"""

# === DPW Microster Credentials ===
# These credentials are used to log in to the DPW Microster.

USERNAME = 'your_portal_username'  # Replace with your DPW portal username
PASSWORD = 'your_portal_password'  # Replace with your DPW portal password

# === ClickSend API Credentials ===
# These credentials are used to authenticate with the ClickSend API for sending SMS messages.

CLICKSEND_USERNAME = 'your_clicksend_username'  # Replace with your ClickSend API username
CLICKSEND_PASSWORD = 'your_clicksend_password'  # Replace with your ClickSend API password

# === SMS Recipients ===
# Define the recipients who will receive the SMS notifications.
# The keys represent roles or identifiers, and the values are the corresponding phone numbers.

RECIPIENTS = {
    'self': '+1234567890',   # Your own phone number (e.g., '+1234567890')
    'wife': '+0987654321',   # Your wife's phone number
    'mum': '+1122334455'     # Your mum's phone number
}

# === Days to Send SMS to Mum ===
# Define days when to send SMS to Mum
MUM_SEND_DAYS = ['wed', 'thu']      # Use lowercase three-letter abbrevia

# MaridaDB config
MARIADB_HOST = 'localhost'          # Replace with your MariaDB host
MARIADB_PORT = 3306                 # Default MariaDB port
MARIADB_USER = 'your_mariadb_username'     	    # Replace with your MariaDB username
MARIADB_PASSWORD = 'your_mariadb_password'    # Replace with your MariaDB password
MARIADB_DB = 'script_logs'          # Your existing database
