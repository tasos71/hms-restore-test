import pytest
import os
import docker
from . import hms_backup_restore_base
from sqlalchemy import create_engine,text


@pytest.mark.order(1)
def test_airport_counts():
    hms_backup_restore_base.assert_count('airport_t', 0)

@pytest.mark.order(10)
def test_flights_counts():
    hms_backup_restore_base.assert_count('flights_t', 0)

@pytest.mark.order(20)
def test_upload_airport_1():
    output = hms_backup_restore_base.upload_airport(1)
    assert 0 == int(output.exit_code), f"Failed to upload airport data for period 1: {output.output.decode('utf-8')}"

@pytest.mark.order(30)
def test_upload_flights_1():
    output = hms_backup_restore_base.upload_flights(1)
    assert 0 == int(output.exit_code), f"Failed to upload flights data for period 1: {output.output.decode('utf-8')}"

@pytest.mark.order(40)
def test_repair_partitions():
    result = hms_backup_restore_base.do_trino_repair()
    print (result)

@pytest.mark.order(50)
def test_notifications():
    hms_backup_restore_base.assert_notifications(['CREATE_DATABASE', 'CREATE_TABLE', 'ALTER_TABLE', 'CREATE_TABLE', 'ALTER_TABLE', 'ADD_PARTITION'])

@pytest.mark.order(60)
def test_airport_counts_after():
    hms_backup_restore_base.assert_count('airport_t', 999)

@pytest.mark.order(70)
def test_flights_counts_after():
    hms_backup_restore_base.assert_count('flights_t', 605765)

@pytest.mark.order(80)
def test_backup_minio():
    hms_backup_restore_base.backup_minio(1)
