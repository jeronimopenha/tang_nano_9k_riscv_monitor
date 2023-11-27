from pyftdi.ftdi import Ftdi
import asyncio
import pyftdi.serialext
import time
import threading
from PIL import Image
from math import ceil, log2


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
                pass  # print(int.from_bytes(data))
            time.sleep(0.01)

    def start_listener(self):
        self.stop_flag = False
        self.start_flag = True
        self.port.reset_input_buffer()
        self.port.reset_output_buffer()
        #Stime.sleep(0.005)
        self.listener.start()

    def stop_listener(self):
        self.stop_flag = True

    def send_data(self, data):
        self.port.write(data)


u = UartInterface()
u.start_listener()

im = Image.open(
    "/home/jeronimo/Documentos/GIT/tang_nano_9k_riscv_monitor/teste_.bmp")
im.load()
height, widht = im.size

for row in range(height):
    for col in range(widht):
        a = im.getpixel((row, col))
        nr = int((a[0]/255)*32)
        ng = int((a[1]/255)*64)
        nb = int((a[2]/255)*32)
        h = 0x00  # (nr << 11) | (ng << 5) | nr
        h_lsb =0x1f
        ''' 11111 111111 11111 '''
        h_msb = (h >> 8) & 0xff
        u.send_data(h_msb.to_bytes(1))
        #time.sleep(0.005)
        u.send_data(h_lsb.to_bytes(1))
        #time.sleep(0.005)
        # u.send_data(int.to_bytes(0x0))


time.sleep(1)
u.stop_listener()
