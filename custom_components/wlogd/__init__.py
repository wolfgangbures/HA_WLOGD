"""WLOGD Wiener Linien custom component for Home Assistant."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry, SOURCE_IMPORT
from homeassistant.core import HomeAssistant

from .const import CONF_FIRST, CONF_FIRST_NEXT, CONF_STOPS, DOMAIN

PLATFORMS = ["sensor"]
_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
	"""Set up the WLOGD integration from YAML (legacy support)."""
	_LOGGER.warning("WLOGD core loaded via YAML setup")

	for sensor_cfg in config.get("sensor", []):
		if sensor_cfg.get("platform") != DOMAIN:
			continue

		import_data = {
			CONF_STOPS: sensor_cfg.get(CONF_STOPS, []),
			CONF_FIRST_NEXT: sensor_cfg.get(CONF_FIRST_NEXT, CONF_FIRST),
		}
		hass.async_create_task(
			hass.config_entries.flow.async_init(
				DOMAIN,
				context={"source": SOURCE_IMPORT},
				data=import_data,
			)
		)

	return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
	"""Set up WLOGD from a config entry."""
	_LOGGER.warning("WLOGD core loaded via config entry: %s", entry.entry_id)
	if entry.source == SOURCE_IMPORT:
		_LOGGER.warning(
			"WLOGD config entry %s is YAML-import marker; sensor setup stays in YAML mode",
			entry.entry_id,
		)
		return True

	await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
	return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
	"""Unload a WLOGD config entry."""
	_LOGGER.warning("WLOGD core unloading config entry: %s", entry.entry_id)
	return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
