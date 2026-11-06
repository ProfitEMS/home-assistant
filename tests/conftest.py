"""Shared fixtures for the ProfitEMS integration tests."""

import pytest

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def enable_custom(enable_custom_integrations):
    """Let Home Assistant load the integration from custom_components."""


INSTALLATION = {
    "wersja": 1,
    "numerBramki": "PE-26-TEST",
    "polaczenie": {"stan": "online", "ostatniOdczyt": "2026-11-02T12:05:54.400Z", "pracaWyspowa": False},
    "teraz": {"socPct": 74, "pvW": 582, "domW": 333, "siecW": -11, "bateriaW": -126},
    "system": {"sterowanieAktywne": True, "tryb": "samokonsumpcja", "trybOd": "2026-11-02T03:00:51.050Z"},
    "energiaDzis": {"pvKwh": 14.2, "domKwh": 6.8, "poborKwh": 0.9, "oddawanieKwh": 7.6, "ladowanieKwh": 5.1, "rozladowanieKwh": 2.4},
    "wartoscDzis": {"razemZl": 6.42, "zPaneliZl": 4.1, "zSystemuZl": 2.32, "sprzedazZl": 1.85, "pokrycieDanychPct": 97, "przeliczono": "2026-11-02T12:20:04.000Z"},
    "plan": [{"od": "13:08", "do": "24:00", "tryb": "samokonsumpcja"}],
    "planDoby": [{"od": "00:00", "do": "06:00", "tryb": "rezerwa"}, {"od": "06:00", "do": "24:00", "tryb": "samokonsumpcja"}],
    "planJutro": None,
    "ceny": {
        "jednostka": "zł/kWh netto",
        "teraz": 2.1941,
        "dzis": [0.7232] * 24,
        "jutro": None,
        "godzinyDzis": [{"od": "2026-11-01T23:00:00.000Z", "do": "2026-11-02T00:00:00.000Z", "cena": 0.7232}],
        "godzinyJutro": None,
    },
    "sygnaly": {"nadwyzkaPv": True, "nadwyzkaPvW": 249, "bateriaPelna": False, "najtanszaGodzina": 2, "najtanszaGodzinaDnia": False},
}
