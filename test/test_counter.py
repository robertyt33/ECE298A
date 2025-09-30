import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

@cocotb.test()
async def test_counter(dut):
    # Start clock
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    # --- Test Asynchronous Reset ---
    dut.rst_n.value = 0  # assert reset
    dut.load.value = 0
    dut.data_in.value = 0
    dut.output_enable.value = 1
    await Timer(1, units='us')
    assert dut.counter_out.value == 0, "Counter didn't reset to 0 (asynchronous reset)"

    dut.rst_n.value = 1  # deassert reset

    # --- Test Synchronous Load ---
    dut.load.value = 1
    dut.data_in.value = 123
    await RisingEdge(dut.clk)
    dut.load.value = 0
    assert dut.counter_out.value == 123, "Counter did not load value synchronously"

    # --- Test Counting ---
    prev = dut.counter_out.value.integer
    await RisingEdge(dut.clk)
    assert dut.counter_out.value == prev + 1, "Counter did not increment"

    # --- Test Tri-state Output ---
    dut.output_enable.value = 0
    await Timer(1, units='us')
    assert str(dut.counter_out.value) == 'ZZZZZZZZ', "Tri-state output not working"

    # --- Re-enable Output ---
    dut.output_enable.value = 1
    await Timer(1, units='us')
    # Should now be driven again
    assert dut.counter_out.value == prev + 1, "Output enable failed after re-enabling"

    dut._log.info("All counter tests passed.")
