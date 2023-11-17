

module io_riscv_controller
(
  input clk,
  input rst,
  input rx,
  output rx_bsy,
  output tx,
  output tx_bsy
);

  reg risc_rst;
  reg risc_clk;

  // Instantiate the RX controller
  wire rx_block_timeout;
  wire rx_data_valid;
  wire [8-1:0] rx_data_out;

  // Instantiate the TX controller
  reg send_trig;
  reg [8-1:0] send_data;

  // Instantiate the RX fifo
  wire rx_fifo_we;
  wire [8-1:0] rx_fifo_in_data;
  reg rx_fifo_re;
  wire rx_fifo_out_valid;
  wire [8-1:0] rx_fifo_out_data;
  wire rx_fifo_empty;
  // The Rx fifo is controlled by the uart_rx module
  assign rx_fifo_we = rx_data_valid;
  assign rx_fifo_in_data = rx_data_out;

  // Config and read data from riscv
  reg [8-1:0] monitor_addr;
  reg config_on;
  wire [8-1:0] mem_dataout;
  wire [8-1:0] reg_dataout;

  // PC to board protocol
  localparam [8-1:0] PROT_PC_B_RESET = 8'h0;
  localparam [8-1:0] PROT_PC_B_CLOCK = 8'h1;

  // IO and protocol controller
  reg [4-1:0] fsm_io;
  localparam [4-1:0] FSM_IDLE = 4'h0;
  localparam [4-1:0] FSM_DECODE_PROTOCOL = 4'h1;
  localparam [4-1:0] FSM_RESET = 4'h2;
  localparam [4-1:0] FSM_EXEC_CLOCK = 4'h3;
  localparam [4-1:0] FSM_SEND_REG_TAM = 4'h4;
  localparam [4-1:0] FSM_SEND_REG_DATA = 4'h5;
  localparam [4-1:0] FSM_SEND_REG_BYTES = 4'h6;
  localparam [4-1:0] FSM_SEND_MEM_TAM = 4'h7;
  localparam [4-1:0] FSM_SEND_MEM_DATA = 4'h8;
  localparam [4-1:0] FSM_SEND_MEM_BYTES = 4'h9;

  always @(posedge clk) begin
    if(rst) begin
      fsm_io <= FSM_IDLE;
      rx_fifo_re <= 1'b0;
      risc_clk <= 1'b0;
      risc_rst <= 1'b0;
      send_trig <= 1'b0;
      config_on <= 1'b0;
    end else begin
      rx_fifo_re <= 1'b0;
      risc_clk <= 1'b0;
      risc_rst <= 1'b0;
      send_trig <= 1'b0;
      case(fsm_io)
        FSM_IDLE: begin
          if(~rx_fifo_empty) begin
            rx_fifo_re <= 1'b1;
            fsm_io <= FSM_DECODE_PROTOCOL;
          end 
        end
        FSM_DECODE_PROTOCOL: begin
          if(rx_fifo_out_valid) begin
            case(rx_fifo_out_data)
              PROT_PC_B_RESET: begin
                fsm_io <= FSM_RESET;
              end
              PROT_PC_B_CLOCK: begin
                fsm_io <= FSM_EXEC_CLOCK;
              end
              default: begin
                fsm_io <= FSM_IDLE;
              end
            endcase
          end 
        end
        FSM_RESET: begin
          risc_rst <= 1'b1;
          risc_clk <= 1'b1;
          fsm_io <= FSM_IDLE;
        end
        FSM_EXEC_CLOCK: begin
          risc_clk <= 1'b1;
          fsm_io <= FSM_SEND_REG_TAM;
        end
        FSM_SEND_REG_TAM: begin
          if(~tx_bsy) begin
            send_trig <= 1'b1;
            send_data <= 8'd32;
            monitor_addr <= 8'd0;
            fsm_io <= FSM_SEND_REG_DATA;
          end 
        end
        FSM_SEND_REG_DATA: begin
          if(monitor_addr == 32) begin
            config_on <= 1'b0;
            fsm_io <= FSM_IDLE;
          end else begin
            config_on <= 1'b1;
            fsm_io <= FSM_SEND_REG_BYTES;
          end
        end
        FSM_SEND_REG_BYTES: begin
          if(~tx_bsy) begin
            monitor_addr <= monitor_addr + 8'd1;
            send_trig <= 1;
            send_data <= reg_dataout;
            fsm_io <= FSM_SEND_REG_DATA;
          end 
        end
        FSM_SEND_MEM_TAM: begin
          if(~tx_bsy) begin
            send_trig <= 1'b1;
            send_data <= 8'd32;
            monitor_addr <= 8'd0;
            fsm_io <= FSM_SEND_MEM_DATA;
          end 
        end
        FSM_SEND_MEM_DATA: begin
          if(monitor_addr == 32) begin
            config_on <= 1'b0;
            fsm_io <= FSM_IDLE;
          end else begin
            config_on <= 1'b1;
            fsm_io <= FSM_SEND_MEM_BYTES;
          end
        end
        FSM_SEND_MEM_BYTES: begin
          if(~tx_bsy) begin
            monitor_addr <= monitor_addr + 8'd1;
            send_trig <= 1;
            send_data <= mem_dataout;
            fsm_io <= FSM_SEND_MEM_DATA;
          end 
        end
        default: begin
          fsm_io <= FSM_IDLE;
        end
      endcase
    end
  end


  fifo
  #(
    .FIFO_WIDTH(8),
    .FIFO_DEPTH_BITS(5)
  )
  rx_fifo
  (
    .clk(clk),
    .rst(rst),
    .we(rx_fifo_we),
    .in_data(rx_fifo_in_data),
    .re(rx_fifo_re),
    .out_valid(rx_fifo_out_valid),
    .out_data(rx_fifo_out_data),
    .empty(rx_fifo_empty)
  );


  uart_rx
  uart_rx
  (
    .clk(clk),
    .rst(rst),
    .rx(rx),
    .rx_bsy(rx_bsy),
    .block_timeout(rx_block_timeout),
    .data_valid(rx_data_valid),
    .data_out(rx_data_out)
  );


  uart_tx
  uart_tx
  (
    .clk(clk),
    .rst(rst),
    .send_trig(send_trig),
    .send_data(send_data),
    .tx(tx),
    .tx_bsy(tx_bsy)
  );


  riscv_rd_5_ird_6
  riscv_rd_5_ird_6
  (
    .clk(risc_clk),
    .rst(risc_rst),
    .monitor_read_on(config_on),
    .monitor_addr(monitor_addr),
    .mem_dataout(mem_dataout),
    .reg_dataout(reg_dataout)
  );


  initial begin
    risc_rst = 1;
    risc_clk = 0;
    send_trig = 0;
    send_data = 0;
    rx_fifo_re = 0;
    monitor_addr = 0;
    config_on = 0;
    fsm_io = 0;
  end


endmodule



module fifo #
(
  parameter FIFO_WIDTH = 32,
  parameter FIFO_DEPTH_BITS = 2,
  parameter FIFO_ALMOSTFULL_THRESHOLD = 2 ** FIFO_DEPTH_BITS - 2,
  parameter FIFO_ALMOSTEMPTY_THRESHOLD = 2
)
(
  input clk,
  input rst,
  input we,
  input [FIFO_WIDTH-1:0] in_data,
  input re,
  output reg out_valid,
  output reg [FIFO_WIDTH-1:0] out_data,
  output reg empty,
  output reg almostempty,
  output reg full,
  output reg almostfull,
  output reg [FIFO_DEPTH_BITS+1-1:0] data_count
);

  reg [FIFO_DEPTH_BITS-1:0] read_pointer;
  reg [FIFO_DEPTH_BITS-1:0] write_pointer;
  reg [FIFO_WIDTH-1:0] mem [0:2**FIFO_DEPTH_BITS-1];

  always @(posedge clk) begin
    if(rst) begin
      empty <= 1;
      almostempty <= 1;
      full <= 0;
      almostfull <= 0;
      read_pointer <= 0;
      write_pointer <= 0;
      data_count <= 0;
    end else begin
      case({ we, re })
        3: begin
          read_pointer <= read_pointer + 1;
          write_pointer <= write_pointer + 1;
        end
        2: begin
          if(~full) begin
            write_pointer <= write_pointer + 1;
            data_count <= data_count + 1;
            empty <= 0;
            if(data_count == FIFO_ALMOSTEMPTY_THRESHOLD - 1) begin
              almostempty <= 0;
            end 
            if(data_count == 2 ** FIFO_DEPTH_BITS - 1) begin
              full <= 1;
            end 
            if(data_count == FIFO_ALMOSTFULL_THRESHOLD - 1) begin
              almostfull <= 1;
            end 
          end 
        end
        1: begin
          if(~empty) begin
            read_pointer <= read_pointer + 1;
            data_count <= data_count - 1;
            full <= 0;
            if(data_count == FIFO_ALMOSTFULL_THRESHOLD) begin
              almostfull <= 0;
            end 
            if(data_count == 1) begin
              empty <= 1;
            end 
            if(data_count == FIFO_ALMOSTEMPTY_THRESHOLD) begin
              almostempty <= 1;
            end 
          end 
        end
      endcase
    end
  end


  always @(posedge clk) begin
    if(rst) begin
      out_valid <= 0;
    end else begin
      out_valid <= 0;
      if(we == 1) begin
        mem[write_pointer] <= in_data;
      end 
      if(re == 1) begin
        out_data <= mem[read_pointer];
        out_valid <= 1;
      end 
    end
  end


endmodule



module uart_rx
(
  input clk,
  input rst,
  input rx,
  output reg rx_bsy,
  output reg block_timeout,
  output reg data_valid,
  output reg [8-1:0] data_out
);

  // 27MHz
  // 3Mbits
  localparam CLKPERFRM = 86;
  // bit order is lsb-msb
  localparam TBITAT = 5;
  // START BIT
  localparam BIT0AT = 11;
  localparam BIT1AT = 20;
  localparam BIT2AT = 29;
  localparam BIT3AT = 38;
  localparam BIT4AT = 47;
  localparam BIT5AT = 56;
  localparam BIT6AT = 65;
  localparam BIT7AT = 74;
  localparam PBITAT = 80;
  // STOP bit
  localparam BLK_TIMEOUT = 20;
  // this depends on your USB UART chip

  // rx flow control
  reg [8-1:0] rx_cnt;

  //logic rx_sync
  reg rx_hold;
  reg timeout;
  wire frame_begin;
  wire frame_end;
  wire start_invalid;
  wire stop_invalid;

  always @(posedge clk) begin
    if(rst) begin
      rx_hold <= 1'b0;
    end else begin
      rx_hold <= rx;
    end
  end

  // negative edge detect
  assign frame_begin = &{ ~rx_bsy, ~rx, rx_hold };
  // final count
  assign frame_end = &{ rx_bsy, rx_cnt == CLKPERFRM };
  // START bit must be low  for 80% of the bit duration
  assign start_invalid = &{ rx_bsy, rx_cnt < TBITAT, rx };
  // STOP  bit must be high for 80% of the bit duration
  assign stop_invalid = &{ rx_bsy, rx_cnt > PBITAT, ~rx };

  always @(posedge clk) begin
    if(rst) begin
      rx_bsy <= 1'b0;
    end else begin
      if(frame_begin) begin
        rx_bsy <= 1'b1;
      end else if(|{ start_invalid, stop_invalid }) begin
        rx_bsy <= 1'b0;
      end else if(frame_end) begin
        rx_bsy <= 1'b0;
      end 
    end
  end

  // count if frame is valid or until the timeout

  always @(posedge clk) begin
    if(rst) begin
      rx_cnt <= 8'd0;
    end else begin
      if(frame_begin) begin
        rx_cnt <= 8'd0;
      end else if(|{ start_invalid, stop_invalid, frame_end }) begin
        rx_cnt <= 8'd0;
      end else if(~timeout) begin
        rx_cnt <= rx_cnt + 1;
      end else begin
        rx_cnt <= 8'd0;
      end
    end
  end

  // this just stops the rx_cnt

  always @(posedge clk) begin
    if(rst) begin
      timeout <= 1'b0;
    end else begin
      if(frame_begin) begin
        timeout <= 1'b0;
      end else if(&{ ~rx_bsy, rx_cnt == BLK_TIMEOUT }) begin
        timeout <= 1'b1;
      end 
    end
  end

  // this signals the end of block uart transfer

  always @(posedge clk) begin
    if(rst) begin
      block_timeout <= 1'b0;
    end else begin
      if(&{ ~rx_bsy, rx_cnt == BLK_TIMEOUT }) begin
        block_timeout <= 1'b1;
      end else begin
        block_timeout <= 1'b0;
      end
    end
  end

  // this pulses upon completion of a clean frame

  always @(posedge clk) begin
    if(rst) begin
      data_valid <= 1'b0;
    end else begin
      if(frame_end) begin
        data_valid <= 1'b1;
      end else begin
        data_valid <= 1'b0;
      end
    end
  end

  // rx data control

  always @(posedge clk) begin
    if(rst) begin
      data_out <= 8'd0;
    end else begin
      if(rx_bsy) begin
        case(rx_cnt)
          BIT0AT: begin
            data_out[0] <= rx;
          end
          BIT1AT: begin
            data_out[1] <= rx;
          end
          BIT2AT: begin
            data_out[2] <= rx;
          end
          BIT3AT: begin
            data_out[3] <= rx;
          end
          BIT4AT: begin
            data_out[4] <= rx;
          end
          BIT5AT: begin
            data_out[5] <= rx;
          end
          BIT6AT: begin
            data_out[6] <= rx;
          end
          BIT7AT: begin
            data_out[7] <= rx;
          end
        endcase
      end 
    end
  end


  initial begin
    rx_bsy = 0;
    block_timeout = 0;
    data_valid = 0;
    data_out = 0;
    rx_cnt = 0;
    rx_hold = 0;
    timeout = 0;
  end


endmodule



module uart_tx
(
  input clk,
  input rst,
  input send_trig,
  input [8-1:0] send_data,
  output reg tx,
  output reg tx_bsy
);

  // 27MHz
  // 3Mbps
  localparam CLKPERFRM = 90;
  // bit order is lsb-msb
  localparam TBITAT = 1;
  // START bit
  localparam BIT0AT = 10;
  localparam BIT1AT = 19;
  localparam BIT2AT = 28;
  localparam BIT3AT = 37;
  localparam BIT4AT = 46;
  localparam BIT5AT = 55;
  localparam BIT6AT = 64;
  localparam BIT7AT = 73;
  localparam PBITAT = 82;
  // STOP bit

  // tx flow control 
  reg [8-1:0] tx_cnt;

  // buffer
  reg [8-1:0] data2send;
  wire frame_begin;
  wire frame_end;
  assign frame_begin = &{ send_trig, ~tx_bsy };
  assign frame_end = &{ tx_bsy, tx_cnt == CLKPERFRM };

  always @(posedge clk) begin
    if(rst) begin
      tx_bsy <= 1'b0;
    end else begin
      if(frame_begin) begin
        tx_bsy <= 1'b1;
      end else if(frame_end) begin
        tx_bsy <= 1'b0;
      end 
    end
  end


  always @(posedge clk) begin
    if(rst) begin
      tx_cnt <= 8'd0;
    end else begin
      if(frame_end) begin
        tx_cnt <= 8'd0;
      end else if(tx_bsy) begin
        tx_cnt <= tx_cnt + 1;
      end 
    end
  end


  always @(posedge clk) begin
    if(rst) begin
      data2send <= 8'd0;
    end else begin
      data2send <= send_data;
    end
  end


  always @(posedge clk) begin
    if(rst) begin
      tx <= 1'b1;
    end else begin
      if(tx_bsy) begin
        case(tx_cnt)
          TBITAT: begin
            tx <= 1'b0;
          end
          BIT0AT: begin
            tx <= data2send[0];
          end
          BIT1AT: begin
            tx <= data2send[1];
          end
          BIT2AT: begin
            tx <= data2send[2];
          end
          BIT3AT: begin
            tx <= data2send[3];
          end
          BIT4AT: begin
            tx <= data2send[4];
          end
          BIT5AT: begin
            tx <= data2send[5];
          end
          BIT6AT: begin
            tx <= data2send[6];
          end
          BIT7AT: begin
            tx <= data2send[7];
          end
          PBITAT: begin
            tx <= 1'b0;
          end
        endcase
      end else begin
        tx <= 1'b1;
      end
    end
  end


  initial begin
    tx = 1;
    tx_bsy = 0;
    tx_cnt = 0;
    data2send = 0;
  end


endmodule



module riscv_rd_5_ird_6
(
  input clk,
  input rst,
  input monitor_read_on,
  input monitor_write_on,
  input [8-1:0] monitor_addr,
  output [8-1:0] mem_dataout,
  output [8-1:0] reg_dataout
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
  // adaptacao para a interface serial controlar a execução do riscV
  // estágio de memoria
  wire mrd;
  wire [32-1:0] maddr;
  assign mrd = |{ memread, monitor_read_on };
  assign maddr = (monitor_read_on)? { 24'd0, monitor_addr } : aluout;
  assign mem_dataout = readdata[7:0];
  //*
  // estágio de decode
  assign reg_dataout = data1[7:0];
  //*
  //*****

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
    .funct(funct),
    .monitor_read_on(monitor_read_on),
    .monitor_addr(monitor_addr[4:0])
  );


  execute
  execute
  (
    .in1(data1),
    .in2(data2),
    .immgen(sigext),
    .alusrc(alusrc),
    .aluop(aluop),
    .funct(funct),
    .zero(zero),
    .aluout(aluout)
  );


  memory
  memory
  (
    .clk(clk),
    .address(maddr),
    .writedata(data2),
    .memread(mrd),
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

  wire [32-1:0] pc;
  wire [32-1:0] pc_4;
  wire [32-1:0] new_pc;

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
    .memread(1'b1),
    .memwrite(1'b0),
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
    if(rst) begin
      pc_out <= 32'd0;
    end 
  end


  initial begin
    pc_out = 0;
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
  output [10-1:0] funct,
  input monitor_read_on,
  input [5-1:0] monitor_addr
);

  wire regwrite;
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
  assign funct = { funct7, funct3 };
  // adaptacao para a interface serial controlar a execução do riscV
  wire [5-1:0] raddr;
  assign raddr = (monitor_read_on)? monitor_addr : rs1;
  // *****

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
    .read_reg1(raddr),
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


  initial begin
    alusrc = 0;
    memtoreg = 0;
    regwrite = 0;
    memread = 0;
    memwrite = 0;
    branch = 0;
    aluop = 0;
    immgen = 0;
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

  integer i_initial;

  initial begin
    for(i_initial=0; i_initial<32; i_initial=i_initial+1) begin
      reg_bank[i_initial] = 0;
    end
  end


endmodule



module execute
(
  input [32-1:0] in1,
  input [32-1:0] in2,
  input [32-1:0] immgen,
  input alusrc,
  input [2-1:0] aluop,
  input [10-1:0] funct,
  output zero,
  output [32-1:0] aluout
);

  wire [32-1:0] alub;
  wire [4-1:0] aluctrl;

  assign alub = (alusrc)? immgen : in2;
  wire zero1;
  wire [3-1:0] f3;
  assign f3 = funct[2:0];
  assign zero = (f3 == 3'b0)? zero1 : 
                (f3 == 3'b1)? ~zero1 : 
                (f3 == 3'b100)? aluout[31] : 
                (f3 == 3'b101)? ~aluout[31] : 
                (f3 == 3'b110)? in1 < alub : 
                (f3 == 3'b111)? ~(in1 < alub) : 0;

  alucontrol
  alucontrol
  (
    .aluop(aluop),
    .funct(funct),
    .alucontrol(aluctrl)
  );


  alu
  alu
  (
    .alucontrol(aluctrl),
    .a(in1),
    .b(alub),
    .aluout(aluout),
    .zero(zero1)
  );


endmodule



module alucontrol
(
  input [2-1:0] aluop,
  input [10-1:0] funct,
  output reg [4-1:0] alucontrol
);

  wire [8-1:0] funct7;
  wire [3-1:0] funct3;
  wire [4-1:0] aluopcode;

  assign funct3 = funct[2:0];
  assign funct7 = funct[9:3];
  assign aluopcode = { funct[5], funct3 };

  always @(*) begin
    case(aluop)
      2'd0: begin
        alucontrol <= 4'd2;
      end
      2'd1: begin
        alucontrol <= 4'd6;
      end
      2'd2: begin
        case(funct3)
          3'd0: begin
            alucontrol <= (funct7 == 0)? 4'd2 : 4'd6;
          end
          3'd1: begin
            alucontrol <= 4'd3;
          end
          3'd2: begin
            alucontrol <= 4'd7;
          end
          3'd3: begin
            alucontrol <= 4'd9;
          end
          3'd4: begin
            alucontrol <= 4'd4;
          end
          3'd5: begin
            alucontrol <= (funct7[5])? 4'd5 : 4'd8;
          end
          3'd6: begin
            alucontrol <= 4'd1;
          end
          3'd7: begin
            alucontrol <= 4'd0;
          end
          default: begin
            alucontrol <= 4'd15;
          end
        endcase
      end
      2'd3: begin
        case(funct3)
          3'd0: begin
            alucontrol <= 4'd2;
          end
          3'd1: begin
            alucontrol <= 4'd3;
          end
          3'd2: begin
            alucontrol <= 4'd7;
          end
          3'd3: begin
            alucontrol <= 4'd9;
          end
          3'd4: begin
            alucontrol <= 4'd4;
          end
          3'd5: begin
            alucontrol <= (funct7[5])? 4'd5 : 4'd8;
          end
          3'd6: begin
            alucontrol <= 4'd1;
          end
          3'd7: begin
            alucontrol <= 4'd0;
          end
          default: begin
            alucontrol <= 4'd15;
          end
        endcase
      end
    endcase
  end


  initial begin
    alucontrol = 0;
  end


endmodule



module alu
(
  input [4-1:0] alucontrol,
  input [32-1:0] a,
  input [32-1:0] b,
  output reg [32-1:0] aluout,
  output zero
);

  assign zero = aluout == 0;

  wire [32-1:0] t;
  wire [32-1:0] sh;
  wire [32-1:0] p;

  slt
  slt
  (
    .a(a),
    .b(b),
    .s(t)
  );


  shiftra
  shiftra
  (
    .a(a),
    .b(b[4:0]),
    .o(sh)
  );


  always @(*) begin
    case(alucontrol)
      4'd0: begin
        aluout <= a & b;
      end
      4'd1: begin
        aluout <= a | b;
      end
      4'd2: begin
        aluout <= a + b;
      end
      4'd3: begin
        aluout <= a << b[4:0];
      end
      4'd4: begin
        aluout <= a ^ b;
      end
      4'd5: begin
        aluout <= sh;
      end
      4'd6: begin
        aluout <= a - b;
      end
      4'd7: begin
        aluout <= t;
      end
      4'd8: begin
        aluout <= a >> b[4:0];
      end
      4'd9: begin
        aluout <= a < b;
      end
      default: begin
        aluout <= 32'd0;
      end
    endcase
  end


  initial begin
    aluout = 0;
  end


endmodule



module slt
(
  input [32-1:0] a,
  input [32-1:0] b,
  output [32-1:0] s
);

  wire [32-1:0] sub;
  assign sub = a - b;
  assign s = (sub[31])? 32'd1 : 32'd0;

endmodule



module shiftra
(
  input [32-1:0] a,
  input [5-1:0] b,
  output [32-1:0] o
);

  wire [32-1:0] s;
  wire [32-1:0] t;
  wire [32-1:0] m;

  assign m = 32'b11111111111111111111111111111111;
  assign s = m >> b;
  assign t = a >> b;
  assign o = (a[31])? ~s | t : t;

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

