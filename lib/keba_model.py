# -*- coding: utf-8 -*-
# pylint: disable=invalid-name
# pylint: disable=too-many-instance-attributes
"""Keba Dataclass Models"""
from datetime import datetime
from dataclasses import dataclass, asdict, fields
from typing import List, Optional


def unix_to_datetime(unix_timestamp: int) -> str:
    """
    convert unix timestamp to datetime
    1655739267733 -> 2022-06-20 17:34:27
    :param unix_timestamp: unix timestamp
    """
    return datetime.fromtimestamp(
        unix_timestamp / 1000
    ).strftime('%Y-%m-%d %H:%M:%S')


def repr_without_none(cls):
    """dataclass decorator for representer without none values"""
    original_repr = cls.__repr__

    def new_repr(self):
        original = original_repr(self)
        fields_with_values = asdict(self)
        none_fields = [k for k, v in fields_with_values.items() if v is None]
        for _field in none_fields:
            original = original.replace(f", {_field}=None", "")
        return original

    cls.__repr__ = new_repr
    return cls


@dataclass
class KebaChargeReport:
    """custom charge report from csv"""
    StationID: int
    Serial: str
    RFID: str
    Status: str
    Start: str
    End: str
    Duration: int
    MeterStart: int
    MeterEnd: int
    Consumption: float

    def __post_init__(self):
        """translation and verification"""
        date_format = '%d-%m-%Y %H:%M:%S'
        self.End = str(datetime.strptime(str(self.End), date_format))
        self.Start = str(datetime.strptime(str(self.Start), date_format))
        self.Duration = int(self.Duration)
        self.StationID = int(self.StationID)
        self.Consumption = float(self.Consumption)
        self.MeterStart = round(float(self.MeterStart))
        self.MeterEnd = round(float(self.MeterEnd))


# @repr_without_none
@dataclass
class KebaRFID:
    """keba model: rfid cards"""
    id: str
    status: str
    serialNumbers: List
    name: str = ''
    master: bool = False
    changedDate: Optional[str] = None
    usedDate: Optional[str] = None
    expiryDate: Optional[str] = None

    def __post_init__(self):
        if self.expiryDate:
            self.expiryDate = unix_to_datetime(int(self.expiryDate))
        if self.usedDate:
            self.usedDate = unix_to_datetime(int(self.usedDate))
        if self.changedDate:
            self.changedDate = unix_to_datetime(int(self.changedDate))
        self.__dict__.pop("serialNumbers")


@dataclass
class MeterLines:
    """keba nested model: StationMeter"""
    socketPhase: str
    current: int
    voltage: int


@dataclass
class StationMeter:
    """keba nested model: KebaStation -> meter"""
    meterValue: int
    totalActivePower: int
    totalPowerFactor: int
    phasesSupported: int
    currentOffered: int
    temperature: int
    lines: List[MeterLines]


@dataclass
class KebaStation:
    """keba model: wallbox stations"""
    number: int
    serialNumber: str
    maxPhases: int
    maxCurrent: int
    phaseUsed: str
    macAddress: str
    ipAddress: str
    state: str
    hasExternalMeter: bool
    authorizationEnabled: bool
    alias: str
    model: str
    # x2active: bool
    # mvaPublicKey: str
    # vehiclePlugged: bool
    # dipSwitchSettings: list[bool]
    # meter: dict[StationMeter]

    def __init__(self, **kwargs):
        """filter unused key, value pairs"""
        names = {f.name for f in fields(self)}
        self.__dict__.update({k: v for k, v in kwargs.items() if k in names})
