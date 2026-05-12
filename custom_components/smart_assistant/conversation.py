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
    extract_media_info,
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
                executed.append(result)
            elif cmd_type == "music":
                result = await self._handle_music(tokens, device_index)
                executed.append(result)
            else:
                result = await self._handle_device(tokens, action_index, device_index, part)
                executed.append(result)

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
        service = find_action(tokens, action_index)
        _LOGGER.debug("Найденное действие: %s для токенов: %s", service, tokens)
        if not service:
            return None

        entity_id = find_device(" ".join(tokens), device_index, service)
        _LOGGER.debug("Найденное устройство: %s", entity_id)
        if not entity_id:
            return None

        domain = entity_id.split(".")[0]

        # Для лампы — все кастомные сервисы → light/turn_on
        ha_service = service
        if service in ("light_brightness_up", "light_brightness_down",
                       "light_set_brightness", "light_set_color", "light_set_effect"):
            ha_service = "turn_on"
            domain = "light"

        service_data = self._build_service_data(tokens, service, entity_id, domain)
        if service_data is None:
            return None

        if not self.hass.services.has_service(domain, ha_service):
            return None

        try:
            await self.hass.services.async_call(
                domain=domain,
                service=ha_service,
                service_data=service_data
            )
            state = self.hass.states.get(entity_id)
            name = state.attributes.get("friendly_name", entity_id) if state else entity_id
            _LOGGER.info("Выполнено: %s → %s", entity_id, ha_service)
            return name
        except Exception as e:
            _LOGGER.error("Ошибка: %s", str(e))
            return None

    def _build_service_data(self, tokens, service, entity_id, domain) -> dict | None:
        from .nlp.action_matcher import extract_light_params

        # Лампа — включить с параметрами
        if domain == "light" and service == "turn_on":
            params = extract_light_params(tokens)
            return {"entity_id": entity_id, **params}

        # Лампа — яркость вверх
        if service == "light_brightness_up":
            return {"entity_id": entity_id, "brightness_step_pct": 20}

        # Лампа — яркость вниз
        if service == "light_brightness_down":
            return {"entity_id": entity_id, "brightness_step_pct": -20}

        # Лампа — установить яркость/цвет/эффект
        if service in ("light_set_brightness", "light_set_color", "light_set_effect"):
            params = extract_light_params(tokens)
            if not params:
                return None
            return {"entity_id": entity_id, **params}

        # Режим очистителя
        if service == "set_preset_mode":
            if domain == "fan":
                mode = extract_preset_mode(tokens, "fan")
                if not mode:
                    return None
                return {"entity_id": entity_id, "preset_mode": mode}
            if domain == "humidifier":
                mode = extract_preset_mode(tokens, "humidifier")
                if not mode:
                    return None
                return {"entity_id": entity_id, "mode": mode}
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

        return {"entity_id": entity_id}

    async def _handle_music(self, tokens: list[str], device_index: dict) -> str | None:
        """Обработка музыкальных команд через Music Assistant"""
        from .nlp.action_matcher import extract_media_info

        media_info = extract_media_info(tokens)

        # По умолчанию — Яндекс Лайт
        entity_id = "media_player.yandex_station_l00sbr700pytvb"

        # Если явно указано другое устройство
        DEVICE_KEYWORDS = {
            "пи": "media_player.pi_assistant_media_player",
            "динамик": "media_player.pi_assistant_media_player",
            "телевизор": "media_player.sony_kd_55x81j_6",
            "телек": "media_player.sony_kd_55x81j_6",
        }
        for keyword, eid in DEVICE_KEYWORDS.items():
            if keyword in tokens:
                entity_id = eid
                break

        state = self.hass.states.get(entity_id)
        player_name = state.attributes.get("friendly_name", entity_id) if state else entity_id

        STOP_TOKENS = {"замолчи", "останови", "хватит", "стоп", "пауза"}
        if any(t in STOP_TOKENS for t in tokens):
            try:
                await self.hass.services.async_call(
                    domain="media_player",
                    service="media_pause",
                    service_data={"entity_id": entity_id}
                )
                return f"Останавливаю на {player_name}"
            except Exception as e:
                _LOGGER.error("Ошибка стоп: %s", e)
                return None

        # Если нет названия — просто play
        if not media_info.get("media_id"):
            try:
                await self.hass.services.async_call(
                    domain="media_player",
                    service="media_play",
                    service_data={"entity_id": entity_id}
                )
                return f"Воспроизвожу на {player_name}"
            except Exception as e:
                _LOGGER.error("Ошибка: %s", e)
                return None

        # Воспроизвести через Music Assistant
        try:
            service_data = {
                "entity_id": entity_id,
                "media_id": media_info["media_id"],
                "enqueue": "replace",
            }
            if media_info.get("media_type"):
                service_data["media_type"] = media_info["media_type"]

            await self.hass.services.async_call(
                domain="music_assistant",
                service="play_media",
                service_data=service_data
            )
            _LOGGER.info("Музыка: %s на %s", media_info["media_id"], entity_id)
            return f"Включаю {media_info['media_id']} на {player_name}"

        except Exception as e:
            _LOGGER.error("Ошибка музыки: %s", e)
            return None