from veriloggen import *

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

        monitor_read_on = m.Input('monitor_read_on')
        monitor_write_on = m.Input('monitor_write_on')
        monitor_addr = m.Input('monitor_addr', 8)
        mem_dataout = m.Output('mem_dataout', 8)
        reg_dataout = m.Output('reg_dataout', 8)

        writedata = m.Wire('writedata', data_width)
        inst = m.Wire('inst', data_width)
        sigext = m.Wire('sigext', data_width)
        data1 = m.Wire('data1', data_width)
        data2 = m.Wire('data2', data_width)
        aluout = m.Wire('aluout', data_width)
        readdata = m.Wire('readdata', data_width)
        zero = m.Wire('zero')
        memread = m.Wire('memread')
        memwrite = m.Wire('memwrite')
        memtoreg = m.Wire('memtoreg')
        branch = m.Wire('branch')
        alusrc = m.Wire('alusrc')
        funct = m.Wire('funct', 10)
        aluop = m.Wire('aluop', 2)

        m.EmbeddedCode(
            '// adaptacao para a interface serial controlar a execução do riscV')
        m.EmbeddedCode('// estágio de memoria')
        mrd = m.Wire('mrd')
        maddr = m.Wire('maddr', data_width)
        mrd.assign(Uor(Cat(memread, monitor_read_on)))
        maddr.assign(Mux(monitor_read_on, Cat(
            Int(0, 24, 10), monitor_addr), aluout))
        mem_dataout.assign(readdata[0:8])
        m.EmbeddedCode('//*')
        m.EmbeddedCode('// estágio de decode')
        reg_dataout.assign(data1[0:8])
        m.EmbeddedCode('//*')
        m.EmbeddedCode('//*****')

        m_fetch = self.create_fetch()
        par = []
        con = [
            ('clk', clk),
            ('rst', rst),
            ('zero', zero),
            ('branch', branch),
            ('sigext', sigext),
            ('inst', inst)
        ]
        m.Instance(m_fetch, m_fetch.name, par, con)

        m_decode = self.create_decode()
        con = [
            ('clk', clk),
            ('inst', inst),
            ('writedata', writedata),
            ('data1', data1),
            ('data2', data2),
            ('immgen', sigext),
            ('alusrc', alusrc),
            ('memread', memread),
            ('memwrite', memwrite),
            ('memtoreg', memtoreg),
            ('branch', branch),
            ('aluop', aluop),
            ('funct', funct),
            ('monitor_read_on', monitor_read_on),
            ('monitor_addr', monitor_addr[0:5]),
        ]
        m.Instance(m_decode, m_decode.name, par, con)

        m_exec = self.create_execute()
        par = []
        con = [
            ('in1', data1),
            ('in2', data2),
            ('immgen', sigext),
            ('alusrc', alusrc),
            ('aluop', aluop),
            ('funct', funct),
            ('zero', zero),
            ('aluout', aluout),
        ]
        m.Instance(m_exec, m_exec.name, par, con)

        m_memory = self.create_memory()
        con = [
            ('clk', clk),
            ('address', maddr),
            ('writedata', data2),
            ('memread', mrd),
            ('memwrite', memwrite),
            ('readdata', readdata),
        ]
        m.Instance(m_memory, m_memory.name, par, con)

        m_writeback = self.create_writeback()
        con = [
            ('aluout', aluout),
            ('readdata', readdata),
            ('memtoreg', memtoreg),
            ('writedata', writedata),
        ]
        m.Instance(m_writeback, m_writeback.name, par, con)

        _u.initialize_regs(m)
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
        inst = m.Output('inst', data_width)

        pc = m.Wire('pc', data_width)
        pc_4 = m.Wire('pc_4', data_width)
        new_pc = m.Wire('new_pc', data_width)

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


        m_memory = self.create_memory()
        con = [
            ('clk', clk),
            ('address', pc[2:data_width]),
            #('writedata', data2),
            ('memread', Int(1,1,2)),
            ('memwrite', Int(0,1,2)),
            ('readdata', inst),
        ]
        m.Instance(m_memory, m_memory.name, par, con)

        '''
        sub x0,x0,x0
        sub x0,x0,x0
        addi x1,x0,1
        addi x2,x0,2
        addi x3,x0,3
        addi x4,x0,4
        addi x5,x0,5
        addi x6,x0,6
        addi x7,x0,7
        addi x8,x0,8
        addi x9,x0,9
        addi x10,x0,10
        addi x11,x0,11
        sub x5,x5,x5
        sub x3,x3,x3
        sub x8,x8,x8
        addi x2,x0,2
        addi x9,x0,9
        add x7,x2,x9
        '''

        '''
        40000033 40000033 00100093
        00200113
        00300193
        00400213
        00500293
        00600313
        00700393
        00800413
        00900493
        00a00513
        00b00593
        405282b3
        403181b3
        40840433
        00200113
        00900493
        009103b3

        '''

        # _u.initialize_regs(m)

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
            If(rst)(
                pc_out(Int(0, pc_out.width, 10))
            )
        )
        self.cache[name] = m

        _u.initialize_regs(m)

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

        monitor_read_on = m.Input('monitor_read_on')
        monitor_addr = m.Input('monitor_addr', 5)

        regwrite = m.Wire('regwrite')
        # writereg = m.Wire('writereg', reg_add_width)
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
        funct.assign(Cat(funct7, funct3))

        m.EmbeddedCode(
            '// adaptacao para a interface serial controlar a execução do riscV')
        rraddr = m.Wire('raddr', 5)
        rraddr.assign(Mux(monitor_read_on, monitor_addr, rs1))
        m.EmbeddedCode('// *****')

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
            ('read_reg1', rraddr),
            ('read_reg2', rs2),
            ('write_reg', rd),
            ('writedata', writedata),
            ('read_data1', data1),
            ('read_data2', data2),
        ]
        m.Instance(m_reg_bank, m_reg_bank.name, par, con)

        _u.initialize_regs(m)

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

        _u.initialize_regs(m)

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

        _u.initialize_regs(m)

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

        _u.initialize_regs(m)

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
        alucontrol = m.OutputReg('alucontrol', 4)

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

        _u.initialize_regs(m)

        return m

    def create_alu(self) -> Module:
        data_width = self.data_width

        name = "alu"
        if name in self.cache.keys():
            return self.cache[name]
        m = Module(name)

        alucontrol = m.Input('alucontrol', 4)
        a = m.Input('a', data_width)
        b = m.Input('b', data_width)
        aluout = m.OutputReg('aluout', data_width)
        zero = m.Output('zero')

        zero.assign(aluout == 0)

        m.EmbeddedCode('')

        t = m.Wire('t', data_width)
        sh = m.Wire('sh', data_width)
        p = m.Wire('p', data_width)

        m_slt = self.create_slt()
        par = []
        con = [
            ('a', a),
            ('b', b),
            ('s', t)
        ]
        m.Instance(m_slt, m_slt.name, par, con)

        m_shiftra = self.create_shiftra()
        con = [
            ('a', a),
            ('b', b[0:5]),
            ('o', sh)
        ]
        m.Instance(m_shiftra, m_shiftra.name, par, con)

        m.Always()(
            Case(alucontrol)(
                When(Int(0, alucontrol.width, 10))(
                    aluout(a & b)
                ),
                When(Int(1, alucontrol.width, 10))(
                    aluout(a | b)
                ),
                When(Int(2, alucontrol.width, 10))(
                    aluout(a+b)
                ),
                When(Int(3, alucontrol.width, 10))(
                    aluout(a << b[0:5])
                ),
                When(Int(4, alucontrol.width, 10))(
                    aluout(a ^ b)
                ),
                When(Int(5, alucontrol.width, 10))(
                    aluout(sh)
                ),
                When(Int(6, alucontrol.width, 10))(
                    aluout(a-b)
                ),
                When(Int(7, alucontrol.width, 10))(
                    aluout(t)
                ),
                When(Int(8, alucontrol.width, 10))(
                    aluout(a >> b[0:5])
                ),
                When(Int(9, alucontrol.width, 10))(
                    aluout(a < b)
                ),
                When()(
                    aluout(Int(0, aluout.width, 10))
                ),
            )
        )

        self.cache[name] = m

        _u.initialize_regs(m)

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

        sub = m.Wire('sub', data_width)
        sub.assign(a-b)
        s.assign(Mux(sub[31], Int(1, data_width, 10), Int(0, data_width, 10)))

        self.cache[name] = m

        _u.initialize_regs(m)

        return m

    def create_shiftra(self) -> Module:
        data_width = self.data_width

        name = "shiftra"
        if name in self.cache.keys():
            return self.cache[name]
        m = Module(name)

        a = m.Input('a', data_width)
        b = m.Input('b', 5)
        o = m.Output('o', data_width)

        s = m.Wire('s', data_width)
        t = m.Wire('t', data_width)
        _m = m.Wire('m', data_width)

        m.EmbeddedCode('')

        _m.assign(Int((2**data_width)-1, data_width, 2))
        s.assign(_m >> b)
        t.assign(a >> b)
        o.assign(Mux(a[31], (~s | t), t))

        self.cache[name] = m

        _u.initialize_regs(m)

        return m

    def create_memory(self) -> Module:
        data_width = self.data_width

        name = "memory"
        if name in self.cache.keys():
            return self.cache[name]
        m = Module(name)

        clk = m.Input('clk')
        address = m.Input('address', data_width)
        writedata = m.Input('writedata', data_width)
        memread = m.Input('memread')
        memwrite = m.Input('memwrite')
        readdata = m.Output('readdata', data_width)

        memory = m.Reg('memory', data_width, 2**self.ram_depth)

        m.EmbeddedCode('')

        readdata.assign(
            Mux(memread, memory[address[2:data_width]], Int(0, data_width, 10)))

        m.Always(Posedge(clk))(
            If(memwrite)(
                memory[address[2:data_width]](writedata)
            )
        )

        self.cache[name] = m

        # _u.initialize_regs(m)

        return m

    def create_writeback(self) -> Module:
        data_width = self.data_width

        name = "writeback"
        if name in self.cache.keys():
            return self.cache[name]
        m = Module(name)

        aluout = m.Input('aluout', data_width)
        readdata = m.Input('readdata', data_width)
        memtoreg = m.Input('memtoreg')
        writedata = m.Output('writedata', data_width)

        writedata.assign(Mux(memtoreg, readdata, aluout))

        self.cache[name] = m

        _u.initialize_regs(m)

        return m

    def testbench(self):
        m = Module(
            "risc_test_bench")
        clk = m.Reg('clk')
        rst = m.Reg('rst')

        m_riscv = self.get_riscv()
        par = []
        con = [
            ('clk', clk),
            ('rst', rst),
            ('monitor_read_on', 0),
            ('monitor_addr', 0)
        ]
        m.Instance(m_riscv, m_riscv.name, par, con)

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

        m.to_verilog('riscv_test.v')
        # sim = simulation.Simulator(m, sim='iverilog')
        # rslt = sim.run()
        # print(rslt)

        return m

