"""Tests run against the real Home Assistant core with a mocked ProfitEMS API."""

import copy
from datetime import timedelta

from homeassistant.config_entries import SOURCE_USER, ConfigEntryState
from homeassistant.const import CONF_API_KEY
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.profitems.const import API_URL, DOMAIN

from .conftest import INSTALLATION

KEY = "pems_klucz_testowy"


async def _setup(hass, aioclient_mock, body=INSTALLATION):
    aioclient_mock.get(API_URL, json=body)
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=body["numerBramki"], data={CONF_API_KEY: KEY}
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def _state(hass, key, platform="sensor"):
    entity_id = er.async_get(hass).async_get_entity_id(
        platform, DOMAIN, f"{INSTALLATION['numerBramki']}_{key}"
    )
    assert entity_id, key
    return hass.states.get(entity_id)


async def test_user_flow_creates_entry_and_trims_key(hass, aioclient_mock):
    aioclient_mock.get(API_URL, json=INSTALLATION)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_KEY: f"  {KEY} "}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "ProfitEMS PE-26-TEST"
    assert result["data"] == {CONF_API_KEY: KEY}
    assert aioclient_mock.mock_calls[-1][3]["Authorization"] == f"Bearer {KEY}"


async def _flow_error(hass, aioclient_mock, **response):
    aioclient_mock.get(API_URL, **response)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_API_KEY: KEY})
    assert result["type"] is FlowResultType.FORM
    return result["errors"]["base"]


async def test_flow_invalid_key(hass, aioclient_mock):
    assert await _flow_error(hass, aioclient_mock, status=401) == "invalid_auth"


async def test_flow_rate_limited(hass, aioclient_mock):
    assert await _flow_error(hass, aioclient_mock, status=429) == "rate_limited"


async def test_flow_server_error(hass, aioclient_mock):
    assert await _flow_error(hass, aioclient_mock, status=500) == "cannot_connect"


async def test_flow_timeout(hass, aioclient_mock):
    assert await _flow_error(hass, aioclient_mock, exc=TimeoutError()) == "cannot_connect"


async def test_flow_unexpected_body(hass, aioclient_mock):
    assert await _flow_error(hass, aioclient_mock, json={"inne": 1}) == "cannot_connect"


async def test_same_installation_only_once(hass, aioclient_mock):
    await _setup(hass, aioclient_mock)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_API_KEY: KEY})
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_entities_show_api_values(hass, aioclient_mock):
    entry = await _setup(hass, aioclient_mock)
    assert entry.state is ConfigEntryState.LOADED
    assert float(_state(hass, "battery_level").state) == 74
    assert float(_state(hass, "pv_power").state) == 582
    assert float(_state(hass, "home_power").state) == 333
    assert float(_state(hass, "grid_power").state) == -11
    assert float(_state(hass, "battery_power").state) == -126
    assert float(_state(hass, "pv_surplus").state) == 249
    assert float(_state(hass, "rce_price").state) == 2.1941
    assert _state(hass, "rce_price").attributes["today"] == [0.7232] * 24
    assert _state(hass, "mode").state == "samokonsumpcja"
    assert _state(hass, "mode").attributes["plan"] == INSTALLATION["plan"]
    assert _state(hass, "connection").state == "online"
    assert _state(hass, "last_reading").state.startswith("2026-11-02T12:05:54")
    assert _state(hass, "pv_surplus_active", "binary_sensor").state == "on"
    assert _state(hass, "battery_full", "binary_sensor").state == "off"
    assert _state(hass, "control_active", "binary_sensor").state == "on"
    assert float(_state(hass, "pv_energy_today").state) == 14.2
    assert float(_state(hass, "home_energy_today").state) == 6.8
    assert float(_state(hass, "grid_import_today").state) == 0.9
    assert float(_state(hass, "grid_export_today").state) == 7.6
    assert float(_state(hass, "battery_charge_today").state) == 5.1
    assert float(_state(hass, "battery_discharge_today").state) == 2.4
    assert _state(hass, "pv_energy_today").attributes["state_class"] == "total_increasing"
    assert float(_state(hass, "value_today").state) == 6.42
    assert _state(hass, "value_today").attributes["state_class"] == "total"
    assert _state(hass, "value_today").attributes["last_reset"]
    assert _state(hass, "value_today").attributes["from_system"] == 2.32
    assert _state(hass, "mode").attributes["plan_today"] == INSTALLATION["planDoby"]
    assert _state(hass, "mode").attributes["plan_tomorrow"] is None
    assert _state(hass, "rce_price").attributes["prices_today"] == INSTALLATION["ceny"]["godzinyDzis"]


async def test_offline_installation_has_unknown_values(hass, aioclient_mock):
    body = copy.deepcopy(INSTALLATION)
    body["polaczenie"] = {"stan": "offline", "ostatniOdczyt": None, "pracaWyspowa": None}
    body["teraz"] = dict.fromkeys(body["teraz"])
    await _setup(hass, aioclient_mock, body)
    assert _state(hass, "battery_level").state == "unknown"
    assert _state(hass, "last_reading").state == "unknown"
    assert _state(hass, "connection").state == "offline"
    assert _state(hass, "island_mode", "binary_sensor").state == "unknown"


async def test_counters_the_brand_does_not_report_are_disabled(hass, aioclient_mock):
    body = copy.deepcopy(INSTALLATION)
    body["energiaDzis"] = {**dict.fromkeys(body["energiaDzis"]), "pvKwh": 18.4}
    await _setup(hass, aioclient_mock, body)
    registry = er.async_get(hass)
    pv = registry.async_get_entity_id("sensor", DOMAIN, f"{INSTALLATION['numerBramki']}_pv_energy_today")
    charge = registry.async_get_entity_id("sensor", DOMAIN, f"{INSTALLATION['numerBramki']}_battery_charge_today")
    assert registry.async_get(pv).disabled_by is None
    assert registry.async_get(charge).disabled_by is er.RegistryEntryDisabler.INTEGRATION


async def test_older_api_without_new_fields_keeps_working(hass, aioclient_mock):
    body = copy.deepcopy(INSTALLATION)
    for key in ("energiaDzis", "wartoscDzis", "planDoby", "planJutro"):
        del body[key]
    for key in ("godzinyDzis", "godzinyJutro"):
        del body["ceny"][key]
    await _setup(hass, aioclient_mock, body)
    assert float(_state(hass, "battery_level").state) == 74
    assert er.async_get(hass).async_get(
        er.async_get(hass).async_get_entity_id("sensor", DOMAIN, f"{INSTALLATION['numerBramki']}_pv_energy_today")
    ).disabled_by is er.RegistryEntryDisabler.INTEGRATION
    assert _state(hass, "value_today").state == "unknown"
    assert _state(hass, "mode").attributes["plan_today"] == []
    assert _state(hass, "rce_price").attributes["prices_today"] is None


async def test_new_mode_from_api_does_not_break_sensor(hass, aioclient_mock):
    body = copy.deepcopy(INSTALLATION)
    body["system"]["tryb"] = "nowy_tryb"
    await _setup(hass, aioclient_mock, body)
    assert _state(hass, "mode").state == "nowy_tryb"


async def test_key_disabled_starts_reauth_and_new_key_recovers(hass, aioclient_mock):
    entry = await _setup(hass, aioclient_mock)
    aioclient_mock.clear_requests()
    aioclient_mock.get(API_URL, status=401)
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=61))
    await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress_by_handler(DOMAIN)
    assert len(flows) == 1
    assert flows[0]["step_id"] == "reauth_confirm"

    aioclient_mock.clear_requests()
    aioclient_mock.get(API_URL, json=INSTALLATION)
    result = await hass.config_entries.flow.async_configure(
        flows[0]["flow_id"], {CONF_API_KEY: "pems_nowy"}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert entry.data[CONF_API_KEY] == "pems_nowy"
    assert entry.state is ConfigEntryState.LOADED


async def test_reauth_rejects_key_of_other_installation(hass, aioclient_mock):
    entry = await _setup(hass, aioclient_mock)
    result = await entry.start_reauth_flow(hass)
    aioclient_mock.clear_requests()
    other = copy.deepcopy(INSTALLATION)
    other["numerBramki"] = "PE-26-INNA"
    aioclient_mock.get(API_URL, json=other)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_KEY: "pems_inny"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "unique_id_mismatch"
    assert entry.data[CONF_API_KEY] == KEY


async def test_rate_limit_keeps_entry_and_recovers(hass, aioclient_mock):
    entry = await _setup(hass, aioclient_mock)
    aioclient_mock.clear_requests()
    aioclient_mock.get(API_URL, status=429, headers={"Retry-After": "30"})
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=61))
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED
    assert _state(hass, "pv_power").state == "unavailable"
    assert not hass.config_entries.flow.async_progress_by_handler(DOMAIN)


async def test_unload(hass, aioclient_mock):
    entry = await _setup(hass, aioclient_mock)
    assert await hass.config_entries.async_unload(entry.entry_id)
    assert entry.state is ConfigEntryState.NOT_LOADED


async def test_key_never_reaches_logs(hass, aioclient_mock, caplog):
    entry = await _setup(hass, aioclient_mock)
    aioclient_mock.clear_requests()
    aioclient_mock.get(API_URL, status=500)
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=61))
    await hass.async_block_till_done()
    assert entry.data[CONF_API_KEY] not in caplog.text
