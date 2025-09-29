/*
 * Copyright (c) 2025 Robert Tang
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

// 8-bit programmable (loadable) binary counter
// - Asynchronous active-low reset (arst_n)
// - Synchronous load (load + load_val)
// - Increment on enable (en)
// - Tri-state outputs when oe = 0

module tt_um_tyt33 (
    input  wire [7:0] ui_in,    // dedicated inputs
    output wire [7:0] uo_out,   // dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path (load_val[7:0])
    output wire [7:0] uio_out,  // IOs: Output path (unused)
    output wire [7:0] uio_oe,   // IOs: Output enable (unused)
    input  wire       ena,      // always 1 when design is powered
    input  wire       clk,      // system clock
    input  wire       rst_n     // reset_n (not used, use ui[3])
);

    // Map pins
    wire en      = ui_in[0];
    wire load    = ui_in[1];
    wire oe      = ui_in[2];
    wire arst_n  = ui_in[3];
    wire [7:0] load_val = uio_in;

    reg [7:0] cnt;

    // Async reset, sync load/increment
    always @(posedge clk or negedge arst_n) begin
        if (!arst_n)
            cnt <= 8'd0;                // reset (clear)
        else if (load)
            cnt <= load_val;            // synchronous load
        else if (en)
            cnt <= cnt + 8'd1;          // up counter
        // else: hold
    end

    // Tri-state output buffer
    assign uo_out  = (oe) ? cnt : 8'b0; // drives 0 when disabled (TinyTapeout requires no 'z')
    assign uio_out = 8'b0;
    assign uio_oe  = 8'b0;

    // Prevent unused warnings
    wire _unused = &{ena, rst_n, 1'b0};

endmodule

