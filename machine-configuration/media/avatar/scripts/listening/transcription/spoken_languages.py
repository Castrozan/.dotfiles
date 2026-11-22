import dataclasses


@dataclasses.dataclass(frozen=True)
class SpokenLanguage:
    iso_639_1: str
    iso_639_3: str

    @property
    def pinning_code(self):
        return self.iso_639_1

    def is_named_by(self, code):
        return code in (self.iso_639_1, self.iso_639_3)


PORTUGUESE = SpokenLanguage("pt", "por")
ENGLISH = SpokenLanguage("en", "eng")
JAPANESE = SpokenLanguage("ja", "jpn")
SPANISH = SpokenLanguage("es", "spa")
SPOKEN_LANGUAGES = (PORTUGUESE, ENGLISH, JAPANESE, SPANISH)


def spoken_language(code):
    return next(
        (language for language in SPOKEN_LANGUAGES if language.is_named_by(code)), None
    )


@dataclasses.dataclass
class RecentLanguage:
    language: SpokenLanguage = PORTUGUESE

    @property
    def pinning_code(self):
        return self.language.pinning_code

    def remember(self, language):
        self.language = language
