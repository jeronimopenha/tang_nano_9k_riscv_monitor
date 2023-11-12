from veriloggen import *
from math import ceil, log2


def create_serial_led() -> Module:
    m = Module("serial_led")
    clk = m.Input('clk_27mhz')
    btn_rst = m.Input('button_s1')
    uart_rx = m.Input('uart_rx')
    led = m.OutputReg('led', 6)
    uart_tx = m.Output('uart_tx')

    m.EmbeddedCode('// Reset signal control')
    rst = m.Wire('rst')
    rst.assign(~btn_rst)
    m.EmbeddedCode('')
    rx_data_valid = m.Wire('rx_data_valid')
    rx_data_out = m.Wire('rx_data_out', 8)

    m.Always(Posedge(clk))(
        If(rst)(
            led(Int(63, led.width, 2))
        ).Else(
            If(rx_data_valid)(
                led(~rx_data_out[0:led.width])
            )
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
    m_uart_rx = create_uart_rx()
    m.Instance(m_uart_rx, m_uart_rx.name, par, con)

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


m = create_serial_led()
m.to_verilog(m.name+".v")
