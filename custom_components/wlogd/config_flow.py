"""Config flow for WLOGD integration."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries

from .const import CONF_FIRST, CONF_FIRST_NEXT, CONF_NEXT, CONF_STOPS, DOMAIN


def _parse_stops(raw: str) -> list[int]:
    """Parse a comma-separated stop list into ints."""
    tokens = [part.strip() for part in raw.replace(";", ",").split(",")]
    stops: list[int] = []
    for token in tokens:
        if not token:
            continue
        stops.append(int(token))
    if not stops:
        raise ValueError("No stops provided")
    return stops


class WlogdConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for WLOGD."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle initial setup step."""
        errors = {}

        if user_input is not None:
            try:
                stops = _parse_stops(user_input[CONF_STOPS])
            except (TypeError, ValueError):
                errors[CONF_STOPS] = "invalid_stops"
            else:
                firstnext = user_input[CONF_FIRST_NEXT]
                unique_id = f"{firstnext}-{'-'.join(map(str, stops))}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"WLOGD ({', '.join(map(str, stops))})",
                    data={
                        CONF_STOPS: stops,
                        CONF_FIRST_NEXT: firstnext,
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_STOPS): str,
                vol.Required(CONF_FIRST_NEXT, default=CONF_FIRST): vol.In(
                    [CONF_FIRST, CONF_NEXT]
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)