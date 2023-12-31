from veriloggen import *
from math import ceil, log2
from general_components_full import GeneralComponents
import util_full as _u


class GeneralComponents:
    _instance = None

    def __new__(class_, *args, **kwargs):
        if not isinstance(class_._instance, class_):
            class_._instance = object.__new__(class_, *args, **kwargs)
        return class_._instance

    def __init__(self,
                 serial_width: int = 8):
        self.serial_width = serial_width
        self.components = GeneralComponents(serial_width=serial_width)
        self.cache = {}

    def get_io_riscv_controller(self, data_width: int = 32, fifo_depth: int = 2) -> Module:
        data_width = data_width
        fifo_depth = fifo_depth
        riscv = self.riscv
        monitor_tam = 32

        name = "io_riscv_controller"
        if name in self.cache.keys():
            return self.cache[name]
        m = Module(name)
        clk = m.Input('clk')
        rst = m.Input('rst')
        rx = m.Input('rx')
        rx_bsy = m.Output('rx_bsy')
        tx = m.Output('tx')
        tx_bsy = m.Output('tx_bsy')

        risc_rst = m.Reg('risc_rst')
        risc_clk = m.Reg('risc_clk')

        m.EmbeddedCode('')
        m.EmbeddedCode('// Instantiate the RX controller')
        rx_block_timeout = m.Wire('rx_block_timeout')
        rx_data_valid = m.Wire('rx_data_valid')
        rx_data_out = m.Wire('rx_data_out', 8)

        m.EmbeddedCode('')
        m.EmbeddedCode('// Instantiate the TX controller')
        tx_send_trig = m.Reg('send_trig')
        tx_send_data = m.Reg('send_data', 8)

        m.EmbeddedCode('')
        m.EmbeddedCode('// Instantiate the RX fifo')
        rx_fifo_we = m.Wire('rx_fifo_we')
        rx_fifo_in_data = m.Wire('rx_fifo_in_data', 8)
        rx_fifo_re = m.Reg('rx_fifo_re')
        rx_fifo_out_valid = m.Wire('rx_fifo_out_valid')
        rx_fifo_out_data = m.Wire('rx_fifo_out_data', 8)
        rx_fifo_empty = m.Wire('rx_fifo_empty')
        m.EmbeddedCode('// The Rx fifo is controlled by the uart_rx module')
        rx_fifo_we.assign(rx_data_valid)
        rx_fifo_in_data.assign(rx_data_out)
        m.EmbeddedCode('')

        m.EmbeddedCode('// Config and read data from riscv')
        monitor_addr = m.Reg('monitor_addr', 8)
        monitor_read_on = m.Reg('config_on')
        mem_dataout = m.Wire('mem_dataout', 8)
        reg_dataout = m.Wire('reg_dataout', 8)

        m.EmbeddedCode('')
        '''
            PC->board
            0x00    reset 8b
            0x01    exec clock - 8b + n_clocks
            
        '''
        m.EmbeddedCode('// PC to board protocol')
        PROT_PC_B_RESET = m.Localparam('PROT_PC_B_RESET', Int(0, 8, 16), 8)
        PROT_PC_B_CLOCK = m.Localparam('PROT_PC_B_CLOCK', Int(1, 8, 16), 8)

        m.EmbeddedCode('')
        m.EmbeddedCode('// IO and protocol controller')
        fsm_io = m.Reg('fsm_io', 4)
        FSM_IDLE = m.Localparam(
            'FSM_IDLE', Int(0, fsm_io.width, 16), fsm_io.width)
        FSM_DECODE_PROTOCOL = m.Localparam(
            'FSM_DECODE_PROTOCOL', Int(1, fsm_io.width, 16), fsm_io.width)
        FSM_RESET = m.Localparam(
            'FSM_RESET', Int(2, fsm_io.width, 16), fsm_io.width)
        FSM_EXEC_CLOCK = m.Localparam(
            'FSM_EXEC_CLOCK', Int(3, fsm_io.width, 16), fsm_io.width)
        FSM_SEND_REG_TAM = m.Localparam(
            'FSM_SEND_REG_TAM', Int(4, fsm_io.width, 16), fsm_io.width)
        FSM_SEND_REG_DATA = m.Localparam(
            'FSM_SEND_REG_DATA', Int(5, fsm_io.width, 16), fsm_io.width)
        FSM_SEND_REG_BYTES = m.Localparam(
            'FSM_SEND_REG_BYTES', Int(6, fsm_io.width, 16), fsm_io.width)
        FSM_SEND_MEM_TAM = m.Localparam(
            'FSM_SEND_MEM_TAM', Int(7, fsm_io.width, 16), fsm_io.width)
        FSM_SEND_MEM_DATA = m.Localparam(
            'FSM_SEND_MEM_DATA', Int(8, fsm_io.width, 16), fsm_io.width)
        FSM_SEND_MEM_BYTES = m.Localparam(
            'FSM_SEND_MEM_BYTES', Int(9, fsm_io.width, 16), fsm_io.width)

        m.Always(Posedge(clk))(
            If(rst)(
                fsm_io(FSM_IDLE),
                rx_fifo_re(Int(0, 1, 2)),
                risc_clk(Int(0, 1, 2)),
                risc_rst(Int(0, 1, 2)),
                tx_send_trig(Int(0, 1, 2)),
                monitor_read_on(Int(0, 1, 2)),
            ).Else(
                rx_fifo_re(Int(0, 1, 2)),
                risc_clk(Int(0, 1, 2)),
                risc_rst(Int(0, 1, 2)),
                tx_send_trig(Int(0, 1, 2)),
                Case(fsm_io)(
                    When(FSM_IDLE)(
                        If(~rx_fifo_empty)(
                            rx_fifo_re(Int(1, 1, 2)),
                            fsm_io(FSM_DECODE_PROTOCOL)
                        )
                    ),
                    When(FSM_DECODE_PROTOCOL)(
                        If(rx_fifo_out_valid)(
                            Case(rx_fifo_out_data)(
                                When(PROT_PC_B_RESET)(
                                    fsm_io(FSM_RESET)
                                ),
                                When(PROT_PC_B_CLOCK)(
                                    fsm_io(FSM_EXEC_CLOCK)
                                ),
                                When()(
                                    fsm_io(FSM_IDLE)
                                ),
                            ),
                        )
                    ),
                    When(FSM_RESET)(
                        risc_rst(Int(1, 1, 2)),
                        risc_clk(Int(1, 1, 2)),
                        fsm_io(FSM_IDLE)
                    ),
                    When(FSM_EXEC_CLOCK)(
                        risc_clk(Int(1, 1, 2)),
                        fsm_io(FSM_SEND_REG_TAM)
                    ),
                    When(FSM_SEND_REG_TAM)(
                        If(~tx_bsy)(
                            tx_send_trig(Int(1, 1, 2)),
                            tx_send_data(Int(monitor_tam, 8, 10)),
                            monitor_addr(Int(0, monitor_addr.width, 10)),
                            fsm_io(FSM_SEND_REG_DATA)
                        ),
                    ),
                    When(FSM_SEND_REG_DATA)(
                        If(monitor_addr == monitor_tam)(
                            monitor_read_on(Int(0, 1, 2)),
                            fsm_io(FSM_IDLE)
                        ).Else(
                            monitor_read_on(Int(1, 1, 2)),
                            fsm_io(FSM_SEND_REG_BYTES)
                        )
                    ),
                    When(FSM_SEND_REG_BYTES)(
                        If(~tx_bsy)(
                            monitor_addr(monitor_addr +
                                         Int(1, monitor_addr.width, 10)),
                            tx_send_trig(1),
                            tx_send_data(reg_dataout),
                            fsm_io(FSM_SEND_REG_DATA)
                        ),
                    ),
                    When(FSM_SEND_MEM_TAM)(
                        If(~tx_bsy)(
                            tx_send_trig(Int(1, 1, 2)),
                            tx_send_data(Int(monitor_tam, 8, 10)),
                            monitor_addr(Int(0, monitor_addr.width, 10)),
                            fsm_io(FSM_SEND_MEM_DATA)
                        ),
                    ),
                    When(FSM_SEND_MEM_DATA)(
                        If(monitor_addr == monitor_tam)(
                            monitor_read_on(Int(0, 1, 2)),
                            fsm_io(FSM_IDLE)
                        ).Else(
                            monitor_read_on(Int(1, 1, 2)),
                            fsm_io(FSM_SEND_MEM_BYTES)
                        )
                    ),
                    When(FSM_SEND_MEM_BYTES)(
                        If(~tx_bsy)(
                            monitor_addr(monitor_addr +
                                         Int(1, monitor_addr.width, 10)),
                            tx_send_trig(1),
                            tx_send_data(mem_dataout),
                            fsm_io(FSM_SEND_MEM_DATA)
                        ),
                    ),
                    When()(
                        fsm_io(FSM_IDLE)
                    )
                )
            )
        )

        m_aux = self.get_fifo()
        par = [
            ('FIFO_WIDTH', 8),
            ('FIFO_DEPTH_BITS', 5)
        ]
        con = [
            ('clk', clk),
            ('rst', rst),
            ('we', rx_fifo_we),
            ('in_data', rx_fifo_in_data),
            ('re', rx_fifo_re),
            ('out_valid', rx_fifo_out_valid),
            ('out_data', rx_fifo_out_data),
            ('empty', rx_fifo_empty)
        ]
        m.Instance(m_aux, 'rx_%s' % m_aux.name, par, con)

        m_aux = self.get_uart_rx()
        par = []
        con = [
            ('clk', clk),
            ('rst', rst),
            ('rx', rx),
            ('rx_bsy', rx_bsy),
            ('block_timeout', rx_block_timeout),
            ('data_valid', rx_data_valid),
            ('data_out', rx_data_out)
        ]
        m.Instance(m_aux, m_aux.name, par, con)

        m_aux = self.get_uart_tx()
        par = []
        con = [
            ('clk', clk),
            ('rst', rst),
            ('send_trig', tx_send_trig),
            ('send_data', tx_send_data),
            ('tx', tx),
            ('tx_bsy', tx_bsy),
        ]
        m.Instance(m_aux, m_aux.name, par, con)

        aux = riscv.get_riscv()
        par = []
        con = [
            ('clk', risc_clk),
            ('rst', risc_rst),
            ('monitor_read_on', monitor_read_on),
            ('monitor_addr', monitor_addr),
            ('mem_dataout', mem_dataout),
            ('reg_dataout', reg_dataout),
        ]

        m.Instance(aux, aux.name, par, con)

        _u.initialize_regs(m, {'tx': 1, 'risc_rst': 1})
        return m
