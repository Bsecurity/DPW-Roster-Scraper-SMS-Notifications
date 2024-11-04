"""
DPW Roster Scraper

This script automates the process of scraping roster information from the DPW Microster,
logs the data, and sends SMS notifications based on the roster details.

Features:
- Scrapes roster data using Selenium WebDriver.
- Logs events and errors with structured data.
- Sends SMS notifications via ClickSend API.
- Supports retry mechanisms for unfinalized rosters.

Usage:
    python3 roster_scraper.py --date YYYY-MM-DD

Dependencies:
    - selenium
    - clicksend-client
    - beautifulsoup4
    - argparse
    - other standard Python libraries
"""

import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from datetime import datetime, timedelta, timezone
from config import (
    MUM_SEND_DAYS, RECIPIENTS, USERNAME, PASSWORD,
    CLICKSEND_USERNAME, CLICKSEND_PASSWORD
)
from offsets import month_offsets
import clicksend_client
from my_clicksend_client import SmsMessage
from clicksend_client.rest import ApiException
import json
import time
import sys
import os
import requests
from bs4 import BeautifulSoup

def log_message(data: dict) -> None:
    """
    Logs a structured message by printing it as JSON.

    Args:
        data (dict): A dictionary containing log information with keys such as 'time', 'level',
                     'event', 'sms_content', 'day', 'date', 'shift_start', 'shift_end',
                     'hours', and 'retry_attempts'.

    Returns:
        None
    """
    # Print the log as JSON
    print(json.dumps(data))

def send_sms(message: str, recipients: list) -> None:
    """
    Sends an SMS message to the specified recipients using the ClickSend API.

    Args:
        message (str): The SMS message content to be sent.
        recipients (list): A list of recipient phone numbers as strings.

    Returns:
        None

    Raises:
        ApiException: If the ClickSend API encounters an error.
        Exception: For any unexpected errors during the SMS sending process.
    """
    try:
        print(f"Attempting to send SMS: {message}")
        configuration = clicksend_client.Configuration()
        configuration.username = CLICKSEND_USERNAME
        configuration.password = CLICKSEND_PASSWORD
        api_instance = clicksend_client.SMSApi(clicksend_client.ApiClient(configuration))
        business_name = "DP WORLD"  # Ensure this is a valid sender ID

        sms_messages = []
        for recipient in recipients:
            sms_message = SmsMessage(
                source="python",
                body=message,
                to=recipient,
                _from=business_name
            )
            sms_messages.append(sms_message)

        sms_message_collection = clicksend_client.SmsMessageCollection(messages=sms_messages)
        print("Sending SMS via ClickSend API...")
        api_response = api_instance.sms_send_post(sms_message_collection)
        print(f"SMS sent successfully: {api_response}")
    except ApiException as e:
        print(f"Exception when sending SMS: {e}")
    except Exception as e:
        print(f"Unexpected error when sending SMS: {e}")

def setup_webdriver() -> webdriver.Chrome:
    """
    Configures and initializes a headless Selenium WebDriver instance for Chrome.

    Returns:
        webdriver.Chrome: An instance of Chrome WebDriver with specified options.

    Raises:
        selenium.common.exceptions.WebDriverException: If the WebDriver fails to initialize.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")  # Optional: Disable GPU if not needed
    chrome_options.add_argument("--no-sandbox")   # Optional: Useful for certain environments
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def process_roster(driver: webdriver.Chrome, wait: WebDriverWait, test_dates: list, calendar_label) -> tuple:
    """
    Processes the roster for the specified test dates by scraping data from the calendar.

    Args:
        driver (webdriver.Chrome): The Selenium WebDriver instance.
        wait (WebDriverWait): The WebDriverWait instance for handling dynamic content.
        test_dates (list): A list of datetime.date objects representing the dates to process.
        calendar_label: The Selenium WebElement representing the current calendar month label.

    Returns:
        tuple: A tuple containing:
            - combined_message (str): The aggregated SMS message content.
            - not_finalised_found (bool): Flag indicating if any roster was not finalized.
            - calendar_label: The updated calendar_label WebElement after processing.

    Raises:
        None
    """
    combined_message = ""
    not_finalised_found = False

    for target_date in test_dates:
        print(f"\nProcessing date: {target_date.strftime('%Y-%m-%d')} ({target_date.strftime('%A')})")

        # Determine the current and target month
        current_month_text = calendar_label.text.strip()  # e.g., "September 2024"
        target_month_text = target_date.strftime("%B %Y")  # e.g., "October 2024"

        # Navigate to the target month if it's different from the current month
        if current_month_text != target_month_text:
            print(f"Current month is {current_month_text}. Target month is {target_month_text}. Navigating to next month...")
            try:
                # Wait for the 'Next Month' button to be clickable and click it
                next_month_link = wait.until(
                    EC.element_to_be_clickable((By.ID, "ctl00_ContentPlaceHolder1_calendar_lnkNextMonth"))
                )
                next_month_link.click()
                print(f"Clicked 'Next Month' link. Waiting for {target_month_text} to load...")
                
                # Wait until the calendar updates to the target month
                wait.until(
                    EC.text_to_be_present_in_element(
                        (By.ID, "ctl00_ContentPlaceHolder1_calendar_lblCurrentMonth"), target_month_text
                    )
                )
                print(f"Successfully navigated to {target_month_text}.")
                
                # Update the calendar_label to the new month after navigation
                calendar_label = driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_calendar_lblCurrentMonth")
            except TimeoutException:
                print(f"Error: Could not navigate to {target_month_text}. Skipping this date.")
                continue  # Skip to the next date if navigation fails

        # Calculate the correct cell index using the month offset
        month = target_date.month
        day = target_date.day
        offset = month_offsets.get(month, 0)  # Default to 0 if month not found
        cell_index = offset + day
        date_cell_id = f"ctl00_ContentPlaceHolder1_calendar_DateCell{cell_index}"
        
        try:
            print(f"Locating date cell with ID: {date_cell_id}")
            date_cell = wait.until(
                EC.presence_of_element_located((By.ID, date_cell_id))
            )
            cell_content = date_cell.get_attribute("textContent").strip()
            print(f"Content of {target_date}: '{cell_content}'")
        except TimeoutException:
            print(f"Error: Date cell {date_cell_id} not found. Skipping this date.")
            continue  # Skip to the next date if date cell is not found

        # Process the cell content
        if not cell_content or cell_content == "&nbsp;":
            message = f"Not rostered for ({target_date.strftime('%A')}) {target_date.day}/{target_date.month}/{target_date.year}."
            shift_data = {
                "time": datetime.now(timezone.utc).isoformat(),
                "level": "INFO",
                "event": "SMS_SENT",
                "sms_content": message,
                "day": target_date.strftime('%A'),
                "date": target_date.strftime("%Y-%m-%d"),
                "shift_start": 0,
                "shift_end": 0,
                "hours": 0,
                "retry_attempts": 0
            }
            log_message(shift_data)
            combined_message += message + '\n'
            print(f"Added message: {message}")
        elif "not finalised" in cell_content.lower():
            print(f"Shift for {target_date} not finalised.")
            message = f"Not finalised for ({target_date.strftime('%A')}) {target_date.day}/{target_date.month}/{target_date.year}."
            shift_data = {
                "time": datetime.now(timezone.utc).isoformat(),
                "level": "WARNING",
                "event": "SHIFT_NOT_FINALISED",
                "sms_content": message,
                "day": target_date.strftime('%A'),
                "date": target_date.strftime("%Y-%m-%d"),
                "shift_start": 0,
                "shift_end": 0,
                "hours": 0,
                "retry_attempts": 0
            }
            log_message(shift_data)
            combined_message += message + '\n'
            print(f"Added warning message: {message}")
            not_finalised_found = True  # Set the flag to indicate that a retry is needed
            break  # Exit the loop to trigger a retry
        else:
            try:
                # Extracting shift details from cell content
                # Replace <br/> with newline and split into lines
                lines = cell_content.replace('<br/>', '\n').split('\n')
                shifts = []
                hours_worked = 0
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    # Example line: "D0600-1400 (8)"
                    shift_type = line[0]  # 'D'
                    times_and_hours = line[1:].strip()  # "0600-1400 (8)"
                    try:
                        times, hours_str = times_and_hours.split('(')
                        shift_start_str, shift_end_str = times.split('-')
                        shift_start = int(shift_start_str.lstrip('0') or '0')  # Convert to integer without leading zeros
                        shift_end = int(shift_end_str.lstrip('0') or '0')      # Convert to integer without leading zeros
                        hours = int(hours_str.replace(')', '').strip())        # Cast to integer
                    except ValueError:
                        print(f"Error parsing line: '{line}'. Skipping this shift.")
                        continue  # Skip this shift if parsing fails
                    hours_worked += hours
                    shifts.append({
                        "shift_type": shift_type,
                        "shift_start": shift_start,
                        "shift_end": shift_end,
                        "hours": hours
                    })
                if not shifts:
                    print(f"No valid shift details found for {target_date}.")
                # Create the SMS content
                sms_content = f"Hours for ({target_date.strftime('%A')}) {target_date.day}/{target_date.month}/{target_date.year} are: {cell_content.strip()} (c) Bsecurity"
                combined_message += sms_content + '\n'
                print(f"Added shift details: {sms_content}")

                # Structuring the data
                shift_data = {
                    "time": datetime.now(timezone.utc).isoformat(),
                    "level": "INFO",
                    "event": "SMS_SENT",
                    "sms_content": sms_content,
                    "day": target_date.strftime('%A'),
                    "date": target_date.strftime("%Y-%m-%d"),
                    "shift_start": shifts[0]['shift_start'] if shifts else 0,
                    "shift_end": shifts[-1]['shift_end'] if shifts else 0,
                    "hours": hours_worked,
                    "retry_attempts": 0
                }
                log_message(shift_data)
            except Exception as e:
                print(f"Error processing shift for {target_date}: {e}")
                # Optionally, log this unexpected error
                error_data = {
                    "time": datetime.now(timezone.utc).isoformat(),
                    "level": "ERROR",
                    "event": "SHIFT_PROCESSING_ERROR",
                    "sms_content": f"Error processing shift for {target_date}: {e}",
                    "day": target_date.strftime('%A'),
                    "date": target_date.strftime("%Y-%m-%d"),
                    "shift_start": 0,
                    "shift_end": 0,
                    "hours": 0,
                    "retry_attempts": 0
                }
                log_message(error_data)

    return combined_message, not_finalised_found, calendar_label

def parse_arguments() -> argparse.Namespace:
    """
    Parses command-line arguments for the script.

    Returns:
        argparse.Namespace: The namespace containing parsed command-line arguments.

    Raises:
        SystemExit: If argument parsing fails.
    """
    parser = argparse.ArgumentParser(description="DPW Roster Scraper")
    parser.add_argument(
        '--date',
        type=str,
        default='today',
        help="Specify the base date for processing. Options: 'today', 'tomorrow', or 'YYYY-MM-DD'"
    )
    args = parser.parse_args()
    return args

def determine_base_date(date_str: str) -> datetime.date:
    """
    Determines the base date for processing based on the input string.

    Args:
        date_str (str): The input date string. Can be 'today', 'tomorrow', or 'YYYY-MM-DD'.

    Returns:
        datetime.date: The determined base date.

    Raises:
        SystemExit: If the date format is invalid.
    """
    if date_str.lower() == 'today':
        base_date = datetime.today().date()
    elif date_str.lower() == 'tomorrow':
        base_date = datetime.today().date() + timedelta(days=1)
    else:
        try:
            base_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            print("Error: Invalid date format. Please use 'today', 'tomorrow', or 'YYYY-MM-DD'.")
            sys.exit(1)
    return base_date

def get_test_dates(base_date: datetime.date) -> list:
    """
    Determines which dates to process based on the base_date.

    - On Fridays, returns Saturday and Sunday.
    - On other days, returns only the next day.

    Args:
        base_date (datetime.date): The reference date.

    Returns:
        list: List of datetime.date objects to process.
    """
    test_dates = []
    weekday = base_date.weekday()  # Monday is 0 and Sunday is 6

    if weekday == 4:  # Friday
        saturday = base_date + timedelta(days=1)
        sunday = base_date + timedelta(days=2)
        test_dates.extend([saturday, sunday])
        print(f"Today is Friday. Processing dates: {saturday} (Saturday), {sunday} (Sunday)")
    else:
        next_day = base_date + timedelta(days=1)
        test_dates.append(next_day)
        print(f"Processing date: {next_day} ({next_day.strftime('%A')})")
    
    return test_dates

def main() -> None:
    """
    The main function that orchestrates the roster scraping and SMS notifications.

    It handles retries for unfinalized rosters and sends SMS notifications based on the processed data.

    Returns:
        None

    Raises:
        SystemExit: Exits the script upon encountering critical errors or after reaching retry limits.
    """
    # Parse command-line arguments
    args = parse_arguments()
    base_date = determine_base_date(args.date)
    print(f"Base date set to: {base_date.strftime('%Y-%m-%d')} ({base_date.strftime('%A')})")

    # Determine test_dates based on the base_date
    test_dates = get_test_dates(base_date)
    print(f"Dates to process: {[date.strftime('%Y-%m-%d') for date in test_dates]}")

    max_retries = 120  # Define your maximum number of retries
    retry_delay = 60    # Delay in seconds between retries
    current_retry = 0

    while current_retry < max_retries:
        driver = setup_webdriver()
        wait = WebDriverWait(driver, 30)

        try:
            # Navigate to the website
            print("Navigating to the login page...")
            driver.get("https://dpw.portal.tambla.net/Microster.SelfService/Default.aspx")
            print("Login page loaded.")

            # Wait for the username field and enter the username
            try:
                print("Waiting for the username field...")
                username_field = wait.until(
                    EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_txtPersonnelId"))
                )
                username_field.send_keys(USERNAME)
                print("Entered username.")
            except TimeoutException:
                print("Error: Username field not found within the expected time.")
                driver.quit()
                sys.exit(1)  # Exit the script if username field is not found

            # Wait for the password field and enter the password
            try:
                print("Waiting for the password field...")
                password_field = wait.until(
                    EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_txtPassword"))
                )
                password_field.send_keys(PASSWORD)
                password_field.send_keys(Keys.RETURN)
                print("Entered password and submitted the login form.")
            except TimeoutException:
                print("Error: Password field not found within the expected time.")
                driver.quit()
                sys.exit(1)  # Exit the script if password field is not found

            # Wait for the main roster page to load by waiting for a specific element
            try:
                print("Waiting for the main roster page to load...")
                calendar_label = wait.until(
                    EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_calendar_lblCurrentMonth"))
                )
                print("Login successful, main roster page loaded.")
            except TimeoutException:
                print("Error: Login failed or main roster page did not load within the expected time.")
                driver.quit()
                sys.exit(1)  # Exit the script if main roster page does not load

            # Process the roster, passing the calendar_label
            combined_message, not_finalised_found, calendar_label = process_roster(driver, wait, test_dates, calendar_label)

            # Close the WebDriver session as processing is done
            driver.quit()
            print("WebDriver session ended.")

            if not_finalised_found:
                current_retry += 1
                if current_retry < max_retries:
                    print(f"Roster not finalised. Retry {current_retry}/{max_retries} in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print(f"Retry limit ({max_retries}) reached. Could not retrieve finalized information.")
                    # Log the failure
                    message = f"Retry limit ({max_retries}) reached. Could not retrieve finalized roster information."
                    log_data = {
                        "time": datetime.now(timezone.utc).isoformat(),
                        "level": "ERROR",
                        "event": "RETRY_LIMIT_REACHED",
                        "sms_content": message,
                        "day": "",
                        "date": "",
                        "shift_start": 0,
                        "shift_end": 0,
                        "hours": 0,
                        "retry_attempts": current_retry
                    }
                    log_message(log_data)
                    # Notify only self and wife about the failure
                    send_sms(message, [RECIPIENTS['self'], RECIPIENTS['wife']])
                    sys.exit(1)  # Exit the script after reaching retry limit
            else:
                if combined_message.strip():
                    # Determine current day
                    current_day = datetime.today().strftime('%a').lower()  # e.g., 'mon', 'tue'
                    print(f"Current day: {current_day}")

                    # Always send to self and wife
                    recipients = [RECIPIENTS['self'], RECIPIENTS['wife']]

                    # Send to mum only on specified days (Wednesday and Thursday)
                    if current_day in MUM_SEND_DAYS:
                        recipients.append(RECIPIENTS['mum'])

                    print(f"Sending SMS to: {recipients}")
                    send_sms(combined_message.strip(), recipients)
                else:
                    print("No messages to send.")
                # Exit the loop as processing is successful
                break

        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            driver.quit()
            # Optionally, send an SMS or email notification about the failure
            error_message = f"Script encountered an error: {e}"
            send_sms(error_message, [RECIPIENTS['self'], RECIPIENTS['wife']])
            # Log the unexpected error
            error_data = {
                "time": datetime.now(timezone.utc).isoformat(),
                "level": "ERROR",
                "event": "UNEXPECTED_ERROR",
                "sms_content": error_message,
                "day": "",
                "date": "",
                "shift_start": 0,
                "shift_end": 0,
                "hours": 0,
                "retry_attempts": current_retry
            }
            log_message(error_data)
            sys.exit(1)  # Exit the script on unexpected errors

    print("Script completed successfully.")

if __name__ == "__main__":
    main()
