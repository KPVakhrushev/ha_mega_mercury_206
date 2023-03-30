from __future__ import annotations
import logging
from datetime import timedelta

from homeassistant.components.sensor import SensorEntityDescription, SensorDeviceClass, SensorStateClass, SensorEntity

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity


from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType


from .const import DOMAIN
from .mercury import Mercury
from .mercury import EntityFormat

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=30)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):    
    Mercury = hass.data[DOMAIN]
    await Mercury.async_update_state()
    entities: list[MercurySensor] = [
        MercurySensor(Mercury.sensorData[v], Mercury) for v in Mercury.sensorData
    ]
    async_add_entities(entities)

class MercurySensor(SensorEntity, CoordinatorEntity):
    """Representation of a sensor."""

    def __init__(self, EntityData: EntityFormat, instance: Mercury):
        """Initialize the sensor."""

        CoordinatorEntity.__init__(
            self=self,
            coordinator=instance,
        )
        self.EntityName = EntityData.name
        self._attr_name = f"{instance.name} {EntityData.name}"
        self._attr_unique_id = f"{instance.name}-{EntityData.name}"

        self._attr_native_unit_of_measurement = EntityData.unit
        self._attr_device_class = EntityData.device
        self._attr_state_class = EntityData.stateclass

        _LOGGER.debug(f"Init of sensor {self.name} ({EntityData.name})")

    @property
    def native_value(self):
        return self.coordinator.sensorData[self.EntityName].value