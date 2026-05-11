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
    detect_command_type,
    extract_state_query,
    extract_number,
    extract_preset_mode,
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
            cmd_type = detect_command_type(tokens)

            if cmd_type == "state_query":
                result = await self._handle_state_query(tokens, device_index)
                if result:
                    executed.append(result)
                else:
                    failed.append(f"Не нашёл информацию: '{part}'")
            else:
                result = await self._handle_device(tokens, action_index, device_index, part)
                if result:
                    executed.append(result)
                else:
                    failed.append(f"Не удалось: '{part}'")

        if executed and not failed:
            response_text = "Готово! " + ", ".join(executed)
        elif executed and failed:
            response_text = f"Выполнено: {', '.join(executed)}. Не удалось: {', '.join(failed)}"
        else:
            response_text = "Не удалось: " + ", ".join(failed)

        intent_response = intent.IntentResponse(language=user_input.language)
        intent_response.async_set_speech(response_text)

        return ConversationResult(
            response=intent_response,
            conversation_id=user_input.conversation_id
        )

    async def _handle_state_query(self, tokens: list[str], device_index: dict) -> str | None:
        """Обработка запросов о состоянии устройств"""
        query = extract_state_query(tokens)
        if not query:
            return None

        entity_id = find_device(query, device_index)
        if not entity_id:
            return None

        state = self.hass.states.get(entity_id)
        if not state:
            return None

        name = state.attributes.get("friendly_name", entity_id)

        if "temperature" in entity_id or "temp" in entity_id:
            unit = state.attributes.get("unit_of_measurement", "°C")
            return f"{name}: {state.state}{unit}"

        if "humidity" in entity_id:
            return f"{name}: {state.state}%"

        state_map = {
            "on":          "включён",
            "off":         "выключен",
            "idle":        "в режиме ожидания",
            "unavailable": "недоступен",
        }
        state_text = state_map.get(state.state, state.state)
        return f"{name} {state_text}"

    async def _handle_device(self, tokens, action_index, device_index, part) -> str | None:
        """Обработка команд устройствами"""
        service = find_action(tokens, action_index)
        if not service:
            return None

        entity_id = find_device(" ".join(tokens), device_index, service)
        if not entity_id:
            return None

        domain = entity_id.split(".")[0]
        service_data = self._build_service_data(tokens, service, entity_id, domain)

        if service_data is None:
            return None

        if not self.hass.services.has_service(domain, service):
            return None

        try:
            await self.hass.services.async_call(
                domain=domain,
                service=service,
                service_data=service_data
            )
            state = self.hass.states.get(entity_id)
            name = state.attributes.get("friendly_name", entity_id) if state else entity_id
            _LOGGER.info("Выполнено: %s → %s", entity_id, service)
            return name
        except Exception as e:
            _LOGGER.error("Ошибка: %s", str(e))
            return None

    def _build_service_data(
        self,
        tokens: list[str],
        service: str,
        entity_id: str,
        domain: str
    ) -> dict | None:
        """Формируем параметры команды"""

        # Режим очистителя
        if service == "set_preset_mode":
            if domain == "fan":
                mode = extract_preset_mode(tokens, "fan")
                if not mode:
                    return None
                return {"entity_id": entity_id, "preset_mode": mode}
            return None

        # Влажность увлажнителя
        if service == "set_humidity":
            number = extract_number(tokens)
            if not number:
                return None
            return {"entity_id": entity_id, "humidity": number}

        # Скорость вентилятора
        if service == "set_percentage":
            number = extract_number(tokens)
            if not number:
                return None
            return {"entity_id": entity_id, "percentage": number}

        # Уровень вентилятора увлажнителя
        if service == "select_option":
            level = extract_preset_mode(tokens, "select")
            if not level:
                return None
            return {"entity_id": entity_id, "option": level}

        # Все остальные команды
        return {"entity_id": entity_id}