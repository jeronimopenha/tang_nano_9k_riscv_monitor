

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
  input [4-1:0] alucontrol
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


endmodule



module alu
(
  input alucontrol,
  input a,
  input b,
  output aluout,
  output zero
);

  assign zero = aluout == 0;

  wire [32-1:0] t;
  wire [32-1:0] sh;
  wire [32-1:0] p;

endmodule

