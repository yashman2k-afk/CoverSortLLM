module top_1(
    input  wire clk,
    input  wire reset,
    input  wire pedestrian_button,
    input  wire car_sensor,
    output reg [2:0] lights
);

    // Traffic light and FSM states combined in one localparam block
    localparam 
        RED    = 3'b001,
        YELLOW = 3'b010,
        GREEN  = 3'b100,
        WAIT   = 2'b00,
        GO     = 2'b01,
        WARN   = 2'b10,
        STOP   = 2'b11;

    reg [1:0] state, next_state;
    reg [3:0] count; // 4-bit counter

    // Synchronous reset and state update
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            state <= WAIT;
            count <= 0;
        end else begin
            state <= next_state;
            if (count == 10)
                count <= 0;
            else
                count <= count + 1;
        end
    end

    // Combinational logic for next state and lights
    always @* begin
        case (state)
            WAIT: begin
                if (car_sensor) begin
                    lights = RED;
                    next_state = GO;
                end else begin
                    lights = YELLOW;
                    next_state = WARN;
                end
            end
            GO: begin
                if (count < 6) begin
                    lights = GREEN;
                    next_state = GO;
                end else begin
                    lights = YELLOW;
                    next_state = WARN;
                end
            end
            WARN: begin
                if (count < 2) begin
                    lights = YELLOW;
                    next_state = WARN;
                end else if (pedestrian_button) begin
                    lights = RED;
                    next_state = STOP;
                end else begin
                    lights = RED;
                    next_state = GO;
                end
            end
            STOP: begin
                $display("line-cover");
                if (count < 4) begin
                    lights = RED;
                    next_state = STOP;
                end else begin
                    lights = GREEN;
                    next_state = GO;
                end
            end
        endcase
    end

endmodule

