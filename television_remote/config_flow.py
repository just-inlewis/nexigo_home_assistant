import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, CONF_NAME, CONF_IP, CONF_PORT

_LOGGER = logging.getLogger(__name__)

class TelevisionRemoteConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data=user_input
            )
        data_schema = vol.Schema({
            vol.Required(CONF_NAME, default="Television"): cv.string,
            vol.Required(CONF_IP): cv.string,
            vol.Required(CONF_PORT, default=8121): cv.port,
        })
        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return TelevisionRemoteOptionsFlowHandler(config_entry)


class TelevisionRemoteOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        data_schema = vol.Schema({
            vol.Optional(CONF_NAME, default=self.config_entry.data.get(CONF_NAME)): cv.string,
            vol.Optional(CONF_IP, default=self.config_entry.data.get(CONF_IP)): cv.string,
            vol.Optional(CONF_PORT, default=self.config_entry.data.get(CONF_PORT)): cv.port,
        })
        return self.async_show_form(step_id="init", data_schema=data_schema)