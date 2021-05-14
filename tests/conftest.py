" Currently not used. But keep for the future. "

# from pathlib import Path
#
# import pytest
#
# from typehints import MonkeyPatch
#
#
# @pytest.fixture(autouse=True, scope='function')
# def set_database_path(monkeypatch: MonkeyPatch):
#     """
#     Inject database path before every test runs.
#     """
#
#     BASE_DIR = Path(__file__).resolve().parent.parent
#
#     URI = f"sqlite:///{BASE_DIR / 'tests' / 'tests.sqlite'}"
#
#     monkeypatch.setenv('SQLALCHEMY_DATABASE_URI', URI, prepend=False)
#
#     yield
