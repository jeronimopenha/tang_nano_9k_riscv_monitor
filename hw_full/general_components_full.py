from veriloggen import *
from math import ceil, log2
import util_full as _u


class GeneralComponents:
    _instance = None

    def __init__(self,
                 serial_width: int = 8):
        self.serial_width = serial_width
        self.cache = {}

    def get_fifo(self, data_width: int = 8, fifo_depth: int = 2) -> Module:
        data_width = data_width
        fifo_depth = fifo_depth

        name = 'fifo'
        if name in self.cache.keys():
            return self.cache[name]
        m = Module(name)
        FIFO_WIDTH = m.Parameter('FIFO_WIDTH', data_width)
        FIFO_DEPTH_BITS = m.Parameter('FIFO_DEPTH_BITS', fifo_depth)
        FIFO_ALMOSTFULL_THRESHOLD = m.Parameter(
            'FIFO_ALMOSTFULL_THRESHOLD', Power(2, FIFO_DEPTH_BITS) - 2)
        FIFO_ALMOSTEMPTY_THRESHOLD = m.Parameter(
            'FIFO_ALMOSTEMPTY_THRESHOLD', 2)

        clk = m.Input('clk')
        rst = m.Input('rst')
        we = m.Input('we')
        in_data = m.Input('in_data', FIFO_WIDTH)
        re = m.Input('re')
        out_valid = m.OutputReg('out_valid')
        out_data = m.OutputReg('out_data', FIFO_WIDTH)
        empty = m.OutputReg('empty')
        almostempty = m.OutputReg('almostempty')
        full = m.OutputReg('full')
        almostfull = m.OutputReg('almostfull')
        data_count = m.OutputReg('data_count', FIFO_DEPTH_BITS + 1)

        read_pointer = m.Reg('read_pointer', FIFO_DEPTH_BITS)
        write_pointer = m.Reg('write_pointer', FIFO_DEPTH_BITS)

        mem = m.Reg('mem', FIFO_WIDTH, Power(2, FIFO_DEPTH_BITS))

        m.Always(Posedge(clk))(
            If(rst)(
                empty(1),
                almostempty(1),
                full(0),
                almostfull(0),
                read_pointer(0),
                write_pointer(0),
                data_count(0)
            ).Else(
                Case(Cat(we, re))(
                    When(3)(
                        read_pointer(read_pointer + 1),
                        write_pointer(write_pointer + 1),
                    ),
                    When(2)(
                        If(~full)(
                            write_pointer(write_pointer + 1),
                            data_count(data_count + 1),
                            empty(0),
                            If(data_count == (FIFO_ALMOSTEMPTY_THRESHOLD - 1))(
                                almostempty(0)
                            ),
                            If(data_count == Power(2, FIFO_DEPTH_BITS) - 1)(
                                full(1)
                            ),
                            If(data_count == (FIFO_ALMOSTFULL_THRESHOLD - 1))(
                                almostfull(1)
                            )
                        )
                    ),
                    When(1)(
                        If(~empty)(
                            read_pointer(read_pointer + 1),
                            data_count(data_count - 1),
                            full(0),
                            If(data_count == FIFO_ALMOSTFULL_THRESHOLD)(
                                almostfull(0)
                            ),
                            If(data_count == 1)(
                                empty(1)
                            ),
                            If(data_count == FIFO_ALMOSTEMPTY_THRESHOLD)(
                                almostempty(1)
                            )
                        )
                    ),
                )
            )
        )
        m.Always(Posedge(clk))(
            If(rst)(
                out_valid(0)
            ).Else(
                out_valid(0),
                If(we == 1)(
                    mem[write_pointer](in_data)
                ),
                If(re == 1)(
                    out_data(mem[read_pointer]),
                    out_valid(1)
                )
            )
        )
        self.cache[name] = m
        return m

    def get_uart_tx(self, sys_clock: float = 27.0, baudrate: float = 3.0) -> Module:
        serial_width = self.serial_width

        name = "uart_tx_%dHz_%dMbps" % (int(sys_clock), int(baudrate))
        if name in self.cache.keys():
            return self.cache[name]
        m = Module(name)
        clk = m.Input('clk')
        rst = m.Input('rst')
        send_trig = m.Input('send_trig')
        send_data = m.Input('send_data', serial_width)
        tx = m.OutputReg('tx')
        tx_bsy = m.OutputReg('tx_bsy')

        m.EmbeddedCode('// %dMHz' % sys_clock)
        m.EmbeddedCode('// %dMbps' % baudrate)

        CLKPERFRM = m.Localparam('CLKPERFRM', int(sys_clock/baudrate)*10)
        m.EmbeddedCode('// bit order is lsb-msb')
        TBITAT = m.Localparam('TBITAT', 1)
        m.EmbeddedCode('// START bit')
        BIT0AT = m.Localparam('BIT0AT', int(sys_clock/baudrate*1)+1)
        BIT1AT = m.Localparam('BIT1AT', int(sys_clock/baudrate*2)+1)
        BIT2AT = m.Localparam('BIT2AT', int(sys_clock/baudrate*3)+1)
        BIT3AT = m.Localparam('BIT3AT', int(sys_clock/baudrate*4)+1)
        BIT4AT = m.Localparam('BIT4AT', int(sys_clock/baudrate*5)+1)
        BIT5AT = m.Localparam('BIT5AT', int(sys_clock/baudrate*6)+1)
        BIT6AT = m.Localparam('BIT6AT', int(sys_clock/baudrate*7)+1)
        BIT7AT = m.Localparam('BIT7AT', int(sys_clock/baudrate*8)+1)
        PBITAT = m.Localparam('PBITAT', int(sys_clock/baudrate*9)+1)
        m.EmbeddedCode('// STOP bit')

        m.EmbeddedCode('')
        m.EmbeddedCode('// tx flow control ')
        tx_cnt = m.Reg('tx_cnt', ceil(log2(CLKPERFRM.value))+1)

        m.EmbeddedCode('')
        m.EmbeddedCode('// buffer')
        data2send = m.Reg('data2send', serial_width)
        frame_begin = m.Wire('frame_begin')
        frame_end = m.Wire('frame_end')
        frame_begin.assign(Uand(Cat(send_trig, ~tx_bsy)))
        frame_end.assign(Uand(Cat(tx_bsy, tx_cnt == CLKPERFRM)))

        m.Always(Posedge(clk))(
            If(rst)(
                tx_bsy(Int(0, 1, 2))
            ).Elif(frame_begin)(
                tx_bsy(Int(1, 1, 2))
            ).Elif(frame_end)(
                tx_bsy(Int(0, 1, 2))
            )
        )

        m.Always(Posedge(clk))(
            If(rst)(
                tx_cnt(Int(0, tx_cnt.width, 10))
            ).Elif(frame_end)(
                tx_cnt(Int(0, tx_cnt.width, 10))
            ).Elif(tx_bsy)(
                tx_cnt.inc()
            )
        )

        m.Always(Posedge(clk))(
            If(rst)(
                data2send(Int(0, data2send.width, 10))
            ).Else(
                data2send(send_data)
            )
        )

        m.Always(Posedge(clk))(
            If(rst)(
                tx(Int(1, 1, 2))
            ).Elif(tx_bsy)(
                Case(tx_cnt)(
                    When(TBITAT)(
                        tx(Int(0, 1, 2))
                    ),
                    When(BIT0AT)(
                        tx(data2send[0])
                    ),
                    When(BIT1AT)(
                        tx(data2send[1])
                    ),
                    When(BIT2AT)(
                        tx(data2send[2])
                    ),
                    When(BIT3AT)(
                        tx(data2send[3])
                    ),
                    When(BIT4AT)(
                        tx(data2send[4])
                    ),
                    When(BIT5AT)(
                        tx(data2send[5])
                    ),
                    When(BIT6AT)(
                        tx(data2send[6])
                    ),
                    When(BIT7AT)(
                        tx(data2send[7])
                    ),
                    When(PBITAT)(
                        tx(Int(0, 1, 2))
                    ),
                )
            ).Else(
                tx(Int(1, 1, 2))
            )
        )

        _u.initialize_regs(m, {'tx': 1})
        return m

    def get_uart_rx(self, sys_clock: float = 27.0, baudrate: float = 3.0) -> Module:
        serial_width = self.serial_width

        name = "uart_rx_%dHz_%dMbps" % (int(sys_clock), int(baudrate))
        if name in self.cache.keys():
            return self.cache[name]
        m = Module(name)
        clk = m.Input('clk')
        rst = m.Input('rst')
        rx = m.Input('rx')
        rx_bsy = m.OutputReg('rx_bsy')
        block_timeout = m.OutputReg('block_timeout')
        data_valid = m.OutputReg('data_valid')
        data_out = m.OutputReg('data_out', serial_width)

        m.EmbeddedCode('// %dMHz' % sys_clock)
        m.EmbeddedCode('// %dMbits' % baudrate)

        SYNC_DELAY = 2  # m.Localparam('SYNC_DELAY', 2)
        CLKPERFRM = m.Localparam('CLKPERFRM', int(
            sys_clock/baudrate*9.8)-SYNC_DELAY)
        m.EmbeddedCode('// bit order is lsb-msb')
        TBITAT = m.Localparam('TBITAT', int(sys_clock/baudrate*0.8)-SYNC_DELAY)
        m.EmbeddedCode('// START BIT')
        BIT0AT = m.Localparam('BIT0AT', int(sys_clock/baudrate*1.5)-SYNC_DELAY)
        BIT1AT = m.Localparam('BIT1AT', int(sys_clock/baudrate*2.5)-SYNC_DELAY)
        BIT2AT = m.Localparam('BIT2AT', int(sys_clock/baudrate*3.5)-SYNC_DELAY)
        BIT3AT = m.Localparam('BIT3AT', int(sys_clock/baudrate*4.5)-SYNC_DELAY)
        BIT4AT = m.Localparam('BIT4AT', int(sys_clock/baudrate*5.5)-SYNC_DELAY)
        BIT5AT = m.Localparam('BIT5AT', int(sys_clock/baudrate*6.5)-SYNC_DELAY)
        BIT6AT = m.Localparam('BIT6AT', int(sys_clock/baudrate*7.5)-SYNC_DELAY)
        BIT7AT = m.Localparam('BIT7AT', int(sys_clock/baudrate*8.5)-SYNC_DELAY)
        PBITAT = m.Localparam('PBITAT', int(sys_clock/baudrate*9.2)-SYNC_DELAY)
        m.EmbeddedCode('// STOP bit')
        BLK_TIMEOUT = m.Localparam('BLK_TIMEOUT', BIT1AT)
        m.EmbeddedCode('// this depends on your USB UART chip')

        m.EmbeddedCode('')
        m.EmbeddedCode('// rx flow control')
        rx_cnt = m.Reg('rx_cnt', ceil(log2(CLKPERFRM.value))+1)

        m.EmbeddedCode('')
        m.EmbeddedCode('//logic rx_sync')
        rx_hold = m.Reg('rx_hold')
        timeout = m.Reg('timeout')
        frame_begin = m.Wire('frame_begin')
        frame_end = m.Wire('frame_end')
        start_invalid = m.Wire('start_invalid')
        stop_invalid = m.Wire('stop_invalid')

        m.Always(Posedge(clk))(
            If(rst)(
                rx_hold(Int(0, 1, 2))
            ).Else(
                rx_hold(rx)
            )
        )

        m.EmbeddedCode('// negative edge detect')
        frame_begin.assign(Uand(Cat(~rx_bsy, ~rx, rx_hold)))
        m.EmbeddedCode('// final count')
        frame_end.assign(Uand(Cat(rx_bsy, rx_cnt == CLKPERFRM)))
        m.EmbeddedCode('// START bit must be low  for 80% of the bit duration')
        start_invalid.assign(Uand(Cat(rx_bsy, rx_cnt < TBITAT, rx)))
        m.EmbeddedCode('// STOP  bit must be high for 80% of the bit duration')
        stop_invalid.assign(Uand(Cat(rx_bsy, rx_cnt > PBITAT, ~rx)))

        m.Always(Posedge(clk))(
            If(rst)(
                rx_bsy(Int(0, 1, 2))
            ).Elif(frame_begin)(
                rx_bsy(Int(1, 1, 2))
            ).Elif(Uor(Cat(start_invalid, stop_invalid)))(
                rx_bsy(Int(0, 1, 2))
            ).Elif(frame_end)(
                rx_bsy(Int(0, 1, 2))
            )
        )

        m.EmbeddedCode('// count if frame is valid or until the timeout')
        m.Always(Posedge(clk))(
            If(rst)(
                rx_cnt(Int(0, rx_cnt.width, 10))
            ).Elif(frame_begin)(
                rx_cnt(Int(0, rx_cnt.width, 10))
            ).Elif(Uor(Cat(start_invalid, stop_invalid, frame_end)))(
                rx_cnt(Int(0, rx_cnt.width, 10))
            ).Elif(~timeout)(
                rx_cnt.inc()
            ).Else(
                rx_cnt(Int(0, rx_cnt.width, 10))
            )
        )

        m.EmbeddedCode('// this just stops the rx_cnt')
        m.Always(Posedge(clk))(
            If(rst)(
                timeout(Int(0, 1, 2))
            ).Elif(frame_begin)(
                timeout(Int(0, 1, 2))
            ).Elif(Uand(Cat(~rx_bsy, rx_cnt == BLK_TIMEOUT)))(
                timeout(Int(1, 1, 2))
            )
        )

        m.EmbeddedCode('// this signals the end of block uart transfer')
        m.Always(Posedge(clk))(
            If(rst)(
                block_timeout(Int(0, 1, 2))
            ).Elif(Uand(Cat(~rx_bsy, rx_cnt == BLK_TIMEOUT)))(
                block_timeout(Int(1, 1, 2))
            ).Else(
                block_timeout(Int(0, 1, 2))
            )
        )

        m.EmbeddedCode('// this pulses upon completion of a clean frame')
        m.Always(Posedge(clk))(
            If(rst)(
                data_valid(Int(0, 1, 2))
            ).Elif(frame_end)(
                data_valid(Int(1, 1, 2))
            ).Else(
                data_valid(Int(0, 1, 2))
            )
        )

        m.EmbeddedCode('// rx data control')
        m.Always(Posedge(clk))(
            If(rst)(
                data_out(Int(0, data_out.width, 10))
            ).Elif(rx_bsy)(
                Case(rx_cnt)(
                    When(BIT0AT)(
                        data_out[0](rx)
                    ),
                    When(BIT1AT)(
                        data_out[1](rx)
                    ),
                    When(BIT2AT)(
                        data_out[2](rx)
                    ),
                    When(BIT3AT)(
                        data_out[3](rx)
                    ),
                    When(BIT4AT)(
                        data_out[4](rx)
                    ),
                    When(BIT5AT)(
                        data_out[5](rx)
                    ),
                    When(BIT6AT)(
                        data_out[6](rx)
                    ),
                    When(BIT7AT)(
                        data_out[7](rx)
                    ),
                )
            )
        )

        _u.initialize_regs(m)
        return m

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

    def get_riscv(self, data_width: int = 32, ram_depth: int = 5, inst_ram_depth: int = 5) -> Module:

        name = "riscv_rd_%d_ird_%d" % (self.ram_depth, self.inst_ram_depth,)
        if name in self.cache.keys():
            return self.cache[name]
        m = Module(name)

        clk = m.Input("clk")
        rst = m.Input("rst")

        monitor_read_on = m.Input('monitor_read_on')
        monitor_write_on = m.Input('monitor_write_on')
        monitor_addr = m.Input('monitor_addr', 8)
        mem_dataout = m.Output('mem_dataout', 8)
        reg_dataout = m.Output('reg_dataout', 8)

        writedata = m.Wire('writedata', data_width)
        inst = m.Wire('inst', data_width)
        sigext = m.Wire('sigext', data_width)
        data1 = m.Wire('data1', data_width)
        data2 = m.Wire('data2', data_width)
        aluout = m.Wire('aluout', data_width)
        readdata = m.Wire('readdata', data_width)
        zero = m.Wire('zero')
        memread = m.Wire('memread')
        memwrite = m.Wire('memwrite')
        memtoreg = m.Wire('memtoreg')
        branch = m.Wire('branch')
        alusrc = m.Wire('alusrc')
        funct = m.Wire('funct', 10)
        aluop = m.Wire('aluop', 2)

        m.EmbeddedCode(
            '// adaptacao para a interface serial controlar a execução do riscV')
        m.EmbeddedCode('// estágio de memoria')
        mrd = m.Wire('mrd')
        maddr = m.Wire('maddr', data_width)
        mrd.assign(Uor(Cat(memread, monitor_read_on)))
        maddr.assign(Mux(monitor_read_on, Cat(
            Int(0, 24, 10), monitor_addr), aluout))
        mem_dataout.assign(readdata[0:8])
        m.EmbeddedCode('//*')
        m.EmbeddedCode('// estágio de decode')
        reg_dataout.assign(data1[0:8])
        m.EmbeddedCode('//*')
        m.EmbeddedCode('//*****')

        m_fetch = self.get_fetch(data_width=data_width)
        par = []
        con = [
            ('clk', clk),
            ('rst', rst),
            ('zero', zero),
            ('branch', branch),
            ('sigext', sigext),
            ('inst', inst)
        ]
        m.Instance(m_fetch, m_fetch.name, par, con)

        m_decode = self.get_decode(data_width=data_width)
        con = [
            ('clk', clk),
            ('inst', inst),
            ('writedata', writedata),
            ('data1', data1),
            ('data2', data2),
            ('immgen', sigext),
            ('alusrc', alusrc),
            ('memread', memread),
            ('memwrite', memwrite),
            ('memtoreg', memtoreg),
            ('branch', branch),
            ('aluop', aluop),
            ('funct', funct),
            ('monitor_read_on', monitor_read_on),
            ('monitor_addr', monitor_addr[0:5]),
        ]
        m.Instance(m_decode, m_decode.name, par, con)

        m_exec = self.get_execute()
        par = []
        con = [
            ('in1', data1),
            ('in2', data2),
            ('immgen', sigext),
            ('alusrc', alusrc),
            ('aluop', aluop),
            ('funct', funct),
            ('zero', zero),
            ('aluout', aluout),
        ]
        m.Instance(m_exec, m_exec.name, par, con)

        m_memory = self.get_memory()
        con = [
            ('clk', clk),
            ('address', maddr),
            ('writedata', data2),
            ('memread', mrd),
            ('memwrite', memwrite),
            ('readdata', readdata),
        ]
        m.Instance(m_memory, m_memory.name, par, con)

        m_writeback = self.get_writeback()
        con = [
            ('aluout', aluout),
            ('readdata', readdata),
            ('memtoreg', memtoreg),
            ('writedata', writedata),
        ]
        m.Instance(m_writeback, m_writeback.name, par, con)

        _u.initialize_regs(m)
        return m

    def get_fetch(self) -> Module:
        data_width: int = 32

        name = "fetch"
        if name in self.cache.keys():
            return self.cache[name]
        m = Module(name)

        clk = m.Input("clk")
        rst = m.Input("rst")
        zero = m.Input('zero')
        branch = m.Input('branch')
        sigext = m.Input('sigext', data_width)
        inst = m.Output('inst', data_width)

        pc = m.Wire('pc', data_width)
        pc_4 = m.Wire('pc_4', data_width)
        new_pc = m.Wire('new_pc', data_width)

        m.EmbeddedCode('')

        pc_4.assign(Int(4, data_width, 10) + pc)
        new_pc.assign(Mux(AndList(branch, zero), pc+sigext, pc_4))

        m_pc = self.get_pc()
        par = []
        con = [
            ('clk', clk),
            ('rst', rst),
            ('pc_in', new_pc),
            ('pc_out', pc)
        ]
        m.Instance(m_pc, m.name, par, con)

        m_memory = self.get_memory()
        con = [
            ('clk', clk),
            ('address', pc[2:data_width]),
            # ('writedata', data2),
            ('memread', Int(1, 1, 2)),
            ('memwrite', Int(0, 1, 2)),
            ('readdata', inst),
        ]
        m.Instance(m_memory, m_memory.name, par, con)

        '''
        sub x0,x0,x0
        sub x0,x0,x0
        addi x1,x0,1
        addi x2,x0,2
        addi x3,x0,3
        addi x4,x0,4
        addi x5,x0,5
        addi x6,x0,6
        addi x7,x0,7
        addi x8,x0,8
        addi x9,x0,9
        addi x10,x0,10
        addi x11,x0,11
        sub x5,x5,x5
        sub x3,x3,x3
        sub x8,x8,x8
        addi x2,x0,2
        addi x9,x0,9
        add x7,x2,x9
        '''

        '''
        40000033 40000033 00100093
        00200113
        00300193
        00400213
        00500293
        00600313
        00700393
        00800413
        00900493
        00a00513
        00b00593
        405282b3
        403181b3
        40840433
        00200113
        00900493
        009103b3

        '''

        # _u.initialize_regs(m)

        self.cache[name] = m
        return m

    def get_pc(self) -> Module:
        data_width = 32

        name = "pc"
        if name in self.cache.keys():
            return self.cache[name]
        m = Module(name)

        clk = m.Input("clk")
        rst = m.Input("rst")
        pc_in = m.Input("pc_in", data_width)
        pc_out = m.OutputReg("pc_out", data_width)

        m.Always(Posedge(clk))(
            pc_out(pc_in),
            If(rst)(
                pc_out(Int(0, pc_out.width, 10))
            )
        )
        self.cache[name] = m

        _u.initialize_regs(m)

        return m

    def get_decode(self) -> Module:
        data_width = 32
        reg_add_width = 5

        name = "decode"
        if name in self.cache.keys():
            return self.cache[name]
        m = Module(name)

        clk = m.Input("clk")
        inst = m.Input("inst", data_width)
        writedata = m.Input("writedata", data_width)
        data1 = m.Output('data1', data_width)
        data2 = m.Output('data2', data_width)
        immgen = m.Output('immgen', data_width)
        alusrc = m.Output('alusrc')
        memread = m.Output('memread')
        memwrite = m.Output('memwrite')
        memtoreg = m.Output('memtoreg')
        branch = m.Output('branch')
        aluop = m.Output('aluop', 2)
        funct = m.Output('funct', 10)

        monitor_read_on = m.Input('monitor_read_on')
        monitor_addr = m.Input('monitor_addr', 5)

        regwrite = m.Wire('regwrite')
        # writereg = m.Wire('writereg', reg_add_width)
        rs1 = m.Wire('rs1', reg_add_width)
        rs2 = m.Wire('rs2', reg_add_width)
        rd = m.Wire('rd', reg_add_width)
        opcode = m.Wire('opcode', 7)
        funct7 = m.Wire('funct7', 7)
        funct3 = m.Wire('funct3', 3)

        m.EmbeddedCode('')
        opcode.assign(inst[0:7])
        rs1.assign(inst[15:20])
        rs2.assign(inst[20:25])
        rd.assign(inst[7:12])
        funct7.assign(inst[25:32])
        funct3.assign(inst[12:15])
        funct.assign(Cat(funct7, funct3))

        m.EmbeddedCode(
            '// adaptacao para a interface serial controlar a execução do riscV')
        rraddr = m.Wire('raddr', 5)
        rraddr.assign(Mux(monitor_read_on, monitor_addr, rs1))
        m.EmbeddedCode('// *****')

        m_uc = self.get_control_unit()
        par = []
        con = [
            ('opcode', opcode),
            ('inst', inst),
            ('alusrc', alusrc),
            ('memtoreg', memtoreg),
            ('regwrite', regwrite),
            ('memread', memread),
            ('memwrite', memwrite),
            ('branch', branch),
            ('aluop', aluop),
            ('immgen', immgen)
        ]
        m.Instance(m_uc, m_uc.name, par, con)

        m_reg_bank = self.get_register_bank()
        con = [
            ('clk', clk),
            ('regwrite', regwrite),
            ('read_reg1', rraddr),
            ('read_reg2', rs2),
            ('write_reg', rd),
            ('writedata', writedata),
            ('read_data1', data1),
            ('read_data2', data2),
        ]
        m.Instance(m_reg_bank, m_reg_bank.name, par, con)

        _u.initialize_regs(m)

        self.cache[name] = m
        return m

    def get_control_unit(self) -> Module:
        data_width = 32

        name = "control_unit"
        if name in self.cache.keys():
            return self.cache[name]
        m = Module(name)

        opcode = m.Input('opcode', 7)
        inst = m.Input('inst', data_width)
        alusrc = m.OutputReg('alusrc')
        memtoreg = m.OutputReg('memtoreg')
        regwrite = m.OutputReg('regwrite')
        memread = m.OutputReg('memread')
        memwrite = m.OutputReg('memwrite')
        branch = m.OutputReg('branch')
        aluop = m.OutputReg('aluop', 2)
        immgen = m.OutputReg('immgen', data_width)

        m.EmbeddedCode('')
        catbits = m.Wire('catbits', 19)
        catbits.assign(Mux(inst[31], Int(
            (2**catbits.width)-1, catbits.width, 2), Int(0, catbits.width, 2)))

        m.EmbeddedCode('')
        R_TYPE = m.Localparam('R_TYPE', Int(51, opcode.width, 2))
        BEQ = m.Localparam('BEQ', Int(99, opcode.width, 2))
        ADDI_SLTI_XORI = m.Localparam(
            'ADDI_SLTI_XORI', Int(19, opcode.width, 2))
        LW = m.Localparam('LW', Int(3, opcode.width, 2))
        SW = m.Localparam('SW', Int(35, opcode.width, 2))

        m.Always()(
            alusrc(Int(0, 1, 10)),
            memtoreg(Int(0, 1, 10)),
            regwrite(Int(0, 1, 10)),
            memread(Int(0, 1, 10)),
            memwrite(Int(0, 1, 10)),
            branch(Int(0, 1, 10)),
            aluop(Int(0, aluop.width, 10)),
            immgen(Int(0, immgen.width, 10)),
            Case(opcode)(
                When(R_TYPE)(
                    regwrite(Int(1, 1, 10)),
                    aluop(Int(2, aluop.width, 10))
                ),
                When(BEQ)(
                    branch(Int(1, 1, 10)),
                    aluop(Int(1, aluop.width, 10)),
                    immgen(
                        Cat(catbits, inst[31], inst[7], inst[25:31], inst[8:12], Int(0, 1, 2)))
                ),
                When(ADDI_SLTI_XORI)(
                    alusrc(Int(1, 1, 10)),
                    regwrite(Int(1, 1, 10)),
                    aluop(Int(3, aluop.width, 10)),
                    immgen(Cat(inst[31], catbits, inst[20:32]))
                ),
                When(LW)(
                    alusrc(Int(1, 1, 10)),
                    memtoreg(Int(1, 1, 10)),
                    regwrite(Int(1, 1, 10)),
                    memread(Int(1, 1, 10)),
                    immgen(Cat(inst[31], catbits, inst[20:32]))
                ),
                When(SW)(
                    alusrc(Int(1, 1, 10)),
                    memwrite(Int(1, 1, 10)),
                    immgen(Cat(inst[31], catbits, inst[25:32], inst[7:12]))
                ),
            )

        )

        _u.initialize_regs(m)

        self.cache[name] = m
        return m

    def get_register_bank(self) -> Module:
        data_width = 32
        reg_add_width = 5
        n_regs = 32

        name = "register_bank"
        if name in self.cache.keys():
            return self.cache[name]
        m = Module(name)

        clk = m.Input('clk')
        regwrite = m.Input('regwrite')
        read_reg1 = m.Input('read_reg1', reg_add_width)
        read_reg2 = m.Input('read_reg2', reg_add_width)
        write_reg = m.Input('write_reg', reg_add_width)
        writedata = m.Input('writedata', data_width)
        read_data1 = m.Output('read_data1', data_width)
        read_data2 = m.Output('read_data2', data_width)

        reg_bank = m.Reg('reg_bank', data_width, n_regs)

        m.EmbeddedCode('')

        read_data1.assign(reg_bank[read_reg1])
        read_data2.assign(reg_bank[read_reg2])

        m.Always(Posedge(clk))(
            If(regwrite)(
                reg_bank[write_reg](writedata)
            )
        )

        self.cache[name] = m

        _u.initialize_regs(m)

        return m

    def get_execute(self) -> Module:
        data_width = 32

        name = "execute"
        if name in self.cache.keys():
            return self.cache[name]
        m = Module(name)

        in1 = m.Input('in1', data_width)
        in2 = m.Input('in2', data_width)
        immgen = m.Input('immgen', data_width)
        alusrc = m.Input('alusrc')
        aluop = m.Input('aluop', 2)
        funct = m.Input('funct', 10)
        zero = m.Output('zero')
        aluout = m.Output('aluout', data_width)

        alu_b = m.Wire('alub', data_width)
        aluctrl = m.Wire('aluctrl', 4)

        m.EmbeddedCode('')

        alu_b.assign(Mux(alusrc, immgen, in2))
        zero1 = m.Wire('zero1')
        f3 = m.Wire('f3', 3)
        f3.assign(funct[0:3])

        zero.assign(
            Mux(f3 == Int(0, f3.width, 2), zero1,
                Mux(f3 == Int(1, f3.width, 2), ~zero1,
                    Mux(f3 == Int(4, f3.width, 2), aluout[31],
                        Mux(f3 == Int(5, f3.width, 2), ~aluout[31],
                            Mux(f3 == Int(6, f3.width, 2), in1 < alu_b,
                                Mux(f3 == Int(7, f3.width, 2), ~(in1 < alu_b), 0)
                                )
                            )
                        )
                    )
                )
        )

        m_alucontrol = self.get_alucontrol()
        par = []
        con = [
            ('aluop', aluop),
            ('funct', funct),
            ('alucontrol', aluctrl),
        ]
        m.Instance(m_alucontrol, m_alucontrol.name, par, con)

        m_alu = self.get_alu()
        con = [
            ('alucontrol', aluctrl),
            ('a', in1),
            ('b', alu_b),
            ('aluout', aluout),
            ('zero', zero1),
        ]
        m.Instance(m_alu, m_alu.name, par, con)

        _u.initialize_regs(m)

        self.cache[name] = m
        return m

    def get_alucontrol(self) -> Module:
        name = "alucontrol"
        if name in self.cache.keys():
            return self.cache[name]
        m = Module(name)

        aluop = m.Input('aluop', 2)
        funct = m.Input('funct', 10)
        alucontrol = m.OutputReg('alucontrol', 4)

        funct7 = m.Wire('funct7', 8)
        funct3 = m.Wire('funct3', 3)
        aluopcode = m.Wire('aluopcode', 4)

        m.EmbeddedCode('')

        ADD_TO_SW_AND_LW = m.Localparam(
            'ADD_TO_SW_AND_LW', Int(0, aluop.width, 10))
        SUB_TO_BRANCH = m.Localparam('SUB_TO_BRANCH', Int(1, aluop.width, 10))
        ADD_SUB = m.Localparam('ADD_SUB', Int(0, funct3.width, 10))
        SLL = m.Localparam('SLL', Int(1, funct3.width, 10))
        SLT = m.Localparam('SLT', Int(2, funct3.width, 10))
        SLTU = m.Localparam('SLTU', Int(3, funct3.width, 10))
        XOR = m.Localparam('XOR', Int(4, funct3.width, 10))
        SRA_SRL = m.Localparam('SRA_SRL', Int(5, funct3.width, 10))
        OR = m.Localparam('OR', Int(6, funct3.width, 10))
        AND = m.Localparam('AND', Int(7, funct3.width, 10))
        ADDI = m.Localparam('ADDI', Int(0, funct3.width, 10))

        m.EmbeddedCode('')

        funct3.assign(funct[0:3])
        funct7.assign(funct[3:10])
        aluopcode.assign(Cat(funct[5], funct3))

        m.Always()(
            Case(aluop)(
                When(ADD_TO_SW_AND_LW)(
                    alucontrol(Int(2, alucontrol.width, 10))

                ),
                When(SUB_TO_BRANCH)(
                    alucontrol(Int(6, alucontrol.width, 10))
                ),
                When(Int(2, aluop.width, 10))(
                    Case(funct3)(
                        When(ADD_SUB)(
                            alucontrol(Mux(funct7 == 0, Int(2, alucontrol.width, 10),
                                           Int(6, alucontrol.width, 10)))
                        ),
                        When(SLL)(
                            alucontrol(Int(3, alucontrol.width, 10))
                        ),
                        When(SLT)(
                            alucontrol(Int(7, alucontrol.width, 10))
                        ),
                        When(SLTU)(
                            alucontrol(Int(9, alucontrol.width, 10))
                        ),
                        When(XOR)(
                            alucontrol(Int(4, alucontrol.width, 10))

                        ),
                        When(SRA_SRL)(
                            alucontrol(
                                Mux(funct7[5], Int(5, alucontrol.width, 10), Int(8, alucontrol.width, 10)))
                        ),
                        When(OR)(
                            alucontrol(Int(1, alucontrol.width, 10))
                        ),
                        When(AND)(
                            alucontrol(Int(0, alucontrol.width, 10))
                        ),
                        When()(
                            alucontrol(Int(15, alucontrol.width, 10))
                        ),
                    )
                ),
                When(Int(3, aluop.width, 10))(
                    Case(funct3)(
                        When(ADDI)(
                            alucontrol(Int(2, alucontrol.width, 10))
                        ),
                        When(SLL)(
                            alucontrol(Int(3, alucontrol.width, 10))
                        ),
                        When(SLT)(
                            alucontrol(Int(7, alucontrol.width, 10))
                        ),
                        When(SLTU)(
                            alucontrol(Int(9, alucontrol.width, 10))
                        ),
                        When(XOR)(
                            alucontrol(Int(4, alucontrol.width, 10))
                        ),
                        When(SRA_SRL)(
                            alucontrol(
                                Mux(funct7[5], Int(5, alucontrol.width, 10), Int(8, alucontrol.width, 10)))
                        ),
                        When(OR)(
                            alucontrol(Int(1, alucontrol.width, 10))
                        ),
                        When(AND)(
                            alucontrol(Int(0, alucontrol.width, 10))
                        ),
                        When()(
                            alucontrol(Int(15, alucontrol.width, 10))
                        ),
                    )
                ),
            )
        )

        self.cache[name] = m

        _u.initialize_regs(m)

        return m

    def get_alu(self) -> Module:
        data_width = self.data_width

        name = "alu"
        if name in self.cache.keys():
            return self.cache[name]
        m = Module(name)

        alucontrol = m.Input('alucontrol', 4)
        a = m.Input('a', data_width)
        b = m.Input('b', data_width)
        aluout = m.OutputReg('aluout', data_width)
        zero = m.Output('zero')

        zero.assign(aluout == 0)

        m.EmbeddedCode('')

        t = m.Wire('t', data_width)
        sh = m.Wire('sh', data_width)
        p = m.Wire('p', data_width)

        m_slt = self.get_slt()
        par = []
        con = [
            ('a', a),
            ('b', b),
            ('s', t)
        ]
        m.Instance(m_slt, m_slt.name, par, con)

        m_shiftra = self.get_shiftra()
        con = [
            ('a', a),
            ('b', b[0:5]),
            ('o', sh)
        ]
        m.Instance(m_shiftra, m_shiftra.name, par, con)

        m.Always()(
            Case(alucontrol)(
                When(Int(0, alucontrol.width, 10))(
                    aluout(a & b)
                ),
                When(Int(1, alucontrol.width, 10))(
                    aluout(a | b)
                ),
                When(Int(2, alucontrol.width, 10))(
                    aluout(a+b)
                ),
                When(Int(3, alucontrol.width, 10))(
                    aluout(a << b[0:5])
                ),
                When(Int(4, alucontrol.width, 10))(
                    aluout(a ^ b)
                ),
                When(Int(5, alucontrol.width, 10))(
                    aluout(sh)
                ),
                When(Int(6, alucontrol.width, 10))(
                    aluout(a-b)
                ),
                When(Int(7, alucontrol.width, 10))(
                    aluout(t)
                ),
                When(Int(8, alucontrol.width, 10))(
                    aluout(a >> b[0:5])
                ),
                When(Int(9, alucontrol.width, 10))(
                    aluout(a < b)
                ),
                When()(
                    aluout(Int(0, aluout.width, 10))
                ),
            )
        )

        self.cache[name] = m

        _u.initialize_regs(m)

        return m

    def get_slt(self) -> Module:
        data_width = self.data_width

        name = "slt"
        if name in self.cache.keys():
            return self.cache[name]
        m = Module(name)

        a = m.Input('a', data_width)
        b = m.Input('b', data_width)
        s = m.Output('s', data_width)

        sub = m.Wire('sub', data_width)
        sub.assign(a-b)
        s.assign(Mux(sub[31], Int(1, data_width, 10), Int(0, data_width, 10)))

        self.cache[name] = m

        _u.initialize_regs(m)

        return m

    def get_shiftra(self) -> Module:
        data_width = self.data_width

        name = "shiftra"
        if name in self.cache.keys():
            return self.cache[name]
        m = Module(name)

        a = m.Input('a', data_width)
        b = m.Input('b', 5)
        o = m.Output('o', data_width)

        s = m.Wire('s', data_width)
        t = m.Wire('t', data_width)
        _m = m.Wire('m', data_width)

        m.EmbeddedCode('')

        _m.assign(Int((2**data_width)-1, data_width, 2))
        s.assign(_m >> b)
        t.assign(a >> b)
        o.assign(Mux(a[31], (~s | t), t))

        self.cache[name] = m

        _u.initialize_regs(m)

        return m

    def get_memory(self) -> Module:
        data_width = self.data_width

        name = "memory"
        if name in self.cache.keys():
            return self.cache[name]
        m = Module(name)

        clk = m.Input('clk')
        address = m.Input('address', data_width)
        writedata = m.Input('writedata', data_width)
        memread = m.Input('memread')
        memwrite = m.Input('memwrite')
        readdata = m.Output('readdata', data_width)

        memory = m.Reg('memory', data_width, 2**self.ram_depth)

        m.EmbeddedCode('')

        readdata.assign(
            Mux(memread, memory[address[2:data_width]], Int(0, data_width, 10)))

        m.Always(Posedge(clk))(
            If(memwrite)(
                memory[address[2:data_width]](writedata)
            )
        )

        self.cache[name] = m

        # _u.initialize_regs(m)

        return m

    def get_writeback(self) -> Module:
        data_width = self.data_width

        name = "writeback"
        if name in self.cache.keys():
            return self.cache[name]
        m = Module(name)

        aluout = m.Input('aluout', data_width)
        readdata = m.Input('readdata', data_width)
        memtoreg = m.Input('memtoreg')
        writedata = m.Output('writedata', data_width)

        writedata.assign(Mux(memtoreg, readdata, aluout))

        self.cache[name] = m

        _u.initialize_regs(m)

        return m

# comp = GeneralComponents()
# comp.get_alucontrol().to_verilog('alucontrol.v')
