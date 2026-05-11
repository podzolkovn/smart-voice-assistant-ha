from homeassistant.core import HomeAssistant
from .dictionaries import (
    BASE_SYNONYMS,
    AUTO_TRANSLATE,
    PURIFIER_MODES,
    HUMIDIFIER_FAN_LEVELS,
    STATE_QUERY_KEYWORDS,
    SPLITTERS,
    STATE_STOP_WORDS,
)


def detect_command_type(tokens: list[str]) -> str:
    has_state_query = any(t in STATE_QUERY_KEYWORDS for t in tokens)
    has_action = any(t in BASE_SYNONYMS for t in tokens)
    if has_state_query and not has_action:
        return "state_query"
    return "device"


def extract_state_query(tokens: list[str]) -> str | None:
    query_tokens = [t for t in tokens if t not in STATE_STOP_WORDS and len(t) > 2]
    return " ".join(query_tokens) if query_tokens else None


def extract_number(tokens: list[str]) -> int | None:
    for token in tokens:
        if token.isdigit():
            return int(token)
    return None


def extract_preset_mode(tokens: list[str], domain: str) -> str | None:
    if domain == "fan":
        for token in tokens:
            if token in PURIFIER_MODES:
                return PURIFIER_MODES[token]
    if domain == "select":
        for token in tokens:
            if token in HUMIDIFIER_FAN_LEVELS:
                return HUMIDIFIER_FAN_LEVELS[token]
    return None


def build_action_index(hass: HomeAssistant) -> dict[str, str]:
    index = dict(BASE_SYNONYMS)
    services = hass.services.async_services()
    for domain_services in services.values():
        for service in domain_services:
            if service in AUTO_TRANSLATE:
                for synonym in AUTO_TRANSLATE[service]:
                    index[synonym] = service
    return index


def find_action(tokens: list[str], action_index: dict[str, str]) -> str | None:
    for token in tokens:
        if token in action_index:
            return action_index[token]
    return None


def split_commands(text: str) -> list[str]:
    for splitter in SPLITTERS:
        text = text.replace(f" {splitter} ", "|")
    return [t.strip() for t in text.split("|")]