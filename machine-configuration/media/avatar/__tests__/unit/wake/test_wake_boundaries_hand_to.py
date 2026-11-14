from unittest.mock import Mock

import conversation_addressee
import listener_runtime
import room_holder
import wake_boundaries
from conversation_addressee import Addressee


def test_a_wake_on_the_avatar_host_gives_the_room_through_the_room_holder(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(listener_runtime, "runtime_directory", lambda: tmp_path)
    shown = Mock()
    monkeypatch.setattr(room_holder.servant_character, "show_for", shown)
    boundaries = wake_boundaries.Boundaries()

    boundaries.hand_to(Addressee("w:p1", "Circe", 0))
    boundaries.hand_to(Addressee("w:p1", "Circe", 5))
    boundaries.hand_to(Addressee("w:p2", "Medea", 5))

    assert [call.args[0] for call in shown.call_args_list] == ["Circe", "Medea"]
    assert conversation_addressee.current(tmp_path) == Addressee("w:p2", "Medea", 5)
