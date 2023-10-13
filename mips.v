

module mips_rd_5_ird_6
(
  input clk,
  input rst
);

  wire [32-1:0] pc_in;
  wire [32-1:0] pc_out;
  wire [32-1:0] pc_4_out;
  wire [32-1:0] inst_out;
  wire [32-1:0] shl2_jump_out;
  wire [32-1:0] jump_add;

  assign jump_add = { pc_4_out[31:28], shl2_jump_out[27:0] };

  pc
  pc
  (
    .clk(clk),
    .rst(rst),
    .pc_in(pc_in),
    .pc_out(pc_out)
  );


  add
  add4
  (
    .add0_in(pc_out),
    .add1_in(32'd4),
    .add_out(pc_4_out)
  );


  shift_left_2
  shift_left_2_jump
  (
    .shl2_in({ 6'd0, inst_out[25:0] }),
    .shl2_out(shl2_jump_out)
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
    if(rst) begin
      pc_out <= 32'd0;
    end else begin
      pc_out <= pc_in;
    end
  end


endmodule



module add
(
  input [32-1:0] add0_in,
  input [32-1:0] add1_in,
  output [32-1:0] add_out
);

  assign add_out = add0_in + add1_in;

endmodule



module shift_left_2
(
  input [32-1:0] shl2_in,
  output [32-1:0] shl2_out
);

  assign shl2_out = { shl2_in[31:2], 2'd0 };

endmodule

