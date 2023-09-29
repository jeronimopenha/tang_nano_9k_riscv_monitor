from pyftdi.ftdi import Ftdi
import asyncio
import pyftdi.serialext
import time,random
import threading


class UartInterface:
    def __init__(self):
        self.stop_flag = False
        self.start_flag = False
        self.queue = asyncio.Queue()
        self.listener = threading.Thread(target=self.listener_routine, args=[1,])
        self.port = pyftdi.serialext.serial_for_url('ftdi://ftdi:2232:1/2', baudrate=3000000, bytesize=8, parity='N', stopbits=1, timeout=0.001)
        
    def listener_routine(self, name):
        data = None
        while not self.stop_flag:
            data = self.port.read()
            if(self.start_flag):
                if data == b'':
                    self.start_flag = False
            elif data != b'':
                print(data)
            time.sleep(0.5)
            

    def start_listener(self):
        self.stop_flag = False
        self.start_flag = True
        self.port.reset_input_buffer()
        time.sleep(0.0005)
        #self.listener = threading.Thread(target=self.listener_routine, args=[1,])
        self.listener.start()

    def stop_listener(self):
        self.stop_flag = True

    def send_data(self, data):
        self.port.write(data)

u = UartInterface()
u.start_listener()
#for i in range(10000):
u.send_data(chr(1))
#time.sleep(0.5)
u.send_data(chr(3))
time.sleep(2.0)
u.stop_listener()
a=1023
print(a.to_bytes(2,'big'))
'''import logging
import threading


def thread_function(name,a):
    logging.info("Thread %s: starting", name)
    time.sleep(2)
    logging.info("Thread %s: finishing", name)

if __name__ == "__main__":
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO,
                        datefmt="%H:%M:%S")

    logging.info("Main    : before creating thread")
    x = threading.Thread(target=thread_function, args=[1,])
    logging.info("Main    : before running thread")
    x.start()
    logging.info("Main    : wait for the thread to finish")
    # x.join()
    logging.info("Main    : all done")'''



#port = pyftdi.serialext.serial_for_url('ftdi://ftdi:2232:1/2', baudrate=3000000, bytesize=8, parity='N', stopbits=1, timeout=0.001)
#port.flush()
#time.sleep(0.0005)
#for i in range(10000):
#port.write(chr(3))
