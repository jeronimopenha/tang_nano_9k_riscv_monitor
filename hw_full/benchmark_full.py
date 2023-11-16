from veriloggen import *
from interface_full import Interface
from math import ceil, log2
import util_full as _u


def testbench(serial_width: int = 8,
              data_width: int = 32,
              ram_depth: int = 5,
              inst_ram_depth: int = 5,
              fifo_depth: int = 2,
              sys_clock: float = 27.0,
              baudrate: float = 3.0
              ):

    interface = Interface(data_width=data_width,
                          serial_width=serial_width,
                          ram_depth=ram_depth,
                          inst_ram_depth=inst_ram_depth,
                          fifo_depth=fifo_depth,
                          sys_clock=sys_clock,
                          baudrate=baudrate)
    components = interface.components
    par = []

    m = Module("tang_nano_9k_riscv_monitor_testbench")
    clk = m.Reg('clk')
    rst = m.Reg('rst')

    led = m.Wire('led', 6)

    m.EmbeddedCode('')
    m.EmbeddedCode('// Uart rx wires and regs')
    uart_rx = m.Wire('uart_rx')
    uart_rx_bsy = m.Wire('uart_rx_bsy')
    uart_rx_block_timeout = m.Wire('uart_rx_block_timeout')
    uart_rx_data_valid = m.Wire('uart_rx_data_valid')
    uart_rx_data_out = m.Wire('uart_rx_data_out', serial_width)
    m.EmbeddedCode('// Uart rx wires and regs -----')

    m.EmbeddedCode('')
    m.EmbeddedCode('// Uart tx wires and regs')
    uart_tx_send_trig = m.Reg('uart_tx_send_trig')
    uart_tx_send_data = m.Reg('uart_tx_send_data',)
    uart_tx = m.Wire('uart_tx')
    uart_tx_bsy = m.Wire('uart_tx_bsy')
    m.EmbeddedCode('// Uart tx wires and regs -----')

    m.EmbeddedCode('')
    m.EmbeddedCode('//Transfer configuration controller')

    

    m.EmbeddedCode('//Transfer configuration controller -----')

    m.EmbeddedCode('')
    m.EmbeddedCode('// Receive data display controller')
    counter_rx = m.Reg('counter_rx', 1 + ceil(log2(data_width/serial_width)))
    word_received = m.Reg('word_received', data_width)

    m.Always(Posedge(clk))(
        If(rst)(
            counter_rx(Int(0, counter_rx.width, 10)),
            word_received(Int(0, word_received.width, 10))
        ).Else(
            If(uart_rx_data_valid)(
                word_received(
                    Cat(uart_rx_data_out, word_received[uart_rx_data_out.width: word_received.width])),
                If(counter_rx == Int((data_width//serial_width)-1, counter_rx.width, 10))(
                    counter_rx(Int(0, counter_rx.width, 10)),
                    Display("%x\\n", word_received)
                ).Else(
                    counter_rx(counter_rx + Int(1, counter_rx.width, 10))
                )
            ),
        )
    )
    m.EmbeddedCode('// Receive data display controller -----')

    m.EmbeddedCode('// Uart rx module instantiation')
    m_aux = components.get_uart_rx()
    con = [
        ('clk', clk),
        ('rst', rst),
        ('rx', uart_rx),
        ('rx_bsy', uart_rx_bsy),
        ('block_timeout', uart_rx_block_timeout),
        ('data_valid', uart_rx_data_valid),
        ('data_out', uart_rx_data_out),
    ]
    m.Instance(m_aux, 'm_' + m_aux.name, par, con)
    m.EmbeddedCode('// Uart rx module instantiation -----')

    m.EmbeddedCode('// Uart tx module instantiation')
    m_aux = components.get_uart_tx()
    con = [
        ('clk', clk),
        ('rst', rst),
        ('send_trig', uart_tx_send_trig),
        ('send_data', uart_tx_send_data),
        ('tx', uart_tx),
        ('tx_bsy', uart_tx_bsy),
    ]
    m.Instance(m_aux, 'm_' + m_aux.name, par, con)
    m.EmbeddedCode('// Uart tx module instantiation -----')

    m.EmbeddedCode('//Config mem instantiation')

    m_aux = .components

    m.EmbeddedCode('//Config mem instantiation -----')

    # interface
    m_aux = interface.get_interface()
    con = [
        ('clk', clk),
        ('btn_rst', rst),
        ('uart_rx', uart_rx),
        ('led', led),
        ('uart_tx', uart_tx)
    ]
    # m.Instance(m_aux, m_aux.name, par, con)
    # interface -----

    _u.initialize_regs(m, {'rst': 0})

    simulation.setup_waveform(m)

    m.Initial(
        EmbeddedCode('@(posedge clk);'),
        EmbeddedCode('@(posedge clk);'),
        EmbeddedCode('@(posedge clk);'),
        rst(1),
        Delay(1000000), Finish()
    )
    m.EmbeddedCode('always #5clk=~clk;')

    m.to_verilog(m.name+'.v')
    # sim = simulation.Simulator(m, sim='iverilog')
    # rslt = sim.run()
    # print(rslt)

    return m


testbench()
