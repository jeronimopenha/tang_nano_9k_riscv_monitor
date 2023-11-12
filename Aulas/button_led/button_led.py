from veriloggen import *


def create_contador_leds():
    m = Module("button_leds")
    clk = m.Input('clk_27mhz')
    btn_in = m.Input('button_s1')
    uart_rx = m.Input('uart_rx')
    led = m.Output('led', 6)
    uart_tx = m.Output('uart_tx')

    m.EmbeddedCode('// Reset signal control')
    btn_wire = m.Wire('btn_wire')
    btn_wire.assign(~btn_in)

    m.EmbeddedCode('')
    counter_led = m.Reg('counter_led', 6)
    led.assign(~counter_led)

    m.EmbeddedCode('')
    counter_debounce = m.Reg('counter_debounce', 23)
    PAR_4HZ = m.Localparam('PAR_4HZ', Int(
        1000000-1, counter_debounce.width, 16), counter_debounce.width)
    
    m.EmbeddedCode('')
    btn_signal = m.Reg('btn_signal')
    btn_active = m.Wire('btn_active')
    ffd1 = m.Reg('ffd1')
    ffd2 = m.Reg('ffd2')
    btn_active.assign(Uand(Cat(ffd1, ~ffd2)))
    m.EmbeddedCode('')

    m.Always(Posedge(clk))(
        If(counter_debounce < PAR_4HZ)(
            counter_debounce(counter_debounce +
                             Int(1, counter_debounce.width, 2))
        ).Else(
            btn_signal(~btn_signal),
            counter_debounce(Int(0, counter_debounce.width, 2))
        )
    )

    m.Always(Posedge(btn_signal))(
        ffd1(btn_wire),
        ffd2(ffd1),
    )

    m.Always(Posedge(btn_active))(
        counter_led(counter_led + Int(1, counter_led.width, 2))
    )

    return m


m = create_contador_leds()
m.to_verilog(m.name + ".v")
