from rapidfuzz import process, fuzz
from homeassistant.core import HomeAssistant


def build_search_index(hass: HomeAssistant) -> dict[str, str]:
    index = {}
    for state in hass.states.async_all():
        entity_id = state.entity_id
        attributes = state.attributes
        name = attributes.get("friendly_name", entity_id).lower()

        index[name] = entity_id

        for word in name.split():
            if len(word) > 3:
                index[word] = entity_id

        for alias in attributes.get("aliases", []):
            index[alias.lower()] = entity_id

    return index


def find_device(query: str, index: dict[str, str], service: str = None) -> str | None:
    """Нечёткий поиск entity_id по запросу"""

    # Если сервис медиа — ищем только среди media_player
    if service in ("play_media", "media_play", "media_pause",
                   "volume_up", "volume_down", "volume_set"):
        filtered_index = {k: v for k, v in index.items()
                          if v.startswith("media_player.")}
    else:
        filtered_index = index

    match = process.extractOne(
        query,
        filtered_index.keys(),
        scorer=fuzz.partial_ratio,
        score_cutoff=60
    )
    if match:
        return filtered_index[match[0]]
    return None