from codeop import Compile
from veriloggen import *
import util as _u
from components import Components


class Interface:
    _instance = None

    def __init__(
            self,
            data_width: int = 8,
            n_channel: int = 1,
            fifo_depth: int = 2
    ):
        self.data_width = data_width
        self.n_channel = n_channel
        self.fifo_depth = fifo_depth

    def get(self):
        return self.__create_interface()

    '''
    Base word of 64b for data transf
    Max data transfer width = 4MB

    PC->board
    0x00    request info 8b
    0x01    reset 8b
    0x02    send config - 8b + meta(8b) + 22b = 38b
    0x03    start 8b
    0x04    send data - 8b + meta(8b) + 64b = 72b
    0x05    data received 8b
    0x06    done rd received 8b
    0x07    done wr received 8b
    0x08    done acc received 8b

    board->pc
    0x00    send info 8b + 8b (nInput) + 8b(n_output) = 24b
    0x01    reseted 8b
    0x02    config received 8b
    0x03    started 8b
    0x04    request data 8b + meta(8b) = 16b
    0x05    send data - 8b + meta(8b) + 64b = 72b
    0x06    done rd 8b + meta(8b)
    0x07    dore wr 8b + meta(8b)
    0x08    done acc 8b + meta(8b)

    '''
    '''
    led[0] - rx
    led[1] - rx_bsy
    led[2] - tx
    led[3] - tx_bsy
    led[4] - rst
    led[5] - start
    '''

    def __create_interface(self) -> Module:
        data_width = self.data_width
        n_channel = self.n_channel
        fifo_depth = self.fifo_depth
        comp = Components(data_width, n_channel,  fifo_depth)

        m = Module(
            "tang_nano_9k_uart_interface_%dIO"%n_channel)
        clk = m.Input('clk_27mhz')
        btn_rst = m.Input('button_s1')
        uart_rx = m.Input('uart_rx')
        led = m.Output('led', 6)
        uart_tx = m.Output('uart_tx')

        m.EmbeddedCode('// Reset signal control')
        sw_rst = m.Wire('sw_rst')
        rst = m.Wire('rst')
        rst.assign(Uor(Cat(sw_rst, ~btn_rst)))

        m.EmbeddedCode('')
        m.EmbeddedCode('// Start signal control')
        start = m.Wire('start')

        m.EmbeddedCode('')
        m.EmbeddedCode('// rx signals and controls')
        rx_bsy = m.Wire('rx_bsy')

        m.EmbeddedCode('')
        m.EmbeddedCode('// tx signals and controls')
        tx_bsy = m.Wire('tx_bsy')

        m.EmbeddedCode('')
        m.EmbeddedCode(
            '// LED assigns. In this board the leds are activated by 0 signal')
        m.EmbeddedCode('// led[0] = rx')
        m.EmbeddedCode('// led[1] = rx_bsy')
        m.EmbeddedCode('// led[2] = tx')
        m.EmbeddedCode('// led[3] = tx_bsy')
        m.EmbeddedCode('// led[4] = rst')
        m.EmbeddedCode('// led[5] = start')
        led[0].assign(uart_rx)
        led[1].assign(~rx_bsy)
        led[2].assign(uart_tx)
        led[3].assign(~tx_bsy)
        led[4].assign(~rst)
        led[5].assign(~start)

        m.EmbeddedCode('')
        m.EmbeddedCode('// I/O data protocol controller')

        aux = comp.create_io_controller()
        par = []
        con = [
            ('clk', clk),
            ('rst', ~btn_rst),
            ('rx', uart_rx),
            ('tx', uart_tx),
            ('sw_rst', sw_rst),
            ('start', start),
        ]
        m.Instance(aux,aux.name,par,con)

        _u.initialize_regs(m)
        return m


interface = Interface()
_int = interface.get()
_int.to_verilog("/home/jeronimo/Documents/tang_projects/fpga_project/src/top_rxtx.v")
#_int.to_verilog("./"+_int.name + ".v")
