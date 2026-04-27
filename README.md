# Wiener Linien OGD for Home Assistant

Custom Home Assistant sensor platform for Wiener Linien realtime departures.

Version: 3.0.0 (final release)

## Features

- Reads realtime departure data from Wiener Linien OGD monitor endpoint.
- Supports multiple stops in one platform configuration.
- Optional line filter per stop.
- Supports `first` and `next` departure selection globally and per stop.
- Uses suitable icons for metro, tram, bus, and S-Bahn lines.
- Exposes useful attributes like destination, platform, direction, countdown, and line id.

## Installation

1. Copy the folder `custom_components/wienerlinien` into your Home Assistant config directory:

```text
<config>/custom_components/wienerlinien
```

2. Restart Home Assistant.

## Configuration

Add to your `configuration.yaml`:

```yaml
sensor:
	- platform: wienerlinien
		firstnext: first
		stops:
			- 141
			- 160
			- stop: 143
				line: 4
				firstnext: next
```

### Options

- `stops` (required): list of stop entries.
- `firstnext` (optional): `first` or `next` (default: `first`).
- `line` (optional per stop): filter by Wiener Linien `lineId`.

### Stop entry formats

Simple stop id:

```yaml
stops:
	- 141
```

Extended stop object:

```yaml
stops:
	- stop: 143
		line: 4
		firstnext: next
```

## Entity behavior

- Sensor state is the departure timestamp.
- Polling interval is 30 seconds.
- If startup fetch fails, entities are still created and recover on later updates.

## 3.0.0 release notes

- Finalized stable sensor behavior for startup and update cycles.
- Improved parser robustness and fallback handling for API response changes.
- Added per-stop departure mode override (`firstnext`) support.
- Expanded README with complete setup and configuration examples.

## Source

- Documentation: https://github.com/wolfgangbures/HA_WLOGD
- Issues: https://github.com/wolfgangbures/HA_WLOGD/issues
