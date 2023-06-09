import pytest

from mx_bluesky.I24.serial.fixed_target.i24ssx_Chip_Collect_py3v1 import (
    get_chip_prog_values,
    get_prog_num,
)


def test_get_chip_prog_values():
    chip_dict = get_chip_prog_values(
        "1",
        "i24",
        "0",
        0,
        0,
        0,
        n_exposures=2,
    )
    assert type(chip_dict) is dict
    assert chip_dict["X_NUM_STEPS"][1] == 20 and chip_dict["X_NUM_BLOCKS"][1] == 8
    assert chip_dict["PUMP_REPEAT"][1] == 0
    assert chip_dict["N_EXPOSURES"][1] == 2


@pytest.mark.parametrize(
    "chip_type, map_type, pump_repeat, expected_prog",
    [
        ("1", "0", "0", 11),  # Oxford chip, full chip, no pump
        ("1", "1", "0", 12),  # Oxford chip, map generated by mapping lite, no pump
        ("6", "", "0", 11),  # Custom chip, map type not needed(full assumed), no pump
        ("1", "", "2", 14),  # Oxford chip, assumes mapping lite, pump 2
    ],
)
def test_get_prog_number(chip_type, map_type, pump_repeat, expected_prog):
    assert get_prog_num(chip_type, map_type, pump_repeat) == expected_prog