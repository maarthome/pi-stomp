#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of pi-stomp.
#
# pi-stomp is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pi-stomp is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with pi-stomp.  If not, see <https://www.gnu.org/licenses/>.

"""Choose how a plugin's parameter window shows its parameters.

    tools/plugin_rings.py "Surge XT.lv2" off     all parameters as horizontal sliders (the default)
    tools/plugin_rings.py "Surge XT.lv2" first4  first 4 parameters as arc rings, the rest sliders
    tools/plugin_rings.py "Surge XT.lv2" all     every parameter as an arc ring (scrolls)
    tools/plugin_rings.py "Surge XT.lv2" on      remove the override, back to the default
    tools/plugin_rings.py "Surge XT.lv2" status

The bundle is a folder name searched in ~/.lv2 and the system LV2 folders, or a
path. Its plugin URIs come from manifest.ttl. The choice is written to
plugins/pinned_params.py in this checkout as a marked block; commit it and run
./deploy.sh to put it on the device.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "plugins" / "pinned_params.py"
LV2_DIRS = [
    Path.home() / ".lv2",
    Path("/usr/local/lib/lv2"),
    Path("/usr/lib/lv2"),
    Path("/usr/lib/aarch64-linux-gnu/lv2"),
]
BEGIN = "# >>> plugin-rings:{uri}\n"
END = "# <<< plugin-rings:{uri}\n"
BLOCK = """{begin}register(
    "{uri}",
    customization=PluginCustomization(pinned_params={pins}),
)
{end}"""
SKIPPED_TTL = {"manifest.ttl", "modgui.ttl", "ui.ttl"}


def find_bundle(arg: str) -> Path:
    path = Path(arg).expanduser()
    if path.is_dir():
        return path
    for d in LV2_DIRS:
        if (d / arg).is_dir():
            return d / arg
    sys.exit(f"bundle '{arg}' not found in: " + ", ".join(map(str, LV2_DIRS)))


def plugin_uris(bundle: Path) -> list[str]:
    text = (bundle / "manifest.ttl").read_text(errors="replace")
    uris = re.findall(r"<([^>]+)>\s+(?:a|rdf:type)\s+lv2:[A-Za-z]*Plugin\b", text)
    if not uris:
        sys.exit(f"no lv2:Plugin in {bundle}/manifest.ttl")
    return list(dict.fromkeys(uris))


def control_ports(bundle: Path) -> list[tuple[str, str]]:
    """(symbol, name) of the visible control input ports, in port order."""
    ports: list[tuple[str, str]] = []
    for ttl in sorted(bundle.glob("*.ttl")):
        if ttl.name in SKIPPED_TTL:
            continue
        chunks = re.split(r"lv2:index\s+\d+", ttl.read_text(errors="replace"))
        for before, after in zip(chunks, chunks[1:]):
            head, body = before[-250:], after[:600]
            if "lv2:InputPort" not in head or "lv2:ControlPort" not in head:
                continue
            if "notOnGUI" in body or "lv2:designation" in body:
                continue
            symbol = re.search(r'lv2:symbol\s+"([^"]+)"', body)
            name = re.search(r'lv2:name\s+"([^"]+)"', body)
            if symbol:
                ports.append((symbol.group(1), (name.group(1) if name else symbol.group(1))[:10]))
    return ports


def remove_block(text: str, uri: str) -> str:
    b, e = BEGIN.format(uri=uri), END.format(uri=uri)
    return re.sub(r"\n*" + re.escape(b) + r".*?" + re.escape(e), "\n", text, flags=re.S)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bundle")
    ap.add_argument("mode", choices=["on", "off", "first4", "all", "status"])
    args = ap.parse_args()

    bundle = find_bundle(args.bundle)
    text = TARGET.read_text()
    original = text

    for uri in plugin_uris(bundle):
        b, e = BEGIN.format(uri=uri), END.format(uri=uri)
        has = b in text
        if args.mode == "status":
            if not has:
                state = "default (all horizontal sliders)"
            elif "pinned_params=()" in text.split(b)[1].split(e)[0]:
                state = "off (all horizontal sliders)"
            elif text.split(b)[1].split(e)[0].count("PinnedParam(") <= 4:
                state = "first4 (first 4 as rings)"
            else:
                state = "all (every parameter a ring)"
            print(f"{uri}: {state}")
        elif args.mode == "on":
            text = remove_block(text, uri)
            print(f"{uri}: default")
        else:
            if args.mode == "off":
                pins = "()"
            else:
                ports = control_ports(bundle)
                if not ports:
                    sys.exit("no control ports found in the bundle's TTL files")
                if args.mode == "first4":
                    ports = ports[:4]
                rows = "".join(f'        PinnedParam(Symbol("{s}"), "{n}"),\n' for s, n in ports)
                pins = f"(\n{rows}    )"
            text = remove_block(text, uri).rstrip("\n") + "\n\n\n" + BLOCK.format(begin=b, end=e, uri=uri, pins=pins)
            print(f"{uri}: {args.mode}")

    if text != original:
        TARGET.write_text(text)
        print("written to plugins/pinned_params.py; commit it and run ./deploy.sh")


main()
