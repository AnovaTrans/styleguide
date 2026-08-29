"""Live Claude model discovery for the model dropdown.

Lists the account's currently available models (via the Models API) so the app
never ships a hardcoded, later-retired id. Legacy generations (Claude 3.x and
older) are filtered out — only current-generation models are offered. Falls
back to a small current-only list when the listing can't be reached.
"""
from __future__ import annotations

import re
from typing import List

import anthropic

# Current-generation fallback if the live listing fails (no key / no network).
FALLBACK_MODELS = ["claude-sonnet-4-6", "claude-opus-4-6", "claude-haiku-4-5"]

# Preference order for the default selection when present in the live list.
_PREFERRED = ["claude-sonnet-4-6", "claude-sonnet-5", "claude-opus-4-6", "claude-haiku-4-5"]

# Friendly labels for known ids; unknown live ids show their raw id.
DISPLAY_NAMES = {
    "claude-sonnet-4-6": "Claude Sonnet 4.6 — best value (recommended)",
    "claude-sonnet-5": "Claude Sonnet 5 — balanced quality",
    "claude-opus-4-8": "Claude Opus 4.8 — most capable",
    "claude-opus-4-7": "Claude Opus 4.7",
    "claude-opus-4-6": "Claude Opus 4.6 — premium quality",
    "claude-haiku-4-5": "Claude Haiku 4.5 — fast & budget",
    "claude-fable-5": "Claude Fable 5",
}

# Legacy generations to hide: Claude 3.x / 2.x / 1.x and the instant line.
# Current models are claude-<name>-4-x / -5, which never match this.
_LEGACY_RE = re.compile(r"^claude-(?:instant|[0-3])[.\-]")


def is_current(model_id: str) -> bool:
    """True for current-generation ids (4.x / 5), False for legacy ones."""
    return not _LEGACY_RE.match(model_id)


def list_model_ids(api_key: str) -> List[str]:
    """Current-generation model ids, newest first. Empty list on any failure."""
    if not api_key:
        return []
    try:
        client = anthropic.Anthropic(api_key=api_key)
        models = list(client.models.list())
        models.sort(key=lambda m: str(getattr(m, "created_at", "") or ""), reverse=True)
        return [m.id for m in models if getattr(m, "id", None) and is_current(m.id)]
    except Exception:
        return []


def default_model(ids: List[str]) -> str:
    """Pick a sensible default from available ids."""
    for pref in _PREFERRED:
        if pref in ids:
            return pref
    return ids[0] if ids else FALLBACK_MODELS[0]


def display_name(model_id: str) -> str:
    """Friendly label for a known id, else the raw id."""
    return DISPLAY_NAMES.get(model_id, model_id)
