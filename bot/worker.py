# builtin imports
import os
from typing import Optional
from datetime import datetime
import logging
import platform  # chromedriver path
import random
import time
from ctypes import c_char_p  # share string between processes
from multiprocessing import Array, Manager, Process, Value

# third-party imports
import selenium
from fake_useragent import UserAgent

# local imports
from .cianbot import CianBot
from .bridge import DatabaseBridge
from settings import DRIVER_UNIX_PATH, DRIVER_WIN_PATH


class StopBotException(Exception):
    """
    Raised to stop the process.
    """
    pass


class BotWorker(object):
    """
    Low-level operator interacting with CianBot in multiprocessing.
    It has a bunch of shared variables that Manager will return to a client.

    Function calls sequence:

        start():        create new Process
            run_bot():      convinient wrapper to restart bot if it exists with Exception
                _run_bot():     create webdriver, instantiate CianBot ...
                    setup_bot():    load cookies, login on website, wait for phone code
                             ..:    infinitely iterate through new leads

    Attributes
    ----------
    signal_run: Value
    signal_quit: Value
    signal_launch: Value
    signal_phone_code: Value
    money_limit: Value
    money_left: Value
    purchased_leads: Array
        Array -> List[Tuple[str, datetime]] List of tuples with lead link and purchase timestamp
    """

    bridge: DatabaseBridge = None

    process: Process = None

    bot: CianBot = None

    driver: selenium.webdriver.chrome.webdriver.WebDriver = None

    signal_run: Value = None
    signal_quit: Value = None
    signal_launch: Value = None
    signal_phone_code: Value = None
    money_limit: Value = None
    money_left: Value = None
    purchased_leads: Array = None

    exc_on_exit: Exception = None

    def __init__(self, bridge: DatabaseBridge):

        manager = Manager()

        self.signal_run = Value("i", 0)
        self.signal_quit = Value("i", 1)
        self.signal_launch = Value("i", 0)
        self.signal_phone_code = Value("i", 0)
        self.money_left = Value("i", -1)
        self.money_limit = Value("i", 3000)

        self.purchased_leads = manager.list()
        self.signal_info = manager.Value(c_char_p, "Бот готов к работе.")
        self.exc_on_exit = manager.Value(c_char_p, "")

        self.bridge = bridge

        self.bridge.worker = self

    def message(self, message: str) -> None:
        """
        Store message to shared variable and log it on screen.
        """

        logging.info(message)
        self.signal_info.value = message

    def check_status(self) -> Optional[StopBotException]:
        """
        Raise StopBotException if signal to stop received.
        It will end in closing opened process.
        """
        if not self.signal_run.value:
            raise StopBotException()

        if 'captcha' in self.bot.current_url:

            self.wait_for_captcha()

    def wait_for_captcha(self) -> None:
        """
        Sleep until captcha is solved.
        """

        self.message("Требуется ввести каптчу. Бот остановлен.")

        while 'captcha' in self.bot.current_url:
            time.sleep(60)


    def start(self):
        """
        Top-level function creating the Process.
        """

        if self.process:

            self.message("Перезапускаю основной процесс ...")
            self.process.terminate()

        self.signal_launch.value = 1
        self.signal_run.value = 1
        self.signal_quit.value = 0
        self.signal_phone_code.value = 0

        self.message("Бот запускается ...")

        self.process = Process(target=self.run_bot)
        self.process.start()

    def run_bot(self) -> None:
        """
        Wrapper for main funciton.
        Handle KeyboardIterrupt and reset
        worker's signals on exit
        """

        try:
            self._run_bot()
        except KeyboardInterrupt:
            pass
        except StopBotException:
            pass
        finally:

            if self.exc_on_exit.value != "":
                # let send exception to a client
                time.sleep(10)
                self.run_bot()

            self.signal_run.value = 0
            self.signal_quit.value = 1

    def _run_bot(self) -> None:
        """
        Main worker function
        """

        self.message("Создаю новое окно браузера ... ")

        self.exc_on_exit.value = ""

        try:

            self.create_driver()

            self.bot = CianBot()

            self.bot.set_driver(self.driver)

            self.signal_launch.value = 0

            self.setup_bot()

            while True:

                if self.signal_quit.value:
                    break

                if not self.signal_run.value:
                    break

                print("Working...")

                settings = self.bridge.get_settings()

                # We need to be sure
                # That if today money_left should be updated
                # It did update
                self.bridge.update_settings(settings)

                if settings.money_left < 300:

                    self.not_enough_money()
                    continue

                self.check_status()

                self.message("Успешно авторизован, устанавливаю фильтры ... ")

                self.bot.set_filters()

                self.check_status()

                self.message(" Изучаю новые заявки ... ")

                try:

                    self.iter_leads(settings)

                except Exception as e:

                    logging.exception(e, exc_info=True)

                    self.message(str(e))

                hour = datetime.now().hour

                if hour > 6 and hour < 20:

                    self.message("Sleep less in the morning")

                    time_sleep = random.randint(25, 60)
                else:
                    time_sleep = random.randint(41, 80)

                self.check_status()

                time.sleep(time_sleep)

        except KeyboardInterrupt:
            pass

        except StopBotException:
            raise

        except Exception as e:

            self.message(f"Ошибка во время загрузки новых заявок: {e}")
            logging.exception(e, exc_info=True)

            self.exc_on_exit.value = str(e)

        finally:

            try:
                self.bot.quit()
            except Exception as e:
                logging.exception(e, exc_info=True)

            self.driver = None

            if self.exc_on_exit.value == "":
                self.message("Работа завершена корректно.")

    def iter_leads(self, settings) -> None:

        for purchased_lead_url in self.bot.iter_leads():

            print(purchased_lead_url)

            if purchased_lead_url == 'no-new-leads':

                # no new lead found
                self.message("Новых заявок пока нет")

                break

            # If saved successfully
            if self.bridge.save_lead(purchased_lead_url):

                self.message(f"Приобретена новая заявка: {purchased_lead_url}")

                settings.money_left -= 300

            settings = self.bridge.update_settings(settings)

            if settings.money_left < 300:

                self.not_enough_money()
                break

            time.sleep(random.randint(1, 3))

    def setup_bot(self) -> None:
        """
        Load bot's cookies
        Launch main page
        If phone confirmation code is required,
        wait until it's found in phone_code.txt file
        Then confirm and login.
        """

        self.check_status()

        self.message("Загружаю cookie-файлы")

        self.bot.load_cookies()

        self.check_status()

        self.message("Проверяю, выполнен ли вход в ЦИАН ... ")

        if not self.bot.is_logged_in():

            self.check_status()

            self.message("Вход не выполнен. Авторизуюсь ... ")

            login_without_code = self.bot.login()

            if not login_without_code:

                self.check_status()

                self.signal_phone_code.value = 1

                code = self.wait_for_code()

                logging.warning(f"Code received: {code}")

                self.signal_phone_code.value = 0

                self.bot.login_with_code(code)

        logging.info("Bot is logged successfully")

    def not_enough_money(self) -> None:
        """
        Log information to signal_info
        And set signal_run to False
        """

        self.message("Недостаточно средств для покупки новых заявок, бот остановлен")
        self.signal_run.value = 0

    def create_driver(self) -> None:

        if self.driver is not None:
            # Delete existing driver
            # And free up RAM

            del self.driver

            self.driver = None

        executable_path = DRIVER_UNIX_PATH if platform.system() == 'Linux' else DRIVER_WIN_PATH

        chrome_options = selenium.webdriver.ChromeOptions()

        userAgent = UserAgent().random

        chrome_options.add_argument("start-maximized")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument(f'user-agent={userAgent}')
        # chrome_options.headless = True

        self.driver = selenium.webdriver.Chrome(executable_path=executable_path, options=chrome_options)

    def wait_for_code(self) -> str:

        while True:

            self.check_status()

            try:

                logging.info("Reading code file")

                with open(os.environ['PHONE_CODE_PATH'], 'r') as f:

                    code = f.read().strip()

                    if len(code) == 4 and code.isdigit():

                        # Erase code
                        open(os.environ['PHONE_CODE_PATH'], 'w').close()
                        return code
                    else:
                        logging.info("Not valid code")

            except FileNotFoundError:
                open(os.environ['PHONE_CODE_PATH'], 'w').close()

            except Exception as e:
                logging.exception(e, exc_info=True)

            time.sleep(10)
