# Assist Satellite Study

Last reviewed: 2026-04-30.

## Goal

Turn Pynab into a Home Assistant Assist Satellite while preserving the existing
Nabaztag hardware features: button, microphone, speaker, LEDs, ears, RFID and
the existing `nabd` TCP protocol.

## Current Pynab Voice Path

The current implementation is centered in `nabd`:

1. A head-button hold starts local ASR if sound input and legacy ASR/NLU are
   available.
2. `NabIO.start_acquisition()` plays the listen sound and records 16 kHz mono
   PCM through `Sound.start_recording()`.
3. `SoundAlsa` captures 100 ms chunks and sends them to Kaldi.
4. Releasing the button finalizes ASR, sends the decoded text to Snips NLU, and
   broadcasts an internal `asr_event`.
5. Existing services subscribe to `asr/<service>` events and answer with local
   Pynab messages.

This path is useful as a hardware and interaction model, but it should not be
kept as the main Assist architecture. Snips/Kaldi is the legacy component we
already split out of the modern runtime.

## Home Assistant Direction

Home Assistant exposes Assist voice services and satellites through Wyoming.
The Wyoming integration connects external voice services and remote voice
satellites to Home Assistant, supports local Whisper/Piper/openWakeWord style
pipelines, and can discover satellites through Zeroconf.

Home Assistant also introduced `AssistSatelliteEntity` to represent satellites
in the entity model. ESPHome and VoIP moved to it first, and Wyoming was called
out as a next target by the HA developer docs.

Important caveat: the historical `wyoming-satellite` project is archived and
its README says it was replaced by Linux Voice Assistant using ESPHome protocol.
That does not make the Wyoming protocol obsolete in HA, but it means copying
the old satellite project wholesale is not a good long-term plan.

Sources:

- https://www.home-assistant.io/integrations/wyoming/
- https://developers.home-assistant.io/blog/2024/10/01/assist-satellite-entity/
- https://github.com/rhasspy/wyoming
- https://github.com/rhasspy/wyoming-satellite

## Implementation Choices

### Option A: Keep Pynab ASR/NLU and bridge intents to Home Assistant

Pynab keeps recording, STT and intent parsing locally, then calls Home
Assistant services or conversation APIs from parsed intents.

Pros:

- Minimal change to the existing Pynab voice flow.
- Existing `asr_event` subscriptions keep working.
- Works without adopting Wyoming immediately.

Cons:

- Keeps the obsolete Snips/Kaldi path as the critical path.
- Does not make Pynab a real Assist Satellite.
- Harder to support HA pipeline selection, wake words, TTS responses, timers
  and future Assist features.
- Duplicates the intent layer instead of using HA's Assist pipeline.

Verdict: not recommended except as a temporary compatibility shim.

### Option B: Add a Pynab Wyoming satellite service beside `nabd`

Add a new daemon, for example `nabassistd`, that speaks Wyoming to Home
Assistant and uses local Pynab hardware APIs for audio, button and feedback.
`nabd` remains responsible for low-level hardware state and existing services.

Proposed shape:

- `nabassistd` connects to/serves Wyoming on a configurable URI.
- It uses existing 16 kHz mono PCM capture from `SoundAlsa`.
- It plays HA TTS audio through existing `Sound`/`NabIO` playback.
- Button hold starts/stops a push-to-talk Assist run for the MVP.
- LEDs/ears expose satellite states: idle, listening, thinking, speaking,
  error.
- Existing Pynab services continue to run; Assist commands can later call into
  Pynab through `nabd` or a web API.

Pros:

- Aligns with Home Assistant's current voice ecosystem.
- Removes Snips/Kaldi from the Assist critical path.
- Keeps hardware code and daemon protocol reuse high.
- Good incremental path: push-to-talk first, wake word later.
- Allows local HA pipeline: Whisper/STT, Piper/TTS, openWakeWord.

Cons:

- Requires implementing enough Wyoming satellite behavior.
- Need careful audio playback format handling for HA TTS streams.
- Need service coordination so local Pynab messages and Assist TTS do not fight
  over the speaker.

Verdict: recommended path.

### Option C: Replace Pynab voice with an external satellite process

Run a generic Linux voice satellite process on the Raspberry Pi and only use
Pynab for LEDs/ears via event hooks or shell commands.

Pros:

- Fastest proof of concept if the generic satellite works on the hardware.
- Less protocol code to write initially.

Cons:

- `wyoming-satellite` is archived.
- Hardware integration becomes a collection of side effects rather than a clean
  Pynab feature.
- Harder to test and package in this repo.
- Risks bypassing `nabd` state management.

Verdict: useful as a lab experiment, not as the repo architecture.

### Option D: Write a Home Assistant custom integration first

Expose Pynab as a custom HA integration with an `AssistSatelliteEntity`, then
have HA call back into Pynab for audio and state.

Pros:

- Best eventual HA UI/entity integration.
- Enables native HA state and automations.

Cons:

- Higher upfront complexity.
- Still needs a transport for audio between Pynab and HA.
- Solves HA representation before the satellite runtime exists.

Verdict: do later, after the Pynab-side satellite is working.

## Recommended Architecture

Implement Option B first:

```text
Nabaztag hardware
  -> NabIO / SoundAlsa / LEDs / ears / button
  -> nabd keeps current local protocol and services
  -> nabassistd handles Assist Satellite behavior
  -> Wyoming protocol
  -> Home Assistant Assist pipeline
```

The first version should be wake-word based, because the target rabbit may be
installed somewhere where the head button is inconvenient to reach. Push-to-talk
can remain a fallback/debug mode, but it should not be the main user workflow.

## MVP Scope

1. Add `nabassistd` as a new service daemon.
2. Add config fields for:
   - enabled/disabled
   - satellite name
   - Wyoming URI or host/port
   - wake-word engine
   - wake-word model
   - optional push-to-talk fallback
   - optional feedback animations
3. Reuse `SoundAlsa` recording at 16 kHz mono S16LE.
4. Run local wake-word detection on the rabbit when hardware allows it.
5. After wake-word detection, stream the command audio to Home Assistant Assist.
6. Reuse existing playback for HA TTS output.
7. Bind the head button only as fallback:
   - hold/release: manual Assist recording for diagnostics
   - click during playback: cancel playback
8. Add visible feedback:
   - listening: nose/bottom LED active
   - processing: short pulse
   - speaking: speaker playback plus optional ears/LED state
   - error: existing ASR failed sound or a new Assist-specific sound
9. Add unit tests with fake wake-word engine, fake Wyoming peer and fake
   `NabIO`.

## Wake-Word Recommendation

Recommended default: local `pymicro-wakeword` first, with optional local
`openWakeWord` for more capable Raspberry Pi hardware.

Why `pymicro-wakeword` first:

- It has Python 3.13 wheels for aarch64 and x86_64.
- It expects exactly the format Pynab already captures: 16-bit mono at 16 kHz.
- It is designed for lightweight on-device wake-word detection.
- Built-in models include common Home Assistant wake words such as `okay_nabu`.
- It keeps always-on raw audio inside the rabbit until the wake word is
  detected.

Why not `openWakeWord` as the first embedded default:

- Home Assistant uses openWakeWord heavily, and it is a strong option on
  commodity hardware.
- The upstream project says a Raspberry Pi 3 core can run many models in real
  time, so it should work well on Pi 3/4/5-class hardware.
- It is larger and heavier than microWakeWord, and is a worse first bet if the
  rabbit is running on a Pi Zero-class board or has limited RAM.
- It is still useful as an optional engine, especially for custom wake words.

Why not HA-side wake word as the primary path:

- Home Assistant's documented approach is often to stream satellite audio to HA
  and run wake-word detection there, which helps weak devices.
- For this project, the priority is embedded wake word because the device is
  always present in a room and privacy/network usage matter.
- HA-side wake word should remain a fallback if the installed Raspberry Pi is
  too small for stable local inference.

Recommended engine order:

1. `pymicro-wakeword` with `okay_nabu` for the first hands-free MVP.
2. `openWakeWord` optional for Pi 3/4/5 and custom models.
3. HA-side Wyoming/openWakeWord fallback only for hardware that cannot run local
   wake word reliably.

Initial code structure:

```text
nabassistd/
  audio.py                  ring buffer and fixed-size PCM chunking
  capture.py                async wrapper around `Sound.start_recording()`
  client.py                 Assist client protocol and Wyoming placeholder
  config.py                 environment-driven Assist configuration
  nabassistd.py             daemon skeleton and audio processor
  pipeline.py               wake-word detection to Assist audio streaming
  processor.py              pre-roll aware wake-word processor
  wakeword/base.py          common wake-word interface
  wakeword/micro.py         lazy pymicro-wakeword backend
  wakeword/openwakeword.py  lazy openWakeWord backend
  wakeword/remote.py        placeholder for HA-side wake-word fallback
```

The optional Assist dependencies are kept in `requirements-assist.txt` so the
modern core runtime and CI do not require wake-word inference libraries.

Hardware decision:

- Raspberry Pi 4/5: support `pymicro-wakeword` and `openWakeWord`.
- Raspberry Pi 3 or Zero 2 W: start with `pymicro-wakeword`; benchmark
  `openWakeWord` only after the MVP.
- Raspberry Pi Zero W / ARMv6: do not promise local wake word until tested;
  likely fallback to HA-side detection or hardware upgrade.

Implementation sketch:

```text
SoundAlsa continuous capture, 16 kHz mono S16LE
  -> wake-word ring buffer
  -> pymicro-wakeword 10 ms frames
  -> detected
  -> play local/listening feedback
  -> stream buffered wake audio + following speech to HA Assist
  -> play HA TTS response through Pynab speaker
```

The ring buffer is important: after the wake word fires, we should include a
small amount of pre-roll audio so Home Assistant does not miss the beginning of
the command.

## Compatibility With Existing Services

Existing `asr_event`-based services should not be the main Assist path. They can
be preserved by adding an optional compatibility bridge:

- HA Assist response controls Home Assistant and speaks back through TTS.
- Existing Pynab voice intents can remain local if legacy ASR is installed.
- Later, HA intents can call Pynab services through a local API instead of using
  Snips NLU.

This avoids blocking Assist on legacy Snips/Kaldi while keeping existing rabbit
features available.

## Open Technical Questions

- Whether the Nabaztag microphone quality is sufficient for remote Whisper or
  requires WebRTC noise suppression/AGC before streaming.
- Whether we implement Wyoming directly with the `wyoming` Python package or
  vendor a small focused subset of the protocol.
- Whether HA TTS audio arrives in a format `SoundAlsa` can play directly, or
  whether we need a small PCM/WAV conversion layer.
- Whether push-to-talk should live in `nabd` and call `nabassistd`, or whether
  `nabassistd` should subscribe to button events from `nabd`.

## Next Step

Build a proof of concept `nabassistd` with local wake-word detection first:

1. Add the daemon skeleton and tests.
2. Add a `WakeWordEngine` interface and a fake engine for tests.
3. Add a `pymicro-wakeword` implementation behind an optional dependency.
4. Feed it canned 16 kHz PCM fixtures in tests.
5. Wire the generic continuous capture wrapper around `Sound.start_recording()`.
6. Add the pipeline that starts an Assist session with pre-roll audio after a
   wake-word detection.
7. Implement Wyoming connect/discovery enough for HA to see the satellite.
8. Stream post-detection audio to Assist and play the TTS response.

This keeps the risk contained: protocol first, hardware second.

Current Wyoming client behavior:

```text
run-pipeline start_stage=asr end_stage=tts wake_word_name=<detected model>
audio-start rate=16000 width=2 channels=1
audio-chunk payload=<pre-roll and speech PCM>
audio-stop
```

The client builds Wyoming-compatible event objects without importing the
`wyoming` package in tests. At runtime, it imports `wyoming.client.AsyncTcpClient`
only when it needs to open a real TCP connection.

Current playback behavior:

```text
Home Assistant returns audio-start/audio-chunk/audio-stop
  -> WyomingAssistClient collects response PCM chunks
  -> AssistPipeline receives response audio after audio-stop
  -> WavAssistAudioPlayer writes a temporary WAV
  -> existing `Sound` playback plays the WAV through the rabbit speaker
```

`NabAssistd` now assembles the continuous capture, Assist pipeline and WAV
player when Assist is enabled and a `Sound` implementation is available.

Current feedback behavior:

- `nabassistd` sends a persistent `info` animation with `info_id=nabassistd`
  to `nabd` for the Assist states.
- listening uses a blue pulse, thinking uses an amber scan, speaking uses a
  green pulse, and error uses a red pulse.
- idle clears the `info` animation.
- error also reuses the existing `asr/failed/*.mp3` sound when a `Sound`
  implementation is available.

Current runtime error behavior:

- If a Wyoming session fails, `AssistPipeline` resets its wake-word processor,
  disconnects the Wyoming client, emits the error feedback state, and re-raises
  the error.
- `NabAssistd.assist_loop()` catches Assist pipeline errors, logs them, waits
  with bounded exponential backoff, and resumes processing microphone chunks.
- The daemon therefore survives temporary Home Assistant, Wyoming or network
  failures without relying on systemd restart for ordinary outages.

Runtime activation:

- Systemd service: `nabassistd/nabassistd.service`.
- Environment file: `nabassistd/nabassistd.conf`.
- Optional dependencies and service activation:
  `PYNAB_INSTALL_ASSIST=1 ./install.sh`.
- Without `PYNAB_INSTALL_ASSIST=1`, `install.sh` skips `nabassistd.service` so
  the core Pynab runtime does not depend on wake-word packages.
- After installation, configure Assist from the web interface and run:
  `venv/bin/python manage.py assist_diagnostics`.
- Docker development:
  `PYNAB_DOCKER_INSTALL_ASSIST=1 PYNAB_DOCKER_DAEMONS="nab8balld nabairqualityd nabbookd nabclockd nabmastodond nabsurprised nabtaichid nabweatherd nabassistd" docker compose -f Docker/docker-compose.yml up --build`.
