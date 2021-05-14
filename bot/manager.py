# builtin imports
import os
import logging
from datetime import datetime
from typing import List, Tuple

# local imports

from .singleton import MetaSingleton
from .worker import BotWorker
from .bridge import DatabaseBridge


class CianBotManager(metaclass=MetaSingleton):
    """
    This class provides high-level interface to manipulate CianBot.
    It creates a botworker which process low level logic
    With multiprocessing and selenium webdriver.

    This class as well as botworker are created and accessiable
    In main process, but prefer not to use botworker directly
    """

    def __init__(self) -> None:

        logging.info("BotManager instantiated.")
        self._bridge = DatabaseBridge()
        self._worker = BotWorker(self._bridge)

    def set_money_day_limit(self, new_day_limit: int) -> None:
        self._worker.money_limit.value = new_day_limit

    def set_phone_code(self, phone_code: str) -> None:
        with open(os.environ['PHONE_CODE_PATH'], 'w') as f:
            f.write(phone_code)

    def run(self) -> None:

        if not self.is_running():

            if self._worker.signal_quit.value:
                logging.info("Bot started.")
                self._worker.start()

            self._worker.signal_quit.value = 0
            self._worker.signal_run.value = 1

    def stop(self) -> None:

        if self.is_running():
            self._worker.signal_run.value = 0
            logging.info("Bot stopped.")

    def quit(self) -> None:

        if not self.is_quited():
            self._worker.signal_quit = 1
            logging.info("Bot closed.")

    def is_running(self) -> bool:
        return bool(self._worker.signal_run.value)

    def is_launching(self) -> bool:
        return bool(self._worker.signal_launch.value)

    def is_quited(self) -> bool:
        return bool(self._worker.signal_quit.value)

    def get_info(self) -> str:
        return self._worker.signal_info.value

    def get_additional_dict(self) -> dict:
        return {'phone_code': self._worker.signal_phone_code.value}

    def get_status(self) -> str:

        if self.is_launching():
            return 'launching'
        elif self.is_running():
            return 'running'
        elif self._worker.exc_on_exit.value != "":
            return 'quited_with_error'
        elif self.is_quited():
            return 'quited'
        else:
            return 'stopped'

    def get_new_leads(self) -> List[Tuple[str, datetime]]:
        """
        Pop all new leads from worker's list

        Returns
        -------
        List[str]
            List with new Leads

        """

        if len(self._worker.purchased_leads) != 0:

            leads = list(self._worker.purchased_leads)

            # Reset list
            self._worker.purchased_leads[:] = []

            return leads

        return []

    def get_money_left(self) -> int:
        return self._worker.money_left.value

    def get_bot_error(self) -> str:
        return self._worker.exc_on_exit.value
