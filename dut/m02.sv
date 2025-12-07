module top_1(
    input  wire clk,
    input  wire rst,
    input  wire LINEA,
    output reg  U
);

    // State encoding
    localparam A = 3'd0;
    localparam B = 3'd1;
    localparam C = 3'd2;
    localparam D = 3'd3;
    localparam E = 3'd4;
    localparam F = 3'd5;
    localparam G = 3'd6;

    // Current state
    reg [2:0] stato;

    // Sequential FSM with nonblocking assignments
    always @(posedge clk or posedge rst) begin
    if (rst) begin
        stato <= A;
        U <= 1'b0;
    end 
    else begin
        case (stato)
            A: begin
                stato <= B;
                U <= 1'b0;
            end
            B: begin
                if (LINEA == 1'b0) begin
                    stato <= C;
                end 
                else begin
                    stato <= F;
                    U <= 1'b0;
                end
            end
            C: begin
                if (LINEA == 1'b0)
                    stato <= D;
                else
                    stato <= G;
                U <= 1'b0;
            end
            D: begin
                stato <= E;
                U <= 1'b0;
            end
            E: begin
                stato <= B;
                U <= 1'b1;
            end
            F: begin
                stato <= G;
                U <= 1'b0;
            end
            G: begin
                if (LINEA == 1'b0)
                    stato <= E;
                else
                    stato <= A;
                U <= 1'b0;
            end
            // verilator coverage_off
            default: begin  // recovery path, ignore for coverage
                stato <= A;   
                U     <= 1'b0;
            end
            // verilator coverage_on
        endcase
        $display("line-cover");
    end
end


endmodule
