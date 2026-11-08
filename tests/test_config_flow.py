import aiohttp
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import fake_pantry
from .conftest import DOMAIN


async def _start(hass):
    r = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert r["type"] is FlowResultType.FORM and r["step_id"] == "user"
    return r["flow_id"]


async def test_user_flow(hass: HomeAssistant, tz, pantry):
    flow = await _start(hass)
    r = await hass.config_entries.flow.async_configure(
        flow, {"url": fake_pantry.URL.removeprefix("http://") + "/", "token": f" {fake_pantry.TOKEN} "})
    assert r["type"] is FlowResultType.CREATE_ENTRY
    assert r["data"] == {"url": fake_pantry.URL, "token": fake_pantry.TOKEN}
    assert r["result"].unique_id == fake_pantry.INSTANCE_ID


async def test_errors(hass: HomeAssistant, tz, pantry):
    flow = await _start(hass)
    pantry(status=401)
    r = await hass.config_entries.flow.async_configure(flow, {"url": fake_pantry.URL, "token": "x"})
    assert r["errors"] == {"base": "invalid_auth"}
    pantry(exc=aiohttp.ClientError())
    r = await hass.config_entries.flow.async_configure(flow, {"url": fake_pantry.URL, "token": "x"})
    assert r["errors"] == {"base": "cannot_connect"}
    pantry(instance_id=None, version="2026.11.07.4")
    r = await hass.config_entries.flow.async_configure(flow, {"url": fake_pantry.URL, "token": "x"})
    assert r["errors"] == {"base": "pantry_outdated"}
    assert r["description_placeholders"]["pantry_version"] == "2026.11.07.4"


async def test_same_pantry_new_address_updates_entry(hass: HomeAssistant, entry, aioclient_mock):
    aioclient_mock.get("http://10.0.0.9:8765/api/ha/state",
                       json=fake_pantry.state(__import__("datetime").date.today()))
    flow = await _start(hass)
    r = await hass.config_entries.flow.async_configure(flow, {"url": "10.0.0.9:8765", "token": "new"})
    assert r["type"] is FlowResultType.ABORT and r["reason"] == "already_configured"
    assert entry.data == {"url": "http://10.0.0.9:8765", "token": "new"}


async def test_reconfigure_refuses_a_different_pantry(hass: HomeAssistant, entry, pantry):
    r = await entry.start_reconfigure_flow(hass)
    pantry(instance_id="ffffffffffffffffffffffffffffffff")
    r = await hass.config_entries.flow.async_configure(r["flow_id"], {"url": fake_pantry.URL, "token": "t"})
    assert r["type"] is FlowResultType.ABORT and r["reason"] == "wrong_pantry"
    pantry()
    r = await entry.start_reconfigure_flow(hass)
    r = await hass.config_entries.flow.async_configure(r["flow_id"], {"url": fake_pantry.URL, "token": "t2"})
    assert r["type"] is FlowResultType.ABORT and r["reason"] == "reconfigure_successful"
    assert entry.data["token"] == "t2"


async def test_reauth(hass: HomeAssistant, entry, pantry):
    pantry(status=401)
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    flows = [f for f in hass.config_entries.flow.async_progress() if f["context"]["source"] == "reauth"]
    assert len(flows) == 1
    r = await hass.config_entries.flow.async_configure(flows[0]["flow_id"], {"token": "wrong"})
    assert r["errors"] == {"base": "invalid_auth"}
    pantry()
    r = await hass.config_entries.flow.async_configure(flows[0]["flow_id"], {"token": "rotated"})
    assert r["type"] is FlowResultType.ABORT and r["reason"] == "reauth_successful"
    assert entry.data["token"] == "rotated"
