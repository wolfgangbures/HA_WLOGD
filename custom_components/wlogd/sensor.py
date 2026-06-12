"""
WLOGD Wiener Linien departure sensor.

Shows the next (or second-next) departure from a given stop for all lines
serving that stop, or filtered to a specific line.

Configuration (in sensors YAML):

    - platform: wlogd
    firstnext: first          # 'first' or 'next' (optional, default: first)
    stops:
      - 141                   # plain stop-id (int or quoted string)
      - 160
      - stop: 143             # extended form – filter to a specific line
        line: 4               # lineId from the API
        firstnext: next       # override per stop
"""
from __future__ import annotations

import asyncio
import logging
from time import monotonic
from datetime import datetime, timedelta, timezone

import aiohttp
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util.dt import parse_datetime

from .const import (
    BASE_URL,
    CONF_APIKEY,
    CONF_FIRST,
    CONF_FIRST_NEXT,
    CONF_LINEID,
    CONF_NEXT,
    CONF_STOP,
    CONF_STOPS,
    DEFAULT_ICON,
    DEPARTURE_INDEX,
    DEPARTURE_LABEL,
    DOMAIN,
    FALLBACK_URL,
    VEHICLE_ICONS,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=30)

# Schema for the extended stop form: {stop: 141, line: 4, firstnext: first}
_STOP_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_STOP): vol.Coerce(int),
        vol.Optional(CONF_LINEID): vol.Coerce(int),
        vol.Optional(CONF_FIRST_NEXT, default=CONF_FIRST): vol.In(
            {CONF_FIRST, CONF_NEXT}
        ),
    }
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_APIKEY): cv.string,
        vol.Required(CONF_STOPS): vol.All(
            cv.ensure_list,
            [vol.Any(vol.Coerce(int), _STOP_SCHEMA)],
        ),
        vol.Optional(CONF_FIRST_NEXT, default=CONF_FIRST): vol.In(
            {CONF_FIRST, CONF_NEXT}
        ),
    }
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up Wiener Linien departure sensors."""
    _LOGGER.warning(
        "WLOGD integration loaded (domain=wlogd, logger=custom_components.wlogd.sensor)"
    )
    global_firstnext = config[CONF_FIRST_NEXT]
    session = async_get_clientsession(hass)
    entities: list[WienerlinienSensor] = []
    seen: set[str] = set()
    integration_data = hass.data.setdefault(DOMAIN, {})
    apis: dict[int, WienerlinienAPI] = integration_data.setdefault("apis", {})

    for stop_entry in config[CONF_STOPS]:
        # Normalise both plain int and dict forms
        if isinstance(stop_entry, int):
            stopid = stop_entry
            lineid = None
            firstnext = global_firstnext
        else:
            stopid = stop_entry[CONF_STOP]
            lineid = stop_entry.get(CONF_LINEID)
            firstnext = stop_entry.get(CONF_FIRST_NEXT, global_firstnext)

        api = apis.get(stopid)
        if api is None or api.session is not session:
            api = WienerlinienAPI(session, stopid)
            apis[stopid] = api

        # Best effort bootstrap. Sensors are still created if startup fetch fails,
        # so they can recover automatically on later update cycles.
        data = await api.get_json()
        monitors = (data or {}).get("data", {}).get("monitors", [])

        monitor_idx = 0
        stopname = f"Stop {stopid}"
        linename = str(lineid) if lineid is not None else "?"
        destination = "unknown"
        vehicle_type = ""

        if monitors:
            if lineid is not None:
                for idx, monitor in enumerate(monitors):
                    if monitor.get("lines", [{}])[0].get("lineId") == lineid:
                        monitor_idx = idx
                        break
                else:
                    _LOGGER.warning(
                        "Line %s not found at stop %s, falling back to first monitor",
                        lineid,
                        stopid,
                    )

            try:
                monitor = monitors[monitor_idx]
                line = monitor["lines"][0]
                stopname = monitor["locationStop"]["properties"]["title"].strip()
                linename = line.get("name", linename).strip()
                destination = line.get("towards", destination).strip()
                vehicle_type = line.get("type", "")
            except (KeyError, IndexError, TypeError, AttributeError):
                _LOGGER.debug("Could not parse monitor bootstrap data for stop %s", stopid)
        else:
            _LOGGER.warning(
                "No monitors returned for stop %s during setup, creating sensor anyway",
                stopid,
            )

        sensor_key = f"{stopid}-{monitor_idx}-{firstnext}"
        if sensor_key in seen:
            _LOGGER.warning("Duplicate sensor skipped: %s", sensor_key)
            continue
        seen.add(sensor_key)

        entities.append(
            WienerlinienSensor(
                api=api,
                stopname=stopname,
                linename=linename,
                destination=destination,
                firstnext=firstnext,
                monitor_idx=monitor_idx,
                vehicle_type=vehicle_type,
                preferred_lineid=lineid,
            )
        )

    async_add_entities(entities, update_before_add=True)


class WienerlinienSensor(SensorEntity):
    """Sensor for a single Wiener Linien departure slot."""

    _attr_device_class = "timestamp"

    def __init__(
        self,
        api: "WienerlinienAPI",
        stopname: str,
        linename: str,
        destination: str,
        firstnext: str,
        monitor_idx: int,
        vehicle_type: str,
        preferred_lineid: int | None,
    ) -> None:
        self._api = api
        self._stopname = stopname
        self._linename = linename
        self._destination = destination
        self._firstnext = firstnext
        self._monitor_idx = monitor_idx
        self._vehicle_type = vehicle_type
        self._preferred_lineid = preferred_lineid

        base = f"{stopname} {linename} -> {destination}"
        self._attr_name = f"{base} {DEPARTURE_LABEL[firstnext]}"
        self._attr_unique_id = (
            f"wienerlinien-{api.stopid}-{monitor_idx}-{firstnext}"
        )
        self._attr_native_value: datetime | None = None
        self._attr_extra_state_attributes: dict = {}

    @property
    def icon(self) -> str:
        return VEHICLE_ICONS.get(self._vehicle_type, DEFAULT_ICON)

    async def async_update(self) -> None:
        """Fetch latest departure data from the API."""
        _LOGGER.debug("Updating sensor: %s", self._attr_name)
        try:
            data = await self._api.get_json()
        except Exception as err:
            _LOGGER.debug("Could not fetch data for %s: %s", self._attr_name, err)
            return

        if not data:
            _LOGGER.debug("No data returned for %s, skipping update", self._attr_name)
            return

        try:
            monitors = data["data"]["monitors"]

            if self._preferred_lineid is not None:
                for idx, monitor in enumerate(monitors):
                    if monitor.get("lines", [{}])[0].get("lineId") == self._preferred_lineid:
                        self._monitor_idx = idx
                        _LOGGER.debug(
                            "Matched line_id %s at monitor index %d for %s",
                            self._preferred_lineid, idx, self._attr_name,
                        )
                        break

            line = monitors[self._monitor_idx]["lines"][0]
            departures = line["departures"]["departure"]
            departure = departures[DEPARTURE_INDEX[self._firstnext]]
            dep_time = departure["departureTime"]

            raw = dep_time.get("timeReal") or dep_time.get("timePlanned")
            if raw:
                self._attr_native_value = parse_datetime(raw)
                _LOGGER.debug(
                    "%s -> departure time: %s (countdown: %s min)",
                    self._attr_name, raw, dep_time.get("countdown"),
                )

            self._attr_extra_state_attributes = {
                "destination": line.get("towards"),
                "platform": line.get("platform"),
                "direction": line.get("direction"),
                "line": line.get("name"),
                "stop_id": self._api.stopid,
                "line_id": line.get("lineId"),
                "barrier_free": line.get("barrierFree"),
                "traffic_jam": line.get("trafficjam"),
                "countdown_min": dep_time.get("countdown"),
            }
        except (KeyError, IndexError, TypeError) as err:
            _LOGGER.debug(
                "Unexpected API response structure for %s: %s", self._attr_name, err
            )


class WienerlinienAPI:
    """Thin async wrapper around the Wiener Linien OGD Realtime API."""

    _global_rate_lock = asyncio.Lock()
    _next_allowed_request_at: float = 0.0
    _min_request_interval_seconds: float = 0.8

    def __init__(self, session: aiohttp.ClientSession, stopid: int) -> None:
        self.session = session
        self.stopid = stopid
        self._lock = asyncio.Lock()
        self._cached_data: dict | None = None
        self._cached_at: float = 0.0
        self._cache_ttl_seconds = 5.0
        self._last_error_at: float = 0.0
        self._error_cooldown_seconds = 8.0

    async def _throttle_global(self) -> None:
        """Limit global request rate to reduce API blocking risk."""
        async with WienerlinienAPI._global_rate_lock:
            now = monotonic()
            wait_seconds = WienerlinienAPI._next_allowed_request_at - now
            if wait_seconds > 0:
                _LOGGER.debug(
                    "Global throttle wait %.2fs before stop %s request",
                    wait_seconds,
                    self.stopid,
                )
                await asyncio.sleep(wait_seconds)

            WienerlinienAPI._next_allowed_request_at = (
                monotonic() + WienerlinienAPI._min_request_interval_seconds
            )

    async def get_json(self) -> dict | None:
        """Return parsed JSON response or None on error."""
        now = monotonic()
        if self._cached_data is not None and (now - self._cached_at) < self._cache_ttl_seconds:
            _LOGGER.debug(
                "Using cached response for stop %s (age: %.2fs)",
                self.stopid,
                now - self._cached_at,
            )
            return self._cached_data

        async with self._lock:
            # Re-check cache inside lock so concurrent sensor updates share one fetch.
            now = monotonic()
            if self._cached_data is not None and (now - self._cached_at) < self._cache_ttl_seconds:
                _LOGGER.debug(
                    "Using cached response for stop %s after lock (age: %.2fs)",
                    self.stopid,
                    now - self._cached_at,
                )
                return self._cached_data

            # Avoid immediate repeat calls after a failed request burst.
            if (now - self._last_error_at) < self._error_cooldown_seconds:
                _LOGGER.debug(
                    "Skipping stop %s fetch due to cooldown (%.2fs remaining)",
                    self.stopid,
                    self._error_cooldown_seconds - (now - self._last_error_at),
                )
                if self._cached_data is not None:
                    return self._cached_data
                return None

            primary_url = BASE_URL.format(self.stopid)
            fallback_url = FALLBACK_URL.format(self.stopid)
            headers = {
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json",
            }
            _LOGGER.debug("Fetching stop %s from %s", self.stopid, primary_url)
            last_err: Exception | None = None
            for attempt in range(2):
                url = primary_url if attempt == 0 else fallback_url
                try:
                    await self._throttle_global()
                    async with asyncio.timeout(10):
                        response = await self.session.get(
                            url,
                            headers=headers,
                            raise_for_status=True,
                        )
                        _LOGGER.debug(
                            "Stop %s responded HTTP %s", self.stopid, response.status
                        )
                        data = await response.json()
                        monitors = (data or {}).get("data", {}).get("monitors", [])
                        _LOGGER.debug(
                            "Stop %s: received %d monitor(s)", self.stopid, len(monitors)
                        )
                        self._cached_data = data
                        self._cached_at = monotonic()
                        self._last_error_at = 0.0
                        return data
                except (aiohttp.ClientError, asyncio.TimeoutError) as err:
                    last_err = err
                    if (
                        isinstance(err, aiohttp.ClientResponseError)
                        and err.status == 403
                        and attempt == 0
                    ):
                        _LOGGER.debug(
                            "Stop %s got 403 on stopid URL, retrying with rbl URL",
                            self.stopid,
                        )
                        await asyncio.sleep(1.0)
                        continue
                    break

            self._last_error_at = monotonic()
            if last_err is not None:
                _LOGGER.warning(
                    "API request failed for stop %s: %s", self.stopid, last_err
                )
            if self._cached_data is not None:
                _LOGGER.debug(
                    "Returning stale cached data for stop %s after request failure",
                    self.stopid,
                )
                return self._cached_data
            return None
