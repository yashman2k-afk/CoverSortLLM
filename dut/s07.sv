module top_1(
    input  [3:0] a,
    input  [3:0] b,
    output       a_gt_b,  // 1 if a > b
    output       a_eq_b,  // 1 if a == b
    output       a_lt_b   // 1 if a < b
);
    assign a_gt_b = (a > b);
    assign a_eq_b = (a == b);
    assign a_lt_b = (a < b);
endmodule
