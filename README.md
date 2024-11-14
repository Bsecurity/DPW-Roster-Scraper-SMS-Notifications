
# DPW Roster Scraper SMS Notifications + Database

## Overview

**DPW Roster Scraper SMS Notifications** is a Python-based automation tool that scrapes roster information from the DPW portal and sends timely SMS notifications via the ClickSend API. It integrates with Grafana to visualize data insights, making it easier to monitor and analyze roster-related information.

---

### Features

- **Automated Roster Scraping**: Uses Selenium WebDriver to navigate and extract roster data from the DPW portal.
- **SMS Notifications**: Sends customized SMS messages to predefined recipients based on the scraped roster data.
- **Configurable Recipients**: Easily manage and specify who should receive the SMS notifications.
- **Retry Mechanism**: Ensures accurate data retrieval by retrying if rosters are not finalized.
- **Grafana Integration**: Visualizes roster data through Grafana charts for effective monitoring and analysis.
- **Logging**: Logs events and errors in a structured JSON format for easy monitoring and debugging.

---

### Example Images

- **Grafana Chart**  
  ![Grafana example](https://github.com/user-attachments/assets/9d513da2-1cfc-4f48-af3c-2b2b3d7ab454)

- **Database Example**  
  ![Database example](https://github.com/user-attachments/assets/e527aa6b-43c6-4e7a-aa6c-2c6c03ef8764)

---

## Installation

Clone the repository:

```bash
git clone https://github.com/yourusername/roster-scraper-sms.git
cd roster-scraper-sms
```

### Install Dependencies

Ensure you have `pip` installed. Then, install the required Python packages:

```bash
pip install -r requirements.txt
```

### Set Up ClickSend Account

1. [Sign up for ClickSend](https://www.clicksend.com/au/) if you don’t have an account.
2. Obtain your API credentials.

### Set Up MariaDB

To enable logging and data storage, set up a MariaDB database and create the required `script_logs` table:

1. [Download MariaDB](https://mariadb.org/download/?t=mariadb&p=mariadb&r=11.5.2).
2. Configure your database and create tables as needed.

### Set Up Grafana

1. [Download Grafana](https://grafana.com/grafana/download?pg=get&plcmt=selfmanaged-box1-cta1).
2. Install and set up your Grafana instance.

---

## Usage

To run the scraper:

```bash
python3 roster_scraper.py --date YYYY-MM-DD
```

### Scheduling the Script

To automate execution, set up a cron job:

```bash
crontab -e
```

Add the following line to schedule the script to run every weekday at 2:00 PM:

```bash
0 14 * * 0-5 python3 roster_scraper.py >> log_roster_scraper.log 2>&1
```

---

## License

Distributed under the MIT License.
