module three_cycle (
    input [7:0] A,
    input [7:0] B,
    input clk,
    input reset_n,
    input start,
    output logic done,
    output logic [15:0] result
);

    logic [7:0] a_int, b_int;
    logic [15:0] mult1, mult2;
    logic done1, done2, done3;

    always @(posedge clk)
        if (!reset_n) begin
            done   <= 0;
            done3  <= 0;
            done2  <= 0;
            done1  <= 0;
            a_int  <= 0;
            b_int  <= 0;
            mult1  <= 0;
            mult2  <= 0;
            result <= 0;
        end else begin  // if (!reset_n)
            a_int  <= A;
            b_int  <= B;
            mult1  <= a_int * b_int;
            mult2  <= mult1;
            result <= mult2;
            done3  <= start & !done;
            done2  <= done3 & !done;
            done1  <= done2 & !done;
            done   <= done1 & !done;
        end  // else: !if(!reset_n)
endmodule : three_cycle
