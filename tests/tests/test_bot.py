from unittest import mock
from unittest.mock import MagicMock

import pytest

from bot.bridge import DatabaseBridge
from bot.cianbot import CianBot
from bot.worker import BotWorker
from typehints import Mocker

mock.patch('sqlalchemy.create_engine')


@pytest.fixture
def get_worker_and_bridge(mocker: Mocker):
    """
    Fixture to test bot inner logic without actually open selenium
    """

    def _get_worker_and_bridge():

        mocker.patch('bot.worker.selenium', autospec=True)
        mocker.patch('bot.worker.time.sleep', autospec=True)

        bridge = DatabaseBridge()

        worker = BotWorker(bridge)

        worker.bot = CianBot()

        return worker, bridge
    return _get_worker_and_bridge


def run_bot(self) -> None:
    """
    Function is used to test bot reloading when exception raised.
    Write exception to exc_on_exit so manager should reload bot.
    After three calls clear exception as it'd be a normal exit.

    Store call_count in bot itself.
    """

    if not hasattr(self, 'call_count'):
        self.call_count = 1

    if self.call_count == 3:
        self.exc_on_exit.value = ""
    else:
        self.call_count += 1
        self.exc_on_exit.value = "Exception raised!"


@pytest.mark.slow
def test_launch_bot(mocker: Mocker):
    """
    Test normal launch.
    Raise KeyboardInterrupt when manager starts to setup bot.
    """

    worker = BotWorker(DatabaseBridge())

    mocker.patch('bot.cianbot.CianBot.quit', new=lambda self: self.driver.quit())
    mocker.patch('bot.worker.BotWorker.setup_bot', side_effect=KeyboardInterrupt())

    worker.run_bot()


def test_reload_when_exception_raised(mocker: Mocker):
    """
    Test reloading mechanism. Bot will write exception to exc_on_exit
    We expect manager to restart it while exc_on_exit is not empty.
    We expect manager to quit if exc_on_exit is an empty string.
    """

    mocker.patch('bot.worker.BotWorker._run_bot', run_bot)
    mocker.patch('bot.worker.time.sleep', autospec=True)

    worker = BotWorker(DatabaseBridge())

    worker.run_bot()

    assert worker.call_count == 3


def test_fail_on_save_lead(get_worker_and_bridge, mocker: Mocker):
    """
    1, 2 or 3 is not a valid lead url, so bridge would fail to save it.
    We test that worker doesn't make message about new lead if it
    Cannot be saved.
    """

    worker, bridge = get_worker_and_bridge()

    settings = MagicMock()
    settings.money_left = 3000

    mock_message = mocker.patch('bot.worker.BotWorker.message', autospec=True)

    mocker.patch.object(worker.bot, 'iter_leads', return_value=range(3))

    worker.iter_leads(settings)

    assert not mock_message.called


def test_money_limit(get_worker_and_bridge, mocker: Mocker):
    """
    Bot would stop when money_left less than 300
    Bot spends 300 on every purchased lead.
    """

    worker, bridge = get_worker_and_bridge()

    settings = MagicMock()
    settings.money_left = 900

    mock_save = mocker.patch('bot.bridge.DatabaseBridge.save_lead', autospec=True)

    mocker.patch.object(worker.bot, 'iter_leads', return_value=range(4))

    worker.iter_leads(settings)

    assert mock_save.call_count == 3


def test_no_new_leads(get_worker_and_bridge, mocker: Mocker):
    """
    If bot receive 'no-new-leads' instead of lead id,
    it should exit from loop.
    """

    worker, bridge = get_worker_and_bridge()

    settings = MagicMock()
    settings.money_left = 3000

    mock_save = mocker.patch('bot.bridge.DatabaseBridge.save_lead', autospec=True)

    # Has enough money to purchase 10
    leads = (1, 2, 3, 'no-new-leads', 4, 5, 6, 7, 8, 9, 10)

    mocker.patch.object(worker.bot, 'iter_leads', return_value=leads)

    worker.iter_leads(settings)

    assert mock_save.call_count == 3
