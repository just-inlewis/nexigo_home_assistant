import logging
import socket
import asyncio
from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import STATE_IDLE
from homeassistant.components.homekit.const import EVENT_HOMEKIT_TV_REMOTE_KEY_PRESSED, ATTR_KEY_NAME
from .const import DOMAIN, CONF_NAME, CONF_IP, CONF_PORT

_LOGGER = logging.getLogger(__name__)

KEYEVENT_KEYS = {
                "arrow_up": 19,
                "arrow_left": 21,
                "arrow_right": 22,
                "arrow_down": 20,
                "select": 66,
                "information": 82,
                "back": 4,
                "volume_up": 24,
                "volume_down": 25,
                "mute": 164,
                "play": 126,
                "pause": 127,
                "menu": 3,
                "hdmi1": [178, 21, 21, 21, 22, 66],
                "hdmi2": [178, 21, 21, 21, 22, 22, 66],
            }

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    config_data = entry.data
    name = config_data[CONF_NAME]
    ip = config_data[CONF_IP]
    port = config_data[CONF_PORT]

    entity = TelevisionRemote(name, ip, port, entry.entry_id)
    async_add_entities([entity], update_before_add=True)

class TelevisionRemote(MediaPlayerEntity):
    def __init__(self, name, address, port, unique_id):
        self._name = name
        self._address = address
        self._port = port
        self._unique_id = unique_id
        self._is_playing = True

    @property
    def should_poll(self):
        return False

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def state(self):
        return STATE_IDLE

    @property
    def supported_features(self):
        _supported_features = (
            MediaPlayerEntityFeature.TURN_ON
            | MediaPlayerEntityFeature.TURN_OFF
            | MediaPlayerEntityFeature.VOLUME_STEP
            | MediaPlayerEntityFeature.VOLUME_MUTE
            | MediaPlayerEntityFeature.PAUSE
            | MediaPlayerEntityFeature.PLAY
            | MediaPlayerEntityFeature.SELECT_SOURCE
        )
        return _supported_features

    @property
    def device_class(self):
        return MediaPlayerDeviceClass.TV

    @property
    def source(self) -> str | None:
        return "Menu"

    @property
    def source_list(self) -> list[str]:
        return ["Menu", "Apple TV", "Playstation"]

    async def async_turn_on(self):
        self.async_schedule_update_ha_state(True)

    async def async_turn_off(self):
        self.async_schedule_update_ha_state(True)

    async def async_volume_up(self) -> None:
        await self.send_key_event(KEYEVENT_KEYS["volume_up"])

    async def async_volume_down(self) -> None:
        await self.send_key_event(KEYEVENT_KEYS["volume_down"])

    async def async_mute_volume(self, mute: bool) -> None:
        await self.send_key_event(KEYEVENT_KEYS["mute"])

    async def async_select_source(self, source: str) -> None:
        if source == "Menu":
            await self.send_key_event(3)
        elif source == "Apple TV":
            await self.send_key_event(KEYEVENT_KEYS["hdmi1"])
        elif source == "Playstation":
            await self.send_key_event(KEYEVENT_KEYS["hdmi2"])
        else:
            _LOGGER.error(source)
        self.async_schedule_update_ha_state(True)

    async def async_media_play_pause(self) -> None:
        if self._is_playing:
            self._is_playing = False
            await self.send_key_event(KEYEVENT_KEYS["pause"])
        else:
            self._is_playing = True
            await self.send_key_event(KEYEVENT_KEYS["play"])

    async def async_added_to_hass(self):
        self.hass.bus.async_listen(EVENT_HOMEKIT_TV_REMOTE_KEY_PRESSED, self._handle_tv_remote_key_press)

    async def _handle_tv_remote_key_press(self, event):
        key = event.data.get(ATTR_KEY_NAME)
        key_event = KEYEVENT_KEYS.get(key) 
        if key_event == None:
            _LOGGER.error(f"Unrecongnized key: {key}")
        await self.send_key_event(key_event)

    async def send_key_event(self, keys):
        if not isinstance(keys, list):
            keys = [keys]

        async def send_single_key_event(key):
            _LOGGER.warning(f"SENDING: {key} -> {self._address}:{self._port}")
            message = f"KEYEVENT\r\n{key}\r\n"
            try:
                with socket.create_connection((self._address, self._port), timeout=1) as client:
                    client.sendall(message.encode())
            except (socket.timeout, ConnectionRefusedError) as err:
                _LOGGER.error(f"Connection error to {self._address}:{self._port} => {err}")
            except Exception as err:
                _LOGGER.error(f"Error sending key event to {self._address}:{self._port} => {err}")

        async def send_with_delay():
            for key in keys:
                await send_single_key_event(key)
                await asyncio.sleep(0.1)

        self.hass.async_create_task(send_with_delay())