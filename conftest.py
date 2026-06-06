"""Root conftest: inject lightweight homeassistant stubs so tests run without
a full HA installation.  Only the interfaces actually used by this integration
are defined; everything else is a MagicMock.
"""
import sys
from enum import Enum
from unittest.mock import MagicMock


# ---------------------------------------------------------------------------
# Minimal HA types
# ---------------------------------------------------------------------------

class _UpdateFailed(Exception):
    pass


class _DataUpdateCoordinator:
    def __init__(self, hass, logger, *, name, update_interval=None, **kwargs):
        self.hass = hass
        self.name = name
        self.update_interval = update_interval
        self.data = None

    def __class_getitem__(cls, item):
        return cls


class _CoordinatorEntity:
    def __init__(self, coordinator):
        self.coordinator = coordinator


class _HomeAssistant:
    pass


class _ConfigEntry:
    def __init__(self, entry_id="test_entry_id", data=None):
        self.entry_id = entry_id
        self.data = data or {}


class _SensorDeviceClass(str, Enum):
    DATA_RATE = "data_rate"


class _SensorStateClass(str, Enum):
    MEASUREMENT = "measurement"


class _SensorEntity:
    pass


class _DeviceInfo(dict):
    def __init__(self, **kwargs):
        super().__init__(kwargs)


class _UnitOfDataRate(str, Enum):
    KILOBITS_PER_SECOND = "kbit/s"
    MEGABITS_PER_SECOND = "Mbit/s"


# ---------------------------------------------------------------------------
# Build stub modules
# ---------------------------------------------------------------------------

def _mod(**attrs):
    m = MagicMock()
    for k, v in attrs.items():
        setattr(m, k, v)
    return m


_ha_core = _mod(HomeAssistant=_HomeAssistant)
_ha_coordinator = _mod(
    DataUpdateCoordinator=_DataUpdateCoordinator,
    UpdateFailed=_UpdateFailed,
    CoordinatorEntity=_CoordinatorEntity,
)
_ha_sensor = _mod(
    SensorDeviceClass=_SensorDeviceClass,
    SensorStateClass=_SensorStateClass,
    SensorEntity=_SensorEntity,
)
_ha_const = _mod(
    CONF_HOST="host",
    CONF_PORT="port",
    CONF_USERNAME="username",
    CONF_PASSWORD="password",
    UnitOfDataRate=_UnitOfDataRate,
)
_ha_device_reg = _mod(DeviceInfo=_DeviceInfo)
_ha_config_entries = _mod(ConfigEntry=_ConfigEntry)

sys.modules.update(
    {
        "homeassistant": MagicMock(),
        "homeassistant.core": _ha_core,
        "homeassistant.const": _ha_const,
        "homeassistant.helpers": MagicMock(),
        "homeassistant.helpers.update_coordinator": _ha_coordinator,
        "homeassistant.helpers.device_registry": _ha_device_reg,
        "homeassistant.helpers.entity_platform": MagicMock(),
        "homeassistant.components": MagicMock(),
        "homeassistant.components.sensor": _ha_sensor,
        "homeassistant.config_entries": _ha_config_entries,
        "homeassistant.data_entry_flow": MagicMock(),
        "voluptuous": MagicMock(),
    }
)
