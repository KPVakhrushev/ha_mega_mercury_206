"""The Tion breezer component."""
from __future__ import annotations

from bleak.backends.device import BLEDevice
import datetime
import logging
import math
from datetime import timedelta
from functools import cached_property

from homeassistant.const import ELECTRIC_POTENTIAL_VOLT, ELECTRIC_CURRENT_AMPERE, ENERGY_KILO_WATT_HOUR, POWER_KILO_WATT

from homeassistant.components.bluetooth import BluetoothCallbackMatcher
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback

from homeassistant.components.sensor import SensorEntityDescription, SensorDeviceClass as DC,  STATE_CLASS_TOTAL_INCREASING, STATE_CLASS_MEASUREMENT

import asyncio
import aiohttp

_LOGGER = logging.getLogger(__name__)

class Mercury(DataUpdateCoordinator):
    mega_url = 'http://192.168.0.14/sec/'
    mercury_sn = "0235C0F9"
    sensorData: dict[EntityFormat] = dict()
    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry):                
        self.__keep_alive = datetime.timedelta(seconds = 10)

        self._config_entry: ConfigEntry = config_entry
        self.hass = hass        
        super().__init__(
            name= 'Mercury206',
            hass=hass,
            logger=_LOGGER,
            update_interval=self.__keep_alive,
            update_method=self.async_update_state, # какой метод будет вызывать DataUpdateCoordinator для обновления данных
        )

    async def request(self, cmd):
        async with aiohttp.ClientSession() as session:
            for i in range(10):            
                url = self.mega_url + "?uart_tx="+self.mercury_sn+cmd+"&mode=rs485" 
                async with session.get(url) as resp:
                    answer = await resp.text()
                await asyncio.sleep(0.2)

                async with session.get(self.mega_url + "?uart_rx=1&mode=rs485") as resp:
                    answer = await resp.text()                
                if answer and answer.find('Error')<0 : break 
            
            answer = str.replace(answer[15:], '|', '')              
        return answer    
    async def parse(self, cmd):
        output = await self.request(cmd)        
        formats = commands[cmd]
        offset = 0        
        for format in formats:  
            format.value = None
            self.sensorData[format.name] = format
            if not output : continue
            substr = output[offset: offset+format.byte*2]
            offset+= format.byte*2
            if format.type == 'bcd':
                value = ''
                for char in substr:
                    value+= str(int(char, base=16))
            elif format.type == 'd':
                value = substr
            value = int(value)/format.precission            
            format.value = value            
        return
    async def async_update_state(self):
        for cmd in commands: 
            await self.parse(cmd)        
        
        # for name in self.sensorData: print ( name + " " + str(self.sensorData[name].value))
        return self.sensorData
    
class EntityFormat:
    byte = 3 
    type='bcd'
    name = 'Мощность'
    unit = 'кВт'
    precission = 1000
        
    def __init__(self, name:str, unit:str, stateclass:str, device_type:str, answer_type:str, byte:int, precission=0):
        self.byte = byte
        self.type = answer_type
        self.name = name
        self.unit = unit
        self.precission = precission
        self.device = device_type
        self.stateclass = stateclass

# https://github.com/home-assistant/core/blob/dev/homeassistant/const.py  - единицы измерения 
# https://github.com/home-assistant/core/blob/dev/homeassistant/components/sensor/const.py - типы устройств

commands = {    
    '27': [        
        EntityFormat('Тариф 1', ENERGY_KILO_WATT_HOUR, STATE_CLASS_TOTAL_INCREASING, DC.ENERGY, 'd', 4, 100),
        EntityFormat('Тариф 2', ENERGY_KILO_WATT_HOUR, STATE_CLASS_TOTAL_INCREASING, DC.ENERGY, 'd', 4, 100)
    ],
    
    '63':[
        EntityFormat('Напряжение', ELECTRIC_POTENTIAL_VOLT, STATE_CLASS_MEASUREMENT, DC.VOLTAGE, 'bcd', 2, 10), 
        EntityFormat('Ток',        ELECTRIC_CURRENT_AMPERE, STATE_CLASS_MEASUREMENT, DC.CURRENT, 'bcd', 2, 100), 
        EntityFormat('Мощность',   POWER_KILO_WATT,         STATE_CLASS_MEASUREMENT, DC.POWER,   'bcd', 3, 1000)
    ]

    #'2B':["Чтение времени последнего отключения напряжения" , 'timedate'],
    #'85':["Чтение содержимого тарифных аккумуляторов реактивной энергии", 4],
    #'26':['Чтение текущей мощности в нагрузке', 'm'],
}
