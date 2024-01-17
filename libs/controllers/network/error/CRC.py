import array

from libs.external.reedsolo import *
from libs.controllers.network.frame import FrameStructure


class CRC:
    def __init__(self):
        self.corrector = RSCodec(FrameStructure.correction_length)
        self.table = array.array("H", [CRC.table(i) for i in range(256)])

    @staticmethod
    def table(c: int) -> int:
        crc = c
        for j in range(8):
            if crc & 0x01:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc = crc >> 1

        return crc

    def checksum(self, data: bytes) -> bytes:
        crc = 0xFFFF
        for c in data:
            crc = (crc >> 8) ^ self.table[(crc ^ c) & 0xFF]

        return crc.to_bytes(FrameStructure.checksum_length, 'big')

    def verify(self, data: bytes, checksum: bytes) -> bool:
        print('verify checksum only: ', self.checksum(data))

        return self.checksum(data) == checksum

    def encode(self, data: bytes) -> bytearray:
        combine = data + self.checksum(data)

        print('encode data with checksum: ', combine)

        return self.corrector.encode(combine)

    def decode(self, frame: bytes) -> bytearray | None:
        try:
            decoded = self.corrector.decode(frame)[0]

            crc = decoded[-FrameStructure.checksum_length:]
            data = decoded[:-FrameStructure.checksum_length]

            if self.verify(data, crc):
                return data
            else:
                return None

        except reedsolo.ReedSolomonError:
            return None


# Testing
# crc = CRC()

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

# Decode data
# decoded_data = crc.decode(encoded_data)
#
# if decoded_data is not None:
#     print("Decoded data:", decoded_data)
# else:
#     print("Error: Unable to correct the data.")
