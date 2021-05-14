import logging

from dotenv import load_dotenv
from selenium import webdriver

from cianbot import CianBot

load_dotenv()


try:

    # Load chrome driver executable from current directory
    driver = webdriver.Chrome(options=webdriver.ChromeOptions())

    bot = CianBot(driver)

    bot.load_cookies()

    if not bot.is_logged_in():
        bot.login()
    else:
        logging.warning("Already logged in")

    bot.set_filters()

    bot.iter_leads()

except KeyboardInterrupt:

    pass

finally:

    bot.quit()
