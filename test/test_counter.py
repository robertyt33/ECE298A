import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer

# Bit mapping for uio_in control (matches RTL):
# [0]=EN, [1]=LOAD, [2]=UP, [3]=OE
def ctrl(en=0, load=0, up=1, oe=0):
    return (oe << 3) | (up << 2) | (load << 1) | (en << 0)

async def reset_dut(dut):
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await Timer(1, units="ns")
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)  # allow state to settle on a clock

async def sync_load(dut, value, oe=1):
    # Synchronous load occurs on the next rising edge with LOAD=1
    dut.ui_in.value = value
    dut.uio_in.value = ctrl(en=0, load=1, up=1, oe=oe)
    await RisingEdge(dut.clk)
    # LOAD is a one-cycle pulse
    dut.uio_in.value = ctrl(en=0, load=0, up=1, oe=oe)
    await RisingEdge(dut.clk)

@cocotb.test()
async def test_basic_reset_and_load(dut):
    """Async reset to 0, then synchronous load and visibility on tri-state bus."""
    # 10ns period clock
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    await reset_dut(dut)

    # After reset, enable OE so we can observe the count on uio_out
    dut.uio_in.value = ctrl(oe=1)
    await RisingEdge(dut.clk)
    assert int(dut.uio_out.value) == 0, "Counter should come out of reset at 0"
    assert int(dut.uio_oe.value) == 0xFF, "OE=1 should drive all uio bits"

    # Synchronous load 0x55
    await sync_load(dut, 0x55, oe=1)
    assert int(dut.uio_out.value) == 0x55, "Synchronous load failed"
    # loaded_pulse is on uo_out[5] for exactly one cycle after LOAD
    assert (int(dut.uo_out.value) >> 5) & 1 == 1, "loaded_pulse not asserted"
    await RisingEdge(dut.clk)
    assert (int(dut.uo_out.value) >> 5) & 1 == 0, "loaded_pulse should clear next cycle"

@cocotb.test()
async def test_count_up_and_wrap(dut):
    """Count up with EN=1, check increment and wrap pulses."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)

    # Load 0xFE, enable counting up, OE on
    await sync_load(dut, 0xFE, oe=1)
    dut.uio_in.value = ctrl(en=1, load=0, up=1, oe=1)

    await RisingEdge(dut.clk)
    assert int(dut.uio_out.value) == 0xFF, "Increment from 0xFE -> 0xFF failed"

    # Next increment should wrap to 0x00 and pulse wrap/carry on uo_out[7:6]
    await RisingEdge(dut.clk)
    assert int(dut.uio_out.value) == 0x00, "Wrap from 0xFF -> 0x00 failed"
    status = int(dut.uo_out.value)
    wrap_pulse   = (status >> 7) & 1
    carry_borrow = (status >> 6) & 1
    assert wrap_pulse == 1 and carry_borrow == 1, "Wrap/carry pulses not asserted on up-wrap"
    await RisingEdge(dut.clk)
    # Pulses should clear
    status = int(dut.uo_out.value)
    assert ((status >> 7) & 1) == 0 and ((status >> 6) & 1) == 0, "Pulses must clear after one cycle"

@cocotb.test()
async def test_count_down_and_wrap(dut):
    """Count down with EN=1, UP=0, check decrement and wrap pulses."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)

    # Load 0x00 then count down -> should wrap to 0xFF with pulses
    await sync_load(dut, 0x00, oe=1)
    dut.uio_in.value = ctrl(en=1, load=0, up=0, oe=1)

    await RisingEdge(dut.clk)
    assert int(dut.uio_out.value) == 0xFF, "Down-wrap from 0x00 -> 0xFF failed"
    status = int(dut.uo_out.value)
    assert ((status >> 7) & 1) == 1 and ((status >> 6) & 1) == 1, "Wrap/borrow pulses not asserted on down-wrap"
    await RisingEdge(dut.clk)
    status = int(dut.uo_out.value)
    assert ((status >> 7) & 1) == 0 and ((status >> 6) & 1) == 0, "Pulses must clear after one cycle"

    # One more step down: 0xFF -> 0xFE
    await RisingEdge(dut.clk)
    assert int(dut.uio_out.value) == 0xFE, "Decrement after wrap failed"

@cocotb.test()
async def test_tristate_enable(dut):
    """Check that OE controls the drive enables on the uio bus."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)

    # Load a value with outputs enabled
    await sync_load(dut, 0xA5, oe=1)
    assert int(dut.uio_oe.value) == 0xFF, "OE=1 should drive all bits"

    # Disable outputs: uio_oe should drop to 0, internal count continues
    dut.uio_in.value = ctrl(en=1, load=0, up=1, oe=0)
    await RisingEdge(dut.clk)
    assert int(dut.uio_oe.value) == 0x00, "OE=0 should set all uio_oe bits low"

    # Re-enable and verify we can still observe the (advanced) count
    dut.uio_in.value = ctrl(en=1, load=0, up=1, oe=1)
    await RisingEdge(dut.clk)
    # After two increments from 0xA5 (one while OE=0, one after OE=1), value should be 0xA7
    assert int(dut.uio_out.value) == 0xA7, "Count should continue when tri-stated; wrong value after re-enable"
