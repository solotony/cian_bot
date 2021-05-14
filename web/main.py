from typing import Optional, Union

from flask import (Blueprint, Response, jsonify, render_template, request,
                   send_from_directory)
from flask_login import current_user, login_required

from .common import db
from .app import bot
from .models import Lead
from .utils import get_bot_settings

main = Blueprint('main', __name__)


@main.route('/')
def index():
    return render_template('index.html')


def NoArgumentsError() -> Response:
    return Response("Error. No arguments passed", status=400, mimetype='application/json')


@main.route('/api')
@login_required
def bot_api() -> Optional[str]:
    """
    Main API called from settings.html with jQuery.
    Manage bot and database settings.
    """

    def check_status() -> str:

        if bot.get_money_left() == -1:
            # Bot do not initialized
            # No need to update money_left
            money_left = None
        else:
            money_left = bot.get_money_left()

        return jsonify(
                status=bot.get_status(),
                info=bot.get_info(),
                leads=bot.get_new_leads(),
                money_left=money_left,
                error=bot.get_bot_error(),
                **bot.get_additional_dict()
            )

    def set_money_limit() -> Union[NoArgumentsError, None]:

        new_day_limit = request.args.get('limit', default=None, type=int)

        if new_day_limit is None:

            return NoArgumentsError()

        get_bot_settings().day_money_limit = new_day_limit

        db.session.commit()

        bot.set_money_day_limit(new_day_limit)

    def set_phone_code() -> Union[str, None]:

        phone_code = request.args.get('phone_code', default='', type=str)

        if not len(phone_code) == 4:
            return jsonify(error='Неверная длина кода')
        elif not phone_code.isdigit():
            return jsonify(error='Код должен состоять из чисел')

        bot.set_phone_code(phone_code)

    def send_bot_settings() -> str:

        bot_settings = get_bot_settings(app=main)

        return jsonify(bot_settings.serialize())

    action = request.args.get('action', default=None, type=str)

    action_table = {
        'check': lambda: None,
        'check_status': check_status,
        'get_bot_settings': send_bot_settings,
        'set_money_limit': set_money_limit,
        'set_phone_code': set_phone_code,
        'run': bot.run,
        'stop': bot.stop
    }

    if action is None:
        return NoArgumentsError()

    try:
        resp = action_table[action]()
        return resp or jsonify(message="OK")

    except KeyError:
        return jsonify(error="unknown action.")

    except Exception as e:

        main.logger.error(e)
        return Response(str(e), status=500, mimetype='application/json')


@main.route('/settings')
@login_required
def settings():
    purchased_leads = Lead.query.order_by(Lead.created_on.desc()).all()
    return render_template('settings.html', username=current_user.username, purchased_leads=purchased_leads)


@main.route('/static/<path:path>')
def serve_static(path: str):
    return send_from_directory('static', path)
