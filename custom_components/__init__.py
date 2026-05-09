from __future__ import annotations
import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.components import conversation

from .conversation import SmartAssistant

_LOGGER = logging.getLogger(__name__)
DOMAIN = "smart_assistant"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    try:
        agent = SmartAssistant(hass)
        conversation.async_set_agent(hass, entry, agent)
        _LOGGER.info("Smart Assistant запущен")
        return True
    except Exception as e:
        _LOGGER.error("Ошибка запуска Smart Assistant: %s", str(e))
        return False


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    conversation.async_unset_agent(hass, entry)
    return True