

module tang_nano_9k_riscv_monitor_testbench
(

);

  reg clk;
  reg rst;
  wire [6-1:0] led;

  // Uart rx wires and regs
  wire uart_rx;
  wire uart_rx_bsy;
  wire uart_rx_block_timeout;
  wire uart_rx_data_valid;
  wire [8-1:0] uart_rx_data_out;
  // Uart rx wires and regs -----

  // Uart tx wires and regs
  reg uart_tx_send_trig;
  reg uart_tx_send_data;
  wire uart_tx;
  wire uart_tx_bsy;
  // Uart tx wires and regs -----

  //Transfer configuration controller
  reg [6-1:0] mem_address;
  wire [32-1:0] mem_readdata;
  //Transfer configuration controller -----

  // Receive data display controller
  reg [3-1:0] counter_rx;
  reg [32-1:0] word_received;

  always @(posedge clk) begin
    if(rst) begin
      counter_rx <= 3'd0;
      word_received <= 32'd0;
    end else begin
      if(uart_rx_data_valid) begin
        word_received <= { uart_rx_data_out, word_received[31:8] };
        if(counter_rx == 3'd3) begin
          counter_rx <= 3'd0;
          $display("%x\n", word_received);
        end else begin
          counter_rx <= counter_rx + 3'd1;
        end
      end 
    end
  end

  // Receive data display controller -----
  // Uart rx module instantiation

  uart_rx_27Hz_3Mbps
  m_uart_rx_27Hz_3Mbps
  (
    .clk(clk),
    .rst(rst),
    .rx(uart_rx),
    .rx_bsy(uart_rx_bsy),
    .block_timeout(uart_rx_block_timeout),
    .data_valid(uart_rx_data_valid),
    .data_out(uart_rx_data_out)
  );

  // Uart rx module instantiation -----
  // Uart tx module instantiation

  uart_tx_27Hz_3Mbps
  m_uart_tx_27Hz_3Mbps
  (
    .clk(clk),
    .rst(rst),
    .send_trig(uart_tx_send_trig),
    .send_data(uart_tx_send_data),
    .tx(uart_tx),
    .tx_bsy(uart_tx_bsy)
  );

  // Uart tx module instantiation -----
  //Config mem instantiation

  memory
  #(
    .READ_F(1),
    .INIT_FILE("config.rom"),
    .RAM_DEPTH(5),
    .DATA_WIDTH(32)
  )
  memory
  (
    .clk(clk),
    .address(mem_address),
    .writedata(32'd0),
    .memread(1'd1),
    .memwrite(1'd0),
    .readdata(mem_readdata)
  );

  //Config mem instantiation -----

  initial begin
    clk = 0;
    rst = 0;
    uart_tx_send_trig = 0;
    uart_tx_send_data = 0;
    mem_address = 0;
    counter_rx = 0;
    word_received = 0;
  end


  initial begin
    $dumpfile("/home/jeronimo/Documentos/GIT/tang_nano_9k_riscv_monitor/waveform_kqygle6m.vcd");
    $dumpvars(0);
  end


  initial begin
    @(posedge clk);
    @(posedge clk);
    @(posedge clk);
    rst = 1;
    #1000000;
    $finish;
  end

  always #5clk=~clk;

endmodule



module uart_rx_27Hz_3Mbps
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



module uart_tx_27Hz_3Mbps
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



module memory #
(
  parameter READ_F = 0,
  parameter INIT_FILE = "mem_file.txt",
  parameter WRITE_F = 0,
  parameter OUTPUT_FILE = "mem_out_file.txt",
  parameter RAM_DEPTH = 5,
  parameter DATA_WIDTH = 32
)
(
  input clk,
  input [RAM_DEPTH-1:0] address,
  input [DATA_WIDTH-1:0] writedata,
  input memread,
  input memwrite,
  output [DATA_WIDTH-1:0] readdata
);

  reg [DATA_WIDTH-1:0] memory [0:2**RAM_DEPTH-1];
  assign readdata = (memread)? memory[address] : 0;

  always @(posedge clk) begin
    if(memwrite) begin
      memory[address] <= writedata;
    end 
  end

  //synthesis translate_off

  always @(posedge clk) begin
    if(memwrite && WRITE_F) begin
      $writememh(OUTPUT_FILE, memory);
    end 
  end

  //synthesis translate_on

  initial begin
    if(READ_F) begin
      $readmemh(INIT_FILE, memory);
    end 
  end


endmodule

