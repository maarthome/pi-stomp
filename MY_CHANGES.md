# My changes to pi-Stomp (branch `My_Changes`)

Fork: `maarthome/pi-stomp` of `TreeFallSound/pi-stomp`. The pi-Stomp itself has no git checkout; the source is
copied from the dev Pi with `./deploy.sh`. Companion repo: `maarthome/surge` (see its `MY_ADAPTIONS.md`), which
adds 48 real LV2 control ports to Surge XT for this display.

## 1. What is changed

| Change | File | Effect |
|---|---|---|
| Tweak 2 press = back | `plugins/base.py` (`PluginPanel.on_event`, `_BACK_TWEAK_ID`) | In any plugin screen (parameter window and the bespoke panels), pressing the Tweak 2 encoder closes it and returns to the pedal block overview. Not active outside plugin screens. NAM capture handles its own events and is not covered. |
| Horizontal sliders by default | `plugins/parameter_window.py` (`ParameterWindow.build_slots`) | A plugin without its own panel and without a hand-set `pinned_params` shows every parameter as a horizontal slider (upstream pinned the first 4 continuous parameters as arc rings). Plugins with a `panel_cls` or a `pinned_params` registration (see the list in section 3) keep their own screens. |
| Full-width parameter window | `plugins/parameter_window.py` (`_window_size`) | A window without rings uses the full display width. |
| Ring/slider choice per plugin | `tools/plugin_rings.py` | Writes a marked block in `plugins/pinned_params.py`: `off` = every parameter a horizontal slider (the default), `first4` = first 4 as rings, `all` = every parameter an arc ring (scrolls), `on` = remove the override. |
| Test | `tests/v3/test_tweak2_back.py` | Tweak 2 press closes the open parameter window. |

Background: a plugin's parameter list is built only from its LV2 control input ports that are also stored in the
saved pedalboard. Pinned parameters (`pinned_params`) are drawn as arc rings, the rest as a scrolling list of
horizontal sliders; an empty `pinned_params=()` means no rings at all.

## 2. Procedures

### Get and deploy

```
cd ~/git
git clone https://github.com/maarthome/pi-stomp.git
cd pi-stomp
git checkout My_Changes
git remote add upstream https://github.com/TreeFallSound/pi-stomp.git
./deploy.sh            # rsync to /home/pistomp/pi-stomp on the pi-Stomp, restarts mod-ala-pi-stomp
```

`deploy.sh` overwrites the source on the device (`--delete`); do not edit files there. Logs:

```
ssh pistomp@pistomp.local "journalctl -u mod-ala-pi-stomp -f"
```

### Choose rings or sliders for a plugin

```
python3 tools/plugin_rings.py "Surge XT.lv2" all      # all rings
python3 tools/plugin_rings.py "Surge XT.lv2" first4   # first 4 rings, rest sliders
python3 tools/plugin_rings.py "Surge XT.lv2" off      # all horizontal sliders (default)
python3 tools/plugin_rings.py "Surge XT.lv2" on       # remove the override
python3 tools/plugin_rings.py "Surge XT.lv2" status
git commit -am "Surge XT: <layout>" && git push
./deploy.sh
```

The bundle name is looked up in `~/.lv2` and the system LV2 folders on the dev Pi (or give a path); the plugin URI is
read from its `manifest.ttl`. For `all`, symbols and names come from the installed bundle's TTL.

### Change which encoder goes back

Edit `_BACK_TWEAK_ID` in `plugins/base.py` (1-3), commit, `./deploy.sh`. To disable the feature, remove the
`isinstance(event, SwitchEvent) ... _BACK_TWEAK_ID` branch in `PluginPanel.on_event`.

### Change when the window goes full width

The condition in `_window_size()` in `plugins/parameter_window.py` (full width for no rings or 4+ rings).

### Which plugins keep their own edit screens

22 plugins register their own panel class (`panel_cls`): the compressors, EQs, GxCabinet, TAP Reverberator, Mixer, Notes. 22 registrations pick their rings by hand (`pinned_params`): System Compressor, Collision Drive, C* AmpVTS, BollieDelay (+XT), TAP Dynamics, TAP Chorus/Flanger, Gx Amp, Valve, Kuiza, Musical Delay, String Machine, ePiano, Degrade, CAPS Noisegate, 3 Band EQ, 3 Band Splitter, MDA MultiBand, MDA Bandisto, NAM. All other plugins use the slider default. To list them from the code:

```
grep -rn "panel_cls=\|pinned_params=" plugins | grep -v "^plugins/.*def "
```

To give another plugin rings, add a `register(URI, customization=PluginCustomization(pinned_params=(PinnedParam(Symbol("..."), "Label"), ...)))` in `plugins/pinned_params.py`, or use `tools/plugin_rings.py`.

### Take over upstream updates

```
git fetch upstream
git merge upstream/main
```

Conflicts can only occur in `plugins/base.py`, `plugins/parameter_window.py` and `plugins/pinned_params.py`
(my changes are small, in `PluginPanel.on_event`, `_window_size()` and the `plugin-rings` blocks). Then:

```
uv sync && uv run pytest && uv run pyright
./deploy.sh
```

Project rules (see `CLAUDE.md`): pyright zero errors, no `getattr`/`hasattr`, AGPL header on production python files, rare short comments.

### Not yet verified

The tests and pyright were not run when these changes were written (no dependencies available there). Run these once on the dev Pi.
Existing LCD snapshots of plugins that used the old ring heuristic will differ; check them and accept with `--snapshot-update`.

```
uv run pytest
uv run pyright
```
