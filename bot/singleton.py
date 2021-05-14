from typing import Any, Callable, Dict, Tuple, Union

ClassProperties = Dict[str, Union[Dict[str, str], None, Callable[[Any, ], Any]]]


class MetaSingleton(type):
    """
    This is a Singleton metaclass. All classes affected by this metaclass
    have the property that only one instance is created for each set of
    arguments passed to the class constructor.

    Source: https://gist.github.com/rcalsaverini/3850065
    """

    def __init__(cls, name: str, bases: Tuple, a_dict: ClassProperties) -> None:

        super(MetaSingleton, cls).__init__(cls, bases, a_dict)

        cls._instanceDict = {}

    def __call__(cls, *args, **kwargs) -> object:

        argdict = {'args': args, 'kwargs': kwargs}
        argset = frozenset(argdict)

        if argset not in cls._instanceDict:
            cls._instanceDict[argset] = super(MetaSingleton, cls).__call__(*args, **kwargs)

        return cls._instanceDict[argset]
