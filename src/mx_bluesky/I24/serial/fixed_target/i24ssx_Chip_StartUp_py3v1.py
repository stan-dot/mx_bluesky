"""
Startup utilities for chip

This version changed to python3 March2020 by RLO
"""
from __future__ import annotations

import inspect
import logging
import os
import string
import time
from pathlib import Path
from typing import Dict, List

import numpy as np

from mx_bluesky.I24.serial import log
from mx_bluesky.I24.serial.parameters.constants import (
    HEADER_FILES_PATH,
    PARAM_FILE_PATH_FT,
)

logger = logging.getLogger("I24ssx.chip_startup")


def setup_logging():
    # Log should now change name daily.
    logfile = time.strftime("i24_%Y_%m_%d.log").lower()
    log.config(logfile)


def scrape_parameter_file(param_path: Path | str = PARAM_FILE_PATH_FT):
    if not isinstance(param_path, Path):
        param_path = Path(param_path)

    with open(param_path / "parameters.txt", "r") as filein:
        f = filein.readlines()
    for line in f:
        entry = line.rstrip().split()
        if "chip_name" in entry[0].lower():
            chip_name = entry[1]
        elif line.startswith("visit"):
            visit = entry[1]
        elif line.startswith("sub_dir"):
            sub_dir = entry[1]
        elif line.startswith("protein_name"):
            sub_dir = entry[1]
        elif "n_exposures" in entry[0].lower():
            n_exposures = entry[1]
        elif "chip_type" in entry[0].lower():
            chip_type = entry[1]
        elif "map_type" in entry[0].lower():
            map_type = entry[1]
        elif "pump_repeat" in entry[0].lower():
            pump_repeat = entry[1]

    for line in f:
        entry = line.rstrip().split()
        if "pumpexptime" == entry[0].lower().strip():
            pumpexptime = entry[1]
        if "exptime" in entry[0].lower():
            exptime = entry[1]
        if "dcdetdist" in entry[0].lower():
            dcdetdist = entry[1]
        if "prepumpexptime" in entry[0].lower():
            prepumpexptime = entry[1]
        if "pumpdelay" in entry[0].lower():
            pumpdelay = entry[1]
        if "det_type" in entry[0].lower():
            det_type = entry[1]
    return (
        chip_name,
        visit,
        sub_dir,
        n_exposures,
        chip_type,
        map_type,
        pump_repeat,
        pumpexptime,
        pumpdelay,
        exptime,
        dcdetdist,
        prepumpexptime,
        det_type,
    )


def read_parameters(
    param_path: Path | str = PARAM_FILE_PATH_FT, filename: str | None = None
) -> Dict[str, str]:
    """
    Read the parameter file into a lookup dictionary.

    Does the same thing as scrape_parameter_file except doesn't rely on you
    getting the order of arguments right every time (or having to load every one
    if you don't need them all).

    Args:
        filename: The file to read. If None, will load from default location.

    Returns:
        A dictionary with a string entry for every key in the file.
    """
    if not isinstance(param_path, Path):
        param_path = Path(param_path)
    if filename is None:
        filename = "parameters.txt"
    datafile = param_path / filename
    data = datafile.read_text()
    args = {}
    for line in data.splitlines():
        key, value = line.split(maxsplit=1)
        args[key.lower()] = value
    return args


def fiducials(chip_type):
    name = inspect.stack()[0][3]

    if chip_type in ["1", "3", "9"]:
        fiducial_list = []
        # No fiducial for custom?

    else:
        logger.warning("%s Unknown chip_type, %s, in fiducials" % (name, chip_type))
        print("Unknown chip_type in fiducials")
    return fiducial_list


def get_format(chip_type):
    name = inspect.stack()[0][3]
    if chip_type == "1":  # Oxford
        w2w = 0.125
        b2b_horz = 0.800
        b2b_vert = 0.800
        chip_format = [8, 8, 20, 20]
    elif chip_type == "3":  # Oxford Inner
        w2w = 0.600
        b2b_horz = 0.0
        b2b_vert = 0.0
        chip_format = [1, 1, 25, 25]
    elif chip_type == "9":  # Mini oxford (1 block)
        w2w = 0.125
        b2b_horz = 0
        b2b_vert = 0
        chip_format = [1, 1, 20, 20]
    else:
        logger.warning("%s Unknown chip_type, %s, in fiducials" % (name, chip_type))
        print("unknown chip type")
    cell_format = chip_format + [w2w, b2b_horz, b2b_vert]
    return cell_format


def get_xy(addr, chip_type):
    entry = addr.split("_")[-2:]
    R, C = entry[0][0], entry[0][1]
    r2, c2 = entry[1][0], entry[1][1]
    blockR = string.uppercase.index(R)
    blockC = int(C) - 1
    lowercase_list = list(string.ascii_lowercase + string.ascii_uppercase + "0")
    windowR = lowercase_list.index(r2)
    windowC = lowercase_list.index(c2)

    (
        x_block_num,
        y_block_num,
        x_window_num,
        y_window_num,
        w2w,
        b2b_horz,
        b2b_vert,
    ) = get_format(chip_type)

    x = (blockC * b2b_horz) + (blockC * (x_window_num - 1) * w2w) + (windowC * w2w)
    y = (blockR * b2b_vert) + (blockR * (y_window_num - 1) * w2w) + (windowR * w2w)
    return x, y


def pathli(l_in=[], way="typewriter", reverse=False):
    name = inspect.stack()[0][3]
    if reverse is True:
        li = list(reversed(l_in))
    else:
        li = list(l_in)
    long_list = []
    if li:
        if way == "typewriter":
            for i in range(len(li) ** 2):
                long_list.append(li[i % len(li)])
        elif way == "snake":
            lr = list(reversed(li))
            for rep in range(len(li)):
                if rep % 2 == 0:
                    long_list += li
                else:
                    long_list += lr
        elif way == "snake53":
            lr = list(reversed(li))
            for rep in range(53):
                if rep % 2 == 0:
                    long_list += li
                else:
                    long_list += lr
        elif way == "expand":
            for entry in li:
                for rep in range(len(li)):
                    long_list.append(entry)
        elif way == "expand28":
            for entry in li:
                for rep in range(28):
                    long_list.append(entry)
        elif way == "expand25":
            for entry in li:
                for rep in range(25):
                    long_list.append(entry)
        else:
            logger.warning("%s no known path, way =  %s" % (name, way))
            print("no known path")
    else:
        logger.warning("%s no list" % (name))
        print("no list")
    return long_list


def zippum(list_1_args, list_2_args):
    list_1, type_1, reverse_1 = list_1_args
    list_2, type_2, reverse_2 = list_2_args
    A_path = pathli(list_1, type_1, reverse_1)
    B_path = pathli(list_2, type_2, reverse_2)
    zipped_list = []
    for a, b in zip(A_path, B_path):
        zipped_list.append(a + b)
    return zipped_list


def get_alphanumeric(chip_type):
    name = inspect.stack()[0][3]
    cell_format = get_format(chip_type)
    blk_num = cell_format[0]
    wnd_num = cell_format[2]
    uppercase_list = list(string.ascii_uppercase)[:blk_num]
    lowercase_list = list(string.ascii_lowercase + string.ascii_uppercase + "0")[
        :wnd_num
    ]
    number_list = [str(x) for x in range(1, blk_num + 1)]

    block_list = zippum([uppercase_list, "expand", 0], [number_list, "typewriter", 0])
    window_list = zippum(
        [lowercase_list, "expand", 0], [lowercase_list, "typewriter", 0]
    )

    alphanumeric_list = []
    for block in block_list:
        for window in window_list:
            alphanumeric_list.append(block + "_" + window)
    print(len(alphanumeric_list))
    logger.info("%s length of alphanumeric list = %s" % (name, len(alphanumeric_list)))
    return alphanumeric_list


def get_shot_order(chip_type):
    name = inspect.stack()[0][3]
    cell_format = get_format(chip_type)
    blk_num = cell_format[0]
    wnd_num = cell_format[2]
    uppercase_list = list(string.ascii_uppercase)[:blk_num]
    number_list = [str(x) for x in range(1, blk_num + 1)]
    lowercase_list = list(string.ascii_lowercase + string.ascii_uppercase + "0")[
        :wnd_num
    ]

    block_list = zippum([uppercase_list, "snake", 0], [number_list, "expand", 0])
    window_dn = zippum([lowercase_list, "expand", 0], [lowercase_list, "snake", 0])
    window_up = zippum([lowercase_list, "expand", 1], [lowercase_list, "snake", 0])

    switch = 0
    count = 0
    collect_list = []
    for block in block_list:
        if switch == 0:
            for window in window_dn:
                collect_list.append(block + "_" + window)
            count += 1
            if count == blk_num:
                count = 0
                switch = 1
        else:
            for window in window_up:
                collect_list.append(block + "_" + window)
            count += 1
            if count == blk_num:
                count = 0
                switch = 0

    print(len(collect_list))
    logger.info("%s length of collect list = %s" % (name, len(collect_list)))
    return collect_list


def write_file(
    location: str = "i24",
    suffix: str = ".addr",
    order: str = "alphanumeric",
    param_file_path: Path = PARAM_FILE_PATH_FT,
    save_path: Path = HEADER_FILES_PATH,
):
    name = inspect.stack()[0][3]
    logger.info("%s" % name)
    if location == "i24":
        (
            chip_name,
            visit,
            sub_dir,
            n_exposures,
            chip_type,
            map_type,
            pump_repeat,
            pumpexptime,
            exptime,
            dcdetdist,
            prepumpexptime,
        ) = scrape_parameter_file(param_file_path)
    else:
        logger.warning("%s Unknown location, %s" % (name, location))
        print("Unknown location in write_file")
    chip_file_path = save_path / f"chips/{sub_dir}/{chip_name}{suffix}"

    fiducial_list = fiducials(chip_type)
    if order == "alphanumeric":
        addr_list = get_alphanumeric(chip_type)

    elif order == "shot":
        addr_list = get_shot_order(chip_type)

    with open(chip_file_path, "a") as g:
        for addr in addr_list:
            xtal_name = "_".join([chip_name, addr])
            (x, y) = get_xy(xtal_name, chip_type)
            if addr in fiducial_list:
                pres = "0"
            else:
                if "rand" in suffix:
                    pres = str(np.random.randint(2))
                else:
                    pres = "-1"
            line = "\t".join([xtal_name, str(x), str(y), "0.0", pres]) + "\n"
            g.write(line)

    logger.info("%s" % name)


def check_files(
    location: str,
    suffix_list: List[str],
    param_file_path: Path | str = PARAM_FILE_PATH_FT,
    save_path: Path = HEADER_FILES_PATH,
):
    name = inspect.stack()[0][3]
    if location == "i24":
        (
            chip_name,
            visit,
            sub_dir,
            n_exposures,
            chip_type,
            map_type,
            exptime,
            pump_repeat,
            pumpdelay,
            pumpexptime,
            dcdetdist,
            prepumpexptime,
            det_type,
        ) = scrape_parameter_file(param_path=param_file_path)
    else:
        logger.warning("%s Unknown location, %s" % (name, location))
        print("Unknown location in write_file")
    chip_file_path = save_path / f"chips/{sub_dir}/{chip_name}"

    try:
        os.stat(chip_file_path)
    except Exception:
        os.makedirs(chip_file_path)
    for suffix in suffix_list:
        full_fid = chip_file_path.with_suffix(suffix)
        if full_fid.is_file():
            time_str = time.strftime("%Y%m%d_%H%M%S_")
            timestamp_fid = full_fid.parent / f"{time_str}_{chip_name}{full_fid.suffix}"
            print("FIX ME")
            # hack / fix
            print("Already exists ... moving old file:", timestamp_fid)
            logger.info("%s File Already Exists\n -->%s" % (name, timestamp_fid))
    return 1


def write_headers(
    location: str,
    suffix_list: List[str],
    param_file_path: Path = PARAM_FILE_PATH_FT,
    save_path: Path = HEADER_FILES_PATH,
):
    name = inspect.stack()[0][3]
    if location == "i24":
        (
            chip_name,
            visit,
            sub_dir,
            n_exposures,
            chip_type,
            map_type,
            pump_repeat,
            pumpexptime,
            pumpdelay,
            exptime,
            dcdetdist,
            prepumpexptime,
            det_type,
        ) = scrape_parameter_file(param_path=PARAM_FILE_PATH_FT)
        chip_file_path = save_path / f"chips/{sub_dir}/{chip_name}"

        for suffix in suffix_list:
            full_fid = chip_file_path.with_suffix(suffix)
            with open(full_fid, "w") as g:
                g.write(
                    "#23456789012345678901234567890123456789012345678901234567890123456789012345678901234567890\n#\n"
                )
                g.write("#&i24\tchip_name    = %s\n" % chip_name)
                g.write("#&i24\tvisit        = %s\n" % visit)
                g.write("#&i24\tsub_dir      = %s\n" % sub_dir)
                g.write("#&i24\tn_exposures  = %s\n" % n_exposures)
                g.write("#&i24\tchip_type    = %s\n" % chip_type)
                g.write("#&i24\tmap_type     = %s\n" % map_type)
                g.write("#&i24\tpump_repeat  = %s\n" % pump_repeat)
                g.write("#&i24\tpumpexptime  = %s\n" % pumpexptime)
                g.write("#&i24\texptime      = %s\n" % exptime)
                g.write("#&i24\tdcdetdist    = %s\n" % dcdetdist)
                g.write("#&i24\tprepumpexptime  = %s\n" % prepumpexptime)
                g.write("#&i24\tdet_Type     = %s\n" % det_type)
                g.write("#\n")
                g.write(
                    "#XtalAddr      XCoord  YCoord  ZCoord  Present Shot  Spare04 Spare03 Spare02 Spare01\n"
                )
    else:
        logger.warning("%s Unknown location, %s" % (name, location))
        print("Unknown location in write_headers")


def run():
    setup_logging()
    name = inspect.stack()[0][3]
    logger.info("%s Run Startup" % name)
    print("Run StartUp")
    logger.info("%s" % name)
    check_files("i24", [".addr", ".shot"])
    print("Checked files")
    logger.info("%s Checked Files" % name)
    write_headers("i24", [".addr", ".shot"])
    print("Written headers")
    logger.info("%s Written Headers" % name)
    print("Written files")
    logger.info("%s Writing to Files has been disabled. Headers Only" % name)
    # Makes a file with random crystal positions
    check_files("i24", ["rando.spec"])
    write_headers("i24", ["rando.spec"])

    print(10 * "Done ")
    logger.info("%s Done" % name)


if __name__ == "__main__":
    run()
