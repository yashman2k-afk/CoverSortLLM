module top_1(
    input  wire             clk,
    input  wire             rst,      
    input  wire [5:0] A_in,
    input  wire [5:0] B_in,
    input  wire [2:0]       opcode_in,
    output reg  [5:0] result,
    output reg              zero,
    output reg              carry,
    output reg              overflow
);
    localparam MSB = 5, ADD = 3'b000, SUB =3'b001, AND = 3'b010, 
                OR = 3'b011, XOR = 3'b100, SHL = 3'b101, RHL = 3'b110,
                ROL = 3'b111;
    
    reg [5:0] A_reg, B_reg;
    reg [2:0]       opcode_reg;
    reg [5:0] alu_result;
    reg alu_carry, alu_overflow;
    wire alu_zero;    
    wire [6:0] add_full;
    wire [6:0] sub_full;
    wire [2:0] shamt = B_reg[2:0];

    assign add_full = {1'b0, A_reg} + {1'b0, B_reg};
    assign sub_full = {1'b0, A_reg} + {1'b0, ~B_reg} + 1'b1;
    assign alu_zero = (alu_result == {6{1'b0}});

    // combinational ALU logic
    always @* begin
        alu_result   = {6{1'b0}};
        alu_carry    = 1'b0;
        alu_overflow = 1'b0;

        case (opcode_reg)
            ADD: begin // ADD
                alu_result = add_full[5:0];
                alu_carry  = add_full[6];
                alu_overflow = (A_reg[MSB] & B_reg[MSB] & ~alu_result[MSB]) |
                               (~A_reg[MSB] & ~B_reg[MSB] & alu_result[MSB]);
            end
            SUB: begin // SUB
                alu_result = sub_full[5:0];
                alu_carry  = sub_full[6];
                alu_overflow = (A_reg[MSB] & ~B_reg[MSB] & ~alu_result[MSB]) |
                               (~A_reg[MSB] & B_reg[MSB] & alu_result[MSB]);
            end
            AND: alu_result = A_reg & B_reg;  // AND
            OR: alu_result = A_reg | B_reg;  // OR
            XOR: alu_result = A_reg ^ B_reg;  // XOR
            SHL: alu_result = (A_reg << shamt); // SHL
            SHR: alu_result = (A_reg >> shamt); // SHR
            ROL: begin // ROL
                if (shamt == 0)
                    alu_result = A_reg;
                else
                    alu_result = (A_reg << shamt) | (A_reg >> (6 - shamt));
            end
        endcase
    end

    // sequential registers
    always @(posedge clk) begin
        if (rst) begin
            A_reg     <= {6{1'b0}};
            B_reg     <= {6{1'b0}};
            opcode_reg<= 3'b000;
            result    <= {6{1'b0}};
            zero      <= 1'b0;
            carry     <= 1'b0;
            overflow  <= 1'b0;
        end else begin
            // latch inputs
            A_reg      <= A_in;
            B_reg      <= B_in;
            opcode_reg <= opcode_in;
            // update outputs (1-cycle delayed)
            result     <= alu_result;
            zero       <= alu_zero;
            carry      <= alu_carry;
            overflow   <= alu_overflow;
        end
    end

endmodule
