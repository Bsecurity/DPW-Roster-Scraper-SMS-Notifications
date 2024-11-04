DPW Roster Scraper SMS Notifications

Overview

DPW Roster Scraper SMS Notifications is a Python-based automation tool designed to scrape roster information from the DPW portal and send timely SMS notifications using the ClickSend API. Additionally, it integrates with Grafana to visualize data insights, making it easier to monitor and analyze roster-related information. Features

Automated Roster Scraping: Utilizes Selenium WebDriver to navigate and extract roster data from the DPW portal.
SMS Notifications: Sends customized SMS messages to predefined recipients based on the scraped roster data.
Configurable Recipients: Easily manage and specify who should receive the SMS notifications.
Retry Mechanism: Implements a retry system to handle unfinalized rosters, ensuring accurate data retrieval.
Grafana Integration: Visualizes roster data through Grafana charts for better monitoring and analysis.
Logging: Logs events and errors in a structured JSON format for easy monitoring and debugging.

Grafana example image
![image](https://github.com/user-attachments/assets/9d513da2-1cfc-4f48-af3c-2b2b3d7ab454)

Database example image
![image](https://github.com/user-attachments/assets/e527aa6b-43c6-4e7a-aa6c-2c6c03ef8764)

Installation

git clone https://github.com/yourusername/roster-scraper-sms.git

cd roster-scraper-sms

Install Dependencies

Ensure you have pip installed. Then, install the required Python packages: pip install -r requirements.txt

Set Up MariaDB

To enable logging and data storage, you'll need to set up a MariaDB database with the required script_logs table.

https://mariadb.org/download/?t=mariadb&p=mariadb&r=11.5.2

Set Up Grafana

https://grafana.com/grafana/download?pg=get&plcmt=selfmanaged-box1-cta1

Useage

python3 roster_scraper.py --date YYYY-MM-DD

Scheduling the Script

To automate the script's execution use a cron job

crontab -e 0 14 * * 0-5 python3 roster_scraper.py >> log_roster_scraper.py 2>&1

Distributed under the MIT License.
