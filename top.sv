module top_1(
    input clk,
    input rst,
    input enable,
    output reg [3:0] count,
    output reg overflow
);

initial begin
    count = 4'b0;
    overflow = 1'b0;
end

always @(posedge clk or posedge rst) begin
    if (rst) begin
        count <= 4'b0;
        overflow <= 1'b0;
    end else if (enable) begin
        if (count == 4'b1111) begin
            overflow <= 1'b1;
        end else begin
            count <= count + 1;
            overflow <= 1'b0;
        end 
    end
end
// Functional Coverage - Verilator Style

// Cover all count values from 0 to 15 when enable is high at every `posedge clk`
cover property (@(posedge clk) enable && count inside {[0:15]});

// Cover overflow signal when count reaches 15 and enable is high on `posedge clk`
cover property (@(posedge clk) enable && count == 4'd15 && overflow);

// Cover enable signal rising edge at `posedge clk`
cover property (@(posedge clk) $rose(enable));

// Cover enable signal falling edge at `posedge clk`
cover property (@(posedge clk) $fell(enable));
endmodule
