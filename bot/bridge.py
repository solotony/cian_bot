# builtin imports
import logging
from datetime import datetime, timedelta
from typing import Optional

# third-party imports
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# local imports
from settings import DATABASE_URI, LEADS_PAGE
from web.models import BotSettings, Lead
from web.utils import get_bot_settings


# Globally accessible Session
session_factory = sessionmaker(bind=create_engine(DATABASE_URI))
Session = scoped_session(session_factory)


class DatabaseBridge(object):
    """
    DatabaseBridge provides access to database to botworker.
    It helps save purchased leads and update bot settings.
    It also updates some of botworker shared variables.
    """

    worker = None

    def get_settings(self) -> BotSettings:
        return get_bot_settings(session=Session)

    def update_settings(self, settings: BotSettings) -> BotSettings:
        """
        Update settings' money_left with provided value
        Every time bot makes purchase.
        Update money_left to money_day_limit if it's a new day.

        Parameters
        ----------
        settings : "web.models.BotSettings"
            First row from settings table

        Returns
        -------
        web.models.BotSettings
            Patched settings instance

        """

        try:

            # Reset money_left
            # if it's update date
            if settings.next_update_date == datetime.now().date():

                settings.money_left = settings.day_money_limit
                settings.next_update_date += timedelta(days=1)

                self.worker.message("Дневной остаток средств обновлен")

            if settings.money_left < 0:
                settings.money_left = 0

            Session.commit()

        except Exception as e:

            Session.rollback()
            logging.exception(e, exc_info=True)

        finally:
            self.worker.money_left.value = settings.money_left
            return settings

    def save_lead(self, lead_url: str) -> Optional[Lead]:
        """
        Save lead to Database and
        Append it's URL and created time to worker's shared list

        Parameters
        ----------
        lead_url : str
            URL of purchased lead

        Returns
        -------
        Optional["Lead"]
            Return new Lead instance if saved successfully

        """

        try:
            # we receive purchased lead's url
            # i.e. https://my.cian.ru/leads/1504220/
            lead_id = lead_url.split('/')[-2]

            logging.info(f"Creating lead {lead_id}")

            lead = Lead(id=int(lead_id))
            Session.add(lead)
            Session.commit()

        except Exception as e:

            logging.exception(e, exc_info=True)

            Session.rollback()

            return None

        lead_link = LEADS_PAGE + f'/{lead.id}/'

        self.worker.purchased_leads.append([lead_link, lead.created_on])

        return lead
