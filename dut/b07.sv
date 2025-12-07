module top(
    input clk,
    input reset,
    input [3:0] in_a,
    input [3:0] in_b,
    output reg [4:0] state,
    output reg carry_flag,
    output reg zero_flag,
    output reg overflow_flag,
    output reg special_out      // extra output
);

localparam S0  = 5'b00000, S1  = 5'b00001, S2  = 5'b00010, S3  = 5'b00011,
           S4  = 5'b00100, S5  = 5'b00101, S6  = 5'b00110, S7  = 5'b00111,
           S8  = 5'b01000, S9  = 5'b01001, S10 = 5'b01010, S11 = 5'b01011,
           S12 = 5'b01100, S13 = 5'b01101, S14 = 5'b01110, S15 = 5'b01111,
           S16 = 5'b10000, S17 = 5'b10001, S18 = 5'b10010, S19 = 5'b10011,
           S20 = 5'b10100, S21 = 5'b10101, S22 = 5'b10110, S23 = 5'b10111,
           S24 = 5'b11000, S25 = 5'b11001, S26 = 5'b11010, S27 = 5'b11011,
           S28 = 5'b11100, S29 = 5'b11101, S30 = 5'b11110, S31 = 5'b11111;

always @(posedge clk or posedge reset) begin
    if (reset) begin
        state <= S0;
        carry_flag <= 0;
        zero_flag <= 0;
        overflow_flag <= 0;
        special_out <= 0;
    end else begin
        // Compute flags (example logic)
        carry_flag <= (in_a + in_b > 15);
        zero_flag <= ((in_a ^ in_b) == 0);
        overflow_flag <= ((in_a[3] & in_b[3] & ~in_a[2]) | (~in_a[3] & ~in_b[3] & in_a[2]));
        special_out <= (state == S20 || state == S31) ? 1'b1 : 1'b0;



        // FSM with if-else inside case for transitions
        case (state)
            S0:
                if (in_a[0] & in_b[0]) begin
                    state <= S1;
                end else begin
                    state <= S2;
                end
            S1:
                if (in_a[1] & ~in_b[1]) begin
                    state <= S3;
                end else begin
                    state <= S4;
                end
            S2:
                if (in_a[2] | in_b[2]) begin
                    state <= S5;
                end else begin
                    state <= S6;
                end
            S5:
                if (in_a[0] ^ in_b[0]) begin
                    state <= S11;
                end else begin
                    state <= S12;
                end
            S3:
                if (~in_a[3] & in_b[3]) begin
                    state <= S7;
                end else begin
                    state <= S8;
                end
            S4:
                if (in_a[0] ^ in_b[1]) begin
                    state <= S9;
                end else begin
                    state <= S10;
                end
            S6:
                if (in_a[2] & ~in_b[2]) begin
                    state <= S13;
                end else begin
                    state <= S14;
                end
            S7:
                if (~in_a[3] | ~in_b[3]) begin
                    state <= S15;
                end else begin
                    state <= S16;
                end
            S8:
                if (in_a[0] & in_b[1]) begin
                    state <= S17;
                end else begin
                    state <= S18;
                end
            S9:
                if (~in_a[1] & in_b[0]) begin
                    state <= S19;
                end else begin
                    state <= S20;
                end
            S10:
                if (in_a[2] | in_b[1]) begin
                    state <= S21;
                end else begin
                    state <= S22;
                end
            S11:
                if (~in_a[3] | in_b[2]) begin
                    state <= S23;
                end else begin
                    state <= S24;
                end
            S12:
                if (in_a[0] & ~in_b[3]) begin
                    state <= S25;
                end else begin
                    state <= S26;
                end
            S13:
                if (in_a[1] | in_b[2]) begin
                    state <= S27;
                end else begin
                    state <= S28;
                end
            S14:
                if (~in_a[2] & ~in_b[1]) begin
                    state <= S29;
                end else begin
                    state <= S30;
                end
            S15:
                if (in_a[3] ^ in_b[3]) begin
                    state <= S31;
                end else begin
                    state <= S0;
                end
            S16:
                if (in_a[0] & in_b[0]) begin
                    state <= S1;
                end else begin
                    state <= S2;
                end
            S17:
                if (in_a[1] & ~in_b[1]) begin
                    state <= S3;
                end else begin
                    state <= S4;
                end
            S18:
                if (in_a[2] | in_b[2]) begin
                    state <= S5;
                end else begin
                    state <= S6;
                end
            S19:
                if (~in_a[3] & in_b[3]) begin
                    state <= S7;
                end else begin
                    state <= S8;
                end
            S20:
                if (in_a[0] ^ in_b[0]) begin
                    state <= S9;
                end else begin
                    state <= S10;
                end
            S21:
                if (~in_a[1] | in_b[1]) begin
                    state <= S11;
                end else begin
                    state <= S12;
                end
            S22:
                if (in_a[2] & ~in_b[2]) begin
                    state <= S13;
                end else begin
                    state <= S14;
                end
            S23:
                if (~in_a[3] | ~in_b[3]) begin
                    state <= S15;
                end else begin
                    state <= S16;
                end
            S24:
                if (in_a[0] & in_b[1]) begin
                    state <= S17;
                end else begin
                    state <= S18;
                end
            S25:
                if (~in_a[1] & in_b[0]) begin
                    state <= S19;
                end else begin
                    state <= S20;
                end
            S26:
                if (in_a[2] | in_b[1]) begin
                    state <= S21;
                end else begin
                    state <= S22;
                end
            S27:
                if (~in_a[3] | in_b[2]) begin
                    state <= S23;
                end else begin
                    state <= S24;
                end
            S28:
                if (in_a[0] & ~in_b[3]) begin
                    state <= S25;
                end else begin
                    state <= S26;
                end
            S29:
                if (in_a[1] | in_b[2]) begin
                    state <= S27;
                end else begin
                    state <= S28;
                end
            S30:
                if (~in_a[2] & ~in_b[1]) begin
                    state <= S29;
                end else begin
                    state <= S30;
                end
            S31:
                if (in_a[3] ^ in_b[3]) begin
                    state <= S31;
                    $display("line-cover");
                end else begin
                    state <= S0;
                end
            // verilator coverage_off
            default: state <= S0;
            // verilator coverage_on
        endcase
    end
end
endmodule
