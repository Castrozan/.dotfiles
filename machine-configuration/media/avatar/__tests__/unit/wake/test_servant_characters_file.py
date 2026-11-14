import collections
import pathlib
import re

AVATAR_DIRECTORY = pathlib.Path(__file__).resolve().parents[3]
REPOSITORY_ROOT = AVATAR_DIRECTORY.parents[2]
ROSTER = REPOSITORY_ROOT / "agent-harness" / "servants" / "roster.txt"
CHARACTERS_FILE = AVATAR_DIRECTORY / "cast" / "servant-characters.txt"
CHARACTERS_DEFINITION = AVATAR_DIRECTORY / "cast" / "characters.nix"

MALE_SERVANTS = {
    "Achilles",
    "Amakusa Shirou",
    "Angra Mainyu",
    "Antonio Salieri",
    "Arjuna",
    "Arthur Pendragon",
    "Astolfo",
    "Avicebron",
    "Bedivere",
    "Beowulf",
    "Billy the Kid",
    "Chiron",
    "Cu Chulainn",
    "Cu Chulainn (Alter)",
    "Cu Chulainn (Caster)",
    "David",
    "Diarmuid Ua Duibhne",
    "Edmond Dantès",
    "EMIYA",
    "EMIYA (Alter)",
    "Enkidu",
    "Gawain",
    "Gilgamesh",
    "Gilles de Rais",
    "Hassan-i-Sabbah",
    "Heracles",
    "Hijikata Toshizō",
    "Iskandar",
    "Karna",
    "King Hassan",
    "Lancelot",
    "Lancelot (Berserker)",
    "Li Shuwen",
    "Merlin",
    "Mozart",
    "Nikola Tesla",
    "Orion",
    "Ozymandias",
    "Paracelsus",
    "Qin Shi Huang",
    "Rama",
    "Robin Hood",
    "Romulus",
    "Sakamoto Ryōma",
    "Sakata Kintoki",
    "Sasaki Kojirou",
    "Sherlock Holmes",
    "Siegfried",
    "Vlad III",
    "Voyager",
    "Yan Qing",
    "Zhuge Liang",
}

KNOWN_FEMALE_SERVANTS = {
    "Medea",
    "Circe",
    "Ishtar",
    "Scheherazade",
    "Francis Drake",
    "Artoria Pendragon",
    "Jeanne d'Arc",
    "Nero Claudius",
    "Mordred",
    "Mash Kyrielight",
}


LIVE_VOICES_BY_GENDER = {
    "woman": {"quartz", "willow", "gleam", "delta", "bossa"},
    "man": {"ripple", "vesper", "stone", "meridian", "beacon", "cinder", "tempo"},
}
LOCAL_VOICE_PREFIX_BY_GENDER = {"woman": "pf_", "man": "pm_"}


def roster_names():
    return [line.split(" | ")[0] for line in ROSTER.read_text().splitlines()]


def assigned_characters():
    pairs = [line.split(" | ") for line in CHARACTERS_FILE.read_text().splitlines()]
    return [(name, character) for name, character in pairs]


def characters_of_gender(builder):
    definition = CHARACTERS_DEFINITION.read_text()
    pattern = rf'\({builder} \{{\s+name = "([^"]+)";'
    return set(re.findall(pattern, definition))


def defined_characters():
    return characters_of_gender("man") | characters_of_gender("woman")


MALE_CHARACTERS = characters_of_gender("man")


def test_the_fixture_lists_at_least_fifteen_male_servants_from_the_roster():
    assert len(MALE_SERVANTS) >= 15
    assert MALE_SERVANTS <= set(roster_names())


def test_every_roster_servant_has_exactly_one_line_in_roster_order():
    assert [name for name, _ in assigned_characters()] == roster_names()
    assert max(collections.Counter(roster_names()).values()) == 1


def test_every_assigned_character_is_defined_in_the_character_list():
    assert {character for _, character in assigned_characters()} <= (
        defined_characters()
    )


def test_male_characters_belong_to_male_servants_and_to_nobody_else():
    wearers = {
        name
        for name, character in assigned_characters()
        if character in MALE_CHARACTERS
    }
    assert wearers == MALE_SERVANTS


def test_well_known_female_servants_never_get_a_male_character():
    characters = dict(assigned_characters())
    assert {characters[name] for name in KNOWN_FEMALE_SERVANTS}.isdisjoint(
        MALE_CHARACTERS
    )


def characters_with_their_voices():
    definition = CHARACTERS_DEFINITION.read_text()
    local_voice_of_a_woman = re.search(r'localVoice = "([^"]+)";', definition)[1]
    for builder, body in re.findall(r"\((woman|man) \{(.*?)\}\)", definition, re.S):
        local_voice = re.search(r'localVoice = "([^"]+)";', body)
        yield (
            builder,
            re.search(r'liveVoice = "([^"]+)";', body)[1],
            local_voice[1] if local_voice else local_voice_of_a_woman,
        )


def test_every_character_speaks_with_voices_of_its_own_gender():
    characters = list(characters_with_their_voices())
    assert len(characters) == len(defined_characters())
    for builder, live_voice, local_voice in characters:
        assert live_voice in LIVE_VOICES_BY_GENDER[builder]
        assert local_voice.startswith(LOCAL_VOICE_PREFIX_BY_GENDER[builder])


def test_every_character_is_used_and_none_piles_up_servants():
    used = {character for _, character in assigned_characters()}
    assert used == defined_characters()
    spread = collections.Counter(character for _, character in assigned_characters())
    assert max(spread.values()) <= 10
