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

# Нативный entity Pi динамика (Wyoming/Linux Voice Assistant).
# НЕ media_player.pi_assistant_media_player_2 — это Music Assistant обёртка.
PI_ENTITY_ID = "media_player.pi_assistant_media_player"

# Нативный entity Яндекс станции от интеграции AlexxIT/YandexStation.
# НЕ media_player.iandeks_lait — это Music Assistant обёртка поверх станции.
# Команды отправляются через play_media с media_content_type: command.
YANDEX_ENTITY_ID = "media_player.yandex_station_l00sbr700pytvb"


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
                # Передаём оригинальный текст (до лемматизации) — нужен для
                # формирования команды Алисе в человекочитаемом виде
                result = await self._handle_music(tokens, device_index, original_text=part)
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

    async def _handle_music(self, tokens: list[str], device_index: dict, original_text: str = "") -> str | None:
        """Обработка музыкальных команд через Music Assistant"""
        from .nlp.action_matcher import extract_media_info

        media_info = extract_media_info(tokens)

        # По умолчанию — Яндекс Лайт
        entity_id = YANDEX_ENTITY_ID

        DEVICE_KEYWORDS = {
            "пи":        PI_ENTITY_ID,
            "динамик":   PI_ENTITY_ID,
            "телевизор": "media_player.sony_kd_55x81j_6",
            "телек":     "media_player.sony_kd_55x81j_6",
            "яндекс":    YANDEX_ENTITY_ID,
            "алиса":     YANDEX_ENTITY_ID,
            "станция":   YANDEX_ENTITY_ID,
            "колонка":   YANDEX_ENTITY_ID,
        }
        for keyword, eid in DEVICE_KEYWORDS.items():
            if keyword in tokens:
                entity_id = eid
                break

        state = self.hass.states.get(entity_id)
        player_name = state.attributes.get("friendly_name", entity_id) if state else entity_id

        from .nlp.dictionaries.media import MEDIA_STOP_KEYWORDS
        if any(t in MEDIA_STOP_KEYWORDS for t in tokens):
            try:
                if entity_id == YANDEX_ENTITY_ID:
                    # FIX: AlexxIT/YandexStation не реагирует на media_pause/media_stop.
                    # Команды отправляются через play_media с media_content_type: command.
                    await self.hass.services.async_call(
                        domain="media_player",
                        service="play_media",
                        service_data={
                            "entity_id": entity_id,
                            "media_content_id": "стоп",
                            "media_content_type": "command",
                        }
                    )
                else:
                    await self.hass.services.async_call(
                        domain="media_player",
                        service="media_pause",
                        service_data={"entity_id": entity_id}
                    )
                _LOGGER.info("Стоп музыки: %s", entity_id)
                return f"Останавливаю на {player_name}"
            except Exception as e:
                _LOGGER.error("Ошибка стоп: %s", e)
                return None

        # Если нет названия — просто play (resume)
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

        # FIX: Яндекс станция (AlexxIT/YandexStation) не управляется через
        # Music Assistant. Команда отправляется напрямую Алисе через play_media
        # с media_content_type: command — Алиса сама ищет и включает музыку.
        if entity_id == YANDEX_ENTITY_ID:
            # Используем оригинальный текст (до лемматизации), иначе Алиса
            # получит сломанную речь типа "включить мой волна".
            # Убираем только слова выбора устройства.
            YANDEX_DEVICE_PHRASES = {
                "на яндексе", "на станции", "на колонке", "на алисе",
                "яндекс", "станция", "колонка", "алиса",
            }
            alice_command = original_text.strip()
            for phrase in YANDEX_DEVICE_PHRASES:
                alice_command = alice_command.replace(phrase, "").strip()
            alice_command = " ".join(alice_command.split())  # убираем двойные пробелы
            try:
                await self.hass.services.async_call(
                    domain="media_player",
                    service="play_media",
                    service_data={
                        "entity_id": entity_id,
                        "media_content_id": alice_command,
                        "media_content_type": "command",
                    }
                )
                _LOGGER.info("Яндекс команда: '%s' → %s", alice_command, entity_id)
                return f"Включаю {media_info.get('media_id') or alice_command} на {player_name}"
            except Exception as e:
                _LOGGER.error("Ошибка Яндекс команды: %s", e)
                return None

        # FIX: Pi динамик не зарегистрирован в Music Assistant —
        # используем стандартный media_player.play_media напрямую.
        if entity_id == PI_ENTITY_ID:
            try:
                await self.hass.services.async_call(
                    domain="media_player",
                    service="play_media",
                    service_data={
                        "entity_id": entity_id,
                        "media_content_id": media_info["media_id"],
                        "media_content_type": media_info.get("media_type") or "music",
                    }
                )
                _LOGGER.info("Pi музыка: %s на %s", media_info["media_id"], entity_id)
                return f"Включаю {media_info['media_id']} на {player_name}"
            except Exception as e:
                _LOGGER.error("Ошибка Pi музыка: %s", e)
                return None

        # Воспроизвести через Music Assistant (другие MA-плееры)
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
            _LOGGER.info("MA музыка: %s на %s", media_info["media_id"], entity_id)
            return f"Включаю {media_info['media_id']} на {player_name}"

        except Exception as e:
            _LOGGER.error("Ошибка музыки: %s", e)
            return None