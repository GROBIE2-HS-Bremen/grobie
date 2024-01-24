from libs.external.reedsolo import *

import array


class CRC:
    def __init__(self):
        self.corrector = RSCodec(5)
        self.table = array.array("H", [CRC.table(i) for i in range(256)])

    @staticmethod
    def table(c: int) -> int:
        crc = c
        for j in range(8):
            if crc & 0x01:
                crc = (crc >> 1) ^ 0x8408
            else:
                crc = crc >> 1

        return crc

    def checksum(self, data: bytes) -> bytes:
        crc = 0x0000
        for c in data:
            crc = (crc >> 8) ^ self.table[(crc ^ c) & 0xFF]

        return crc.to_bytes(2, 'big')

    def verify(self, data: bytes, checksum: bytes) -> bool:
        return self.checksum(data) == checksum

    def encode(self, data: bytes) -> bytearray:
        combine = data + self.checksum(data)

        return self.corrector.encode(combine)

    def decode(self, frame: bytes) -> bytearray | None:
        try:
            decoded = self.corrector.decode(frame)[0]

            crc = decoded[-2:]
            data = decoded[:-2]

            if self.verify(data, crc):
                return data
            else:
                return None

        except reedsolo.ReedSolomonError:
            return None

# # Testing
# crc = CRC()
#
# # Encode data
# original_data = b"hello world"
# encoded_data = crc.encode(original_data)
# print("Encoded data:", encoded_data)
#
# print(len(encoded_data))
#
# # Simulate errors
# encoded_data[2] ^= 0xFF  # introduce an error
# encoded_data[5] ^= 0xFF  # introduce an error
#
# print("corrupt data:", encoded_data)
#
# # Decode data
# decoded_data = crc.decode(encoded_data)
#
# if decoded_data is not None:
#     print("Decoded data:", decoded_data)
# else:
#     print("Error: Unable to correct the data.")
