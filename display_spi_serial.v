

module display_spi_serial
(
  input clk_27mhz,
  input button_s1,
  input resetn,
  output lcd_resetn,
  output lcd_clk,
  output lcd_cs,
  output lcd_rs,
  output lcd_data,
  input uart_rx,
  output reg [6-1:0] led,
  output uart_tx
);

  wire rst;
  assign rst = ~button_s1;

  wire rx_data_valid;
  wire [8-1:0] rx_data_out;

  localparam MAX_CMDS = 70;

  wire [9-1:0] init_cmd;
  reg [4-1:0] init_state;
  reg [7-1:0] cmd_index;
  reg [32-1:0] clk_cnt;
  reg [5-1:0] bit_loop;
  reg [16-1:0] pixel_cnt;
  reg lcd_cs_r;
  reg lcd_rs_r;
  reg lcd_reset_r;
  reg [8-1:0] spi_data;

  localparam INIT_RESET = 4'b0;
  localparam INIT_PREPARE = 4'b1;
  localparam INIT_WAKEUP = 4'b10;
  localparam INIT_SNOOZE = 4'b11;
  localparam INIT_WORKING = 4'b100;
  localparam INIT_DONE = 4'b101;

  localparam CNT_100MS = 32'd2700000;
  localparam CNT_120MS = 32'd3240000;
  localparam CNT_200MS = 32'd5400000;

  assign lcd_resetn = lcd_reset_r;
  assign lcd_clk = ~clk_27mhz;
  assign lcd_cs = lcd_cs_r;
  assign lcd_rs = lcd_rs_r;
  // MSB
  assign lcd_data = spi_data[7];
  // gen color bar
  reg [16-1:0] pixel;
  reg counter_bytes_in;
  reg lcd_fire;

  always @(posedge clk_27mhz) begin
    if(rst) begin
      counter_bytes_in <= 1'd0;
      lcd_fire <= 1'b0;
    end else begin
      lcd_fire <= 1'b0;
      if(rx_data_valid) begin
        if(counter_bytes_in == 1) begin
          counter_bytes_in <= 1'd0;
          lcd_fire <= 1'b1;
        end else begin
          counter_bytes_in <= counter_bytes_in + 1'd0;
        end
        pixel <= { rx_data_out, pixel[15:8] };
      end 
    end
  end


  always @(posedge clk_27mhz) begin
    if(~resetn) begin
      clk_cnt <= 32'd0;
      cmd_index <= 7'd0;
      init_state <= INIT_RESET;
      lcd_cs_r <= 1'd1;
      lcd_rs_r <= 1'd1;
      lcd_reset_r <= 1'd0;
      spi_data <= 8'hff;
      bit_loop <= 5'd0;
      pixel_cnt <= 16'd0;
    end else begin
      case(init_state)
        INIT_RESET: begin
          if(clk_cnt == CNT_100MS) begin
            clk_cnt <= 32'd0;
            init_state <= INIT_PREPARE;
            lcd_reset_r <= 1'd1;
          end else begin
            clk_cnt <= clk_cnt + 32'd1;
          end
        end
        INIT_PREPARE: begin
          if(clk_cnt == CNT_200MS) begin
            clk_cnt <= 32'd0;
            init_state <= INIT_WAKEUP;
          end else begin
            clk_cnt <= clk_cnt + 32'd1;
          end
        end
        INIT_WAKEUP: begin
          if(bit_loop == 5'd0) begin
            lcd_cs_r <= 1'd0;
            lcd_rs_r <= 1'd0;
            spi_data <= 8'h11;
            bit_loop <= bit_loop + 5'd1;
          end else if(bit_loop == 5'd8) begin
            lcd_cs_r <= 1'd1;
            lcd_rs_r <= 1'd1;
            bit_loop <= 5'd0;
            init_state <= INIT_SNOOZE;
          end else begin
            spi_data <= { spi_data[6:0], 1'd1 };
            bit_loop <= bit_loop + 5'd1;
          end
        end
        INIT_SNOOZE: begin
          if(clk_cnt == CNT_120MS) begin
            clk_cnt <= 32'd0;
            init_state <= INIT_WORKING;
          end else begin
            clk_cnt <= clk_cnt + 32'd1;
          end
        end
        INIT_WORKING: begin
          if(cmd_index == MAX_CMDS) begin
            init_state <= INIT_DONE;
          end else if(bit_loop == 5'd0) begin
            lcd_cs_r <= 1'd0;
            lcd_rs_r <= init_cmd[8];
            spi_data <= init_cmd[7:0];
            bit_loop <= bit_loop + 5'd1;
          end else if(bit_loop == 5'd8) begin
            lcd_cs_r <= 1'd1;
            lcd_rs_r <= 1'd1;
            bit_loop <= 5'd0;
            cmd_index <= cmd_index + 7'd1;
          end else begin
            spi_data <= { spi_data[6:0], 1'd1 };
            bit_loop <= bit_loop + 5'd1;
          end
        end
        INIT_DONE: begin
          if(pixel_cnt == 16'd32400) begin
          end else if((bit_loop == 5'd0) && lcd_fire) begin
            lcd_cs_r <= 1'd0;
            lcd_rs_r <= 1'd1;
            spi_data <= pixel[15:8];
            bit_loop <= bit_loop + 5'd1;
          end else if(bit_loop == 5'd8) begin
            spi_data <= pixel[7:0];
            bit_loop <= bit_loop + 5'd1;
          end else if(bit_loop == 5'd16) begin
            lcd_cs_r <= 1'd1;
            lcd_rs_r <= 1'd1;
            bit_loop <= 5'd0;
            pixel_cnt <= pixel_cnt + 16'd1;
          end else begin
            spi_data <= { spi_data[6:0], 1'd1 };
            bit_loop <= bit_loop + 5'd1;
          end
        end
      endcase
    end
  end


  config_rom
  config_rom
  (
    .address(cmd_index),
    .data_out(init_cmd)
  );



  m_uart_rx
  m_uart_rx
  (
    .clk(clk_27mhz),
    .rst(rst),
    .rx(uart_rx),
    .data_valid(rx_data_valid),
    .data_out(rx_data_out)
  );


endmodule



module config_rom
(
  input [7-1:0] address,
  output [9-1:0] data_out
);

  localparam MAX_CMDS = 70;

  wire [9-1:0] config_rom [0:MAX_CMDS-1];
  assign data_out = config_rom[address];

  assign config_rom[0] = 9'h36;
  assign config_rom[1] = 9'h170;
  assign config_rom[2] = 9'h3a;
  assign config_rom[3] = 9'h105;
  assign config_rom[4] = 9'hb2;
  assign config_rom[5] = 9'h10c;
  assign config_rom[6] = 9'h10c;
  assign config_rom[7] = 9'h100;
  assign config_rom[8] = 9'h133;
  assign config_rom[9] = 9'h133;
  assign config_rom[10] = 9'hb7;
  assign config_rom[11] = 9'h135;
  assign config_rom[12] = 9'hbb;
  assign config_rom[13] = 9'h119;
  assign config_rom[14] = 9'hc0;
  assign config_rom[15] = 9'h12c;
  assign config_rom[16] = 9'hc2;
  assign config_rom[17] = 9'h101;
  assign config_rom[18] = 9'hc3;
  assign config_rom[19] = 9'h112;
  assign config_rom[20] = 9'hc4;
  assign config_rom[21] = 9'h120;
  assign config_rom[22] = 9'hc6;
  assign config_rom[23] = 9'h10f;
  assign config_rom[24] = 9'hd0;
  assign config_rom[25] = 9'h1a4;
  assign config_rom[26] = 9'h1a1;
  assign config_rom[27] = 9'he0;
  assign config_rom[28] = 9'h1d0;
  assign config_rom[29] = 9'h104;
  assign config_rom[30] = 9'h10d;
  assign config_rom[31] = 9'h111;
  assign config_rom[32] = 9'h113;
  assign config_rom[33] = 9'h12b;
  assign config_rom[34] = 9'h13f;
  assign config_rom[35] = 9'h154;
  assign config_rom[36] = 9'h14c;
  assign config_rom[37] = 9'h118;
  assign config_rom[38] = 9'h10d;
  assign config_rom[39] = 9'h10b;
  assign config_rom[40] = 9'h11f;
  assign config_rom[41] = 9'h123;
  assign config_rom[42] = 9'he1;
  assign config_rom[43] = 9'h1d0;
  assign config_rom[44] = 9'h104;
  assign config_rom[45] = 9'h10c;
  assign config_rom[46] = 9'h111;
  assign config_rom[47] = 9'h113;
  assign config_rom[48] = 9'h12c;
  assign config_rom[49] = 9'h13f;
  assign config_rom[50] = 9'h144;
  assign config_rom[51] = 9'h151;
  assign config_rom[52] = 9'h12f;
  assign config_rom[53] = 9'h11f;
  assign config_rom[54] = 9'h11f;
  assign config_rom[55] = 9'h120;
  assign config_rom[56] = 9'h123;
  assign config_rom[57] = 9'h21;
  assign config_rom[58] = 9'h29;
  // column
  assign config_rom[59] = 9'h2a;
  assign config_rom[60] = 9'h100;
  assign config_rom[61] = 9'h128;
  assign config_rom[62] = 9'h101;
  assign config_rom[63] = 9'h117;
  // row
  assign config_rom[64] = 9'h2b;
  assign config_rom[65] = 9'h100;
  assign config_rom[66] = 9'h135;
  assign config_rom[67] = 9'h100;
  assign config_rom[68] = 9'h1bb;
  // start
  assign config_rom[69] = 9'h2c;

endmodule



module m_uart_rx
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


endmodule

