from veriloggen import *
from math import ceil, log2


def create_spi_lcd_image() -> Module:
    m = Module("spi_lcd_image")
    clk = m.Input('clk_27mhz')
    btn_rst = m.Input('button_s1')
    resetn = m.Input('resetn')

    lcd_resetn = m.Output('lcd_resetn')
    lcd_clk = m.Output('lcd_clk')
    lcd_cs = m.Output('lcd_cs')
    lcd_rs = m.Output('lcd_rs')
    lcd_data = m.Output('lcd_data')

    uart_rx = m.Input('uart_rx')
    led = m.OutputReg('led', 6)
    uart_tx = m.Output('uart_tx')

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
    INIT_DONE = m.Localparam('INIT_DONE', Int(5, 4, 2))

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
    pixel = m.Wire('pixel', 16)
    pixel.assign(
        Mux(pixel_cnt >= Int(21600, pixel_cnt.width, 10),
            Int(0xF800, pixel.width, 16),
            Mux(pixel_cnt >= Int(10800, pixel_cnt.width, 10),
                Int(0x07E0, pixel.width, 16),
                Int(0x001F, pixel.width, 16),
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
                        init_state(INIT_DONE)
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
                When(INIT_DONE)(
                    If(pixel_cnt == Int(32400, pixel_cnt.width, 10))(

                    ).Else(
                        If(bit_loop == Int(0, bit_loop.width, 10))(
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
                        ).Else(
                            spi_data(Cat(spi_data[0:7], Int(1, 1, 10))),
                            bit_loop(bit_loop + Int(1, bit_loop.width, 10)),
                        )
                    )
                ),
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


m = create_spi_lcd_image()
m.to_verilog(m.name+'.v')
