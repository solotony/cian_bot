from flask_login import login_user, logout_user, login_required, current_user

from flask import Blueprint, flash, redirect, render_template, request, url_for

from werkzeug.security import check_password_hash

from .common import db
from .models import User

auth = Blueprint('auth', __name__)


@auth.route('/login')
def login() -> str:

    if current_user.is_authenticated:
        return redirect(url_for('main.settings'))
    return render_template('login.html')


@auth.route('/login', methods=['POST'])
def login_post():

    username = request.form.get('username')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False

    user = User.query.filter_by(username=username).first()

    # check if the user actually exists
    # take the user-supplied password, hash it, and compare it to the hashed password in the database
    if not user or not check_password_hash(user.password, password):
        flash('Пожалуйста, проверьте корректность введённых данных')
        # if the user doesn't exist or password is wrong, reload the page
        return redirect(url_for('auth.login'))

    login_user(user, remember=remember)

    # if the above check passes, then we know the user has the right credentials

    return redirect(url_for('main.settings'))


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))
