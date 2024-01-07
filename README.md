# KEBA Wallbox Charge Importer for MySQL/MariaDB

These scripts are used to download a charge session report via Keba Wallbox's WebUI and import into a database.
Optional you can import rfid cards and wallbox stations. Existing entries will not be overwritten. 

> Feel inspired to adapt them to your needs. I made it so simple as i can.


## Prerequisites / Requirements

* MariaDB/MySQL Database Server
* Python3 with Modules from requirements.txt (BeautifulSoup, Requests, SQLAlchemy, Dotenv)
* For an OS independent installation a Python virtual environment or python docker container
* Tested with Keba P30 wallbox and rfid authentication


## Script processing and workflow

1. Open Wallbox WebUI
2. Get CSRF Token and Login with Username/Password
3. Charges: Request a csv export for the last 45 days and import new charges.
4. RFID Cards: Call web api (json) and import rfid cards.
5. Stations: Call web api (json) and import wallbox stations.

> Credentials are stored in .env environment file. See installation example.

## Installation Example

1. Install OS Packages (MariaDB)
2. Create database with custom user. You don't need to create tables by your self.
```bash
mysql -u root -p
CREATE DATABASE keba;
CREATE USER 'keba'@'localhost' IDENTIFIED BY 'secret-password';
GRANT ALL PRIVILEGES ON database.* TO 'keba'@'localhost';
FLUSH PRIVILEGES;
```
3. Install Python3 Venv with Modules.
```bash
python3 -m venv .venv
source venv .venv/bin/activate
pip install -r requirements.txt
```
4. Create configuration environment file `.env`.
```bash
# Wallbox Settings
KEBA_USER="admin"
KEBA_PASS="secret-password"
KEBA_HOST="192.168.1.1"

# Database Settings
DB_USERNAME="keba"
DB_PASSWORD="secret-password"
DB_DATABASE="keba"
DB_HOSTNAME="localhost"
DB_PORT=3306
```
5. Modify shebang (first line) on *get_report.py* for your python venv (Example: `#!/opt/keba/.venv/bin/python3`)
6. Optional: Modify your import time range from *lib/keba.py* `def gen_unix_date(days: int = 45)`.
7. Tables structures automatically created on first use.


## Execution

```bash
./get_report.py -h
usage: get_report.py [-h] [-c] [-r] [-s] [-w] [-v]

Keba Importer v20240101

options:
  -h, --help     show this help message and exit
  -c, --charge   import charge sessions from last 45 days
  -r, --rfid     import rfid cards
  -s, --station  import wallbox stations
  -w, --write    write reports to json files
  -a, --all      full import charges, stations, rfid cards
  -v, --version  show program version

```

```bash
# Import Charge Sessions
./get_report.py -c

# Import RFID Cards
./get_report.py -r

# Import Wallbox Stations
./get_report.py -r
```

## Cron Task Example

Daily Session Import, Cronjob 10.30
```
30 10 * * * /opt/keba/get_report.py -c
```
