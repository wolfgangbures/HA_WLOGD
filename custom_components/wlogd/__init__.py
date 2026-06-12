"""WLOGD Wiener Linien custom component for Home Assistant."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

PLATFORMS = ["sensor"]
_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
	"""Set up the WLOGD integration from YAML (legacy support)."""
	_LOGGER.warning("WLOGD core loaded via YAML setup")
	return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
	"""Set up WLOGD from a config entry."""
	_LOGGER.warning("WLOGD core loaded via config entry: %s", entry.entry_id)
	await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
	return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
	"""Unload a WLOGD config entry."""
	_LOGGER.warning("WLOGD core unloading config entry: %s", entry.entry_id)
	return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
