from veriloggen import *
from math import ceil, log2


def create_display_spi_serial() -> Module:
    m = Module("display_spi_serial")
    clk = m.Input('clk_27mhz')
    btn_rst = m.Input('button_s1')
    resetn = m.Input('resetn')

    lcd_resetn = m.Output('lcd_resetn')
    lcd_clk = m.Output('lcd_clk')
    lcd_cs = m.Output('lcd_cs')
    lcd_rs = m.Output('lcd_rs')
    lcd_data = m.Output('lcd_data')

    uart_rx = m.Input('uart_rx')
    led = m.Output('led', 6)
    uart_tx = m.Output('uart_tx')

    '''
    assign led[0] = uart_rx;
    assign led[1] = ~rx_bsy;
    assign led[2] = uart_tx;
    assign led[3] = ~tx_bsy;
    assign led[4] = ~rst;
    assign led[5] = ~running;
    '''

    m.EmbeddedCode('')
    rx_bsy = m.Wire('rx_bsy')
    rx_data_valid = m.Wire('rx_data_valid')
    rx_data_out = m.Wire('rx_data_out', 8)
    send_trig = m.Reg('send_trig')
    send_data = m.Reg('send_data')
    led[0].assign(~rx_bsy)
    led[1].assign(uart_rx)

    m.EmbeddedCode('')
    MAX_CMDS = m.Localparam('MAX_CMDS', 70)

    m.EmbeddedCode('')
    init_cmd = m.Wire('init_cmd', 9)
    init_state = m.Reg('init_state', 4)
    cmd_index = m.Reg('cmd_index', 7)
    clk_cnt = m.Reg('clk_cnt', 32)
    bit_loop = m.Reg('bit_loop', 5)
    pixel_cnt = m.Reg('pixel_cnt', 16)
    lcd_cs_r = m.Reg('lcd_cs_r')
    lcd_rs_r = m.Reg('lcd_rs_r')
    lcd_reset_r = m.Reg('lcd_reset_r')
    spi_data = m.Reg('spi_data', 8)

    m.EmbeddedCode('')
    INIT_RESET = m.Localparam('INIT_RESET', Int(0, 4, 2))
    INIT_PREPARE = m.Localparam('INIT_PREPARE', Int(1, 4, 2))
    INIT_WAKEUP = m.Localparam('INIT_WAKEUP', Int(2, 4, 2))
    INIT_SNOOZE = m.Localparam('INIT_SNOOZE', Int(3, 4, 2))
    INIT_WORKING = m.Localparam('INIT_WORKING', Int(4, 4, 2))
    INIT_WAIT_SERIAL = m.Localparam('INIT_WAIT_SERIAL', Int(5, 4, 2))
    INIT_WRITE = m.Localparam('INIT_WRITE', Int(6, 4, 2))
    INIT_DONE = m.Localparam('INIT_DONE', Int(7, 4, 2))

    m.EmbeddedCode('')
    CNT_100MS = m.Localparam('CNT_100MS', Int(2700000, clk_cnt.width, 10))
    CNT_120MS = m.Localparam('CNT_120MS', Int(3240000, clk_cnt.width, 10))
    CNT_200MS = m.Localparam('CNT_200MS', Int(5400000, clk_cnt.width, 10))

    m.EmbeddedCode('')
    lcd_resetn.assign(lcd_reset_r)
    lcd_clk.assign(~clk)
    lcd_cs.assign(lcd_cs_r)
    lcd_rs.assign(lcd_rs_r)
    m.EmbeddedCode('// MSB')
    lcd_data.assign(spi_data[7])
    m.EmbeddedCode('// gen color bar')
    pixel = m.Reg('pixel', 16)
    '''pixel.assign(
        Mux(pixel_cnt >= Int(21600, pixel_cnt.width, 10),
            Int(0xF800, pixel.width, 16),
            Mux(pixel_cnt >= Int(10800, pixel_cnt.width, 10),
                Int(0x07E0, pixel.width, 16),
                Int(0x001F, pixel.width, 16),
                )
            )
    )'''

    counter_bytes_in = m.Reg('counter_bytes_in')
    lcd_fire = m.Reg('lcd_fire')

    m.Always(Posedge(clk))(
        If(~resetn)(
            counter_bytes_in(Int(0, 1, 10)),
            lcd_fire(Int(0, 1, 2)),
            send_trig(Int(0, 1, 2))
        ).Else(
            lcd_fire(Int(0, 1, 2)),
            send_trig(Int(0, 1, 2)),
            If(rx_data_valid)(
                If(counter_bytes_in == Int(1, 1, 10))(
                    counter_bytes_in(Int(0, 1, 10)),
                    lcd_fire(Int(1, 1, 2)),
                ).Else(
                    counter_bytes_in(counter_bytes_in + Int(1, 1, 10)),
                ),
                pixel(Cat(rx_data_out, pixel[8:16])),
                send_data(rx_data_out),
            )
        )
    )

    m.Always(Posedge(clk))(
        If(~resetn)(
            clk_cnt(Int(0, clk_cnt.width, 10)),
            cmd_index(Int(0, cmd_index.width, 10)),
            init_state(INIT_RESET),
            lcd_cs_r(Int(1, 1, 10)),
            lcd_rs_r(Int(1, 1, 10)),
            lcd_reset_r(Int(0, 1, 10)),
            spi_data(Int(0xFF, spi_data.width, 16)),
            bit_loop(Int(0, bit_loop.width, 10)),
            pixel_cnt(Int(0, pixel_cnt.width, 10)),
        ).Else(
            Case(init_state)(
                When(INIT_RESET)(
                    If(clk_cnt == CNT_100MS)(
                        clk_cnt(Int(0, clk_cnt.width, 10)),
                        init_state(INIT_PREPARE),
                        lcd_reset_r(Int(1, 1, 10))
                    ).Else(
                        clk_cnt(clk_cnt + Int(1, clk_cnt.width, 10))
                    )
                ),
                When(INIT_PREPARE)(
                    If(clk_cnt == CNT_200MS)(
                        clk_cnt(Int(0, clk_cnt.width, 10)),
                        init_state(INIT_WAKEUP),
                    ).Else(
                        clk_cnt(clk_cnt + Int(1, clk_cnt.width, 10))
                    )
                ),
                When(INIT_WAKEUP)(
                    If(bit_loop == Int(0, bit_loop.width, 10))(
                        # start
                        lcd_cs_r(Int(0, 1, 10)),
                        lcd_rs_r(Int(0, 1, 10)),
                        spi_data(Int(0x11, spi_data.width, 16)),
                        bit_loop(bit_loop+Int(1, bit_loop.width, 10)),
                    ).Elif(bit_loop == Int(8, bit_loop.width, 10))(
                        lcd_cs_r(Int(1, 1, 10)),
                        lcd_rs_r(Int(1, 1, 10)),
                        bit_loop(Int(0, bit_loop.width, 10)),
                        init_state(INIT_SNOOZE),
                    ).Else(
                        spi_data(Cat(spi_data[0:7], Int(1, 1, 10))),
                        bit_loop(bit_loop + Int(1, bit_loop.width, 10)),
                    )
                ),
                When(INIT_SNOOZE)(
                    If(clk_cnt == CNT_120MS)(
                        clk_cnt(Int(0, clk_cnt.width, 10)),
                        init_state(INIT_WORKING),
                    ).Else(
                        clk_cnt(clk_cnt + Int(1, clk_cnt.width, 10))
                    )
                ),
                When(INIT_WORKING)(
                    If(cmd_index == MAX_CMDS)(
                        init_state(INIT_WAIT_SERIAL)
                    ).Else(
                        If(bit_loop == Int(0, bit_loop.width, 10))(
                            lcd_cs_r(Int(0, 1, 10)),
                            lcd_rs_r(init_cmd[8]),
                            spi_data(init_cmd[0:8]),
                            bit_loop(bit_loop+Int(1, bit_loop.width, 10)),
                        ).Elif(bit_loop == Int(8, bit_loop.width, 10))(
                            lcd_cs_r(Int(1, 1, 10)),
                            lcd_rs_r(Int(1, 1, 10)),
                            bit_loop(Int(0, bit_loop.width, 10)),
                            cmd_index(cmd_index+Int(1, cmd_index.width, 10)),
                        ).Else(
                            spi_data(Cat(spi_data[0:7], Int(1, 1, 10))),
                            bit_loop(bit_loop + Int(1, bit_loop.width, 10)),
                        )
                    )
                ),
                When(INIT_WAIT_SERIAL)(
                    If(AndList(bit_loop == Int(0, bit_loop.width, 10), lcd_fire))(
                        lcd_cs_r(Int(0, 1, 10)),
                        lcd_rs_r(Int(1, 1, 10)),
                        spi_data(pixel[8:16]),
                        bit_loop(bit_loop + Int(1, bit_loop.width, 10)),
                        init_state(INIT_WRITE)
                    )
                ),
                When(INIT_WRITE)(
                    If(AndList(bit_loop == Int(0, bit_loop.width, 10), lcd_fire))(
                        lcd_cs_r(Int(0, 1, 10)),
                        lcd_rs_r(Int(1, 1, 10)),
                        spi_data(pixel[8:16]),
                        bit_loop(bit_loop + Int(1, bit_loop.width, 10)),
                    ).Elif(bit_loop == Int(8, bit_loop.width, 10))(
                        spi_data(pixel[0:8]),
                        bit_loop(bit_loop + Int(1, bit_loop.width, 10)),
                    ).Elif(bit_loop == Int(16, bit_loop.width, 10))(
                        lcd_cs_r(Int(1, 1, 10)),
                        lcd_rs_r(Int(1, 1, 10)),
                        bit_loop(Int(0, bit_loop.width, 10)),
                        pixel_cnt(pixel_cnt+Int(1, pixel_cnt.width, 10)),
                        If(pixel_cnt == Int(32400-1, pixel_cnt.width, 10))(
                            init_state(INIT_DONE)
                        ).Else(
                            init_state(INIT_WAIT_SERIAL)
                        )
                    ).Else(
                        spi_data(Cat(spi_data[0:7], Int(1, 1, 10))),
                        bit_loop(bit_loop + Int(1, bit_loop.width, 10)),
                    )
                ),
                When(INIT_DONE)(
                )
            )
        )
    )

    m_aux = create_lcd_config_rom()
    par = []
    con = [
        ('address', cmd_index),
        ('data_out', init_cmd),
    ]
    m.Instance(m_aux, m_aux.name, par, con)

    m.EmbeddedCode('')
    par = []
    con = [
        ('clk', clk),
        ('rst', ~resetn),
        ('rx', uart_rx),
        ('rx_bsy', rx_bsy),
        ('data_valid', rx_data_valid),
        ('data_out', rx_data_out),
    ]
    m_uart_rx = create_uart_rx()
    m.Instance(m_uart_rx, m_uart_rx.name, par, con)

    con = [
        ('clk', clk),
        ('rst', ~resetn),
        ('send_trig', send_trig),
        ('send_data', send_data),
        ('tx', uart_tx),
        # ('tx_bsy', tx_bsy)
    ]
    m_aux = create_uart_tx()
    m.Instance(m_aux, m_aux.name, par, con)

    initialize_regs(m)

    return m


def create_lcd_config_rom() -> Module:
    m = Module("config_rom")
    address = m.Input('address', 7)
    data_out = m.Output('data_out', 9)

    MAX_CMDS = m.Localparam('MAX_CMDS', 70)
    m.EmbeddedCode('')

    config_rom = m.Wire('config_rom', 9, MAX_CMDS)

    data_out.assign(config_rom[address])

    m.EmbeddedCode('')
    config_rom[0].assign(Int(0x036, config_rom.width, 16))
    config_rom[1].assign(Int(0x170, config_rom.width, 16))
    config_rom[2].assign(Int(0x03A, config_rom.width, 16))
    config_rom[3].assign(Int(0x105, config_rom.width, 16))
    config_rom[4].assign(Int(0x0B2, config_rom.width, 16))
    config_rom[5].assign(Int(0x10C, config_rom.width, 16))
    config_rom[6].assign(Int(0x10C, config_rom.width, 16))
    config_rom[7].assign(Int(0x100, config_rom.width, 16))
    config_rom[8].assign(Int(0x133, config_rom.width, 16))
    config_rom[9].assign(Int(0x133, config_rom.width, 16))
    config_rom[10].assign(Int(0x0B7, config_rom.width, 16))
    config_rom[11].assign(Int(0x135, config_rom.width, 16))
    config_rom[12].assign(Int(0x0BB, config_rom.width, 16))
    config_rom[13].assign(Int(0x119, config_rom.width, 16))
    config_rom[14].assign(Int(0x0C0, config_rom.width, 16))
    config_rom[15].assign(Int(0x12C, config_rom.width, 16))
    config_rom[16].assign(Int(0x0C2, config_rom.width, 16))
    config_rom[17].assign(Int(0x101, config_rom.width, 16))
    config_rom[18].assign(Int(0x0C3, config_rom.width, 16))
    config_rom[19].assign(Int(0x112, config_rom.width, 16))
    config_rom[20].assign(Int(0x0C4, config_rom.width, 16))
    config_rom[21].assign(Int(0x120, config_rom.width, 16))
    config_rom[22].assign(Int(0x0C6, config_rom.width, 16))
    config_rom[23].assign(Int(0x10F, config_rom.width, 16))
    config_rom[24].assign(Int(0x0D0, config_rom.width, 16))
    config_rom[25].assign(Int(0x1A4, config_rom.width, 16))
    config_rom[26].assign(Int(0x1A1, config_rom.width, 16))
    config_rom[27].assign(Int(0x0E0, config_rom.width, 16))
    config_rom[28].assign(Int(0x1D0, config_rom.width, 16))
    config_rom[29].assign(Int(0x104, config_rom.width, 16))
    config_rom[30].assign(Int(0x10D, config_rom.width, 16))
    config_rom[31].assign(Int(0x111, config_rom.width, 16))
    config_rom[32].assign(Int(0x113, config_rom.width, 16))
    config_rom[33].assign(Int(0x12B, config_rom.width, 16))
    config_rom[34].assign(Int(0x13F, config_rom.width, 16))
    config_rom[35].assign(Int(0x154, config_rom.width, 16))
    config_rom[36].assign(Int(0x14C, config_rom.width, 16))
    config_rom[37].assign(Int(0x118, config_rom.width, 16))
    config_rom[38].assign(Int(0x10D, config_rom.width, 16))
    config_rom[39].assign(Int(0x10B, config_rom.width, 16))
    config_rom[40].assign(Int(0x11F, config_rom.width, 16))
    config_rom[41].assign(Int(0x123, config_rom.width, 16))
    config_rom[42].assign(Int(0x0E1, config_rom.width, 16))
    config_rom[43].assign(Int(0x1D0, config_rom.width, 16))
    config_rom[44].assign(Int(0x104, config_rom.width, 16))
    config_rom[45].assign(Int(0x10C, config_rom.width, 16))
    config_rom[46].assign(Int(0x111, config_rom.width, 16))
    config_rom[47].assign(Int(0x113, config_rom.width, 16))
    config_rom[48].assign(Int(0x12C, config_rom.width, 16))
    config_rom[49].assign(Int(0x13F, config_rom.width, 16))
    config_rom[50].assign(Int(0x144, config_rom.width, 16))
    config_rom[51].assign(Int(0x151, config_rom.width, 16))
    config_rom[52].assign(Int(0x12F, config_rom.width, 16))
    config_rom[53].assign(Int(0x11F, config_rom.width, 16))
    config_rom[54].assign(Int(0x11F, config_rom.width, 16))
    config_rom[55].assign(Int(0x120, config_rom.width, 16))
    config_rom[56].assign(Int(0x123, config_rom.width, 16))
    config_rom[57].assign(Int(0x021, config_rom.width, 16))
    config_rom[58].assign(Int(0x029, config_rom.width, 16))
    m.EmbeddedCode('// column')
    config_rom[59].assign(Int(0x02A, config_rom.width, 16))  # column
    config_rom[60].assign(Int(0x100, config_rom.width, 16))
    config_rom[61].assign(Int(0x128, config_rom.width, 16))
    config_rom[62].assign(Int(0x101, config_rom.width, 16))
    config_rom[63].assign(Int(0x117, config_rom.width, 16))
    m.EmbeddedCode('// row')
    config_rom[64].assign(Int(0x02B, config_rom.width, 16))  # row
    config_rom[65].assign(Int(0x100, config_rom.width, 16))
    config_rom[66].assign(Int(0x135, config_rom.width, 16))
    config_rom[67].assign(Int(0x100, config_rom.width, 16))
    config_rom[68].assign(Int(0x1BB, config_rom.width, 16))
    m.EmbeddedCode('// start')
    config_rom[69].assign(Int(0x02C, config_rom.width, 16))  # start

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


m = create_display_spi_serial()
m.to_verilog(m.name+'.v')
