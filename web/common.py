# builtin imports
import os
import sys
from pathlib import Path

# third-party imports
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy

# local imports
from settings import DATABASE_URI


os.environ['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI

# init SQLAlchemy so we can use it later in our models
db = SQLAlchemy()
