from __future__ import annotations
import voluptuous as vol
from homeassistant import config_entries

DOMAIN = "smart_assistant"


class SmartAssistantConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    VERSION = 1

    async def async_step_user(self, user_input=None):
        # убрали await — метод не корутина
        self._async_abort_entries_match({})

        if user_input is not None:
            return self.async_create_entry(
                title="Smart Assistant",
                data={}
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({})
        )