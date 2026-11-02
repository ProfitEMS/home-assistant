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
    "plan": [{"od": "13:08", "do": "24:00", "tryb": "samokonsumpcja"}],
    "ceny": {"jednostka": "zł/kWh netto", "teraz": 2.1941, "dzis": [0.7232] * 24, "jutro": None},
    "sygnaly": {"nadwyzkaPv": True, "nadwyzkaPvW": 249, "bateriaPelna": False, "najtanszaGodzina": 2, "najtanszaGodzinaDnia": False},
}
