import click
from flask import Blueprint
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

from .common import db
from .models import User

management_blueprint = Blueprint('manage', __name__)


@management_blueprint.cli.command('create_user')
@click.argument('username')
@click.argument('password')
def create_user(username: str, password: str) -> None:
    """ Create a user with access to bot's settings """

    new_user = User(username=username, password=generate_password_hash(password, method='sha256'))

    try:
        db.session.add(new_user)
        db.session.commit()
    except IntegrityError:
        print(f"User with username {username} already exists")
    else:
        print(f"Create user: {username}")


@management_blueprint.cli.command('migrate')
def migrate() -> None:
    """ Migrate the database with Models """

    from .app import create_app

    db.create_all(app=create_app())
