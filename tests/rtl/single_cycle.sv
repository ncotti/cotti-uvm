module single_cycle (
    input [7:0] A,
    input [7:0] B,
    input [2:0] op,
    input clk,
    input reset_n,
    input start,
    output logic done,
    output logic [15:0] result
);

    always @(posedge clk)
        if (!reset_n) result <= 0;
        else
            case (op)
                3'b001:  result <= 16'(A + B);
                3'b010:  result <= 16'(A & B);
                3'b011:  result <= 16'(A ^ B);
                default: result <= '0;
            endcase  // case (op)

    always @(posedge clk)
        if (!reset_n) done <= 0;
        else done <= ((start == 1'b1) && (op != 3'b000));

endmodule : single_cycle
