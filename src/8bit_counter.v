// 8-bit programmable (loadable) binary counter
// Asynchronous active-low reset (arst_n)
// Synchronous load (load + load_val)
// Increment on enable (en)
// Tri-state outputs when oe = 0
`timescale 1ns/1ps
module counter8_tristate (
    input  wire        clk,
    input  wire        arst_n,     // async reset, active-low
    input  wire        en,         // count enable
    input  wire        load,       // synchronous load
    input  wire [7:0]  load_val,   // value to load when load=1
    input  wire        oe,         // output enable (1 = drive, 0 = Hi-Z)
    output wire [7:0]  q           // tri-stated output bus
);

    reg [7:0] cnt;

    // Async reset, sync load/increment
    always @(posedge clk or negedge arst_n) begin
        if (!arst_n)
            cnt <= 8'd0;                 //reset (clear)
        else if (load)
            cnt <= load_val;             //sync
        else if (en)
            cnt <= cnt + 8'd1;           //up counter, increment
        //else hold
    end

    // Tri-state output buffer
    assign uo_out  = (oe) ? cnt : 8'b0; // drives 0 when disabled (TinyTapeout requires no 'z')
    assign uio_out = 8'b0;
    assign uio_oe  = 8'b0;

endmodule

