module top_1(
    input  LINE1,
    input  LINE2,
    input  clk, 
    input  rst,
    output reg OUTP, 
    output reg OVERFLW
);

    reg [2:0] stato;

    // State encoding using a single localparam
    localparam 
        a   = 3'b000,
        b   = 3'b001,
        c   = 3'b010,
        e   = 3'b011,
        f   = 3'b100,
        g   = 3'b101,
        wf0 = 3'b110,
        wf1 = 3'b111;

    always @(posedge clk) begin
        if (rst) begin
            stato    <= a;
            OUTP     <= 0;
            OVERFLW  <= 0;
        end else begin
            case (stato)
                a: begin
                    stato   <= (LINE1 & LINE2) ? f : b;
                    OUTP    <= LINE1 ^ LINE2;
                    OVERFLW <= 0;
                end
                e: begin
                    stato   <= (LINE1 & LINE2) ? f : b;
                    OUTP    <= LINE1 ^ LINE2;
                    OVERFLW <= 1;
                end
                b: begin
                    stato   <= (LINE1 & LINE2) ? g : c;
                    OUTP    <= LINE1 ^ LINE2;
                    OVERFLW <= 0;
                end
                f: begin
                    stato   <= (LINE1 | LINE2) ? g : c;
                    OUTP    <= ~(LINE1 ^ LINE2);
                    OVERFLW <= 0;
                end
                c: begin
                    stato   <= (LINE1 & LINE2) ? wf1 : wf0;
                    OUTP    <= LINE1 ^ LINE2;
                    OVERFLW <= 0;
                end
                g: begin
                    stato   <= (LINE1 | LINE2) ? wf1 : wf0;
                    OUTP    <= ~(LINE1 ^ LINE2);
                    OVERFLW <= 0;
                end
                wf0: begin
                    stato   <= (LINE1 & LINE2) ? e : a;
                    OUTP    <= LINE1 ^ LINE2;
                    OVERFLW <= 0;
                end
                wf1: begin
                    stato   <= (LINE1 | LINE2) ? e : a;
                    OUTP    <= ~(LINE1 ^ LINE2);
                    OVERFLW <= 0;
                end
                // verilator coverage_off
                default: begin
                    stato   <= a;
                    OUTP    <= 0;
                    OVERFLW <= 0;
                end
                // verilator coverage_on
            endcase
            $display("line-cover");
        end
    end

endmodule
