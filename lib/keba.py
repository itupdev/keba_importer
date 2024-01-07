# -*- coding: utf-8 -*-
"""Keba Wallbox Reader"""
import os
import time
import csv
from datetime import datetime, timedelta
from calendar import timegm
from json import JSONDecodeError
from http.client import HTTPConnection
from bs4 import BeautifulSoup
import requests
import keba_model

__version__ = '20240107'

# Debug Request Call 0/1 from `http.client.HTTPConnection`
HTTPConnection.debuglevel = 0


def gen_unix_date(days: int = 45) -> tuple[str, str]:
    """
    generate unix timestamp from now and before x days
    :param days: days before now
    :return: tuple with two strings (start, end)
    """
    date_start = datetime.utcnow()
    date_end = datetime.utcnow() - timedelta(days)
    utc_time_start = timegm(date_start.utctimetuple()) * 1000
    utc_time_end = timegm(date_end.utctimetuple()) * 1000
    return str(utc_time_start), str(utc_time_end)


def csv_to_dict(csv_content: str,
                field_names: list,
                csv_delimiter=";",
                skip_header: bool = False
                ) -> list:
    """
    convert csv content to a list of dictionary
    :param csv_content: content of csv from string or file
    :param field_names: table field names
    :param csv_delimiter: csv delimiter
    :param skip_header: ignore header
    :return: list of dicts
    """
    if skip_header:
        csv_content = csv_content.split("\n", 1)[1]

    csv_dict = csv.DictReader(
        csv_content.splitlines(),
        fieldnames=field_names,
        delimiter=csv_delimiter
    )
    return list(csv_dict)


def table_header_charges() -> list:
    """csv header for charge reports"""
    return [
        'StationID',
        'Serial',
        'RFID',
        'Status',
        'Start',
        'End',
        'Duration',
        'MeterStart',
        'MeterEnd',
        'Consumption'
    ]


class KebaWallbox:
    """Keba Wallbox WebUI Class"""

    def __init__(
        self,
        username=os.environ.get("KEBA_USER", "admin"),
        password=os.environ.get("KEBA_PASS", "admin"),
        hostname=os.environ.get("KEBA_HOST", "192.168.0.1"),
        proto=os.environ.get("KEBA_PROTO", "http")
    ) -> None:
        """init class definition"""
        self.__url_base = f"{proto}://{hostname}"
        self.__url_ajax = self.__url_base + "/ajax.php"
        self.__header = {
            "Accept": "*/*",
            "Content-Type": "application/json"
        }
        self.__session = self.__login__(username, password)

    def __login__(self, username, password):
        """initialize login session from webui"""
        session = requests.Session()
        session.verify = False
        session.trust_env = True

        # read csrf-token from login page
        # <meta content="XXXXX" name="csrf-token"/>
        response = session.get(self.__url_base + "/", headers=self.__header)
        dom_document = BeautifulSoup(response.text, 'lxml')
        try:
            csrf_meta = dom_document.find('meta', attrs={'name': 'csrf-token'})
            csrf_token = csrf_meta.get("content")
        except AttributeError as error:
            raise SystemExit("ErrorAPI: cant get csrf token") from error

        # login WebUI
        response = session.post(
            self.__url_ajax,
            headers=self.__header,
            json={
                "username": username,
                "password": password,
                "csrftoken": csrf_token
            }
        )
        if not response.ok or "Access Denied" in response.text:
            raise SystemExit("ErrorAPI: can't open login session")

        self.csrf = csrf_token
        return session

    def __request_model(self, path, method="GET") -> dict:
        """
        define request model
        :param path: model path
        :param method: model method
        :return: dict of request model
        """
        return {
            "csrftoken": self.csrf,
            "cpmrestrequest": {
                "path": path,
                "method": method
            }
        }

    def __post_ajax(self, path: str):
        """
        post ajax call
        :param path: requested model path
        """
        response = self.__session.post(
            self.__url_ajax,
            headers=self.__header,
            json=self.__request_model(path)
        )
        if not response.ok:
            raise TypeError("ErrorAPI: Request response to {path} failed.")
        return response

    @property
    def get_charge(self):
        """get charge sessions"""
        report_start, report_end = gen_unix_date()
        data = {
            "csrftoken": self.csrf,
            "exportchargingsessions": {
                "columns": [
                    {"data": "wallboxNumber", "search": {"value": ""}},
                    {"data": "wallboxSerialNumber", "search": {"value": ""}},
                    {"data": "tokenId", "search": {"value": ""}},
                    {"data": "startDate", "search": {"value": report_end}},
                    {"data": "endDate", "search": {"value": report_start}}
                ], "order": [{"column": 5, "dir": "desc"}]
            }
        }
        response = self.__session.post(
            self.__url_ajax,
            headers=self.__header,
            json=data
        )
        if not response.ok:
            raise SystemExit("ErrorAPI: cant execute report request.")

        # slow down. the wallbox is not very fast,...
        time.sleep(1)

        # get export status
        response = self.__session.post(
            self.__url_ajax,
            headers=self.__header,
            json=self.__request_model("/chargingsessions/export/status")
        )
        try:
            # {"total":4,"exported":4}
            export_status = response.json()
        except JSONDecodeError as error:
            raise TypeError("ErrorAPI: cant get valid json response") from error

        if not export_status.get('exported') or export_status['exported'] == 0:
            # we found no exported reports
            return None

        # slow down. the wallbox is not very fast,...
        time.sleep(1)

        response = self.__session.get(
            self.__url_base + f"/export.php?chargingsessions=&t={report_start}",
            headers=self.__header
        )
        if not response.ok:
            raise SystemExit("ErrorAPI: cant initiate csv export.")

        # header: Content-Disposition: attachment; filename="ChargingSession_22269607.csv"
        # header: Content-Type: text/csv;charset=UTF-8
        resp_header = response.headers
        content_type = resp_header.get("Content-Type")
        if 'text/csv' not in content_type.lower():
            raise ValueError("ErrorAPI: cant find Content-Type: text/csv on csv export.")
        return response

    def get_rfid(self):
        """get rfid tokens"""
        response = self.__session.post(
            self.__url_ajax,
            headers=self.__header,
            json=self.__request_model("/chargingtokens")
        )
        if not response.ok:
            raise SystemExit("ErrorAPI: cant get rfid tokens.")
        return response

    def get_station(self):
        """get wallbox stations"""
        response = self.__session.post(
            self.__url_ajax,
            headers=self.__header,
            json=self.__request_model("/wallboxes")
        )
        if not response.ok:
            raise SystemExit("ErrorAPI: cant get wallbox stations.")

        return response

    def read_charges(self) -> list:
        """
        read charges, validate and translate to dictionary
        :return: list(dict of charges)
        """
        charge_imported = self.get_charge
        report_content = charge_imported.text
        report_dict = csv_to_dict(
            report_content, table_header_charges(), ";", True
        )

        # Workaround for empty End for Status != CLOSED
        report_dict = [z for z in report_dict if z['End'] != '']
        return [vars(keba_model.KebaChargeReport(**x)) for x in report_dict]

    def read_rfids(self) -> list:
        """
        read rfid cards and translate to custom format
        :return: list(dict of charges)
        """
        rfid_imported = self.get_rfid()
        rfid_cards = rfid_imported.json()
        return [vars(keba_model.KebaRFID(**x)) for x in rfid_cards]

    def read_stations(self) -> list:
        """
        read wallbox stations and translate to custom format
        :return: list(dict of charges)
        """
        station_imported = self.get_station()
        stations = station_imported.json()
        return [vars(keba_model.KebaStation(**x)) for x in stations]
