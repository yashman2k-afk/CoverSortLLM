module top(
  input  LINE1,
  input LINE2,
  input  clk, 
  input rst,
  output reg OUTP, 
  output reg OVERFLW
);

  reg [2:0] stato;

  parameter a=0;
  parameter b=1;
  parameter c=2;
  parameter e=3;
  parameter f=4;
  parameter g=5;
  parameter wf0=6;
  parameter wf1=7;

  initial begin
    stato = a;
    OUTP = 0;
    OVERFLW = 0;
  end

  always @ (posedge clk) begin
    if(rst) begin
      stato = a;
      OUTP = 0;
      OVERFLW = 0;
    end
    else
      case (stato)
        a: begin
          if (LINE1 & LINE2)
            stato = f;
          else
            stato = b;
          OUTP = LINE1 ^ LINE2;
          OVERFLW = 0;
        end
        e: begin
          if (LINE1 & LINE2)
            stato = f;
          else
            stato = b;
          OUTP = LINE1 ^ LINE2;
          OVERFLW = 1;
        end
        b: begin
          if (LINE1 & LINE2)
            stato = g;
          else 
            stato = c;
          OUTP = LINE1 ^ LINE2;
          OVERFLW = 0;
        end
        f: begin
          if (LINE1 | LINE2)
            stato = g; 
          else
            stato = c;
          OUTP = ~(LINE1 ^ LINE2);
          OVERFLW = 0;
        end
        c: begin
          if (LINE1 & LINE2)
            stato = wf1;
          else
            stato = wf0;
          OUTP = LINE1 ^ LINE2;
          OVERFLW = 0;
        end
        g: begin
          if (LINE1 | LINE2)
            stato = wf1;
          else
            stato = wf0;
          OUTP = ~(LINE1 ^ LINE2);
          OVERFLW = 0;
        end
        wf0: begin
          if (LINE1 & LINE2)
            stato = e;
          else
            stato = a; 
          OUTP = LINE1 ^ LINE2;
          OVERFLW = 0;
        end
        wf1: begin
          if (LINE1 | LINE2)
            stato = e;
          else             
            stato = a;
          OUTP = ~(LINE1 ^ LINE2);
          OVERFLW = 0;
        end
      endcase
  end
// ======================================================
// Functional coverage for outputs
// ======================================================
cover property (@(posedge clk) OUTP inside {1'b0, 1'b1});
cover property (@(posedge clk) OVERFLW inside {1'b0, 1'b1});

// ======================================================
// Functional coverage for state transitions
// ======================================================
cover property (@(posedge clk) (stato == 3'd0 && next_state inside {3'd1, 3'd4})); // a -> b or f
cover property (@(posedge clk) (stato == 3'd1 && next_state inside {3'd2, 3'd5})); // b -> c or g
cover property (@(posedge clk) (stato == 3'd2 && next_state inside {3'd6, 3'd7})); // c -> wf0 or wf1
cover property (@(posedge clk) (stato == 3'd3 && next_state inside {3'd1, 3'd4})); // e -> b or f
cover property (@(posedge clk) (stato == 3'd4 && next_state inside {3'd2, 3'd5})); // f -> c or g
cover property (@(posedge clk) (stato == 3'd5 && next_state inside {3'd6, 3'd7})); // g -> wf0 or wf1
cover property (@(posedge clk) (stato == 3'd6 && next_state inside {3'd0, 3'd3})); // wf0 -> a or e
cover property (@(posedge clk) (stato == 3'd7 && next_state inside {3'd0, 3'd3})); // wf1 -> a or e

endmodule
