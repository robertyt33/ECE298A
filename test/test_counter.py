import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

@cocotb.test()
async def test_counter(dut):
    # Start clock
    clock = Clock(dut.clk, 10, unit="us")
    cocotb.start_soon(clock.start())

    # Pin mapping (as per module)
    # ui_in[0] = en
    # ui_in[1] = load
    # ui_in[2] = oe
    # ui_in[3] = arst_n
    # uio_in   = load_val[7:0]
    # rst_n, ena are not used for logic

    dut.ui_in.value = 0b0000      # en=0, load=0, oe=0, arst_n=0
    dut.uio_in.value = 0          # load_val
    dut.ena.value = 1             # always 1
    dut.rst_n.value = 1           # not used
    await Timer(1, units='us')

    # --- Asynchronous Reset ---
    # arst_n low resets counter
    dut.ui_in.value = 0b0000      # arst_n=0
    await Timer(1, units='us')
    assert dut.uo_out.value == 0, "Counter didn't reset to 0 (asynchronous reset)"

    # De-assert reset
    dut.ui_in.value = 0b1000      # arst_n=1

    # --- Synchronous Load ---
    # load high loads load_val
    dut.uio_in.value = 0x55       # Example: load_val=85
    dut.ui_in.value = 0b1010      # load=1, arst_n=1
    await RisingEdge(dut.clk)
    dut.ui_in.value = 0b1000      # load=0, arst_n=1
    assert dut.uo_out.value == 0x55, "Counter did not load value synchronously"

    # --- Counting ---
    # en high increments counter
    dut.ui_in.value = 0b1001      # en=1, arst_n=1
    prev = dut.uo_out.value.integer
    await RisingEdge(dut.clk)
    assert dut.uo_out.value == (prev + 1) % 256, "Counter did not increment"

    # --- Tri-state Output (TinyTapeout: drives 0 when disabled) ---
    dut.ui_in.value = 0b1000      # oe=0, arst_n=1
    await Timer(1, units='us')
    assert dut.uo_out.value == 0, "Output not zero when output enable is low"

    # --- Re-enable Output ---
    dut.ui_in.value = 0b1100      # oe=1, arst_n=1
    await Timer(1, units='us')
    assert dut.uo_out.value == (prev + 1) % 256, "Output enable failed after re-enabling"

    dut._log.info("All counter tests passed.")
