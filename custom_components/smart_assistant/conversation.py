from __future__ import annotations
import logging
import aiohttp
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
    extract_media_title,
    detect_command_type,
    extract_state_query,
)

_LOGGER = logging.getLogger(__name__)

MUSIC_ASSISTANT_URL = "http://localhost:8095"


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
                # Запрос состояния устройства
                result = await self._handle_state_query(tokens, device_index)
                if result:
                    executed.append(result)
                else:
                    failed.append(f"Не нашёл информацию: '{part}'")

            elif cmd_type == "music":
                # Музыкальная команда через Music Assistant
                result = await self._handle_music(tokens, device_index, part)
                if result:
                    executed.append(result)
                else:
                    failed.append(f"Не удалось воспроизвести: '{part}'")

            else:
                # Обычная команда устройством
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

        # Температура
        if "temperature" in entity_id or "temp" in entity_id:
            unit = state.attributes.get("unit_of_measurement", "°C")
            return f"{name}: {state.state}{unit}"

        # Влажность
        if "humidity" in entity_id:
            return f"{name}: {state.state}%"

        # Обычное состояние
        state_map = {
            "on": "включён",
            "off": "выключен",
            "idle": "в режиме ожидания",
            "playing": "воспроизводит",
            "paused": "на паузе",
            "unavailable": "недоступен",
        }
        state_text = state_map.get(state.state, state.state)
        return f"{name} {state_text}"

    async def _handle_music(self, tokens: list[str], device_index: dict, part: str) -> str | None:
        """Обработка музыкальных команд через Music Assistant"""
        title = extract_media_title(tokens)

        # Ищем устройство для воспроизведения
        entity_id = find_device(" ".join(tokens), device_index, "play_media")

        if not entity_id:
            # Если устройство не указано — используем Яндекс Лайт по умолчанию
            for eid in self.hass.states.async_entity_ids("media_player"):
                if "yandex" in eid.lower():
                    entity_id = eid
                    break

        if not entity_id:
            return None

        state = self.hass.states.get(entity_id)
        player_name = state.attributes.get("friendly_name", entity_id) if state else entity_id

        if not title:
            # Без названия — просто play
            try:
                await self.hass.services.async_call(
                    domain="media_player",
                    service="media_play",
                    service_data={"entity_id": entity_id}
                )
                return f"Воспроизвожу на {player_name}"
            except Exception as e:
                _LOGGER.error("Ошибка воспроизведения: %s", e)
                return None

        # Ищем трек в Music Assistant
        try:
            ma_player_id = await self._get_ma_player_id(entity_id)
            if ma_player_id:
                success = await self._play_via_music_assistant(title, ma_player_id)
                if success:
                    return f"Включаю {title} на {player_name}"

            # Fallback — через HA напрямую
            await self.hass.services.async_call(
                domain="media_player",
                service="play_media",
                service_data={
                    "entity_id": entity_id,
                    "media_content_id": title,
                    "media_content_type": "music"
                }
            )
            return f"Включаю {title} на {player_name}"

        except Exception as e:
            _LOGGER.error("Ошибка музыки: %s", e)
            return None

    async def _get_ma_player_id(self, entity_id: str) -> str | None:
        """Получаем ID плеера в Music Assistant по entity_id"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{MUSIC_ASSISTANT_URL}/api/players") as resp:
                    if resp.status == 200:
                        players = await resp.json()
                        for player in players:
                            if entity_id in str(player.get("extra_data", {})):
                                return player["player_id"]
                            if entity_id.split(".")[-1] in player.get("player_id", ""):
                                return player["player_id"]
        except Exception as e:
            _LOGGER.error("MA players error: %s", e)
        return None

    async def _play_via_music_assistant(self, title: str, player_id: str) -> bool:
        """Воспроизведение через Music Assistant API"""
        try:
            async with aiohttp.ClientSession() as session:
                # Поиск трека
                async with session.get(
                        f"{MUSIC_ASSISTANT_URL}/api/search",
                        params={"query": title, "media_types": "track", "limit": "1"}
                ) as resp:
                    if resp.status != 200:
                        return False
                    results = await resp.json()

                tracks = results.get("tracks", [])
                if not tracks:
                    return False

                track_uri = tracks[0].get("uri")
                if not track_uri:
                    return False

                # Воспроизвести
                async with session.post(
                        f"{MUSIC_ASSISTANT_URL}/api/players/{player_id}/play_media",
                        json={"uri": track_uri, "media_type": "track"}
                ) as resp:
                    return resp.status in (200, 204)

        except Exception as e:
            _LOGGER.error("MA play error: %s", e)
            return False

    async def _handle_device(self, tokens, action_index, device_index, part) -> str | None:
        """Обработка команд устройствами"""
        service = find_action(tokens, action_index)
        if not service:
            return None

        entity_id = find_device(" ".join(tokens), device_index, service)
        if not entity_id:
            return None

        domain = entity_id.split(".")[0]
        if not self.hass.services.has_service(domain, service):
            return None

        service_data: dict = {"entity_id": entity_id}

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