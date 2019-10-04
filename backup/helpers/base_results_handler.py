from abc import ABC
from abc import abstractmethod


class ResultsHandler(ABC):
    handlers = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.handlers.append(cls())

    @abstractmethod
    def configure(self, api):
        pass

    @abstractmethod
    def execute(self, api, activity, config):
        pass
