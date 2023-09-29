from veriloggen import *
from math import ceil, log2

import util as _u


class Components:
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
        self.cache = {}

    def create_fifo(self) -> Module:
        data_width = self.data_width
        n_channel = self.n_channel
        fifo_depth = self.fifo_depth

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

    def create_uart_tx(self) -> Module:
        name = "uart_tx"
        if name in self.cache.keys():
            return self.cache[name]
        m = Module(name)
        clk = m.Input('clk')
        rst = m.Input('rst')
        send_trig = m.Input('send_trig')
        send_data = m.Input('send_data', 8)
        tx = m.OutputReg('tx')
        tx_bsy = m.OutputReg('tx_bsy')

        SYSCLOCK = 27.0
        BAUDRATE = 3.0
        m.EmbeddedCode('// %dMHz' % SYSCLOCK)
        m.EmbeddedCode('// %dMbps' % BAUDRATE)

        CLKPERFRM = m.Localparam('CLKPERFRM', int(SYSCLOCK/BAUDRATE)*10)
        m.EmbeddedCode('// bit order is lsb-msb')
        TBITAT = m.Localparam('TBITAT', 1)
        m.EmbeddedCode('// START bit')
        BIT0AT = m.Localparam('BIT0AT', int(SYSCLOCK/BAUDRATE*1)+1)
        BIT1AT = m.Localparam('BIT1AT', int(SYSCLOCK/BAUDRATE*2)+1)
        BIT2AT = m.Localparam('BIT2AT', int(SYSCLOCK/BAUDRATE*3)+1)
        BIT3AT = m.Localparam('BIT3AT', int(SYSCLOCK/BAUDRATE*4)+1)
        BIT4AT = m.Localparam('BIT4AT', int(SYSCLOCK/BAUDRATE*5)+1)
        BIT5AT = m.Localparam('BIT5AT', int(SYSCLOCK/BAUDRATE*6)+1)
        BIT6AT = m.Localparam('BIT6AT', int(SYSCLOCK/BAUDRATE*7)+1)
        BIT7AT = m.Localparam('BIT7AT', int(SYSCLOCK/BAUDRATE*8)+1)
        PBITAT = m.Localparam('PBITAT', int(SYSCLOCK/BAUDRATE*9)+1)
        m.EmbeddedCode('// STOP bit')

        m.EmbeddedCode('')
        m.EmbeddedCode('// tx flow control ')
        tx_cnt = m.Reg('tx_cnt', ceil(log2(CLKPERFRM.value))+1)

        m.EmbeddedCode('')
        m.EmbeddedCode('// buffer')
        data2send = m.Reg('data2send', 8)
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

    def create_uart_rx(self) -> Module:
        name = "uart_rx"
        if name in self.cache.keys():
            return self.cache[name]
        m = Module(name)
        clk = m.Input('clk')
        rst = m.Input('rst')
        rx = m.Input('rx')
        rx_bsy = m.OutputReg('rx_bsy')
        block_timeout = m.OutputReg('block_timeout')
        data_valid = m.OutputReg('data_valid')
        data_out = m.OutputReg('data_out', 8)

        SYSCLOCK = 27.0
        BAUDRATE = 3.0
        m.EmbeddedCode('// %dMHz' % SYSCLOCK)
        m.EmbeddedCode('// %dMbits' % BAUDRATE)

        SYNC_DELAY = 2  # m.Localparam('SYNC_DELAY', 2)
        CLKPERFRM = m.Localparam('CLKPERFRM', int(
            SYSCLOCK/BAUDRATE*9.8)-SYNC_DELAY)
        m.EmbeddedCode('// bit order is lsb-msb')
        TBITAT = m.Localparam('TBITAT', int(SYSCLOCK/BAUDRATE*0.8)-SYNC_DELAY)
        m.EmbeddedCode('// START BIT')
        BIT0AT = m.Localparam('BIT0AT', int(SYSCLOCK/BAUDRATE*1.5)-SYNC_DELAY)
        BIT1AT = m.Localparam('BIT1AT', int(SYSCLOCK/BAUDRATE*2.5)-SYNC_DELAY)
        BIT2AT = m.Localparam('BIT2AT', int(SYSCLOCK/BAUDRATE*3.5)-SYNC_DELAY)
        BIT3AT = m.Localparam('BIT3AT', int(SYSCLOCK/BAUDRATE*4.5)-SYNC_DELAY)
        BIT4AT = m.Localparam('BIT4AT', int(SYSCLOCK/BAUDRATE*5.5)-SYNC_DELAY)
        BIT5AT = m.Localparam('BIT5AT', int(SYSCLOCK/BAUDRATE*6.5)-SYNC_DELAY)
        BIT6AT = m.Localparam('BIT6AT', int(SYSCLOCK/BAUDRATE*7.5)-SYNC_DELAY)
        BIT7AT = m.Localparam('BIT7AT', int(SYSCLOCK/BAUDRATE*8.5)-SYNC_DELAY)
        PBITAT = m.Localparam('PBITAT', int(SYSCLOCK/BAUDRATE*9.2)-SYNC_DELAY)
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
        '''

    always@(posedge clk) begin
        if (rst) begin
            data_out[7:0] <= 8'd0;
        end else if (rx_bsy) begin
            case(rx_cnt)
                BIT0AT: data_out[0] <= rx;
                BIT1AT: data_out[1] <= rx;
                BIT2AT: data_out[2] <= rx;
                BIT3AT: data_out[3] <= rx;
                BIT4AT: data_out[4] <= rx;
                BIT5AT: data_out[5] <= rx;
                BIT6AT: data_out[6] <= rx;
                BIT7AT: data_out[7] <= rx;
            endcase
        end
    end

endmodule
        '''

    def create_io_controller(self) -> Module:
        data_width = self.data_width
        n_channel = self.n_channel
        fifo_depth = self.fifo_depth

        name = "io_protocol_controller"
        if name in self.cache.keys():
            return self.cache[name]
        m = Module(name)
        clk = m.Input('clk')
        rst = m.Input('rst')
        rx = m.Input('rx')
        tx = m.Output('tx')
        sw_rst = m.OutputReg('sw_rst')
        start = m.OutputReg('start')

        m.EmbeddedCode('// Interface info to send, n_channel')
        INFO_TO_SEND = m.Localparam('INFO_TO_SEND', Int(n_channel, 8, 10), 8)

        m.EmbeddedCode('')
        m.EmbeddedCode('// Instantiate the RX controller')
        rx_bsy = m.Wire('rx_bsy')
        rx_block_timeout = m.Wire('rx_block_timeout')
        rx_data_valid = m.Wire('rx_data_valid')
        rx_data_out = m.Wire('rx_data_out', 8)

        m.EmbeddedCode('')
        m.EmbeddedCode('// Instantiate the TX controller')
        tx_send_trig = m.Reg('send_trig')
        tx_send_data = m.Reg('send_data', 8)
        tx_bsy = m.Wire('tx_bsy')

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
        m.EmbeddedCode('// PC to board protocol')
        PROT_PC_B_REQ_INFO = m.Localparam(
            'PROT_PC_B_REQ_INFO', Int(0, 8, 16), 8)
        PROT_PC_B_RESET = m.Localparam('PROT_PC_B_RESET', Int(1, 8, 16), 8)
        PROT_PC_B_SEND_CONFIG = m.Localparam(
            'PROT_PC_B_SEND_CONFIG', Int(2, 8, 16), 8)
        PROT_PC_B_START = m.Localparam('PROT_PC_B_START', Int(3, 8, 16), 8)
        PROT_PC_B_SEND_DATA = m.Localparam(
            'PROT_PC_B_SEND_DATA', Int(4, 8, 16), 8)

        m.EmbeddedCode('')
        m.EmbeddedCode('// Board to PC protocol')
        PROT_B_PC_SEND_INFO = m.Localparam(
            'PROT_B_PC_SEND_INFO', Int(0, 8, 16), 8)
        PROT_B_PC_RESETED = m.Localparam('PROT_B_PC_RESETED', Int(1, 8, 16), 8)
        PROT_B_PC_CONF_RECEIVED = m.Localparam(
            'PROT_B_PC_CONF_RECEIVED', Int(2, 8, 16), 8)
        PROT_B_PC_STARTED = m.Localparam('PROT_B_PC_STARTED', Int(3, 8, 16), 8)
        PROT_B_PC_REQ_DATA = m.Localparam(
            'PROT_B_PC_REQ_DATA', Int(4, 8, 16), 8)
        PROT_B_PC_SEND_DATA = m.Localparam(
            'PROT_B_PC_SEND_DATA', Int(5, 8, 16), 8)
        PROT_B_PC_DONE_RD = m.Localparam('PROT_B_PC_DONE_RD', Int(6, 8, 16), 8)
        PROT_B_PC_DONE_WR = m.Localparam('PROT_B_PC_DONE_WR', Int(7, 8, 16), 8)
        PROT_B_PC_DONE_ACC = m.Localparam(
            'PROT_B_PC_DONE_ACC', Int(8, 8, 16), 8)

        m.EmbeddedCode('')
        m.EmbeddedCode('// IO and protocol controller')
        fsm_io_send_data = m.Reg('fsm_io_send_data', 8)
        fsm_io = m.Reg('fsm_io', 4)
        FSM_IDLE = m.Localparam(
            'FSM_IDLE', Int(0, fsm_io.width, 16), fsm_io.width)
        FSM_DECODE_PROTOCOL = m.Localparam(
            'FSM_DECODE_PROTOCOL', Int(1, fsm_io.width, 16), fsm_io.width)
        FSM_SEND_INFO = m.Localparam(
            'FSM_SEND_INFO', Int(2, fsm_io.width, 16), fsm_io.width)
        FSM_RESET = m.Localparam(
            'FSM_RESET', Int(3, fsm_io.width, 16), fsm_io.width)
        FSM_SEND_CONFIG = m.Localparam(
            'FSM_SEND_CONFIG', Int(4, fsm_io.width, 16), fsm_io.width)
        FSM_START_ACC = m.Localparam(
            'FSM_START_ACC', Int(5, fsm_io.width, 16), fsm_io.width)
        # FSM_START_ACK = m.Localparam(
        #    'FSM_START_ACK', Int(6, fsm_io.width, 16), fsm_io.width)
        FSM_MOVE_DATA_TO_ACC = m.Localparam(
            'FSM_MOVE_DATA_TO_ACC', Int(6, fsm_io.width, 16), fsm_io.width)

        m.Always(Posedge(clk))(
            If(rst)(
                fsm_io(FSM_IDLE),
                rx_fifo_re(Int(0, 1, 2)),
                sw_rst(0),
                tx_send_trig(0),
                start(0),
            ).Else(
                rx_fifo_re(Int(0, 1, 2)),
                sw_rst(0),
                tx_send_trig(0),
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
                                When(PROT_PC_B_REQ_INFO)(
                                    fsm_io(FSM_IDLE)
                                ),
                                When(PROT_PC_B_RESET)(
                                    fsm_io(FSM_RESET)
                                ),
                                When(PROT_PC_B_SEND_CONFIG)(
                                    fsm_io(FSM_IDLE)
                                ),
                                When(PROT_PC_B_START)(
                                    fsm_io(FSM_START_ACC)
                                ),
                                When(PROT_PC_B_SEND_DATA)(
                                    fsm_io(FSM_IDLE)
                                ),
                            ),
                        )
                    ),
                    When(FSM_SEND_INFO)(
                        # TODO
                    ),
                    When(FSM_RESET)(
                        If(~tx_bsy)(
                            tx_send_trig(1),
                            tx_send_data(PROT_B_PC_RESETED),
                            sw_rst(~sw_rst),
                            fsm_io(FSM_IDLE)
                        )
                    ),
                    When(FSM_SEND_CONFIG)(

                    ),
                    When(FSM_START_ACC)(
                        If(~tx_bsy)(
                            tx_send_trig(1),
                            tx_send_data(PROT_B_PC_STARTED),
                            start(~start),
                            fsm_io(FSM_IDLE)
                        ),
                    ),

                    When(FSM_MOVE_DATA_TO_ACC)(

                    ),
                )
            )
        )

        aux = self.create_fifo()
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
        m.Instance(aux, 'rx_%s' % aux.name, par, con)

        aux = self.create_uart_rx()
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
        m.Instance(aux, aux.name, par, con)

        aux = self.create_uart_tx()
        par = []
        con = [
            ('clk', clk),
            ('rst', rst),
            ('send_trig', tx_send_trig),
            ('send_data', tx_send_data),
            ('tx', tx),
            ('tx_bsy', tx_bsy),
        ]
        m.Instance(aux, aux.name, par, con)

        _u.initialize_regs(m, {'tx': 1})
        return m


cmp = Components()
cmp.create_io_controller().to_verilog('io_controller.v')
