

module riscv_rd_5_ird_6
(
  input clk,
  input rst
);

  wire [32-1:0] writedata;
  wire [32-1:0] inst;
  wire [32-1:0] sigext;
  wire [32-1:0] data1;
  wire [32-1:0] data2;
  wire [32-1:0] aluout;
  wire [32-1:0] readdata;
  wire zero;
  wire memread;
  wire memwrite;
  wire memtoreg;
  wire branch;
  wire alusrc;
  wire [10-1:0] funct;
  wire [2-1:0] aluop;

  fetch
  fetch
  (
    .clk(clk),
    .rst(rst),
    .zero(zero),
    .branch(branch),
    .sigext(sigext),
    .inst(inst)
  );


  decode
  decode
  (
    .clk(clk),
    .inst(inst),
    .writedata(writedata),
    .data1(data1),
    .data2(data2),
    .immgen(sigext),
    .alusrc(alusrc),
    .memread(memread),
    .memwrite(memwrite),
    .memtoreg(memtoreg),
    .branch(branch),
    .aluop(aluop),
    .funct(funct)
  );


  memory
  memory
  (
    .clk(clk),
    .address(aluout),
    .writedata(data2),
    .memread(memread),
    .memwrite(memwrite),
    .readdata(readdata)
  );


  writeback
  writeback
  (
    .aluout(aluout),
    .readdata(readdata),
    .memtoreg(memtoreg),
    .writedata(writedata)
  );


endmodule



module fetch
(
  input clk,
  input rst,
  input zero,
  input branch,
  input [32-1:0] sigext,
  output [32-1:0] inst
);

  wire pc;
  wire pc_4;
  wire new_pc;

  assign pc_4 = 32'd4 + pc;
  assign new_pc = (branch && zero)? pc + sigext : pc_4;

  pc
  fetch
  (
    .clk(clk),
    .rst(rst),
    .pc_in(new_pc),
    .pc_out(pc)
  );


  memory
  memory
  (
    .clk(clk),
    .address(pc[31:2]),
    .memread(1'd1),
    .memwrite(1'd0),
    .readdata(inst)
  );


endmodule



module pc
(
  input clk,
  input rst,
  input [32-1:0] pc_in,
  output reg [32-1:0] pc_out
);


  always @(posedge clk) begin
    pc_out <= pc_in;
    if(~rst) begin
      pc_out <= 32'd0;
    end 
  end


endmodule



module memory
(
  input clk,
  input [32-1:0] address,
  input [32-1:0] writedata,
  input memread,
  input memwrite,
  output [32-1:0] readdata
);

  reg [32-1:0] memory [0:32-1];

  assign readdata = (memread)? memory[address[31:2]] : 32'd0;

  always @(posedge clk) begin
    if(memwrite) begin
      memory[address[31:2]] <= writedata;
    end 
  end


endmodule



module decode
(
  input clk,
  input [32-1:0] inst,
  input [32-1:0] writedata,
  output [32-1:0] data1,
  output [32-1:0] data2,
  output [32-1:0] immgen,
  output alusrc,
  output memread,
  output memwrite,
  output memtoreg,
  output branch,
  output [2-1:0] aluop,
  output [10-1:0] funct
);

  wire regwrite;
  wire [5-1:0] writereg;
  wire [5-1:0] rs1;
  wire [5-1:0] rs2;
  wire [5-1:0] rd;
  wire [7-1:0] opcode;
  wire [7-1:0] funct7;
  wire [3-1:0] funct3;

  assign opcode = inst[6:0];
  assign rs1 = inst[19:15];
  assign rs2 = inst[24:20];
  assign rd = inst[11:7];
  assign funct7 = inst[31:25];
  assign funct3 = inst[14:12];
  assign funct = inst[{ funct7, funct3 }];

  control_unit
  control_unit
  (
    .opcode(opcode),
    .inst(inst),
    .alusrc(alusrc),
    .memtoreg(memtoreg),
    .regwrite(regwrite),
    .memread(memread),
    .memwrite(memwrite),
    .branch(branch),
    .aluop(aluop),
    .immgen(immgen)
  );


  register_bank
  register_bank
  (
    .clk(clk),
    .regwrite(regwrite),
    .read_reg1(rs1),
    .read_reg2(rs2),
    .write_reg(rd),
    .writedata(writedata),
    .read_data1(data1),
    .read_data2(data2)
  );


endmodule



module control_unit
(
  input [7-1:0] opcode,
  input [32-1:0] inst,
  output reg alusrc,
  output reg memtoreg,
  output reg regwrite,
  output reg memread,
  output reg memwrite,
  output reg branch,
  output reg [2-1:0] aluop,
  output reg [32-1:0] immgen
);


  wire [19-1:0] catbits;
  assign catbits = (inst[31])? 19'b1111111111111111111 : 19'b0;

  always @(*) begin
    alusrc <= 1'd0;
    memtoreg <= 1'd0;
    regwrite <= 1'd0;
    memread <= 1'd0;
    memwrite <= 1'd0;
    branch <= 1'd0;
    aluop <= 2'd0;
    immgen <= 32'd0;
    case(opcode)
      7'b110011: begin
        regwrite <= 1'd1;
        aluop <= 2'd2;
      end
      7'b1100011: begin
        branch <= 1'd1;
        aluop <= 2'd1;
        immgen <= { catbits, inst[31], inst[7], inst[30:25], inst[11:8], 1'b0 };
      end
      7'b10011: begin
        alusrc <= 1'd1;
        regwrite <= 1'd1;
        aluop <= 2'd3;
        immgen <= { inst[31], catbits, inst[31:20] };
      end
      7'b11: begin
        alusrc <= 1'd1;
        memtoreg <= 1'd1;
        regwrite <= 1'd1;
        memread <= 1'd1;
        immgen <= { inst[31], catbits, inst[31:20] };
      end
      7'b100011: begin
        alusrc <= 1'd1;
        memwrite <= 1'd1;
        immgen <= { inst[31], catbits, inst[31:25], inst[11:7] };
      end
    endcase
  end


endmodule



module register_bank
(
  input clk,
  input regwrite,
  input [5-1:0] read_reg1,
  input [5-1:0] read_reg2,
  input [5-1:0] write_reg,
  input [32-1:0] writedata,
  output [32-1:0] read_data1,
  output [32-1:0] read_data2
);

  reg [32-1:0] reg_bank [0:32-1];

  assign read_data1 = reg_bank[read_reg1];
  assign read_data2 = reg_bank[read_reg2];

  always @(posedge clk) begin
    if(regwrite) begin
      reg_bank[write_reg] <= writedata;
    end 
  end


endmodule



module writeback
(
  input [32-1:0] aluout,
  input [32-1:0] readdata,
  input memtoreg,
  output [32-1:0] writedata
);

  assign writedata = (memtoreg)? readdata : aluout;

endmodule

