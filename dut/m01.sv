module top_1(
    input  wire clk,
    input  wire rst,
    input  wire inp1,
    input  wire inp2,
    output reg  outp
);

    localparam S0 = 2'b00,
               S1 = 2'b01,
               S2 = 2'b10,
               S3 = 2'b11;

    reg [1:0] current_state, next_state;

    always @* begin
        next_state = current_state;
        outp       = 1'b0;

        case (current_state)
            S0: begin
                outp = 1'b0;
                if (inp1)       next_state = S1;
                else if (inp2)  next_state = S2;
            end
            S1: begin
                outp = 1'b1;
                if (inp1)       next_state = S3;
                else if (inp2)  next_state = S0;
            end
            S2: begin
                outp = 1'b0;
                if (inp1)       next_state = S0;
                else if (inp2)  next_state = S3;
            end
            S3: begin
                outp = 1'b1;
                if (inp1)       next_state = S2;
                else if (inp2)  next_state = S1;
            end
        endcase
        $display("line-cover");
    end

    always @(posedge clk or posedge rst) begin
        if (rst) current_state <= S0;
        else     current_state <= next_state;
    end
endmodule

