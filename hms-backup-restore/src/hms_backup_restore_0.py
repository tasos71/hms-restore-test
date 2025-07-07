import pytest
import os
import docker
from . import hms_backup_restore_base
from sqlalchemy import create_engine,text


@pytest.mark.order(10)
def test_create_schema():
    hms_backup_restore_base.create_schema()

@pytest.mark.order(20)
def test_create_airport_table():
    hms_backup_restore_base.create_airport_table()

@pytest.mark.order(30)
def test_create_flights_table():
    hms_backup_restore_base.create_flights_table()


@pytest.mark.order(40)
def test_airport_counts():
    hms_backup_restore_base.assert_count('airport_t', 0)

@pytest.mark.order(50)
def test_flights_counts():
    hms_backup_restore_base.assert_count('flights_t', 0)

@pytest.mark.order(60)
def test_notifications():
    hms_backup_restore_base.assert_notifications(['CREATE_DATABASE', 'CREATE_TABLE', 'ALTER_TABLE', 'CREATE_TABLE', 'ALTER_TABLE'])

@pytest.mark.order(70)
def test_airport_counts_after():
    hms_backup_restore_base.assert_count('airport_t', 0)

@pytest.mark.order(80)
def test_flights_counts_after():
    hms_backup_restore_base.assert_count('flights_t', 0)

