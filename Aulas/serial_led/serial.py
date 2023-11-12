from pyftdi.ftdi import Ftdi
import asyncio
import pyftdi.serialext
import time
import random
import threading


class UartInterface:
    def __init__(self):
        self.stop_flag = False
        self.start_flag = False
        self.queue = asyncio.Queue()
        self.port = pyftdi.serialext.serial_for_url(
            'ftdi://ftdi:2232:1/2', baudrate=3000000, bytesize=8, parity='N', stopbits=1, timeout=0.001)

    def send_data(self, data):
        self.port.write(data)


u = UartInterface()

op = 0
while op != 65:
    print("Digite um número entre 0 e 63: ")
    op = int(input())
    u.send_data(int.to_bytes(op))
