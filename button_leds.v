

module button_leds
(
  input clk_27mhz,
  input button_s1,
  input uart_rx,
  output [6-1:0] led,
  output uart_tx
);

  // Reset signal control
  wire btn_wire;
  assign btn_wire = ~button_s1;

  reg [6-1:0] counter_led;
  assign led = ~counter_led;

  reg [23-1:0] counter_debounce;
  localparam [23-1:0] PAR_4HZ = 23'hf423f;

  reg btn_signal;
  wire btn_active;
  reg ffd1;
  reg ffd2;
  assign btn_active = &{ ffd1, ~ffd2 };


  always @(posedge clk_27mhz) begin
    if(counter_debounce < PAR_4HZ) begin
      counter_debounce <= counter_debounce + 23'b1;
    end else begin
      btn_signal <= ~btn_signal;
      counter_debounce <= 23'b0;
    end
  end


  always @(posedge btn_signal) begin
    ffd1 <= btn_wire;
    ffd2 <= ffd1;
  end


  always @(posedge btn_active) begin
    counter_led <= counter_led + 6'b1;
  end


endmodule

