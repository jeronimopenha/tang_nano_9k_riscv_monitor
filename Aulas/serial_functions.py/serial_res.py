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
        self.listener = threading.Thread(
            target=self.listener_routine, args=[1,])
        self.port = pyftdi.serialext.serial_for_url(
            'ftdi://ftdi:2232:1/2', baudrate=3000000, bytesize=8, parity='N', stopbits=1, timeout=0.001)

    def listener_routine(self, name):
        data = None
        while not self.stop_flag:
            data = self.port.read()
            if data != b'':
                ret = int.from_bytes(data)
                # if ret == 0:
                # print('Par')
                # else:
                print(ret)

            time.sleep(0.01)

    def start_listener(self):
        self.stop_flag = False
        self.start_flag = True
        self.port.reset_input_buffer()
        self.port.reset_output_buffer()
        time.sleep(0.005)
        self.listener.start()

    def stop_listener(self):
        self.stop_flag = True

    def send_data(self, data):
        self.port.write(data)


u = UartInterface()
u.start_listener()

n = 0
print("Digite a quantidade de valores a serem enviados (max 255): ")
n = int(input())
u.send_data(int.to_bytes(n))
for i in range(n):
    print("Digite o %d valor (max 255): " % (i+1))
    val = int(input())
    u.send_data(int.to_bytes(val))
#u.send_data(int.to_bytes(val))
print()
time.sleep(1)
u.stop_listener()
