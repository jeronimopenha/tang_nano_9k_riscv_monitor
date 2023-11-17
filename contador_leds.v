

module contador_leds
(
  input clk_27mhz,
  input button_s1,
  input uart_rx,
  output reg [6-1:0] led,
  output uart_tx
);

  // Reset signal control
  wire rst;
  assign rst = ~button_s1;

  reg [24-1:0] counter;


  always @(posedge clk_27mhz) begin
    if(rst) begin
      counter <= 24'd0;
    end else begin
      if(counter < 24'hcdfe5f) begin
        counter <= counter + 24'd1;
      end else begin
        counter <= 0;
      end
    end
  end


  always @(posedge clk_27mhz) begin
    if(rst) begin
      led <= 6'b111110;
    end else begin
      if(counter == 24'hcdfe5f) begin
        led <= { led[4:0], led[5] };
      end 
    end
  end


endmodule

