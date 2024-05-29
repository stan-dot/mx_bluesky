import json
from typing import List
from unittest.mock import ANY, MagicMock, call, mock_open, patch

import pytest
from dodal.devices.i24.pmac import PMAC
from ophyd_async.core import get_mock_put

from mx_bluesky.I24.serial.fixed_target.ft_utils import Fiducials
from mx_bluesky.I24.serial.fixed_target.i24ssx_Chip_Manager_py3v1 import (
    cs_maker,
    cs_reset,
    initialise,
    laser_control,
    moveto,
    moveto_preset,
    parse_args_and_run_parsed_function,
    pumpprobe_calc,
    scrape_mtr_directions,
    scrape_mtr_fiducials,
    set_pmac_strings_for_cs,
)
from mx_bluesky.I24.serial.setup_beamline import Eiger

mtr_dir_str = """#Some words
mtr1_dir=1
mtr2_dir=-1
mtr3_dir=-1"""

fiducial_1_str = """MTR RBV RAW Corr f_value
MTR1 0 0 1 0
MTR2 1 -1 -1 1
MTR3 0 0 -1 0"""

cs_json = '{"scalex":1, "scaley":2, "scalez":3, "skew":-0.5, "Sx_dir":1, "Sy_dir":-1, "Sz_dir":0}'


@patch("mx_bluesky.I24.serial.fixed_target.i24ssx_Chip_Manager_py3v1.sys")
@patch("mx_bluesky.I24.serial.fixed_target.i24ssx_Chip_Manager_py3v1.get_detector_type")
@patch("mx_bluesky.I24.serial.fixed_target.i24ssx_Chip_Manager_py3v1.caput")
async def test_initialise(
    fake_caput: MagicMock, fake_det: MagicMock, fake_sys: MagicMock, pmac: PMAC, RE
):
    fake_det.return_value = Eiger()
    RE(initialise(pmac))

    fake_caput.assert_called_with(ANY, "eiger")  # last call should be detector

    assert await pmac.x.velocity.get_value() == 20
    assert await pmac.y.acceleration_time.get_value() == 0.01
    assert await pmac.z.high_limit_travel.get_value() == 5.1
    assert await pmac.z.low_limit_travel.get_value() == -4.1

    mock_pmac_str = get_mock_put(pmac.pmac_string)
    mock_pmac_str.assert_has_calls(
        [
            call("m508=100 m509=150", wait=True, timeout=10.0),
            call("m608=100 m609=150", wait=True, timeout=10.0),
            call("m708=100 m709=150", wait=True, timeout=10.0),
            call("m808=100 m809=150", wait=True, timeout=10.0),
        ]
    )


@patch("mx_bluesky.I24.serial.fixed_target.i24ssx_Chip_Manager_py3v1.caget")
async def test_moveto_oxford_origin(fake_caget: MagicMock, pmac: PMAC, RE):
    fake_caget.return_value = 0
    RE(moveto(Fiducials.origin, pmac))
    assert fake_caget.call_count == 1
    assert await pmac.x.user_readback.get_value() == 0.0
    assert await pmac.y.user_readback.get_value() == 0.0


@patch("mx_bluesky.I24.serial.fixed_target.i24ssx_Chip_Manager_py3v1.caget")
async def test_moveto_oxford_inner_f1(fake_caget: MagicMock, pmac: PMAC, RE):
    fake_caget.return_value = 1
    RE(moveto(Fiducials.fid1, pmac))
    assert fake_caget.call_count == 1
    assert await pmac.x.user_readback.get_value() == 24.60
    assert await pmac.y.user_readback.get_value() == 0.0


async def test_moveto_chip_aspecific(pmac: PMAC, RE):
    RE(moveto("zero", pmac))
    assert await pmac.pmac_string.get_value() == "!x0y0z0"


@patch("mx_bluesky.I24.serial.fixed_target.i24ssx_Chip_Manager_py3v1.caput")
async def test_moveto_preset(fake_caput: MagicMock, pmac: PMAC, RE):
    RE(moveto_preset("zero", pmac))
    assert await pmac.pmac_string.get_value() == "!x0y0z0"

    RE(moveto_preset("load_position", pmac))
    assert fake_caput.call_count == 3


@pytest.mark.parametrize(
    "pos_request, expected_num_caput, expected_pmac_move",
    [
        ("collect_position", 3, [0.0, 0.0, 0.0]),
        ("microdrop_position", 0, [6.0, -7.8, 0.0]),
    ],
)
@patch("mx_bluesky.I24.serial.fixed_target.i24ssx_Chip_Manager_py3v1.caput")
async def test_moveto_preset_with_pmac_move(
    fake_caput: MagicMock,
    pos_request: str,
    expected_num_caput: int,
    expected_pmac_move: List,
    pmac: PMAC,
    RE,
):
    RE(moveto_preset(pos_request, pmac))
    assert fake_caput.call_count == expected_num_caput

    assert await pmac.x.user_readback.get_value() == expected_pmac_move[0]
    assert await pmac.y.user_readback.get_value() == expected_pmac_move[1]
    assert await pmac.z.user_readback.get_value() == expected_pmac_move[2]


@pytest.mark.parametrize(
    "laser_setting, expected_pmac_string",
    [
        ("laser1on", " M712=1 M711=1"),
        ("laser1off", " M712=0 M711=1"),
        ("laser2on", " M812=1 M811=1"),
        ("laser2off", " M812=0 M811=1"),
    ],
)
async def test_laser_control_on_and_off(
    laser_setting: str, expected_pmac_string: str, pmac: PMAC, RE
):
    RE(laser_control(laser_setting, pmac))

    assert await pmac.pmac_string.get_value() == expected_pmac_string


@patch("mx_bluesky.I24.serial.fixed_target.i24ssx_Chip_Manager_py3v1.caget")
@patch("mx_bluesky.I24.serial.fixed_target.i24ssx_Chip_Manager_py3v1.bps.sleep")
def test_laser_control_burn_setting(
    fake_sleep: MagicMock, fake_caget: MagicMock, pmac: PMAC, RE
):
    fake_caget.return_value = 0.1
    RE(laser_control("laser1burn", pmac))

    fake_sleep.assert_called_once_with(0.1)
    mock_pmac_str = get_mock_put(pmac.pmac_string)
    mock_pmac_str.assert_has_calls(
        [
            call(" M712=1 M711=1", wait=True, timeout=10.0),
            call(" M712=0 M711=1", wait=True, timeout=10.0),
        ]
    )


@patch(
    "mx_bluesky.I24.serial.fixed_target.i24ssx_Chip_Manager_py3v1.open",
    mock_open(read_data=mtr_dir_str),
)
def test_scrape_mtr_directions():
    res = scrape_mtr_directions()
    assert len(res) == 3
    assert res == (1.0, -1.0, -1.0)


@patch(
    "mx_bluesky.I24.serial.fixed_target.i24ssx_Chip_Manager_py3v1.open",
    mock_open(read_data=fiducial_1_str),
)
def test_scrape_mtr_fiducials():
    res = scrape_mtr_fiducials(1)
    assert len(res) == 3
    assert res == (0.0, 1.0, 0.0)


def test_cs_pmac_str_set(pmac: PMAC, RE):
    RE(
        set_pmac_strings_for_cs(
            pmac,
            {
                "cs1": "#1->-10000X+0Y+0Z",
                "cs2": "#2->+0X+10000Y+0Z",
                "cs3": "#3->0X+0Y+10000Z",
            },
        )
    )
    mock_pmac_str = get_mock_put(pmac.pmac_string)
    mock_pmac_str.assert_has_calls(
        [
            call("&2", wait=True, timeout=10.0),
            call("#1->-10000X+0Y+0Z", wait=True, timeout=10.0),
            call("#2->+0X+10000Y+0Z", wait=True, timeout=10.0),
            call("#3->0X+0Y+10000Z", wait=True, timeout=10.0),
        ]
    )


@patch(
    "mx_bluesky.I24.serial.fixed_target.i24ssx_Chip_Manager_py3v1.set_pmac_strings_for_cs"
)
def test_cs_reset(mock_set_pmac_str: MagicMock, pmac: PMAC, RE):
    RE(cs_reset(pmac))
    mock_set_pmac_str.assert_called_once()


@patch(
    "mx_bluesky.I24.serial.fixed_target.i24ssx_Chip_Manager_py3v1.open",
    mock_open(read_data='{"a":11, "b":12,}'),
)
@patch("mx_bluesky.I24.serial.fixed_target.i24ssx_Chip_Manager_py3v1.caget")
@patch(
    "mx_bluesky.I24.serial.fixed_target.i24ssx_Chip_Manager_py3v1.scrape_mtr_directions"
)
@patch(
    "mx_bluesky.I24.serial.fixed_target.i24ssx_Chip_Manager_py3v1.scrape_mtr_fiducials"
)
def test_cs_maker_raises_error_for_invalid_json(
    fake_fid: MagicMock,
    fake_dir: MagicMock,
    fake_caget: MagicMock,
    pmac: PMAC,
    RE,
):
    fake_dir.return_value = (1, 1, 1)
    fake_fid.return_value = (0, 0, 0)
    with pytest.raises(json.JSONDecodeError):
        RE(cs_maker(pmac))


@patch(
    "mx_bluesky.I24.serial.fixed_target.i24ssx_Chip_Manager_py3v1.open",
    mock_open(read_data='{"scalex":11, "skew":12}'),
)
@patch("mx_bluesky.I24.serial.fixed_target.i24ssx_Chip_Manager_py3v1.caget")
@patch(
    "mx_bluesky.I24.serial.fixed_target.i24ssx_Chip_Manager_py3v1.scrape_mtr_directions"
)
@patch(
    "mx_bluesky.I24.serial.fixed_target.i24ssx_Chip_Manager_py3v1.scrape_mtr_fiducials"
)
def test_cs_maker_raises_error_for_missing_key_in_json(
    fake_fid: MagicMock,
    fake_dir: MagicMock,
    fake_caget: MagicMock,
    pmac: PMAC,
    RE,
):
    fake_dir.return_value = (1, 1, 1)
    fake_fid.return_value = (0, 0, 0)
    with pytest.raises(KeyError):
        RE(cs_maker(pmac))


@patch(
    "mx_bluesky.I24.serial.fixed_target.i24ssx_Chip_Manager_py3v1.open",
    mock_open(read_data=cs_json),
)
@patch("mx_bluesky.I24.serial.fixed_target.i24ssx_Chip_Manager_py3v1.caget")
@patch(
    "mx_bluesky.I24.serial.fixed_target.i24ssx_Chip_Manager_py3v1.scrape_mtr_directions"
)
@patch(
    "mx_bluesky.I24.serial.fixed_target.i24ssx_Chip_Manager_py3v1.scrape_mtr_fiducials"
)
def test_cs_maker_raises_error_for_wrong_direction_in_json(
    fake_fid: MagicMock,
    fake_dir: MagicMock,
    fake_caget: MagicMock,
    pmac: PMAC,
    RE,
):
    fake_dir.return_value = (1, 1, 1)
    fake_fid.return_value = (0, 0, 0)
    with pytest.raises(ValueError):
        RE(cs_maker(pmac))


@patch(
    "mx_bluesky.I24.serial.fixed_target.i24ssx_Chip_Manager_py3v1.fiducial",
    autospec=True,
)
def test_arg_parser_runs_fiducial_function_as_expected(mock_fiducial: MagicMock):
    parse_args_and_run_parsed_function(["fiducial", "2"])
    mock_fiducial.assert_called_once_with(2)


@patch(
    "mx_bluesky.I24.serial.fixed_target.i24ssx_Chip_Manager_py3v1.define_current_chip",
    autospec=True,
)
def test_arg_parser_runs_define_current_chip_function_as_expected(
    mock_define_current_chip: MagicMock,
):
    parse_args_and_run_parsed_function(["define_current_chip", "chip_id"])
    mock_define_current_chip.assert_called_once_with("chip_id")


@patch("mx_bluesky.I24.serial.fixed_target.i24ssx_Chip_Manager_py3v1.caput")
@patch("mx_bluesky.I24.serial.fixed_target.i24ssx_Chip_Manager_py3v1.caget")
def test_pumpprobe_calc(fake_caget: MagicMock, fake_caput: MagicMock, RE):
    fake_caget.side_effect = [0.01, 0.005]
    RE(pumpprobe_calc())
    assert fake_caget.call_count == 2
    assert fake_caput.call_count == 5
    fake_caput.assert_has_calls(
        [
            call(ANY, 0.62),
            call(ANY, 1.24),
            call(ANY, 1.86),
            call(ANY, 3.1),
            call(ANY, 6.2),
        ]
    )
