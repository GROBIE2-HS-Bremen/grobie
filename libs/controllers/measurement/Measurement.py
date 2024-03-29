import libs.external.umsgpack as umsgpack

class Measurement:
    data: dict[str, float | int]

    def __init__(self, timestamp= None, **kwargs) -> None:
        self.data = kwargs
        self.timestamp = timestamp

    def encode(self):
        """ encode data to bytes """
        dump = {
            "timestamp": self.timestamp,
        }
        dump.update(self.data)

        return umsgpack.dumps(dump)

    @staticmethod
    def decode(bits: bytes):
        """ decode data from bytes """
        return Measurement(**umsgpack.loads(bits))

    def __str__(self):
        # convert to csv
        return ",".join([str(value) for value in self.data.values()])

    def __repr__(self) -> str:
        # convert data to json
        msg = "{"
        for key, value in self.data.items():
            msg += f"\"{key}\": {value}, "

        # remove the last comma and add closing bracket
        msg = msg[:-2]
        msg += "}"

        return msg
