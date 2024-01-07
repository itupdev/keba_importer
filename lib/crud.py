# -*- coding: utf-8 -*-
# pylint: disable=too-few-public-methods
"""
Database Model and Functions for KEBA Reporter
"""
import os
from datetime import datetime
from sqlalchemy import Column, Integer, String
from sqlalchemy.types import DateTime, DECIMAL, DATETIME
from sqlalchemy import exc as sqlalchemy_exception
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


# database config
db_user = os.environ.get("DB_USERNAME", "keba")
db_pass = os.environ.get("DB_PASSWORD", "keba")
db_name = os.environ.get("DB_DATABASE", "keba")
db_host = os.environ.get("DB_HOSTNAME", "localhost")
db_port = os.environ.get("DB_PORT", 3306)


# create database connection and table
Base = declarative_base()
engine = create_engine(
    f"mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}",
    echo=False
)

# Try to establish a connection
try:
    connection = engine.connect()

except sqlalchemy_exception.OperationalError as exception_error:
    raise SystemExit(str(exception_error)) from exception_error


class TableImport(Base):
    """ORM Model: charge sessions"""
    __tablename__ = 'charges'

    Id = Column(Integer, primary_key=True, index=True)
    StationID = Column(Integer)
    Serial = Column(String(50))
    RFID = Column(String(50))
    Status = Column(String(50))
    Start = Column(DateTime)
    End = Column(DateTime)
    Duration = Column(Integer)
    MeterStart = Column(Integer)
    MeterEnd = Column(Integer)
    Consumption = Column(DECIMAL(20, 2))


class TableRfidCards(Base):
    """ORM Model: rfid cards"""
    __tablename__ = 'rfid'

    id = Column('id', String(50), primary_key=True, unique=True, nullable=False)
    status = Column('status', String(50))
    master = Column('master', String(50), default=0)
    changedDate = Column('changedDate', DATETIME)
    expiryDate = Column('expiryDate', DATETIME)
    usedDate = Column('usedDate', DATETIME)
    name = Column('name', String(50))
    # serialNumbers = Column('Serial', String)


class TableStations(Base):
    """ORM Model: wallbox stations"""
    __tablename__ = 'stations'

    serialNumber = Column(String(50), primary_key=True, unique=True)
    model = Column(String(50))
    alias = Column(String(50))
    macAddress = Column(String(50))
    ipAddress = Column(String(50))
    state = Column(String(50))
    maxPhases = Column(Integer)
    maxCurrent = Column(Integer)
    phaseUsed = Column(String(50))
    authorizationEnabled = Column(String(50))
    hasExternalMeter = Column(String(50))
    number = Column(Integer)


# init database tables
Base.metadata.create_all(engine)

# create the session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = SessionLocal()


def unix_to_datetime(unix_timestamp: int) -> str:
    """
    convert unix timestamp to datetime
    1655739267733 -> 2022-06-20 17:34:27
    :param unix_timestamp: unix timestamp
    """
    return datetime.fromtimestamp(
        int(unix_timestamp) / 1000
    ).strftime('%Y-%m-%d %H:%M:%S')


def date_to_datetime(date_timestamp: str) -> datetime:
    """
    convert unix timestamp to datetime
    13-07-2022 18:24:06 -> 2022-07-13 18:24:06
    :param date_timestamp: date timestamp
    """
    return datetime.strptime(
        str(date_timestamp), '%d-%m-%Y %H:%M:%S'
    )


class KebaDB:
    """Keba database crud"""
    def __init__(self, db_session=session):
        self.session = db_session

    def get_charge(self, search_filter: dict = None):
        """
        get charge session to verify existing entries
        :param search_filter: elements to filter
        """
        search_filter = search_filter or {}
        return self.session.query(TableImport).filter_by(**search_filter).first()

    def get_rfid_card(self, search_filter: dict = None):
        """
        get rfid cars to verify existing entries
        :param search_filter: elements to filter
        """
        search_filter = search_filter or {}
        return self.session.query(TableRfidCards).filter_by(**search_filter).first()

    def get_stations(self, search_filter: dict = None):
        """
        get wallbox stations to verify existing entries
        :param search_filter: elements to filter
        """
        search_filter = search_filter or {}
        return self.session.query(TableStations).filter_by(**search_filter).first()

    def insert_charge(self, data_dict: dict) -> bool:
        """
        insert new wallbox charge
        :param data_dict: dictionary with charges
        :return: True/False
        """
        charge = TableImport(**data_dict)
        if self.get_charge(data_dict):
            return False

        self.session.add(charge)
        self.session.commit()
        return True

    def insert_rfid_card(self, data_dict: dict) -> bool:
        """
        insert/update new rfid card
        :param data_dict: dictionary with rfid card
        :return: True/False
        """
        existing_entry = self.session.query(TableRfidCards).filter_by(
            id=data_dict.get("id")
        )
        if existing_entry:
            if not self.get_rfid_card(data_dict):
                # update changes
                existing_entry.update(data_dict, synchronize_session=False)
                self.session.commit()
                return True
            # no changes
            return False

        # new entry
        self.session.add(TableRfidCards(**data_dict))
        self.session.commit()
        return True

    def insert_station(self, data_dict: dict) -> bool:
        """
        insert/update wallbox station
        :param data_dict: dictionary with wallbox stations
        :return: True/False
        """
        existing_entry = self.session.query(TableStations).filter_by(
            serialNumber=data_dict.get("serialNumber")
        )
        if existing_entry:
            if not self.get_stations(data_dict):
                # update changes
                existing_entry.update(data_dict, synchronize_session=False)
                self.session.commit()
                return True
            # no changes
            return False

        # new entry
        self.session.add(TableStations(**data_dict))
        self.session.commit()
        return True
