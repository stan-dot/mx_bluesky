from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from bluesky.run_engine import RunEngine
from dodal.beamlines import i24
from dodal.devices.i24.pmac import PMAC
from dodal.devices.zebra import Zebra
from ophyd_async.core import callback_on_mock_put, set_mock_value
from ophyd_async.epics.motion import Motor


def pass_on_mock(motor, call_log: MagicMock | None = None):
    def _pass_on_mock(value, **kwargs):
        set_mock_value(motor.user_readback, value)
        if call_log is not None:
            call_log(value, **kwargs)

    return _pass_on_mock


def patch_motor(
    motor: Motor, initial_position: float = 0, call_log: MagicMock | None = None
):
    set_mock_value(motor.user_setpoint, initial_position)
    set_mock_value(motor.user_readback, initial_position)
    set_mock_value(motor.deadband, 0.001)
    set_mock_value(motor.motor_done_move, 1)
    return callback_on_mock_put(motor.user_setpoint, pass_on_mock(motor, call_log))


@pytest.fixture
def zebra() -> Zebra:
    RunEngine()
    zebra = i24.zebra(fake_with_ophyd_sim=True)

    async def mock_disarm(_):
        await zebra.pc.arm.armed._backend.put(0)  # type: ignore

    async def mock_arm(_):
        await zebra.pc.arm.armed._backend.put(1)  # type: ignore

    zebra.pc.arm.arm_set.set = AsyncMock(side_effect=mock_arm)
    zebra.pc.arm.disarm_set.set = AsyncMock(side_effect=mock_disarm)
    return zebra


@pytest.fixture
def pmac():
    RunEngine()
    pmac: PMAC = i24.pmac(fake_with_ophyd_sim=True)
    with (
        patch_motor(pmac.x),
        patch_motor(pmac.y),
        patch_motor(pmac.z),
    ):
        yield pmac


@pytest.fixture
def RE():
    return RunEngine()
