from __future__ import annotations
import logging
from homeassistant.core import HomeAssistant
from homeassistant.components.conversation import AbstractConversationAgent, ConversationResult
from homeassistant.components.conversation.models import ConversationInput, intent

from .nlp import (
    normalize_text,
    build_search_index,
    find_device,
    build_action_index,
    find_action,
    split_commands,
)

_LOGGER = logging.getLogger(__name__)


class SmartAssistant(AbstractConversationAgent):

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    @property
    def supported_languages(self) -> list[str]:
        return ["ru"]

    async def async_process(self, user_input: ConversationInput) -> ConversationResult:
        text = user_input.text.lower()
        _LOGGER.debug("Команда: %s", text)

        device_index = build_search_index(self.hass)
        action_index = build_action_index(self.hass)

        parts = split_commands(text)
        executed = []
        failed = []

        for part in parts:
            tokens = normalize_text(part)

            service = find_action(tokens, action_index)
            if not service:
                failed.append(f"Не понял действие: '{part}'")
                continue

            entity_id = find_device(" ".join(tokens), device_index)
            if not entity_id:
                failed.append(f"Устройство не найдено: '{part}'")
                continue

            domain = entity_id.split(".")[0]
            if not self.hass.services.has_service(domain, service):
                failed.append(f"Команда '{service}' недоступна для {entity_id}")
                continue

            try:
                await self.hass.services.async_call(
                    domain=domain,
                    service=service,
                    service_data={"entity_id": entity_id}
                )
                state = self.hass.states.get(entity_id)
                name = state.attributes.get("friendly_name", entity_id) if state else entity_id
                executed.append(name)
                _LOGGER.info("Выполнено: %s → %s", entity_id, service)

            except Exception as e:
                failed.append(f"Ошибка {entity_id}: {str(e)}")
                _LOGGER.error("Ошибка: %s", str(e))

        if executed and not failed:
            response_text = "Готово! " + ", ".join(executed)
        elif executed and failed:
            response_text = f"Выполнено: {', '.join(executed)}. Не удалось: {', '.join(failed)}"
        else:
            response_text = "Не удалось: " + ", ".join(failed)

        # Правильный формат для HA 2026
        intent_response = intent.IntentResponse(language=user_input.language)
        intent_response.async_set_speech(response_text)

        return ConversationResult(
            response=intent_response,
            conversation_id=user_input.conversation_id
        )