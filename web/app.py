# builtin imports
import logging
import os

# third-party imports
import flask as fl
from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate

from sqlalchemy.exc import OperationalError


# local imports
from bot.manager import CianBotManager
from settings import DATABASE_URI, STATIC_DIR
from .common import db


LOG_FORMAT = "[%(asctime)s] {%(pathname)s:%(lineno)d} | %(funcName)s | %(levelname)s - %(message)s"
logging.getLogger('werkzeug').setLevel(logging.WARNING)
logging.basicConfig(filename=os.environ['LOG_FILE_PATH'],
                    filemode='a+', level=logging.INFO, format=LOG_FORMAT)
logging.getLogger().addHandler(logging.StreamHandler())


bot = CianBotManager()

def create_app() -> fl.app.Flask:

    app = Flask(__name__, static_url_path='/static',
                static_folder=str(STATIC_DIR))

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
    # os.getenv('SQLALCHEMY_DATABASE_URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    from .models import User

    @login_manager.user_loader
    def load_user(user_id: str) -> User:
        """
        Since the user_id is just the primary key of our user table,
        Use it in the query for the user
        """
        return User.query.get(int(user_id))

    # blueprint for auth routes in our app
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    # blueprint for non-auth parts of app
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # register custom management commands
    from .commands import management_blueprint
    app.register_blueprint(management_blueprint)

    # If fails then it's a migration
    from .main import get_bot_settings

    try:
        with app.app_context():

            bot.set_money_day_limit(get_bot_settings().day_money_limit)

    except OperationalError as e:
        logging.exception(e, exc_info=True)

    return app


if __name__ == "__main__":

    app = create_app()
    migrate = Migrate(app, db)
