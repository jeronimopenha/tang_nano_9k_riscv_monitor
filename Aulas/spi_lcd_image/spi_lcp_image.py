from veriloggen import *
from math import ceil, log2


def create_spi_lcd_image() -> Module:
    m = Module("spi_lcd_image")
    clk = m.Input('clk_27mhz')
    btn_rst = m.Input('button_s1')
    lcd_resetn = m.Output('lcd_resetn')
    lcd_clk = m.Output('lcd_clk')
    lcd_cs = m.Output('lcd_cs')
    lcd_rs = m.Output('lcd_rs')
    lcd_data = m.Output('lcd_data')

    MAX_CMDS = m.Localparam('MAX_CMDS',70)
    m.EmbeddedCode('')

    init_cmd = m.Wire('init_cmd',9,MAX_CMDS)
    
    cmds = [Int(0x036,init_cmd.width,16),Int(0x170,init_cmd.width,16),Int(0x03a,init_cmd.width,16),Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),
            Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),
            Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),
            Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),
            Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),
            Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),
            Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),
            Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),
            Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),
            Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),
            Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),
            Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),
            Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),
            Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),Int(0x,init_cmd.width,16),
            ]

    m.EmbeddedCode('' )
    init_cmd[0].assign()
    init_cmd[1].assign()
    init_cmd[2].assign()
    init_cmd[3].assign()
    init_cmd[4].assign()
    init_cmd[5].assign()
    init_cmd[6].assign()
    init_cmd[7].assign()
    init_cmd[8].assign()
    init_cmd[9].assign()
    init_cmd[0].assign()
    init_cmd[1].assign()
    init_cmd[2].assign()
    init_cmd[3].assign()
    init_cmd[4].assign()
    init_cmd[5].assign()
    init_cmd[6].assign()
    init_cmd[7].assign()
    init_cmd[8].assign()
    init_cmd[9].assign()
    init_cmd[0].assign()
    init_cmd[1].assign()
    init_cmd[2].assign()
    init_cmd[3].assign()
    init_cmd[4].assign()
    init_cmd[5].assign()
    init_cmd[6].assign()
    init_cmd[7].assign()
    init_cmd[8].assign()
    init_cmd[9].assign()
    init_cmd[0].assign()
    init_cmd[1].assign()
    init_cmd[2].assign()
    init_cmd[3].assign()
    init_cmd[4].assign()
    init_cmd[5].assign()
    init_cmd[6].assign()
    init_cmd[7].assign()
    init_cmd[8].assign()
    init_cmd[9].assign()
    init_cmd[0].assign()
    init_cmd[].assign()
    init_cmd[].assign()
    init_cmd[].assign()
    init_cmd[].assign()
    init_cmd[].assign()
    init_cmd[].assign()
    init_cmd[].assign()
    init_cmd[].assign()
    init_cmd[].assign()
    init_cmd[].assign()
    init_cmd[].assign()
    init_cmd[].assign()
    init_cmd[].assign()
    init_cmd[].assign()
    init_cmd[].assign()
    init_cmd[].assign()
    init_cmd[].assign()
    init_cmd[].assign()
    init_cmd[].assign()
    init_cmd[].assign()
    init_cmd[].assign()
    init_cmd[].assign()
    init_cmd[].assign()
    init_cmd[].assign()
    init_cmd[].assign()
    init_cmd[].assign()
    init_cmd[].assign()
    init_cmd[].assign()
    init_cmd[].assign()