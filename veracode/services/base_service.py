from abc import ABC
from abc import abstractmethod


class Service(ABC):
    services = []
    test = "yes, it works"

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.services.append(cls())


    @abstractmethod
    def add_parser(self, parsers):
        pass

    @abstractmethod
    def execute(self, args, config, api, out):
        pass
