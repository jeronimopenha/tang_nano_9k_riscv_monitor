from veriloggen import *
from math import ceil, log2

import util as _u


class Riscv:
    _instance = None

    def __init__(
        self, data_width: int = 32, ram_depth: int = 5, inst_ram_depth: int = 6
    ):
        self.data_width = data_width
        self.ram_depth = ram_depth
        self.inst_ram_depth = inst_ram_depth
        self.cache = {}

    def get_riscv(
        self, data_width: int = 32, ram_depth: int = 5, inst_ram_depth: int = 6
    ):
        self.data_width = data_width
        self.ram_depth = ram_depth
        self.inst_ram_depth = inst_ram_depth

        name = "riscv_rd_%d_ird_%d" % (
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

        m_add = self.create_decode()
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

    def create_fetch(self) -> Module:
        data_width = self.data_width

        name = "fetch"
        if name in self.cache.keys():
            return self.cache[name]
        m = Module(name)

        clk = m.Input("clk")
        rst = m.Input("rst")
        zero = m.Input('zero')
        branch = m.Input('branch')
        sigext = m.Input('sigext', data_width)
        inst = m.Output('isnt', data_width)

        pc = m.Wire('pc')
        pc_4 = m.Wire('pc_4')
        new_pc = m.Wire('new_pc')

        m.EmbeddedCode('')

        pc_4.assign(Int(4, data_width, 10) + pc)
        new_pc.assign(Mux(AndList(branch, zero), pc+sigext, pc_4))

        m_pc = self.create_pc()
        par = []
        con = [
            ('clk', clk),
            ('rst', rst),
            ('pc_in', new_pc),
            ('pc_out', pc)
        ]
        m.Instance(m_pc, m.name, par, con)

        self.cache[name] = m
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
            pc_out(pc_in),
            If(~rst)(
                pc_out(Int(0, pc_out.width, 10))
            )
        )
        self.cache[name] = m
        return m

    def create_decode(self) -> Module:
        data_width = self.data_width
        reg_add_width = 5

        name = "decode"
        if name in self.cache.keys():
            return self.cache[name]
        m = Module(name)

        clk = m.Input("clk")
        inst = m.Input("inst", data_width)
        writedata = m.Input("writedata", data_width)
        data1 = m.Output('data1', data_width)
        data2 = m.Output('data2', data_width)
        immgen = m.Output('immgen', data_width)
        alusrc = m.Output('alusrc')
        memread = m.Output('memread')
        memwrite = m.Output('memwrite')
        memtoreg = m.Output('memtoreg')
        branch = m.Output('branch')
        aluop = m.Output('aluop', 2)
        funct = m.Output('funct', 10)

        regwrite = m.Wire('regwrite')
        writereg = m.Wire('writereg', reg_add_width)
        rs1 = m.Wire('rs1', reg_add_width)
        rs2 = m.Wire('rs2', reg_add_width)
        rd = m.Wire('rd', reg_add_width)
        opcode = m.Wire('opcode', 7)
        funct7 = m.Wire('funct7', 7)
        funct3 = m.Wire('funct3', 3)

        m.EmbeddedCode('')
        opcode.assign(inst[0:7])
        rs1.assign(inst[15:20])
        rs2.assign(inst[20:25])
        rd.assign(inst[7:12])
        funct7.assign(inst[25:32])
        funct3.assign(inst[12:15])
        funct.assign(inst[Cat(funct7, funct3)])

        m_uc = self.create_control_unit()
        par = []
        con = [
            ('opcode', opcode),
            ('inst', inst),
            ('alusrc', alusrc),
            ('memtoreg', memtoreg),
            ('regwrite', regwrite),
            ('memread', memread),
            ('memwrite', memwrite),
            ('branch', branch),
            ('aluop', aluop),
            ('immgen', immgen)
        ]
        m.Instance(m_uc, m_uc.name, par, con)

        m_reg_bank = self.create_register_bank()
        con = [
            ('clk', clk),
            ('regwrite', regwrite),
            ('read_reg1', rs1),
            ('read_reg2', rs2),
            ('write_reg', rd),
            ('writedata', writedata),
            ('read_data1', data1),
            ('read_data2', data2),
        ]
        m.Instance(m_reg_bank, m_reg_bank.name, par, con)

        self.cache[name] = m
        return m

    def create_control_unit(self) -> Module:
        data_width = self.data_width
        reg_add_width = 5

        name = "control_unit"
        if name in self.cache.keys():
            return self.cache[name]
        m = Module(name)

        opcode = m.Input('opcode', 7)
        inst = m.Input('inst', data_width)
        alusrc = m.OutputReg('alusrc')
        memtoreg = m.OutputReg('memtoreg')
        regwrite = m.OutputReg('regwrite')
        memread = m.OutputReg('memread')
        memwrite = m.OutputReg('memwrite')
        branch = m.OutputReg('branch')
        aluop = m.OutputReg('aluop', 2)
        immgen = m.OutputReg('immgen', data_width)

        m.EmbeddedCode('')
        catbits = m.Wire('catbits', 19)
        catbits.assign(Mux(inst[31], Int(
            (2**catbits.width)-1, catbits.width, 2), Int(0, catbits.width, 2)))

        m.Always()(
            alusrc(Int(0, 1, 10)),
            memtoreg(Int(0, 1, 10)),
            regwrite(Int(0, 1, 10)),
            memread(Int(0, 1, 10)),
            memwrite(Int(0, 1, 10)),
            branch(Int(0, 1, 10)),
            aluop(Int(0, aluop.width, 10)),
            immgen(Int(0, immgen.width, 10)),
            Case(opcode)(
                When(Int(51, 7, 2))(
                    regwrite(Int(1, 1, 10)),
                    aluop(Int(2, aluop.width, 10))
                ),
                When(Int(99, 7, 2))(
                    branch(Int(1, 1, 10)),
                    aluop(Int(1, aluop.width, 10)),
                    immgen(
                        Cat(catbits, inst[31], inst[7], inst[25:31], inst[8:12], Int(0, 1, 2)))
                ),
                When(Int(19, 7, 2))(
                    alusrc(Int(1, 1, 10)),
                    regwrite(Int(1, 1, 10)),
                    aluop(Int(3, aluop.width, 10)),
                    immgen(Cat(inst[31], catbits, inst[20:32]))
                ),
                When(Int(3, 7, 2))(
                    alusrc(Int(1, 1, 10)),
                    memtoreg(Int(1, 1, 10)),
                    regwrite(Int(1, 1, 10)),
                    memread(Int(1, 1, 10)),
                    immgen(Cat(inst[31], catbits, inst[20:32]))
                ),
                When(Int(35, 7, 2))(
                    alusrc(Int(1, 1, 10)),
                    memwrite(Int(1, 1, 10)),
                    immgen(Cat(inst[31], catbits, inst[25:32], inst[7:12]))
                ),
            )

        )

        self.cache[name] = m
        return m

    def create_register_bank(self) -> Module:
        data_width = self.data_width
        reg_add_width = 5
        n_regs = 32

        name = "register_bank"
        if name in self.cache.keys():
            return self.cache[name]
        m = Module(name)

        clk = m.Input('clk')
        regwrite = m.Input('regwrite')
        read_reg1 = m.Input('read_reg1', reg_add_width)
        read_reg2 = m.Input('read_reg2', reg_add_width)
        write_reg = m.Input('write_reg', reg_add_width)
        writedata = m.Input('writedata', data_width)
        read_data1 = m.Output('read_data1', data_width)
        read_data2 = m.Output('read_data2', data_width)

        reg_bank = m.Reg('reg_bank', data_width, n_regs)

        m.EmbeddedCode('')

        read_data1.assign(reg_bank[read_reg1])
        read_data2.assign(reg_bank[read_reg2])

        m.Always(Posedge(clk))(
            If(regwrite)(
                reg_bank[write_reg](writedata)
            )
        )

        self.cache[name] = m
        return m

    def create_execute(self) -> Module:
        data_width = self.data_width

        name = "execute"
        if name in self.cache.keys():
            return self.cache[name]
        m = Module(name)

        in1 = m.Input('in1', data_width)
        in2 = m.Input('in2', data_width)
        immgen = m.Input('immgen', data_width)
        alusrc = m.Input('alusrc')
        aluop = m.Input('aluop', 2)
        funct = m.Input('funct', 10)
        zero = m.Output('zero')
        aluout = m.Output('aluout', data_width)

        alu_b = m.Wire('alub', data_width)
        aluctrl = m.Wire('aluctrl', 4)

        m.EmbeddedCode('')

        alu_b.assign(Mux(alusrc, immgen, in2))
        zero1 = m.Wire('zero1')
        f3 = m.Wire('f3', 3)
        f3.assign(funct[0:3])

        zero.assign(
            Mux(f3 == Int(0, f3.width, 2), zero1,
                Mux(f3 == Int(1, f3.width, 2), ~zero1,
                    Mux(f3 == Int(4, f3.width, 2), aluout[31],
                        Mux(f3 == Int(5, f3.width, 2), ~aluout[31],
                            Mux(f3 == Int(6, f3.width, 2), in1 < alu_b,
                                Mux(f3 == Int(7, f3.width, 2), ~(in1 < alu_b), 0)
                                )
                            )
                        )
                    )
                )
        )

        m_alucontrol = self.create_alucontrol()
        par = []
        con = [
            ('aluop', aluop),
            ('funct', funct),
            ('alucontrol', aluctrl),
        ]
        m.Instance(m_alucontrol, m_alucontrol.name, par, con)

        m_alu = self.create_alu()
        con = [
            ('alucontrol', aluctrl),
            ('a', in1),
            ('b', alu_b),
            ('aluout', aluout),
            ('zero', zero1),
        ]
        m.Instance(m_alu, m_alu.name, par, con)

        self.cache[name] = m
        return m

    def create_alucontrol(self) -> Module:
        data_width = self.data_width

        name = "alucontrol"
        if name in self.cache.keys():
            return self.cache[name]
        m = Module(name)

        aluop = m.Input('aluop', 2)
        funct = m.Input('funct', 10)
        alucontrol = m.Input('alucontrol', 4)

        funct7 = m.Wire('funct7', 8)
        funct3 = m.Wire('funct3', 3)
        aluopcode = m.Wire('aluopcode', 4)

        m.EmbeddedCode('')

        funct3.assign(funct[0:3])
        funct7.assign(funct[3:10])
        aluopcode.assign(Cat(funct[5], funct3))

        m.Always()(
            Case(aluop)(
                When(Int(0, aluop.width, 10))(
                    alucontrol(Int(2, alucontrol.width, 10))

                ),
                When(Int(1, aluop.width, 10))(
                    alucontrol(Int(6, alucontrol.width, 10))
                ),
                When(Int(2, aluop.width, 10))(
                    Case(funct3)(
                        When(Int(0, funct3.width, 10))(
                            alucontrol(Mux(funct7 == 0, Int(2, alucontrol.width, 10),
                                           Int(6, alucontrol.width, 10)))
                        ),
                        When(Int(1, funct3.width, 10))(
                            alucontrol(Int(3, alucontrol.width, 10))
                        ),
                        When(Int(2, funct3.width, 10))(
                            alucontrol(Int(7, alucontrol.width, 10))
                        ),
                        When(Int(3, funct3.width, 10))(
                            alucontrol(Int(9, alucontrol.width, 10))
                        ),
                        When(Int(4, funct3.width, 10))(
                            alucontrol(Int(4, alucontrol.width, 10))

                        ),
                        When(Int(5, funct3.width, 10))(
                            alucontrol(
                                Mux(funct7[5], Int(5, alucontrol.width, 10), Int(8, alucontrol.width, 10)))
                        ),
                        When(Int(6, funct3.width, 10))(
                            alucontrol(Int(1, alucontrol.width, 10))
                        ),
                        When(Int(7, funct3.width, 10))(
                            alucontrol(Int(0, alucontrol.width, 10))
                        ),
                        When()(
                            alucontrol(Int(15, alucontrol.width, 10))
                        ),
                    )
                ),
                When(Int(3, aluop.width, 10))(
                    Case(funct3)(
                        When(Int(0, funct3.width, 10))(
                            alucontrol(Int(2, alucontrol.width, 10))
                        ),
                        When(Int(1, funct3.width, 10))(
                            alucontrol(Int(3, alucontrol.width, 10))
                        ),
                        When(Int(2, funct3.width, 10))(
                            alucontrol(Int(7, alucontrol.width, 10))
                        ),
                        When(Int(3, funct3.width, 10))(
                            alucontrol(Int(9, alucontrol.width, 10))
                        ),
                        When(Int(4, funct3.width, 10))(
                            alucontrol(Int(4, alucontrol.width, 10))
                        ),
                        When(Int(5, funct3.width, 10))(
                            alucontrol(
                                Mux(funct7[5], Int(5, alucontrol.width, 10), Int(8, alucontrol.width, 10)))
                        ),
                        When(Int(6, funct3.width, 10))(
                            alucontrol(Int(1, alucontrol.width, 10))
                        ),
                        When(Int(7, funct3.width, 10))(
                            alucontrol(Int(0, alucontrol.width, 10))
                        ),
                        When()(
                            alucontrol(Int(15, alucontrol.width, 10))
                        ),
                    )
                ),
            )
        )

        self.cache[name] = m
        return m

    def create_alu(self) -> Module:
        data_width = self.data_width

        name = "alu"
        if name in self.cache.keys():
            return self.cache[name]
        m = Module(name)

        alucontrol = m.Input('alucontrol')
        a = m.Input('a')
        b = m.Input('b')
        aluout = m.Output('aluout')
        zero = m.Output('zero')

        zero.assign(aluout == 0)

        m.EmbeddedCode('')

        t = m.Wire('t', data_width)
        sh = m.Wire('sh', data_width)
        p = m.Wire('p', data_width)


        m_slt = self.create_slt()
        


        self.cache[name] = m
        return m

    def create_slt(self) -> Module:
        data_width = self.data_width

        name = "slt"
        if name in self.cache.keys():
            return self.cache[name]
        m = Module(name)

        
        a = m.Input('a', data_width)
        b = m.Input('b', data_width)
        s = m.Output('s', data_width)
        

        self.cache[name] = m
        return m

    def create_shiftra(self) -> Module:
        data_width = self.data_width

        name = "alu"
        if name in self.cache.keys():
            return self.cache[name]
        m = Module(name)

        alucontrol = m.Input('alucontrol')
        a = m.Input('a')
        b = m.Input('b')
        aluout = m.Output('aluout')
        zero = m.Output('zero')

        self.cache[name] = m
        return m


riscv = Riscv()
# mips.get_riscv().to_verilog('mips.v')
riscv.create_execute().to_verilog('risc.v')
