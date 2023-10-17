module usb_top (
    input  clk_27mhz,
    input  button_s1,
    input uart_rx,
    output [5:0] led,
    output uart_tx
    );
    
    assign uart_tx = uart_rx;
    //assign uart_tx=uart_rx;

    reg [24:0] counter;
    wire tx_busy;
    reg start;
    wire clk;
    wire rst_in;
    wire rst;

    assign clk = clk_27mhz;

    //assign led[0] = uart_tx;//~rst;//rst;//~start;//~uart_tx;//counter[24];
    //assign led[1] = data_counter[0];
    
    //assign start = counter == 0 && ~tx_bsy;
    reg [7:0] data_send;
    reg [4:0] data_counter;
    assign rst = ~button_s1;
    //assign uart_tx_buf = 1;//uart_tx; // FPGA TX and RX signals do not normally connect to board pins
    assign led[0] = uart_tx;
    assign led[5:1]  = ~data_send[4:0];
    always@(posedge clk) begin
        if(rst) begin
            data_send <=0;
        end else  begin
            case(data_counter)
                5'd0 : data_send = 8'h30; // 0
                5'd1 : data_send = 8'h31; // 1
                5'd2 : data_send = 8'h32; // 2
                5'd3 : data_send = 8'h33; // 3
                5'd4 : data_send = 8'h34; // 4 
                5'd5 : data_send = 8'h35; // 5
                5'd6 : data_send = 8'h36; // 6
                5'd7 : data_send = 8'h37; // 7
                5'd8 : data_send = 8'h38; // 8
                5'd9 : data_send = 8'h39; // 9
                5'd10 : data_send = 8'h41; // A
                5'd11 : data_send = 8'h42; // B
                5'd12 : data_send = 8'h43; // C
                5'd13 : data_send = 8'h44; // D
                5'd14 : data_send = 8'h45; // E
                5'd15 : data_send = 8'h46; // F
                5'd16 : data_send = 8'h53; // S, SYNC-1
                5'd17 : data_send = 8'h54; // T, SYNC-2
                5'd18 : data_send = 8'h55; // U, SYNC-3
                5'd19 : data_send = 8'h51; // Q, RST-1
                5'd20 : data_send = 8'h52; // R, RST-2
                5'd21 : data_send = 8'h0D; // CR, EOP
                5'd22 : data_send = 8'h0A; // NL, preable begining detect
                default  : data_send = 8'h58; // X, invalid
  endcase
        end
    end

    always@(posedge clk) begin
        if(rst) begin
            counter <= 0;
            data_counter <= 0;
            start <= 0;
        end else begin
            if(counter == 1024 ) begin
                start <= 1;
                data_counter <= data_counter + 5'd1;
            end else begin
                //if(tx_busy) begin
                    start <= 0;
                //end
            end
            counter<=counter+25'd1;
        end
    end
    
    uart_tx 
    u_uart_tx
    (.clk(clk),// input
     .rst(rst),// input
     .send_trig(start),// input
     .send_data(data_send[7:0]),// input [7:0]
     .tx(),// output
     .tx_bsy(tx_busy)// output
    );

/*
case({bit_1,bit_buffer})
    5'b11110 : char_out = 8'h30; // 0
    5'b01001 : char_out = 8'h31; // 1
    5'b10100 : char_out = 8'h32; // 2
    5'b10101 : char_out = 8'h33; // 3
    5'b01010 : char_out = 8'h34; // 4 
    5'b01011 : char_out = 8'h35; // 5
    5'b01110 : char_out = 8'h36; // 6
    5'b01111 : char_out = 8'h37; // 7
    5'b10010 : char_out = 8'h38; // 8
    5'b10011 : char_out = 8'h39; // 9
    5'b10110 : char_out = 8'h41; // A
    5'b10111 : char_out = 8'h42; // B
    5'b11010 : char_out = 8'h43; // C
    5'b11011 : char_out = 8'h44; // D
    5'b11100 : char_out = 8'h45; // E
    5'b11101 : char_out = 8'h46; // F
    5'b11000 : char_out = 8'h53; // S, SYNC-1
    5'b10001 : char_out = 8'h54; // T, SYNC-2
    5'b00110 : char_out = 8'h55; // U, SYNC-3
    5'b00111 : char_out = 8'h51; // Q, RST-1
    5'b11001 : char_out = 8'h52; // R, RST-2
    5'b01101 : char_out = 8'h0D; // CR, EOP
    5'b00000 : char_out = 8'h0A; // NL, preable begining detect
    default  : char_out = 8'h58; // X, invalid
  endcase
*/

endmodule

module uart_tx
    //# ( parameter SYSCLOCK = 27.0, // MHz
    //    parameter BAUDRATE = 1.0 ) // Mbits
    (input clk,
     input rst,  
     input send_trig,
     input [7:0] send_data,
     output reg tx,
     output reg tx_bsy
    );

    localparam SYSCLOCK = 27.0;
    localparam BAUDRATE = 1.0;

    localparam CLKPERFRM = (SYSCLOCK/BAUDRATE)*10;//270;//(SYSCLOCK/BAUDRATE)*10;
    // bit order is lsb-msb
    localparam TBITAT    = 1; // START bit
    localparam BIT0AT    = (SYSCLOCK/BAUDRATE*1)+1;//28;//(SYSCLOCK/BAUDRATE*1)+1;
    localparam BIT1AT    = (SYSCLOCK/BAUDRATE*2)+1;//55;//(SYSCLOCK/BAUDRATE*2)+1;
    localparam BIT2AT    = (SYSCLOCK/BAUDRATE*3)+1;//82;//(SYSCLOCK/BAUDRATE*3)+1;
    localparam BIT3AT    = (SYSCLOCK/BAUDRATE*4)+1;//109;//(SYSCLOCK/BAUDRATE*4)+1;
    localparam BIT4AT    = (SYSCLOCK/BAUDRATE*5)+1;//136;//(SYSCLOCK/BAUDRATE*5)+1;
    localparam BIT5AT    = (SYSCLOCK/BAUDRATE*6)+1;//163;//(SYSCLOCK/BAUDRATE*6)+1;
    localparam BIT6AT    = (SYSCLOCK/BAUDRATE*7)+1;//190;//(SYSCLOCK/BAUDRATE*7)+1;
    localparam BIT7AT    = (SYSCLOCK/BAUDRATE*8)+1;//217;//(SYSCLOCK/BAUDRATE*8)+1;
    localparam PBITAT    = (SYSCLOCK/BAUDRATE*9)+1;//244;//(SYSCLOCK/BAUDRATE*9)+1; // STOP bit

    reg [9-1:0] tx_cnt; // tx flow control
//[$clog2(CLKPERFRM+1)-1:0] tx_cnt; // tx flow control
    reg [7:0] data2send; // buffer
    wire frame_begin;
    wire frame_end;

    assign frame_begin = send_trig & (~tx_bsy);
    assign frame_end = tx_bsy && (tx_cnt == CLKPERFRM);
    
    always@(posedge clk) begin
        if(rst) begin
            tx_bsy <= 1'b0;
        end else if (frame_begin) begin
            tx_bsy <= 1'b1;
        end else if (frame_end) begin
            tx_bsy <= 1'b0;
        end
    end
 
    always@(posedge clk) begin
        if (rst) begin
            tx_cnt <= 'd0;
        end else if (frame_end) begin
            tx_cnt <= 'd0;
        end else if (tx_bsy) begin
            tx_cnt <= tx_cnt + 1'b1;
        end
    end

    always@(posedge clk) begin
        if (rst) begin
            data2send <= 8'd0;
        end else if (frame_begin) begin
            data2send <= send_data;
        end
    end

    always@(posedge clk) begin 
        if (rst) begin
            tx <= 1'b1; // init val should be 1
        end else if (tx_bsy) begin
            case(tx_cnt) 
                TBITAT: tx <= 1'b0;
                BIT0AT: tx <= data2send[0];
                BIT1AT: tx <= data2send[1];
                BIT2AT: tx <= data2send[2];
                BIT3AT: tx <= data2send[3];
                BIT4AT: tx <= data2send[4];
                BIT5AT: tx <= data2send[5];
                BIT6AT: tx <= data2send[6];
                BIT7AT: tx <= data2send[7];
                PBITAT: tx <= 1'b1;
            endcase
        end else begin
            tx <= 1'b1;
        end
    end
endmodule
