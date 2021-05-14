" Global type hints "

from typing import Any, Callable, Dict, List, Union

from selenium.webdriver.remote.webelement import WebElement

from _pytest.main import Session  # Session Type
from _pytest.monkeypatch import MonkeyPatch
from py._path.local import LocalPath
from pytest_mock import MockerFixture as Mocker

JSONContent = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]

JSONType = Dict[str, JSONContent]

Cookies = List[JSONType]

ClassProperties = Dict[str, Union[Dict[str, str], None, Callable[[Any, ], Any]]]
