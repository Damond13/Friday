"""Executor 模块测试的共享 fixture"""

import os
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock

import pytest


@pytest.fixture
def tmp_db(tmp_path: Path) -> Path:
    """提供一个临时 SQLite 数据库路径"""
    return tmp_path / "test_executor.db"


@pytest.fixture
def confirm_yes():
    """总是返回 True 的确认回调"""
    return lambda cmd, level: True


@pytest.fixture
def confirm_no():
    """总是返回 False 的确认回调"""
    return lambda cmd, level: False
