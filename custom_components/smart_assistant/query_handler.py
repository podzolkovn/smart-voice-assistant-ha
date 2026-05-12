from __future__ import annotations
import logging
from datetime import datetime, timedelta

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

# Entity ID для TTS и динамика Pi
TTS_SERVICE    = "tts.piper"
SPEAKER_ENTITY = "media_player.pi_assistant_media_player"

# Entity ID для данных
WEATHER_ENTITY = "weather.forecast_home_assistant"

# Датчики дома
HOME_SENSORS = {
    "температура":  "sensor.zhimi_sg_975905212_rmb1_temperature_p_3_7",
    "влажность":    "sensor.zhimi_sg_975905212_rmb1_relative_humidity_p_3_1",
    "pm":           "sensor.zhimi_sg_975905212_rmb1_pm2_5_density_p_3_4",
    "увлажнитель":  "sensor.deerma_sg_922777967_jsq2w_temperature_p_3_7",
}

# Перевод состояния погоды
WEATHER_STATE_MAP = {
    "sunny":           "солнечно",
    "clear-night":     "ясная ночь",
    "partlycloudy":    "переменная облачность",
    "cloudy":          "облачно",
    "fog":             "туман",
    "hail":            "град",
    "lightning":       "гроза",
    "lightning-rainy": "гроза с дождём",
    "pouring":         "сильный дождь",
    "rainy":           "дождь",
    "snowy":           "снег",
    "snowy-rainy":     "мокрый снег",
    "windy":           "ветрено",
    "windy-variant":   "ветрено с облаками",
    "exceptional":     "необычная погода",
}

# Русские названия дней недели
WEEKDAYS = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
MONTHS   = ["января", "февраля", "марта", "апреля", "мая", "июня",
            "июля", "августа", "сентября", "октября", "ноября", "декабря"]


async def handle_query(hass: HomeAssistant, tokens: list[str], original_text: str) -> str | None:
    """Определяем тип вопроса и формируем ответ."""

    WEATHER_WORDS = {"погода", "прогноз", "дождь", "снег", "облачно", "тепло", "холодно", "жарко"}
    TIME_WORDS    = {"время", "час", "минута", "сколько"}
    DATE_WORDS    = {"день", "дата", "число", "сегодня", "неделя",
                     "понедельник", "вторник", "среда", "четверг",
                     "пятница", "суббота", "воскресение"}
    TIMER_WORDS   = {"таймер"}
    HOME_WORDS    = {"температура", "влажность", "pm", "воздух", "очиститель"}

    if any(t in WEATHER_WORDS for t in tokens):
        text = await _weather(hass, tokens)
    elif any(t in TIMER_WORDS for t in tokens):
        text = await _timer(hass, tokens, original_text)
    elif any(t in TIME_WORDS for t in tokens):
        text = _time()
    elif any(t in DATE_WORDS for t in tokens):
        text = _date()
    elif any(t in HOME_WORDS for t in tokens):
        text = _home(hass, tokens)
    else:
        return None

    if not text:
        return None

    await _speak(hass, text)
    return text


async def _weather(hass: HomeAssistant, tokens: list[str]) -> str:
    """Погода из weather entity."""
    state = hass.states.get(WEATHER_ENTITY)
    if not state:
        return "Данные о погоде недоступны"

    attrs = state.attributes
    condition = WEATHER_STATE_MAP.get(state.state, state.state)
    temp      = attrs.get("temperature")
    humidity  = attrs.get("humidity")
    wind      = attrs.get("wind_speed")

    parts = [f"Сейчас {condition}"]
    if temp is not None:
        parts.append(f"температура {temp:.0f} градусов")
    if humidity is not None:
        parts.append(f"влажность {humidity:.0f} процентов")
    if wind is not None:
        parts.append(f"ветер {wind:.0f} километров в час")

    return ", ".join(parts)


def _time() -> str:
    """Текущее время."""
    now = datetime.now()
    h, m = now.hour, now.minute
    if m == 0:
        return f"Сейчас {h} часов ровно"
    return f"Сейчас {h} часов {m} минут"


def _date() -> str:
    """Текущая дата и день недели."""
    now = datetime.now()
    weekday = WEEKDAYS[now.weekday()]
    month   = MONTHS[now.month - 1]
    return f"Сегодня {weekday}, {now.day} {month} {now.year} года"


def _home(hass: HomeAssistant, tokens: list[str]) -> str:
    """Температура, влажность, PM2.5 дома."""
    parts = []

    # Определяем что именно спросили
    if "температура" in tokens:
        state = hass.states.get(HOME_SENSORS["температура"])
        if state:
            parts.append(f"Температура в комнате {state.state} градусов")

    if "влажность" in tokens:
        state = hass.states.get(HOME_SENSORS["влажность"])
        if state:
            parts.append(f"Влажность {state.state} процентов")

    if any(t in ("pm", "воздух", "пыль") for t in tokens):
        state = hass.states.get(HOME_SENSORS["pm"])
        if state:
            parts.append(f"PM2.5 равно {state.state} микрограмм")

    # Если ничего конкретного — выдаём всё
    if not parts:
        t = hass.states.get(HOME_SENSORS["температура"])
        h = hass.states.get(HOME_SENSORS["влажность"])
        p = hass.states.get(HOME_SENSORS["pm"])
        if t: parts.append(f"температура {t.state} градусов")
        if h: parts.append(f"влажность {h.state} процентов")
        if p: parts.append(f"PM2.5 равно {p.state}")

    return ", ".join(parts) if parts else "Данные недоступны"


async def _timer(hass: HomeAssistant, tokens: list[str], original_text: str) -> str:
    """Таймер через автоматизацию HA."""
async def _timer(hass: HomeAssistant, tokens: list[str], original_text: str) -> str:
    """Таймер через HA timer entity."""

    CANCEL_WORDS = {"остановить", "отменить", "выключить", "сбросить", "стоп"}

    # Отмена таймера
    if any(t in CANCEL_WORDS for t in tokens):
        try:
            await hass.services.async_call(
                domain="timer",
                service="cancel",
                target={"entity_id": "timer.assistant_timer"},
            )
            return "Таймер отменён"
        except Exception as e:
            _LOGGER.error("Ошибка отмены таймера: %s", e)
            return "Не удалось отменить таймер"

    minutes = _extract_duration(tokens, "минута")
    seconds = _extract_duration(tokens, "секунда")
    hours   = _extract_duration(tokens, "час")

    total_seconds = (hours * 3600) + (minutes * 60) + seconds

    if total_seconds <= 0:
        return "Не понял на сколько поставить таймер"

    try:
        await hass.services.async_call(
            domain="timer",
            service="start",
            service_data={
                "duration": str(timedelta(seconds=total_seconds)),
            },
            target={"entity_id": "timer.assistant_timer"},
        )
    except Exception:
        _LOGGER.warning("timer.assistant_timer не найден, создайте его в HA")
        return "Таймер не настроен. Создайте timer.assistant_timer в Home Assistant"

    # Формируем ответ
    parts = []
    if hours:   parts.append(f"{hours} {'час' if hours == 1 else 'часа' if hours < 5 else 'часов'}")
    if minutes: parts.append(f"{minutes} {'минуту' if minutes == 1 else 'минуты' if minutes < 5 else 'минут'}")
    if seconds: parts.append(f"{seconds} {'секунду' if seconds == 1 else 'секунды' if seconds < 5 else 'секунд'}")

    return f"Таймер на {' '.join(parts)} запущен"


def _extract_duration(tokens: list[str], unit: str) -> int:
    """Извлекаем число перед единицей времени."""
    for i, token in enumerate(tokens):
        if token == unit and i > 0:
            prev = tokens[i - 1]
            clean = prev.rstrip("%")
            if clean.isdigit():
                return int(clean)
    # Если единица есть но числа нет рядом — ищем любое число
    if unit in tokens:
        for token in tokens:
            clean = token.rstrip("%")
            if clean.isdigit():
                return int(clean)
    return 0


async def _speak(hass: HomeAssistant, text: str) -> None:
    """Озвучиваем ответ через Piper TTS на Pi динамике."""
    try:
        await hass.services.async_call(
            domain="tts",
            service="speak",
            service_data={
                "message": text,
                "cache": False,
            },
            target={
                "entity_id": TTS_SERVICE,
            },
        )
        # Даём TTS время подготовить аудио, затем воспроизводим
        await hass.services.async_call(
            domain="media_player",
            service="play_media",
            service_data={
                "entity_id": SPEAKER_ENTITY,
                "media_content_id": f"media-source://tts/{TTS_SERVICE}?message={text}",
                "media_content_type": "music",
                "announce": True,
            },
        )
    except Exception as e:
        _LOGGER.error("Ошибка TTS: %s", e)