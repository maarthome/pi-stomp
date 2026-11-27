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

"""Shortcircuit XT (maarthome/shortcircuit-xt LV2): the macro ports p0..p15 show the
macro names set in Shortcircuit, which the plugin reports as a patch property."""

from __future__ import annotations

from dataclasses import dataclass

from common.parameter import Parameter
from modalapi.plugin import Plugin
from modalapi.plugin_customization import PluginExtraData, extra_data_as
from plugins.customization import PluginCustomization, register

SCXT_URI = "https://github.com/maarthome/shortcircuit-xt#lv2"
_MACRO_NAMES_URI = SCXT_URI + "-macro_names"
_MACRO_COUNT = 16


@dataclass(frozen=True)
class ScxtMacroNames(PluginExtraData):
    names: tuple[str, ...]


def _patch_scxt(param_uri: str, value: str) -> ScxtMacroNames | None:
    if param_uri != _MACRO_NAMES_URI:
        return None
    # mod-ui passes strings through quoted
    text = value.strip()
    if len(text) >= 2 and text[0] == text[-1] == '"':
        text = text[1:-1]
    return ScxtMacroNames(names=tuple(n.strip() for n in text.split("~")))


def _macro_index(param: Parameter) -> int | None:
    sym = str(param.symbol)
    if len(sym) < 2 or sym[0] != "p" or not sym[1:].isdigit():
        return None
    i = int(sym[1:])
    return i if i < _MACRO_COUNT else None


def _scxt_param_label(plugin: Plugin, param: Parameter) -> str | None:
    data = extra_data_as(plugin, ScxtMacroNames)
    i = _macro_index(param)
    if data is None or i is None or i >= len(data.names):
        return None
    return data.names[i] or None


register(
    SCXT_URI,
    customization=PluginCustomization(param_label_fn=_scxt_param_label),
    patch_data_fn=_patch_scxt,
)
