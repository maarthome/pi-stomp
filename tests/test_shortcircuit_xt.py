"""Shortcircuit XT's macro ports take the macro names it reports as a patch property."""

from dataclasses import replace

from common.parameter import Parameter
from modalapi.plugin import Plugin
from plugins.customization import lookup, patch_extra_data
from plugins.shortcircuit_xt import SCXT_URI

_NAMES_URI = SCXT_URI + "-macro_names"


def _plugin() -> tuple[Plugin, Parameter, Parameter, Parameter]:
    p0 = Parameter({"symbol": "p0", "name": "Macro 1"}, 0.0, None, "scxt")
    p3 = Parameter({"symbol": "p3", "name": "Macro 4"}, 0.0, None, "scxt")
    other = Parameter({"symbol": "gain", "name": "Gain"}, 0.0, None, "scxt")
    plugin = Plugin("scxt", {p0.symbol: p0, p3.symbol: p3, other.symbol: other}, {}, uri=SCXT_URI, customization=lookup(SCXT_URI))
    return plugin, p0, p3, other


def test_port_names_until_names_arrive():
    plugin, p0, _, _ = _plugin()
    assert plugin.param_label(p0) == "Macro 1"


def test_macro_names_from_patch_set():
    plugin, p0, p3, other = _plugin()
    extra = patch_extra_data(SCXT_URI, _NAMES_URI, '"Cutoff~Macro 2~Drive~"')
    assert extra is not None
    plugin.customization = replace(plugin.customization, extra_data=extra)
    assert plugin.param_label(p0) == "Cutoff"
    assert plugin.param_label(p3) == "Macro 4"  # empty name keeps the port name
    assert plugin.param_label(other) == "Gain"


def test_other_properties_ignored():
    assert patch_extra_data(SCXT_URI, SCXT_URI + "-names", "x") is None
