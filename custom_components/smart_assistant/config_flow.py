from __future__ import annotations
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant

DOMAIN = "smart_assistant"


class SmartAssistantConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow для Smart Assistant"""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        # Разрешаем только одну установку
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(
                title="Smart Assistant",
                data={}
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
            description_placeholders={
                "description": "Нажмите Подтвердить для установки"
            }
        )