import logging
from typing import Optional

import flask as fl
from sqlalchemy.orm import exc

from .common import db
from .models import BotSettings


def get_bot_settings(session: Optional[int] = None, app: Optional[fl.app.Flask] = None) -> Optional[BotSettings]:
    """
    Select first entry from settings table or create new one.
    Database exception except NoResultFound aren't handled.
    """

    session = session or db.session

    try:

        return session.query(BotSettings).one()

    except exc.NoResultFound:

        try:
            new_settings = BotSettings(day_money_limit=3000)
            session.add(new_settings)
            session.commit()

            return new_settings

        except Exception as e:

            if app:
                app.logger.error(e)
            else:
                logging.exception(e, exc_info=True)

            return None
