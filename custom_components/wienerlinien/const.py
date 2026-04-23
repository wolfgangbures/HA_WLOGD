"""Constants for the Wiener Linien integration."""

DOMAIN = "wienerlinien"

BASE_URL = "https://www.wienerlinien.at/ogd_realtime/monitor?stopid={}"

CONF_STOPS = "stops"
CONF_STOP = "stop"
CONF_APIKEY = "apikey"
CONF_FIRST_NEXT = "firstnext"
CONF_LINEID = "line"
CONF_FIRST = "first"
CONF_NEXT = "next"

DEPARTURE_INDEX = {
    CONF_FIRST: 0,
    CONF_NEXT: 1,
}

DEPARTURE_LABEL = {
    CONF_FIRST: "first departure",
    CONF_NEXT: "next departure",
}

VEHICLE_ICONS = {
    "ptMetro": "mdi:subway",
    "ptTram": "mdi:tram",
    "ptTramWLB": "mdi:train-variant",
    "ptBusCity": "mdi:bus",
    "ptBusNight": "mdi:bus-clock",
    "ptTrainS": "mdi:train",
}
DEFAULT_ICON = "mdi:bus"
