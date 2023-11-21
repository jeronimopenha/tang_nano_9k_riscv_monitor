from veriloggen import *


def create_contador_leds():
    m = Module("contador_leds")
    clk = m.Input('clk_27mhz')
    btn_rst = m.Input('button_s1')
    uart_rx = m.Input('uart_rx')
    led = m.OutputReg('led', 6)
    uart_tx = m.Output('uart_tx')

    m.EmbeddedCode('// Reset signal control')
    rst = m.Wire('rst')
    rst.assign(~btn_rst)

    m.EmbeddedCode('')
    counter = m.Reg('counter', 24)
    m.EmbeddedCode('')

    m.Always(Posedge(clk))(
        If(rst)(
            counter(Int(0, counter.width, 10))
        ).Else(
            If(counter < Int(13499999, counter.width, 10))(
                counter(counter+Int(1, counter.width, 10))
            ).Else(
                counter(0),
            )
        )
    )

    m.Always(Posedge(clk))(
        If(rst)(
            led(Int(62, led.width, 2))
        ).Else(
            If(counter == Int(13499999, counter.width, 16))(
                led(Cat(led[0:led.width-1], led[led.width-1]))
            )
        )
    )

    return m


m = create_contador_leds()
m.to_verilog(m.name + ".v")
