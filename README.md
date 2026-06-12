# Wiener Linien OGD for Home Assistant

Custom Home Assistant sensor platform for Wiener Linien realtime departures.

Version: 4.0.0

## Features

- Reads realtime departure data from Wiener Linien OGD monitor endpoint.
- Supports multiple stops in one platform configuration.
- Optional line filter per stop.
- Supports `first` and `next` departure selection globally and per stop.
- Uses suitable icons for metro, tram, bus, and S-Bahn lines.
- Exposes useful attributes like destination, platform, direction, countdown, and line id.

## Installation

1. Copy the folder `custom_components/wlogd` into your Home Assistant config directory:

```text
<config>/custom_components/wlogd
```

2. Restart Home Assistant.

## Configuration

Add to your `configuration.yaml`:

```yaml
sensor:
	- platform: wlogd
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

## Migration from old domain

- Remove old folder `<config>/custom_components/wienerlinien` if present.
- Install this integration under `<config>/custom_components/wlogd`.
- Update YAML from `platform: wienerlinien` to `platform: wlogd`.
- Restart Home Assistant.

After migration, logs must come from `custom_components.wlogd.sensor`. If you still see `custom_components.wienerlinien.sensor`, Home Assistant is still loading an old integration copy.

## 4.0.0 release notes

- Renamed integration domain/platform to `wlogd` to avoid collisions with older copies.
- Added explicit startup warning identifying the active integration namespace.
- Keeps request de-duplication/caching logic to reduce burst traffic and temporary 403 responses.

## Acknowledgements

- Original project reference: https://github.com/tofuSCHNITZEL/home-assistant-wienerlinien
- This custom component builds on and adapts ideas from the upstream implementation.

## AI assistance

- Parts of the code and documentation updates were prepared with AI assistance.
- All changes were reviewed and validated by the maintainer before release.

## Source

- Documentation: https://github.com/wolfgangbures/HA_WLOGD
- Issues: https://github.com/wolfgangbures/HA_WLOGD/issues
