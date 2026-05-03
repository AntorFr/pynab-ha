# Home Assistant Control

Pynab exposes basic Home Assistant controls through MQTT discovery with the
`nabhomeassistantd` daemon.

This path is intentionally separate from `nabassistd`:

- `nabassistd` handles Assist Satellite voice audio, wake words and Wyoming.
- `nabhomeassistantd` exposes regular Home Assistant entities and translates
  their commands to the existing `nabd` protocol.

## First Scope

The first implementation exposes:

- `sensor.<device>_state`: current `nabd` state such as `idle`, `asleep`,
  `playing` or `recording`.
- `button.<device>_sleep`: sends a `{"type": "sleep"}` packet to `nabd`.
- `button.<device>_wake_up`: sends a `{"type": "wakeup"}` packet to `nabd`.
- `number.<device>_volume`: sends `{"type": "volume", "level": N}` to `nabd`.
- `switch.<device>_mute`: sends `{"type": "mute", "muted": true/false}` to
  `nabd`.

## MQTT Topics

Default topics:

```text
pynab/availability
pynab/state
pynab/volume
pynab/mute
pynab/command/sleep
pynab/command/wakeup
pynab/command/volume
pynab/command/mute
```

Default Home Assistant discovery topics:

```text
homeassistant/sensor/pynab/state/config
homeassistant/button/pynab/sleep/config
homeassistant/button/pynab/wakeup/config
homeassistant/number/pynab/volume/config
homeassistant/switch/pynab/mute/config
```

The web configuration allows changing the MQTT host, port, credentials,
discovery prefix, topic prefix and displayed device name.

## Runtime Flow

```text
Home Assistant
  -> MQTT button command
  -> nabhomeassistantd
  -> nabd TCP packet
  -> Nabaztag state change
  -> nabhomeassistantd publishes updated state to MQTT
```

`nabhomeassistantd` does not talk to the sound card, ears or LEDs directly. It
uses `nabd` as the single hardware coordination point.
