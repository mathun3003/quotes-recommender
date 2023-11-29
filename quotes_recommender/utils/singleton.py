from abc import abstractmethod
from typing import Any


class Singleton:
    """
    Base Singleton class

    Reference: https://www.python.org/download/releases/2.2/descrintro/#__new__
    """

    def __new__(cls, *args: Any, **kwargs: Any) -> "Singleton":
        """overriding __new__ method"""

        it_id = '__it__'
        it = cls.__dict__.get(it_id, None)
        if it is not None:
            return it
        it = object.__new__(cls)
        setattr(cls, it_id, it)
        it.init(*args, **kwargs)
        return it

    @abstractmethod
    def init(self, *args: Any, **kwargs: Any) -> None:
        """set init method"""
