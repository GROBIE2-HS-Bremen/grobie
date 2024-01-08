
class ISensor:
    def get_measurement(self) -> dict[str, int]:
        raise NotImplementedError('class {} does not implement get_measurement()'.format(self.__class__.__name__))