from veriloggen import *
from math import ceil, log2

import util as _u


class Mips:
    _instance = None

    def __init__(
        self,
    ):
        self.cache = {}

    def get_mips(
        self, data_width: int = 32, ram_depth: int = 5, inst_ram_depth: int = 6
    ):
        self.data_width = data_width
        self.ram_depth = ram_depth
        self.inst_ram_depth = inst_ram_depth

        name = "mips_rd_%d_ird_%d" % (
            self.ram_depth,
            self.inst_ram_depth,
        )
        if name in self.cache.keys():
            return self.cache[name]
        m = Module(name)

        clk = m.Input("clk")
        rst = m.Input("rst")

        pc_in = m.Wire("pc_in", self.data_width)
        pc_out = m.Wire("pc_out", self.data_width)
        pc_4_out = m.Wire("pc_4_out", self.data_width)
        inst_out = m.Wire('inst_out', self.data_width)
        shl2_jump_out = m.Wire('shl2_jump_out', self.data_width)
        jump_add = m.Wire('jump_add', self.data_width)
        c_jump = m.Wire('c_jump')

        m.EmbeddedCode('')
        jump_add.assign(Cat(pc_4_out[28:32], shl2_jump_out[0:28]))

        m_pc = self.create_pc()
        par = []
        con = [
            ("clk", clk),
            ("rst", rst),
            ("pc_in", pc_in),
            ("pc_out", pc_out)
        ]
        m.Instance(m_pc, m_pc.name, par, con)

        m_add = self.create_add()
        con = [
            ("add0_in", pc_out),
            ("add1_in", Int(4, pc_out.width, 10)),
            ("add_out", pc_4_out)
        ]
        m.Instance(m_add, m_add.name + "4", par, con)

        m_shl2 = self.create_shift_left_2()
        con = [
            ("shl2_in", Cat(Int(0, 6, 10), inst_out[0:26])),
            ("shl2_out", shl2_jump_out)
        ]
        m.Instance(m_shl2, m_shl2.name + "_jump", par, con)

        m_mux21 = self.create_mux21()
        con = [
            ('mux_sel', c_jump),
            ('mux0_in',),
            ('mux1_in',),
            ('mux_out',)
        ]
        m.Instance(m_mux21, m_mux21.name + "_mux_jump", par, con)

        return m

    def create_pc(self) -> Module:
        data_width = self.data_width

        name = "pc"
        if name in self.cache.keys():
            return self.cache[name]
        m = Module(name)

        clk = m.Input("clk")
        rst = m.Input("rst")
        pc_in = m.Input("pc_in", data_width)
        pc_out = m.OutputReg("pc_out", data_width)

        m.Always(Posedge(clk))(
            If(rst)(pc_out(Int(0, pc_out.width, 10))).Else(pc_out(pc_in))
        )
        self.cache[name] = m
        return m

    def create_add(self) -> Module:
        data_width = self.data_width

        name = "add"
        if name in self.cache.keys():
            return self.cache[name]
        m = Module(name)

        add0_in = m.Input("add0_in", data_width)
        add1_in = m.Input("add1_in", data_width)
        add_out = m.Output("add_out", data_width)

        add_out.assign(add0_in + add1_in)

        self.cache[name] = m
        return m

    def create_shift_left_2(self) -> Module:
        data_width = self.data_width

        name = "shift_left_2"
        if name in self.cache.keys():
            return self.cache[name]
        m = Module(name)

        shl2_in = m.Input("shl2_in", data_width)
        shl2_out = m.Output("shl2_out", data_width)

        shl2_out.assign(Cat(shl2_in[2:shl2_in.width], Int(0, 2, 10)))

        self.cache[name] = m
        return m

    def create_mux21(self) -> Module:
        data_width = self.data_width

        name = "mux21"
        if name in self.cache.keys():
            return self.cache[name]
        m = Module(name)

        mux_sel = m.Input('Mux_sel')
        mux0_in = m.Input("mux0_in", data_width)
        mux1_in = m.Input("mux1_in", data_width)
        mux_out = m.Output("mux_out", data_width)

        mux_out.assign(Mux(mux_sel, mux1_in, mux0_in))

        self.cache[name] = m
        return m


mips = Mips()
mips.get_mips().to_verilog('mips.v')
