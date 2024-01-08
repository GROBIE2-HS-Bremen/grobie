import array

PRESET = 0xFFFF
# bit reverse of 0x8005
POLYNOMIAL = 0xA001


class CRC:
    def __init__(self):
        self.__table = array.array("H", [self.__initial(i) for i in range(256)])

    # Create a single entry to the CRC table
    def __initial(self, c: int):
        crc = c
        for j in range(8):
            if crc & 0x01:
                crc = (crc >> 1) ^ POLYNOMIAL
            else:
                crc = crc >> 1

        return crc

    # Checksum calculation
    def checksum(self, data: str):
        crc = PRESET
        for c in bytes(data, 'utf-8'):
            crc = (crc >> 8) ^ self.__table[(crc ^ c) & 0xff]

        return hex(crc)

    def verify(self, data: str, checksum: str):
        return checksum == self.checksum(data)


# crc = CRC()
# data = bytes('Hello World', 'utf-8')
#
# print(crc.verify(data, '0xdaed'))
