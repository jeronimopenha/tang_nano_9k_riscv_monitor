from veriloggen import *
import util as _u
from components import Components


class Interface:
    _instance = None

    def __init__(
            self,
            data_width: int = 32,
            serial_width:int=8,
            ram_depth: int = 5,
            inst_ram_depth: int = 6,
    ):
        self.data_width = data_width
        self.ram_depth = ram_depth
        self.inst_ram_depth = inst_ram_depth
        self.serial_width = serial_width
        self.fifo_depth = 2

    def get(self):
        return self.__create_interface()

    '''
    led[0] - rx
    led[1] - rx_bsy
    led[2] - tx
    led[3] - tx_bsy
    led[4] - rst
    led[5] - running
    '''

    def __create_interface(self) -> Module:
        data_width = self.data_width
        serial_width = self.serial_width
        ram_depth = self.ram_depth
        inst_ram_depth = self.inst_ram_depth
        fifo_depth = self.fifo_depth
        comp = Components()

        m = Module(
            "tang_nano_9k_riscv_monitor")
        clk = m.Input('clk_27mhz')
        btn_rst = m.Input('button_s1')
        uart_rx = m.Input('uart_rx')
        led = m.Output('led', 6)
        uart_tx = m.Output('uart_tx')

        m.EmbeddedCode('// Reset signal control')
        rst = m.Wire('rst')
        running = m.Wire('running')
        rst.assign(~btn_rst)
        running.assign(~rst)

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
        m.EmbeddedCode('// led[5] = desligado')
        led[0].assign(uart_rx)
        led[1].assign(~rx_bsy)
        led[2].assign(uart_tx)
        led[3].assign(~tx_bsy)
        led[4].assign(~rst)
        led[5].assign(~running)

        m.EmbeddedCode('')
        m.EmbeddedCode('// I/O data protocol controller')

        m_aux = comp.create_io_riscv_controller()
        par = []
        con = [
            ('clk', clk),
            ('rst', ~btn_rst),
            ('rx', uart_rx),
            ('rx_bsy', rx_bsy),
            ('tx', uart_tx),
            ('tx_bsy', tx_bsy),
        ]
        m.Instance(m_aux, m_aux.name, par, con)

        _u.initialize_regs(m)
        return m


interface = Interface()
_int = interface.get()
_int.to_verilog("riscv.v")
# _int.to_verilog("./"+_int.name + ".v")
