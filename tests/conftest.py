"""Shared fixtures for DrayTek DSL unit tests.

Creates a DraytekDslCoordinator without a real HomeAssistant instance by
bypassing __init__ and setting only the attributes our code actually reads.
"""
import pytest
from custom_components.draytek_dsl.coordinator import DraytekDslCoordinator


@pytest.fixture
def coordinator():
    """Minimal coordinator instance — no HA runtime required."""
    coord = object.__new__(DraytekDslCoordinator)
    coord.host = "192.168.1.1"
    coord._port = 80
    coord._username = "admin"
    coord._password = "testpass"
    coord._base_url = "http://192.168.1.1:80"
    return coord
