
class Singleton:
    """Base Singleton class"""

    def __new__(cls, *args, **kwds):
        """overriding __new__ method"""

        it = cls.__dict__.get("__it__")
        if it is not None:
            return it
        cls.__it__ = it = object.__new__(cls)
        it.init(*args, **kwds)
        return it

    def init(self, *args, **kwds):
        """set init method"""
        pass
