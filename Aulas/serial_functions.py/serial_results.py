from veriloggen import *
from math import ceil, log2


def create_results() -> Module:
    m = Module("serial_results")
    clk = m.Input('clk_27mhz')
    btn_rst = m.Input('button_s1')
    uart_rx = m.Input('uart_rx')
    led = m.Output('led', 6)
    uart_tx = m.Output('uart_tx')

    m.EmbeddedCode('// Reset signal control')
    rst = m.Wire('rst')
    rst.assign(~btn_rst)

    m.EmbeddedCode('')
    rx_data_valid = m.Wire('rx_data_valid')
    rx_data_out = m.Wire('rx_data_out', 8)

    m.EmbeddedCode('')
    tx_bsy = m.Wire('tx_bsy')

    m.EmbeddedCode('')
    led.assign(Int(2**led.width-1, led.width, 2))

    m.EmbeddedCode('')
    sum_ = m.Reg('sum', 8)
    max_ = m.Reg('max', 8)

    m.EmbeddedCode('')
    send_trig = m.Reg('send_trig')
    send_data = m.Reg('send_data', 8)

    m.EmbeddedCode('')
    start = m.Reg('start')
    n_data = m.Reg('n_data', 8)
    counter_rec_data = m.Reg('counter_rec_data', 9)

    m.EmbeddedCode('')
    fsm_controller = m.Reg('fsm_controller', 3)
    FSM_IDLE = m.Localparam('FSM_IDLE', Int(0, fsm_controller.width, 10))
    FSM_READ_DATA = m.Localparam(
        'FSM_READ_DATA', Int(1, fsm_controller.width, 10))
    FSM_SEND_SUM = m.Localparam(
        'FSM_SEND_SUM', Int(2, fsm_controller.width, 10))
    FSM_SEND_MAX = m.Localparam(
        'FSM_SEND_MAX', Int(3, fsm_controller.width, 10))

    m.Always(Posedge(clk))(
        If(rst)(
            send_trig(Int(0, 1, 2)),
            start(Int(0, 1, 2)),
            fsm_controller(FSM_IDLE)
        ).Else(
            send_trig(Int(0, 1, 2)),
            Case(fsm_controller)(
                When(FSM_IDLE)(
                    start(Int(0, 1, 2)),
                    If(rx_data_valid)(
                        n_data(rx_data_out),
                        counter_rec_data(
                            Int(0, counter_rec_data.width, 10)),
                        start(Int(1, 1, 2)),
                        # send_data(rx_data_out),
                        # send_trig(Int(1, 1, 2)),
                        fsm_controller(FSM_READ_DATA),
                    )
                ),
                When(FSM_READ_DATA)(
                    If(rx_data_valid)(
                        If(counter_rec_data == n_data - 1)(
                            fsm_controller(FSM_SEND_SUM)
                        ).Else(
                            counter_rec_data(
                                counter_rec_data + Int(1, counter_rec_data.width, 10))
                        )
                    )
                ),
                When(FSM_SEND_SUM)(
                    If(AndList(~tx_bsy, ~send_trig))(
                        send_data(sum_),
                        send_trig(Int(1, 1, 2)),
                        fsm_controller(FSM_SEND_MAX)
                    )
                ),
                When(FSM_SEND_MAX)(
                    If(AndList(~tx_bsy, ~send_trig))(
                        send_data(max_),
                        send_trig(Int(1, 1, 2)),
                        fsm_controller(FSM_IDLE)
                    )
                ),
            ),
        )
    )

    m.EmbeddedCode('// somatorio')
    m.Always(Posedge(clk))(
        If(start)(
            If((rx_data_valid))(
                sum_(sum_ + rx_data_out)
            )
        ).Else(
            sum_(Int(0, 8, 10))
        )
    )

    m.EmbeddedCode('// maior')
    m.Always(Posedge(clk))(
        If(start)(
            If((rx_data_valid))(
                If(rx_data_out > max_)(
                    max_(rx_data_out)
                )
            )
        ).Else(
            max_(Int(0, 8, 10))
        )
    )

    m.EmbeddedCode('')
    par = []
    con = [
        ('clk', clk),
        ('rst', rst),
        ('rx', uart_rx),
        ('data_valid', rx_data_valid),
        ('data_out', rx_data_out),
    ]
    m_aux = create_uart_rx()
    m.Instance(m_aux, m_aux.name, par, con)

    con = [
        ('clk', clk),
        ('rst', rst),
        ('send_trig', send_trig),
        ('send_data', send_data),
        ('tx', uart_tx),
        ('tx_bsy', tx_bsy)
    ]
    m_aux = create_uart_tx()
    m.Instance(m_aux, m_aux.name, par, con)

    initialize_regs(m)

    return m


def create_uart_rx() -> Module:
    m = Module("m_uart_rx")
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

    return m


def create_uart_tx() -> Module:
    m = Module("m_uart_tx")
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
    initialize_regs(m, {'tx': 1})

    return m


def initialize_regs(module: Module, values=None):
    regs = []
    if values is None:
        values = {}
    flag = False
    for r in module.get_vars().items():
        if module.is_reg(r[0]):
            regs.append(r)
            if r[1].dims:
                flag = True

    if len(regs) > 0:
        if flag:
            i = module.Integer("i_initial")
        s = module.Initial()
        for r in regs:
            if values:
                if r[0] in values.keys():
                    value = values[r[0]]
                else:
                    value = 0
            else:
                value = 0
            if r[1].dims:
                genfor = For(i(0), i < r[1].dims[0], i.inc())(r[1][i](value))
                s.add(genfor)
            else:
                s.add(r[1](value))


m = create_results()
name = m.name
m.to_verilog(name+".v")
