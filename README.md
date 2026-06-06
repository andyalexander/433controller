# DrayTek DSL Speed Monitor for Home Assistant

A Home Assistant custom integration that exposes two sensors showing the current DSL line sync speeds on a **DrayTek Vigor 2862** (and other Vigor VDSL/ADSL routers).

| Sensor | Unit | Description |
|--------|------|-------------|
| DSL Download Speed | kbit/s | Downstream DSL sync rate |
| DSL Upload Speed | kbit/s | Upstream DSL sync rate |

Home Assistant automatically converts kbit/s to Mbit/s in dashboards and energy cards.

---

## Requirements

- DrayTek Vigor 2862 (or similar Vigor VDSL/ADSL router)
- Router web interface accessible from your Home Assistant host (same LAN)
- Router admin credentials

No additional router configuration is required — SNMP does **not** need to be enabled.

---

## Installation

### Via HACS (recommended)

1. In Home Assistant, open **HACS → Integrations**
2. Click the three-dot menu **⋮ → Custom repositories**
3. Add `https://github.com/andyalexander/433controller` with category **Integration**
4. Search for **DrayTek DSL** and install
5. Restart Home Assistant

### Manual

1. Copy the `custom_components/draytek_dsl/` folder into your HA config directory:
   ```
   <config>/custom_components/draytek_dsl/
   ```
2. Restart Home Assistant

---

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **DrayTek DSL Speed Monitor**
3. Fill in the form:

| Field | Default | Description |
|-------|---------|-------------|
| Router IP address | — | Local IP of your router, e.g. `192.168.1.1` |
| Web interface port | `80` | `80` for HTTP, `443` for HTTPS |
| Admin username | `admin` | Router admin username |
| Admin password | — | Router admin password |

Credentials are stored **encrypted** in Home Assistant's config store and are never written to plain-text files.

---

## How It Works

1. On each poll (every 60 seconds), the integration authenticates with the router's web management interface at `/cgi-bin/wlogin.cgi` using base64-encoded credentials — the same mechanism the router's own web UI uses.
2. It then fetches the DSL diagnostics page (under **Diagnostics → DSL Status** in the router UI) and parses the downstream and upstream sync rates.
3. The two sensor values update automatically.

---

## Troubleshooting

**Sensors show "unavailable"**

- Check that the router IP is reachable from HA: `ping 192.168.1.1`
- Verify the credentials are correct by logging into the router web UI manually
- Enable debug logging in `configuration.yaml`:
  ```yaml
  logger:
    logs:
      custom_components.draytek_dsl: debug
  ```
  Then check **Settings → System → Logs** for details on which DSL status page URL was tried.

**Both speeds show as 0 or unknown**

Your firmware version may use a slightly different URL path for the DSL status page. With debug logging enabled, you will see which paths were attempted. Please [open an issue](https://github.com/andyalexander/433controller/issues) with your firmware version and the debug log output.

**HTTPS / self-signed certificate errors**

Set port to `443`. The integration skips certificate verification (routers use self-signed certs), so no extra configuration is needed.

---

## Tested Firmware

| Model | Firmware | Status |
|-------|----------|--------|
| Vigor 2862 | 3.9.x | Supported |

Contributions for other Vigor models welcome — please open a PR or issue.
