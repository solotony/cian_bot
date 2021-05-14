# built-in libraries
import os
import json  # save ignored leads
import logging
import os
import pickle
import time
from typing import Generator, List, Optional, Union, Any

# third-party libraries
from selenium.common import exceptions
from selenium.webdriver import chrome
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.expected_conditions import visibility_of_element_located as elem_visible
from selenium.webdriver.support.expected_conditions import presence_of_all_elements_located as elems_located
from selenium.webdriver.support.expected_conditions import element_to_be_clickable as elem_clickable
from selenium.webdriver.support.ui import WebDriverWait

# local libraries
from .singleton import MetaSingleton

from typehints import Cookies, WebElement


from settings import LOGIN_PAGE, LEADS_PAGE, REGIONS, CIAN_PHONE


class SeleniumOperator(object):
    """
    Operator class which holds low-level operations with Selenium WebDriver.
    Overwrite JS syntax with couple of functions.
    Contain functions to operate windows, tabs and cookies.
    """

    driver: chrome.webdriver.WebDriver = None

    @property
    def current_url(self) -> str:
        return self.driver.current_url

    def wait(self, timeout: int, *args: Any, **kw: Any) -> WebDriverWait:
        return WebDriverWait(self.driver, timeout, *args, **kw)

    def chain(self, *args: Any, **kw: Any) -> ActionChains:
        return ActionChains(self.driver, *args, **kw)

    def switch(self, index: int) -> None:
        self.driver.switch_to_window(self.driver.window_handles[index])

    def set_driver(self, driver: chrome.webdriver.WebDriver) -> None:
        """
        Set driver explicitly following Open-Closed Principle
        """

        if self.driver != driver:
            self.driver = driver

    def _enter_input(self, elem: Union[WebElement, str], value: str) -> None:

        if isinstance(elem, str):
            elem = self.driver.find_element_by_name(elem)

        elem.send_keys(value)
        elem.send_keys(Keys.ENTER)

    def load_cookies(self) -> None:
        """
        Loading cookies to current driver using pickle
        """

        logging.info("Loading cookies")

        if not os.path.exists(os.environ['COOKIES_PATH']):
            logging.warning("No cookies found")
            return

        try:
            # load cookies for given websites
            cookies: Cookies = pickle.load(open(os.environ['COOKIES_PATH'], "rb"))

            self.driver.get(LOGIN_PAGE)

            for cookie in cookies:
                self.driver.add_cookie(cookie)

            self.driver.refresh()

        except Exception as e:
            logging.exception(e, exc_info=True)

    def save_cookies(self) -> None:
        """
        Dump current browser's cookies to a file with pickle
        """

        logging.warning("Saving cookies")

        cookies: Cookies = self.driver.get_cookies()

        pickle.dump(cookies, open(os.environ['COOKIES_PATH'], "wb"))

    def close_all(self) -> None:
        """
        Close all tabs in current browser
        """

        if len(self.driver.window_handles) < 1:
            return

        for window_handle in self.driver.window_handles[:]:

            self.driver.switch_to.window(window_handle)
            self.driver.close()

    def quit(self) -> None:
        """
        Saving cookies and closing all tabs
        """

        self.switch(0)

        self.save_ignore_leads()
        self.save_cookies()

        # self.close_all()
        self.driver.quit()

        self.set_driver(None)


class CianBot(SeleniumOperator, metaclass=MetaSingleton):
    """
    CianBot made for automate buying leads
    """

    ignore_leads: List[str] = None

    def __init__(self) -> None:

        self.load_ignore_leads()

    def load_ignore_leads(self) -> None:
        """
        Load ignored leads' dates from json.
        """

        logging.info("Loading ignored leads ...")

        if os.stat(os.environ['IGN_LEADS_PATH']).st_size > 0:

            try:
                with open(os.environ['IGN_LEADS_PATH'], 'r') as f:
                    self.ignore_leads = json.loads(f.read())
                return

            except Exception as e:
                logging.exception(e, exc_info=True)

        # If file is empty or
        # Exception raised set to an empty list
        self.ignore_leads = []

    def save_ignore_leads(self) -> None:

        logging.info(f"Store {len(self.ignore_leads)} ignored leads")

        with open(os.environ['IGN_LEADS_PATH'], 'w') as f:
            f.write(json.dumps(self.ignore_leads))

    def is_connection_lost(self) -> bool:

        try:
            self.driver.find_element_by_xpath("//*[@data-name='ErrorPanelComponent']")
            return True
        except exceptions.NoSuchElementException:
            return False

    def is_logged_in(self, trg_url: Optional[str] = None) -> bool:
        """
        Check that login button is presented on login page

        Returns
        -------
        bool
            Whether user logged in or not

        """

        trg_url = trg_url or LOGIN_PAGE

        try:
            self.driver.get(trg_url)
            self.driver.find_element_by_id('login-btn')
            return False
        except exceptions.NoSuchElementException:
            return True

    def login(self, trg_url: Optional[str] = None) -> bool:
        """
        Fill username and password with values from environment.
        If it's a first time login, code will be required
        with blocking sync input()
        """

        print(os.environ['CIAN_ID'])

        trg_url = trg_url or LOGIN_PAGE

        # Getting target url loaded
        self.driver.get(trg_url)

        # Click on login button
        self.driver.find_element_by_id('login-btn').click()

        # Find username field with Email or ID input
        self._enter_input('username', os.environ['CIAN_ID'])

        # After hitting enter password field becomes available
        self._enter_input('password', os.environ['CIAN_PASSWORD'])

        try:

            # After entering password we should enter phone number
            # Associated with this Cian ID
            # input_phone = self.driver.find_element_by_name('phone')
            self.wait(5).until(elem_visible((By.NAME, 'phone')))

        except exceptions.TimeoutException:

            # When we already logged in after entering password
            # The page will be reloaded and we will be logged in
            if self.is_logged_in():
                logging.warning("Logged in without entering new code")
                return True

            raise

        input_phone = self.wait(5).until(elem_visible((By.NAME, 'phone')))

        self._enter_input(input_phone, CIAN_PHONE)
        # Need to enter phone validation code
        return False

    def login_with_code(self, code: str):

        input_code = self.wait(5).until(elem_visible((By.NAME, 'code')))

        input_code.send_keys(code)

    def set_filters(self) -> None:
        """
        Filtering leads on leads_url
        """

        if not self.is_logged_in(LEADS_PAGE):
            self.login(LEADS_PAGE)

        self.driver.get(LEADS_PAGE)

        # Check the box "Скрыть заявки от агентов"
        self.driver.find_element_by_xpath(
            ".//*[contains(text(), 'Скрыть заявки от агентов')]").click()

        # Change leads type to "Продать"

        dropdown_menu = self.driver.find_element_by_xpath(
            '//*[@aria-haspopup="listbox"]')

        dropdown_menu.click()

        dropdown_menu.send_keys(Keys.ARROW_DOWN)
        dropdown_menu.send_keys(Keys.ENTER)

        # Open all filters list

        all_filters = self.driver.find_element_by_xpath(
            '//*[@data-name="MoreFiltersBtn"]')

        all_filters.click()

        region_input = self.driver.find_element_by_id('geo-suggest-input')

        for region in REGIONS:

            region_input.send_keys(region)

            # wait for render the region autocomplete suggestions drop-down list
            region_suggestions = self.wait(5).until(elem_visible(
                (By.XPATH, "//*[contains(@class, 'group-container')]")))

            time.sleep(0.3)

            # Select first suggestion
            region_suggestions.find_element_by_xpath(
                "//*[contains(@class, 'item-selected')]").click()

            # Wait until it'll be added to choosen region list
            self.wait(5).until(elem_visible(
                (By.XPATH, "//*[contains(@class, 'tag_content')]")))

        # set object type

        object_type_dropdown = self.driver.find_element_by_xpath(
            "//div[@role='button' and @aria-haspopup='listbox' and .//*[text()='Любой объект']]"
        )

        object_type_dropdown.click()

        # Check first checkbox - flat type

        self.driver.find_element_by_xpath("//div[@role='option']").click()

    def refresh_leads(self) -> None:

        self.switch(0)

        submit_button = self.driver.find_element_by_xpath(
            '//button[@data-name="SubmitContainer"]')

        # selenium.common.exceptions.ElementClickInterceptedException
        # Click on submit button

        try:
            submit_button.click()
        except exceptions.ElementClickInterceptedException:
            self.driver.execute_script("arguments[0].click();", submit_button)

        time.sleep(1)

        if self.is_connection_lost():
            logging.info("Connection lost. Sleeping")
            time.sleep(120)
            self.set_filters()
            self.refresh_leads()

    def iter_leads(self) -> Generator[str, bool, None]:

        self.refresh_leads()

        # Iterate through lead cards
        # Implicitly wait for leads to load
        time.sleep(2)

        try:
            self.wait(5).until(elems_located((By.XPATH, '//*[@data-name="LeadsCardsWrapper"]')))

            leads: List[WebElement] = self.driver.find_elements_by_xpath('//div[@data-name="LeadsCardsWrapper"]')

        except exceptions.TimeoutException:

            logging.warning("No new leads found")

            yield 'no-new-leads'
            return False

        for lead in leads:

            try:

                # Open tab with leads list
                self.switch(0)

                lead_url = self.open_lead(lead)

                if lead_url == 'ignore-lead':
                    # Lead was cached and not opened

                    continue

                logging.warning(f"Purchased {lead_url}")

                self.driver.close()

                if lead_url is not None:

                    yield lead_url

            except exceptions.StaleElementReferenceException:

                yield 'no-new-leads'
                return False

            except Exception as e:
                logging.exception(e, exc_info=True)

    def open_lead(self, lead: WebElement) -> Optional[str]:

        # Move to current lead
        self.chain().move_to_element(lead).perform()

        lead_creation_time = lead.find_element_by_xpath(".//*[@data-name='SecondInfo']").find_element_by_xpath(".//span").text

        if lead_creation_time in self.ignore_leads:

            logging.warning(f"Lead {lead_creation_time} was ignored")

            return 'ignore-lead'

        # Open new tab with lead information

        open_lead = lead.find_element_by_xpath(
            './/button[@data-name="OpenLead"]')

        try:

            self.wait(10).until(elem_clickable((By.XPATH, '//button[@data-name="OpenLead"]')))
            open_lead.click()

        except exceptions.ElementClickInterceptedException as e:

            logging.exception(e, exc_info=True)
            self.driver.execute_script("arguments[0].click();", open_lead)

        self.switch(-1)

        # Check that nobody already bought it
        lead_price = self.driver.find_element_by_xpath(
            "//h3[contains(@class, 'header_text')]")

        if lead_price.text.startswith('100'):

            # Lead already in proccess
            logging.debug("Lead is already purchased by someone")

            self.ignore_leads.append(lead_creation_time)

            return None

        lead_locations = self.driver.find_element_by_xpath("//*[@data-mark='location']").find_elements_by_xpath(".//*")

        lead_location = " ".join([location.text for location in lead_locations])

        if not any(region in lead_location for region in REGIONS):

            logging.warning(f"Location {lead_location} is not what I want...")

            self.ignore_leads.append(lead_creation_time)

            return None

        try:

            # NOTE: Not tested functionality

            lead_type = self.driver.find_element_by_xpath("//*[@data-mark='demand_message-info_title']").text

            if not all(x in lead_type.lower() for x in ('продать', 'квартиру')):

                logging.warning(f"Lead {self.current_url} has improper type")

                return None

        except Exception as e:

            logging.exception(e, exc_info=True)


        # Open buy lead modal dialog

        open_buy_modal = self.driver.find_element_by_xpath(
            "//button[contains(@class, 'button_component-blue')]")

        open_buy_modal.click()

        buy_lead_btn = self.driver.find_element_by_xpath(
            "//button[contains(text(), 'Оплатить ')]")

        buy_lead_btn.click()

        time.sleep(1)
        logging.warning(f"Buy lead {self.current_url}")

        return self.current_url
