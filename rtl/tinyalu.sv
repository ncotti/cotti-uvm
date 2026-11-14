module tinyalu (
    input clk,
    input [7:0] A,
    input [7:0] B,
    input [2:0] op,
    input reset_n,
    input start,
    output done,
    output [15:0] result
);

    wire [15:0] result_aax, result_mult;
    wire start_single, start_mult;

    logic done_aax, done_mult;

    assign start_single = start & ~op[2];
    assign start_mult   = start & op[2];

    single_cycle and_add_xor (
        .A,
        .B,
        .op,
        .clk,
        .reset_n,
        .start (start_single),
        .done  (done_aax),
        .result(result_aax)
    );

    three_cycle mult (
        .A,
        .B,
        .clk,
        .reset_n,
        .start (start_mult),
        .done  (done_mult),
        .result(result_mult)
    );


    assign done   = (op[2]) ? done_mult : done_aax;

    assign result = (op[2]) ? result_mult : result_aax;

endmodule  // tinyalu





