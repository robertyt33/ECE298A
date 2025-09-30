import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

@cocotb.test()
async def test_counter(dut):
    clock = Clock(dut.clk, 10, unit="us")
    cocotb.start_soon(clock.start())

    # --- Asynchronous Reset ---
    dut.ui_in.value = 0b0000  # arst_n=0 (active low), all other signals low
    dut.uio_in.value = 0
    dut.ena.value = 1
    dut.rst_n.value = 1
    await Timer(1, unit='us')
    assert dut.uo_out.value == 0, "Counter didn't reset to 0 (async reset)"

    # --- Deassert reset ---
    dut.ui_in.value = 0b1000  # arst_n=1, all other signals low
    await RisingEdge(dut.clk)

    # --- Synchronous Load ---
    # Set load_val, load=1, arst_n=1, oe=1
    dut.uio_in.value = 0x55
    dut.ui_in.value = 0b1110  # arst_n=1, load=1, oe=1, en=0
    await RisingEdge(dut.clk)
    # Deassert load, keep output enabled
    dut.ui_in.value = 0b1100  # arst_n=1, load=0, oe=1, en=0
    await RisingEdge(dut.clk)
    dut._log.info(f"uo_out value after load: {dut.uo_out.value.integer}")
    assert dut.uo_out.value == 0x55, f"Counter did not load value synchronously, got {dut.uo_out.value.integer}"

    # --- Counting ---
    dut.ui_in.value = 0b1101  # arst_n=1, load=0, oe=1, en=1
    prev = dut.uo_out.value.integer
    await RisingEdge(dut.clk)
    dut._log.info(f"uo_out value after count: {dut.uo_out.value.integer}")
    assert dut.uo_out.value == (prev + 1) % 256, "Counter did not increment"

    # --- Output Enable Low ---
    dut.ui_in.value = 0b1000  # oe=0, arst_n=1, others low
    await Timer(1, unit='us')
    assert dut.uo_out.value == 0, "Output not zero when output enable is low"

    # --- Re-enable output ---
    dut.ui_in.value = 0b1100  # oe=1, arst_n=1, others low
    await Timer(1, unit='us')
    dut._log.info(f"uo_out value after re-enable: {dut.uo_out.value.integer}")
    assert dut.uo_out.value == (prev + 1) % 256, "Output enable failed after re-enabling"

    dut._log.info("All counter tests passed.")
