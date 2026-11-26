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

"""A Tweak 2 press closes an open plugin window and returns to the pedalboard overview."""

from __future__ import annotations

import time

from pistomp.controller import ControlType
from pistomp.input.event import SwitchEvent, SwitchEventKind
from tests.types import SystemFixture
from tests.v3.test_caps_noisegate_menu import open_menu


def _tweak(v3_system: SystemFixture, tweak_id: int):
    for enc in v3_system.handler.hardware.encoders:
        if enc.type == ControlType.KNOB and enc.id == tweak_id:
            return enc
    raise AssertionError(f"no tweak {tweak_id} encoder")


def _press(v3_system: SystemFixture, tweak_id: int) -> None:
    event = SwitchEvent(controller=_tweak(v3_system, tweak_id), kind=SwitchEventKind.PRESS, timestamp=time.monotonic())
    v3_system.handler.handle(event)
    v3_system.handler.poll_lcd_updates()


def test_tweak2_press_closes_parameter_window(v3_system: SystemFixture):
    open_menu(v3_system)
    pstack = v3_system.handler.lcd.pstack
    opened = pstack.current

    _press(v3_system, 2)

    assert pstack.current is not opened

