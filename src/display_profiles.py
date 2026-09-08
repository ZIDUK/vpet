"""Host-side display geometry for build and simulation targets."""
from dataclasses import dataclass


@dataclass(frozen=True)
class DisplayProfile:
    name: str
    width: int
    height: int
    menu_height: int
    cell_width: int
    icon_size: int
    pet_size: int
    portrait_size: int

    @property
    def content_rect(self):
        return (0, self.menu_height, self.width, self.height - self.menu_height)


PROFILES = {
    "tdisplay": DisplayProfile("tdisplay", 240, 135, 24, 30, 20, 88, 36),
    "pico": DisplayProfile("pico", 128, 128, 16, 16, 14, 64, 32),
}


def get_display_profile(name="tdisplay"):
    try:
        return PROFILES[name]
    except KeyError as error:
        raise ValueError(f"Unknown display profile: {name}") from error

