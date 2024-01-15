import array
from libs.external.reedsolo import *

PRESET = 0xFFFF
POLYNOMIAL = 0xA001
CRC_LENGTH = 2


class CRC:
    def __init__(self):
        self.corrector = RSCodec(5)
        self.table = array.array("H", [self.table(i) for i in range(256)])

    def table(self, c: int):
        crc = c
        for j in range(8):
            if crc & 0x01:
                crc = (crc >> 1) ^ POLYNOMIAL
            else:
                crc = crc >> 1

        return crc

    def checksum(self, data: bytes):
        crc = PRESET
        for c in data:
            crc = (crc >> 8) ^ self.table[(crc ^ c) & 0xFF]

        return crc.to_bytes(CRC_LENGTH, 'big')

    def verify(self, data: bytes, checksum: bytes):
        return self.checksum(data) == checksum

    def encode(self, data: bytes):
        combine = data + self.checksum(data)

        return self.corrector.encode(combine)

    def decode(self, frame: bytes):
        try:
            decoded = self.corrector.decode(frame)[0]

            crc = decoded[-CRC_LENGTH:]
            data = decoded[:-CRC_LENGTH]

            if self.verify(data, crc):
                return data
            else:
                return None

        except reedsolo.ReedSolomonError:
            return None


crc = CRC()

# Encode data
original_data = b"hello world"
encoded_data = crc.encode(original_data)
print("Encoded data:", encoded_data)

print(len(encoded_data))

# Simulate errors
encoded_data[2] ^= 0xFF  # introduce an error

print("corrupt data:", encoded_data)

# Decode data
decoded_data = crc.decode(encoded_data)

if decoded_data is not None:
    print("Decoded data:", decoded_data)
else:
    print("Error: Unable to correct the data.")
