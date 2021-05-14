import os
from dotenv import load_dotenv
from pathlib import Path
from typing import List

# Directories

BASE_DIR = Path(__file__).resolve().parent

load_dotenv()

SRC_DIR = BASE_DIR / 'src'

STATIC_DIR = BASE_DIR / 'web' / 'static'


# Database settings

DATABASE_URI = f"sqlite:///{SRC_DIR / 'web.sqlite'}"
TEST_DATABASE_URI = f"sqlite:///{SRC_DIR / 'tests.sqlite'}"


# Additional Files Settings

LOG_FILE_PATH = os.getenv('LOG_FILE_PATH', str(BASE_DIR / 'flask_logs.log'))

DRIVER_UNIX_PATH = '/usr/lib/chromium-browser/chromedriver'
DRIVER_WIN_PATH = SRC_DIR / 'chromedriver.exe'

os.environ['LOG_FILE_PATH'] = str(BASE_DIR / 'flask_logs.log')
os.environ['COOKIES_PATH'] = str(SRC_DIR / 'cookies.pkl')
os.environ['IGN_LEADS_PATH'] = str(SRC_DIR / 'ignored_leads.json')
os.environ['PHONE_CODE_PATH'] = str(SRC_DIR / 'phone_code.txt')

# URL Settings

LOGIN_PAGE = "http://cian.ru/"
LEADS_PAGE = "https://my.cian.ru/leads"

REGIONS: List[str] = ['Королев', 'Мытищи', 'Пушкино', 'Ивантеевка',
                      'Щёлково', 'Фрязино', 'Дмитров', 'Лобня',
                      'Долгопрудный', 'Химки', 'Москва']

# Bot Settings

CIAN_ID = os.getenv("CIAN_ID")
CIAN_PASSWORD = os.getenv("CIAN_PASSWORD")
CIAN_PHONE = os.getenv("CIAN_PHONE")


def second_bot_set():

    print("Called")

    os.environ['CIAN_ID'] = os.getenv('CIAN_ID_2')
    os.environ['CIAN_PASSWORD'] = os.getenv('CIAN_PASSWORD_2')

    os.environ['LOG_FILE_PATH'] = str(BASE_DIR / 'flask_logs_2.log')
    os.environ['COOKIES_PATH'] = str(SRC_DIR / 'cookies_2.pkl')
    os.environ['IGN_LEADS_PATH'] = str(SRC_DIR / 'ignored_leads_2.json')
    os.environ['PHONE_CODE_PATH'] = str(SRC_DIR / 'phone_code_2.txt')
