#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""KEBA Download Charge Report from WebUI"""
import sys
import json
import argparse

# custom modules
from lib import crud
from lib import keba

__author__ = 'Frank Hofmann'
__version__ = '20240101'
__app_desc__ = f'Keba Importer v{__version__}'


def load_arguments(description: str, version: str):
    """
    read arguments from cli
    :param description: script description
    :param version: version information
    :return: namespace from parsed arguments
    """
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawTextHelpFormatter
    )
    # optional parameters
    parser.add_argument('-c', '--charge',
                        help='import charge sessions from last 45 days', action="store_true"
                        )
    parser.add_argument('-r', '--rfid',
                        help='import rfid cards', action="store_true"
                        )
    parser.add_argument('-s', '--station',
                        help='import wallbox stations', action="store_true"
                        )
    parser.add_argument('-w', '--write',
                        help='write reports to json files', action="store_true"
                        )
    parser.add_argument("-a", "--all",
                        help="full import charges, stations, rfid cards", action="store_true"
                        )
    parser.add_argument('-v', '--version',
                        help='show program version', action="store_true"
                        )
    parser.parse_args()
    args = parser.parse_args(args=None if sys.argv[1:] else ['--help'])
    if args.version:
        sys.exit(version)

    return args


def write_json_file(content, file_name) -> bool:
    """
    write list of dicts to json file
    :param content:
    :param file_name:
    :return:
    """
    with open(file_name, 'w', encoding="utf-8") as outfile:
        json.dump(content, outfile)
    return True


if __name__ == "__main__":
    param = load_arguments(__app_desc__, __version__)

    # initialize wallbox and database session
    # read configuration from .env
    keba_session = keba.KebaWallbox()
    db = crud.KebaDB()

    # Full Import
    if param.all:
        param.rfid = True
        param.charge = True
        param.station = True

    # Import RFID Cards
    if param.rfid:
        rfid_cards = keba_session.read_rfids()
        if param.write:
            write_json_file(rfid_cards, "/tmp/keba_rfids.json")
        for x in rfid_cards:
            db.insert_rfid_card(x)

    # Import Wallbox Charges
    if param.charge:
        charge_report = keba_session.read_charges()
        if param.write:
            write_json_file(charge_report, "/tmp/keba_charges.json")
        for x in charge_report:
            db.insert_charge(x)

    # Import Wallbox Stations
    if param.station:
        station_report = keba_session.read_stations()
        if param.write:
            write_json_file(station_report, "/tmp/keba_stations.json")
        for x in station_report:
            db.insert_station(x)

