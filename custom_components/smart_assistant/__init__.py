from __future__ import annotations
import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.conversation import async_set_agent

from .conversation import SmartAssistant

_LOGGER = logging.getLogger(__name__)
DOMAIN = "smart_assistant"


def _init_morph():
    from .nlp.morphology import get_morph
    get_morph()


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    try:
        await hass.async_add_executor_job(_init_morph)
        agent = SmartAssistant(hass)
        async_set_agent(hass, entry, agent)
        _LOGGER.info("Smart Assistant запущен")
        return True
    except Exception as e:
        _LOGGER.error("Ошибка: %s", str(e))
        return False


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    from homeassistant.components.conversation import async_unset_agent
    async_unset_agent(hass, entry)
    return True