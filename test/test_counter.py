import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

@cocotb.test()
async def test_counter(dut):
    clock = Clock(dut.clk, 10, unit="us")
    cocotb.start_soon(clock.start())

    # --- Reset ---
    dut.ui_in.value = 0b0000  # arst_n=0, all other signals low
    dut.uio_in.value = 0
    dut.ena.value = 1
    dut.rst_n.value = 1
    await Timer(1, unit='us')
    assert dut.uo_out.value == 0, "Counter didn't reset to 0 (async reset)"

    # --- Deassert reset ---
    dut.ui_in.value = 0b1000  # arst_n=1, all other signals low
    await RisingEdge(dut.clk)

    # --- Synchronous Load ---
    # Set load_val and load high
    dut.uio_in.value = 0x55
    dut.ui_in.value = 0b1010  # load=1, arst_n=1
    await RisingEdge(dut.clk)
    # Deassert load (hold arst_n high)
    dut.ui_in.value = 0b1000  # load=0, arst_n=1
    await RisingEdge(dut.clk)
    # Output should now be 0x55
    dut._log.info(f"uo_out value after load: {dut.uo_out.value.integer}")
    assert dut.uo_out.value == 0x55, f"Counter did not load value synchronously, got {dut.uo_out.value.integer}"

    # --- Counting ---
    dut.ui_in.value = 0b1001  # en=1, arst_n=1
    prev = dut.uo_out.value.integer
    await RisingEdge(dut.clk)
    assert dut.uo_out.value == (prev + 1) % 256, "Counter did not increment"

    # --- Output Enable ---
    dut.ui_in.value = 0b1000  # oe=0, arst_n=1
    await Timer(1, unit='us')
    assert dut.uo_out.value == 0, "Output not zero when output enable is low"

    # --- Re-enable output ---
    dut.ui_in.value = 0b1100  # oe=1, arst_n=1
    await Timer(1, unit='us')
    assert dut.uo_out.value == (prev + 1) % 256, "Output enable failed after re-enabling"

    dut._log.info("All counter tests passed.")
