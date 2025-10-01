/*
 * Copyright (c) 2025 Robert Tang
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

// 8-bit programmable counter
// - Asynchronous reset (active-low rst_n)
// - Synchronous parallel load from ui_in[7:0]
// - Enable and Up/Down controls
// - Tri-state outputs presented on the uio bus, gated by OE
//
// Control mapping (read from uio_in):
//   uio_in[0] : EN   (1 = count, 0 = hold)
//   uio_in[1] : LOAD (1 = synchronously load ui_in on next clk)
//   uio_in[2] : UP   (1 = up-count, 0 = down-count)  -- ignored during LOAD
//   uio_in[3] : OE   (1 = drive count on uio_out, 0 = high-Z)
//   uio_in[7:4] : unused (read as 0)
//
// Data mapping:
//   ui_in[7:0] : parallel load value (P[7:0])
//
// Outputs:
//   uio_out[7:0] : tri-stated count value; driven only when OE=1
//   uio_oe[7:0]  : output enables (replicated OE)
//   uo_out[7:0]  : status/debug (always driven):
//                  [7] wrap_pulse   (1-cycle pulse on FF->00 or 00->FF)
//                  [6] carry_borrow (carry on up wrap, borrow on down wrap)
//                  [5] loaded_pulse (1-cycle pulse when LOAD occurred)
//                  [4:0] current count[4:0] (low 5 bits for quick visibility)
module tt_um_tyt33 (
    input  wire [7:0] ui_in,    // Dedicated inputs (parallel load value)
    output wire [7:0] uo_out,   // Dedicated outputs (status/debug)
    input  wire [7:0] uio_in,   // IOs: Input path (control signals)
    output wire [7:0] uio_out,  // IOs: Output path (tri-state count)
    output wire [7:0] uio_oe,   // IOs: Enable path (1=drive uio_out)
    input  wire       ena,      // always 1 when powered (unused)
    input  wire       clk,      // clock
    input  wire       rst_n     // asynchronous reset, active-low
);

  // ---- Control decode -------------------------------------------------------
  wire en_i   = uio_in[0];
  wire load_i = uio_in[1];
  wire up_i   = uio_in[2];
  wire oe_i   = uio_in[3];

  // ---- Counter core ---------------------------------------------------------
  reg  [7:0] count_q, count_d;
  reg        wrap_pulse_q, wrap_pulse_d;
  reg        carry_borrow_q, carry_borrow_d;
  reg        loaded_pulse_q, loaded_pulse_d;

  // Next-state logic
  always @* begin
    // defaults
    count_d         = count_q;
    wrap_pulse_d    = 1'b0;
    carry_borrow_d  = 1'b0;
    loaded_pulse_d  = 1'b0;

    if (load_i) begin
      // synchronous parallel load
      count_d        = ui_in;
      loaded_pulse_d = 1'b1;
    end else if (en_i) begin
      if (up_i) begin
        // up-count
        if (count_q == 8'hFF) begin
          count_d        = 8'h00;
          wrap_pulse_d   = 1'b1;
          carry_borrow_d = 1'b1; // carry on wrap
        end else begin
          count_d = count_q + 8'd1;
        end
      end else begin
        // down-count
        if (count_q == 8'h00) begin
          count_d        = 8'hFF;
          wrap_pulse_d   = 1'b1;
          carry_borrow_d = 1'b1; // borrow on wrap
        end else begin
          count_d = count_q - 8'd1;
        end
      end
    end
  end

  // Async reset, sync update
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      count_q         <= 8'h00;
      wrap_pulse_q    <= 1'b0;
      carry_borrow_q  <= 1'b0;
      loaded_pulse_q  <= 1'b0;
    end else begin
      count_q         <= count_d;
      wrap_pulse_q    <= wrap_pulse_d;
      carry_borrow_q  <= carry_borrow_d;
      loaded_pulse_q  <= loaded_pulse_d;
    end
  end

  // ---- Tri-state output bus (uio) ------------------------------------------
  assign uio_out = count_q;           // value to drive when enabled
  assign uio_oe  = {8{oe_i}};         // drive all 8 bits only when OE=1

  // ---- Always-driven debug/status pins -------------------------------------
  assign uo_out = {
      wrap_pulse_q,        // [7]
      carry_borrow_q,      // [6]
      loaded_pulse_q,      // [5]
      count_q[4:0]         // [4:0] low bits of count
  };

  // ---- Unused inputs packed to avoid lint/synthesis warnings ----------------
  wire _unused = &{ena, 1'b0};

endmodule

