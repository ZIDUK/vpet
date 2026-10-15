"""Routes shown inside the exploration icon on the T-Display simulator."""
from core.i18n import STAT_STRINGS


ROUTES = (
    {"id": "patio", "es": "PATIO", "en": "PATIO", "detail": "30M"},
    {"id": "jornada", "es": "JORNADA", "en": "SHIFT", "detail": "8H"},
    {"id": "noche", "es": "NOCHE", "en": "NIGHT", "detail": "8H"},
)
STATS = ("hp", "mp", "off", "def", "spd", "brn")
WINDOW = 3


class ExplorationMenu:
    def __init__(self, species="rookie"):
        self.species = species
        self.page = "routes"
        self.index = 0
        self.choice = None

    def allowed(self):
        return self.species not in ("egg", "baby")

    def title(self, spanish=True):
        if not self.allowed():
            return "EN CASA" if spanish else "AT HOME"
        if self.page == "stats":
            return "JORNADA" if spanish else "SHIFT"
        return "EXPLORAR" if spanish else "EXPLORE"

    def rows(self, spanish=True):
        back = {"id": "back", "label": "ATRAS" if spanish else "BACK", "detail": ""}
        if not self.allowed():
            return [back]
        if self.page == "stats":
            rows = []
            for stat in STATS:
                label = STAT_STRINGS[stat]["ES" if spanish else "EN"]
                rows.append({"id": stat, "label": label, "detail": ""})
            rows.append(back)
            return rows
        rows = []
        for route in ROUTES:
            rows.append({
                "id": route["id"],
                "label": route["es"] if spanish else route["en"],
                "detail": route["detail"],
            })
        rows.append(back)
        return rows

    def visible(self, spanish=True):
        rows = self.rows(spanish)
        count = len(rows)
        start = min(max(0, self.index - 1), max(0, count - WINDOW))
        return rows[start:start + WINDOW], start

    def next(self):
        self.index = (self.index + 1) % len(self.rows())

    def action(self):
        if not self.allowed():
            return "back"
        row = self.rows()[self.index]
        if self.page == "stats":
            if row["id"] == "back":
                self.page = "routes"
                self.index = 1
                return "routes"
            self.choice = ("jornada", row["id"])
            self.page = "routes"
            self.index = 1
            return self.choice
        if row["id"] == "back":
            return "back"
        if row["id"] == "jornada":
            self.page = "stats"
            self.index = 0
            return "stats"
        self.choice = (row["id"], None)
        return self.choice
