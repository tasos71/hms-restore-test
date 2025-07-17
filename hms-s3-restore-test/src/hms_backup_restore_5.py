import pytest
import os
import docker
from . import hms_backup_restore_base
from sqlalchemy import create_engine,text

period = 5

@pytest.mark.order(1)
def test_backup_hms():
    hms_backup_restore_base.backup_hms('D')
