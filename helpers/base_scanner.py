from abc import ABC
from abc import abstractmethod


class Scanner(ABC):
    scanners = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.scanners.append(cls())

    @abstractmethod
    def configure(self, api):
        pass

    @abstractmethod
    def execute(self, api, activity, config):
        pass
