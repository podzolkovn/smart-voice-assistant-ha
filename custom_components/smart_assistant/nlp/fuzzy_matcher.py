from rapidfuzz import process, fuzz
from homeassistant.core import HomeAssistant

# Домены которые поддерживают медиа команды
MEDIA_DOMAINS = {
    "ma_play", "play_media", "media_play", "media_pause",
    "volume_up", "volume_down", "volume_set"
}

def build_search_index(hass: HomeAssistant) -> dict[str, str]:
    """Строим индекс для поиска устройств"""
    index = {}
    for state in hass.states.async_all():
        entity_id = state.entity_id
        attributes = state.attributes
        name = attributes.get("friendly_name", entity_id).lower()

        # Полное имя
        index[name] = entity_id

        # Каждое слово из имени
        for word in name.split():
            if len(word) > 3:
                index[word] = entity_id

        # Псевдонимы из HA
        for alias in attributes.get("aliases", []):
            index[alias.lower()] = entity_id

    return index


def find_device(query: str, index: dict[str, str], service: str = None) -> str | None:
    """Нечёткий поиск entity_id по запросу"""

    # Медиа команды — только media_player
    if service in MEDIA_DOMAINS:
        filtered_index = {
            k: v for k, v in index.items()
            if v.startswith("media_player.")
        }
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