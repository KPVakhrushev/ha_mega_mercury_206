"""The Tion breezer component."""
from __future__ import annotations

from bleak.backends.device import BLEDevice
import datetime
import logging
import math
from datetime import timedelta
from functools import cached_property

from homeassistant.components import bluetooth
from homeassistant.components.bluetooth import BluetoothCallbackMatcher
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.typing import ConfigType

import asyncio

from .mercury import Mercury

_LOGGER = logging.getLogger(__name__)

def setup(hass: HomeAssistant, config: ConfigType) -> bool:
    instance = Mercury(hass, config)
    hass.data[DOMAIN] = instance 
    hass.helpers.discovery.load_platform('sensor', DOMAIN, {}, config)
    return True