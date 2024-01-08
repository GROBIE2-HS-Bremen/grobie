from machine import UART, Pin
from utime import sleep_ms

MODE_NORMAL = 0
MODE_TRANSMIT_ONLY = 1
MODE_RECEIVE_ONLY = 2
MODE_CONFIG = 3
MODE_DEEP_SLEEP = 3

BAUD_RATES = {
    0x00: 1200,
    0x20: 2400,
    0x40: 4800,
    0x60: 9600,
    0x80: 19200,
    0xa0: 38400,
    0xc0: 57600,
    0xe0: 115200,
}

SERIAL_PARITY_BIT = {
    0x00: '8N1',
    0x08: '8O1',
    0x10: '8E1',
    0x18: '8N1',
}

AIR_RATE = {
    0x00: 2.4,
    0x01: 2.4,
    0x02: 2.4,
    0x03: 4.8,
    0x04: 9.6,
    0x05: 19.2,
    0x06: 38.4,
    0x07: 62.5,
}

SUB_PACKET = {
    0x00: 200,
    0x40: 128,
    0x80: 64,
    0xc0: 32,
}

TRANSMIT_POWER = {
    0x00: 22,
    0x01: 17,
    0x02: 13,
    0x03: 10,
}

WOR_CYCLE = {
    0x00: 500,
    0x01: 1000,
    0x02: 1500,
    0x03: 2000,
    0x04: 2500,
    0x05: 3000,
    0x06: 3500,
    0x07: 4000,
}

class E220:
    def __init__(self, uart: UART, m0: Pin, m1: Pin) -> None:
        self.serial = uart
        self.m0 = m0
        self.m1 = m1

        # All them configs
        self.address = b'\xff\xff'
        self.baud_rate = -1
        self.serial_parity_bit = 'unkown'
        self.air_rate = -1.0
        self.sub_packet = -1
        self.rssi_ambient_noice_enable = False
        self.transmit_power = -1
        self.channel = -1
        self.frequency = -1.0
        self.rssi_enabled = False
        self.transmission_method = False
        self.lbt_enabled = False
        self.wor_cycle = -1

    def __str__(self) -> str:
        return f"""Address:                    {self.address}
Baud Rate:                  {self.baud_rate}
Serial Parity Bit:          {self.serial_parity_bit}
Air Rate:                   {self.air_rate}K
Sub Packet:                 {self.sub_packet} bytes
RSSI Ambient Noice Enabled: {'yes' if self.rssi_ambient_noice_enable else 'no'}
Transmit Power:             {self.transmit_power}dBm
Channel:                    {self.channel}
Frequency:                  {self.frequency} MHz
RSSI Enabled:               {'yes' if self.rssi_enabled else 'no'}
Transmission Method:        {'Fixed transmission mode' if self.transmission_method else 'Transparent transmission mode'}
LBT Enabled:                {'yes' if self.lbt_enabled else 'no'}
WOR Cycle:                  {self.wor_cycle}ms"""

    def set_mode(self, mode: int) -> None:
        """ Change the mode
        """
        if mode == MODE_NORMAL:
            self.m0.low()
            self.m1.low()
        elif mode == MODE_TRANSMIT_ONLY:
            self.m0.high()
            self.m1.low()
        elif mode == MODE_RECEIVE_ONLY:
            self.m0.low()
            self.m1.high()
        elif mode == MODE_CONFIG:
            self.m0.value(1)
            self.m1.value(1)
        else:
            raise Exception('Unkown mode')
        self.serial.read()
        sleep_ms(100)

    def read(self) -> bytes:
        return self.serial.read()

    def write(self, text: bytes) -> None:
        self.serial.write(text)
        self.serial.flush()

    def send(self, address: bytes, text: bytes) -> None:
        self.write(b''.join([address, self.channel.to_bytes(1, 'little'), text]))

    def broadcast(self, text: bytes) -> None:
        self.send(b'\xff\xff', text)

    def get_settings(self) -> None:
        self.read()
        self.write(b'\xc1\x00\x06')
        sleep_ms(100)

        msg = self.read()
        if msg == None:
            raise Exception('did not receive a response from the module')

        self.address = msg[3:5]
        self.baud_rate = BAUD_RATES[msg[5] & 0xe0]
        self.serial_parity_bit = SERIAL_PARITY_BIT[msg[5] & 0x18]
        self.air_rate = AIR_RATE[msg[5] & 0x07]
        self.sub_packet = SUB_PACKET[msg[6] & 0xc0]
        self.rssi_ambient_noice_enable = msg[6] & 0x20 == 0x20
        self.transmit_power = TRANSMIT_POWER[msg[6] & 0x03]
        self.channel = msg[7]
        self.frequency = 850.125 + msg[7]
        self.rssi_enabled = msg[8] & 0x80 == 0x80
        self.transmission_method = msg[8] & 0x40 == 0x40
        self.lbt_enabled = msg[8] & 0x10 == 0x10
        self.wor_cycle = WOR_CYCLE[msg[8] & 0x07]

    def save(self) -> None:
        header = b'\xc0\x00\x06'

        baud_rate = [k for k, v in BAUD_RATES.items() if v == self.baud_rate]
        if len(baud_rate) is not 1:
            raise Exception('Baud rate not found')

        serial_parity_bit = [k for k, v in SERIAL_PARITY_BIT.items() if v == self.serial_parity_bit]
        if len(serial_parity_bit) is 0:
            raise Exception('seraial parity bit not found')

        air_rate = [k for k, v in AIR_RATE.items() if v == self.air_rate]
        if len(air_rate) is 0:
            raise Exception('Air rate not found')

        sub_packet = [k for k, v in SUB_PACKET.items() if v == self.sub_packet]
        if len(sub_packet) is not 1:
            raise Exception('Sub packet not found')

        transmit_power = [k for k, v in TRANSMIT_POWER.items() if v == self.transmit_power]
        if len(transmit_power) is not 1:
            raise Exception('Transmit power not found')

        wor_cycle = [k for k, v in WOR_CYCLE.items() if v == self.wor_cycle]
        if len(wor_cycle) is not 1:
            raise Exception('Wor cycle not found')

        reg02 = baud_rate[0] | serial_parity_bit[0] | air_rate[-1]
        reg03 = sub_packet[0] | (0x20 if self.rssi_ambient_noice_enable else 0x00) | transmit_power[0]
        reg05 = (0x80 if self.rssi_enabled else 0x00) | (0x40 if self.transmission_method else 0x00) | (0x10 if self.lbt_enabled else 0x00) | wor_cycle[0]

        self.write(b''.join([header, self.address, reg02.to_bytes(1, 'little'), reg03.to_bytes(1, 'little'), self.channel.to_bytes(1, 'little'), reg05.to_bytes(1, 'little')]))
        self.read()
