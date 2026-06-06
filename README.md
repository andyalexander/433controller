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

### Option A — HACS (recommended)

[HACS](https://hacs.xyz) is the standard way to manage custom integrations in Home Assistant.

1. In Home Assistant, open **HACS → Integrations**
2. Click the three-dot menu **⋮** in the top-right corner, then **Custom repositories**
3. Paste `https://github.com/andyalexander/2862-HA` into the URL field, set the category to **Integration**, and click **Add**
4. Close the dialog, then search for **DrayTek DSL** and click **Download**
5. Restart Home Assistant

### Option B — Manual

1. Download or clone this repository
2. Copy the `custom_components/draytek_dsl/` folder into your Home Assistant config directory:

   ```
   /config/custom_components/draytek_dsl/
   ```

   If you are unsure where your config directory is, check **Settings → System → Storage** in Home Assistant — it shows the config path.

3. Restart Home Assistant

---

## Setting Up the Integration (Username & Password)

Your router credentials are entered through the Home Assistant UI and stored **encrypted** in HA's internal config store. They are never written to any plain-text file such as `configuration.yaml`.

1. Go to **Settings → Devices & Services**
2. Click **+ Add Integration** (bottom-right)
3. Search for **DrayTek DSL Speed Monitor** and select it
4. Fill in the setup form:

   | Field | Default | What to enter |
   |-------|---------|---------------|
   | Router IP address or hostname | — | The local IP of your DrayTek, e.g. `192.168.1.1`. Find it on the router's label or your broadband router's DHCP table. |
   | Web interface port | `80` | Leave as `80` unless you have changed the router's HTTP port. Use `443` if your router is configured for HTTPS only. |
   | Admin username | `admin` | The username you use to log into the router web UI (default is `admin`). |
   | Admin password | — | The router admin password. This is the password for the web interface, **not** your broadband/ISP password. |

5. Click **Submit**. The integration will attempt to log in and fetch the DSL status page. If it succeeds, two new sensors will appear under a **DrayTek Vigor** device.

> **Where is the password stored?**
> Home Assistant encrypts all config entry data (including passwords) using its internal secret store. The password is never visible in `configuration.yaml`, `.storage/`, or any log output.

### Updating credentials

If you change the router password, go to **Settings → Devices & Services → DrayTek DSL Speed Monitor → ⋮ → Reconfigure** to update the stored credentials.

### Locating your router admin password

The default admin password for the Vigor 2862 is printed on the label on the underside of the router. If it has been changed and you cannot remember it, you can reset the router to factory defaults by holding the **Factory Reset** button for 5 seconds (note: this resets all router settings, not just the password).

---

## How It Works

1. Every 60 seconds the integration logs in to the router at `/cgi-bin/wlogin.cgi` using your credentials (base64-encoded, the same way the router's own web UI does it)
2. It fetches the DSL diagnostics page — equivalent to **Diagnostics → DSL Status** in the router web UI — and parses the downstream and upstream sync rates
3. The two sensor values update in Home Assistant automatically

---

## Troubleshooting

**Sensors show "unavailable"**

- Check that the router is reachable from the machine running Home Assistant: open a terminal and run `ping 192.168.1.1`
- Log in to the router web UI manually at `http://192.168.1.1` to confirm the IP address and credentials are correct
- Enable debug logging by adding the following to `configuration.yaml`, then restarting HA:

  ```yaml
  logger:
    logs:
      custom_components.draytek_dsl: debug
  ```

  Go to **Settings → System → Logs** and look for `draytek_dsl` entries — you will see exactly which URLs were tried and what HTTP status codes were returned.

**Speeds show as unknown or 0**

Your firmware version may use a slightly different URL for the DSL status page. With debug logging enabled you will see which paths were attempted. Please [open an issue](https://github.com/andyalexander/2862-HA/issues) with:
- Your router model and firmware version (visible at the top of the router web UI)
- The debug log output

**HTTPS / certificate errors**

Set the port to `443` when configuring the integration. Certificate verification is skipped automatically (routers use self-signed certificates that HA would otherwise reject).

---

## Running the Tests

The test suite runs without a Home Assistant installation. There are two kinds of tests:

### Unit tests (no router required)

These test credential encoding, HTML parsing, and URL construction entirely offline.

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all unit tests
pytest tests/test_credentials.py tests/test_parse_speeds.py tests/test_urls.py -v
```

### Integration tests (real router required)

These connect to an actual router and verify that login succeeds and both speeds are returned. They are **skipped automatically** if credentials are not provided.

**Step 1 — create a `.env` file**

Copy the example file and fill in your router details:

```bash
cp .env.example .env
```

Then edit `.env`:

```
DRAYTEK_HOST=192.168.1.1
DRAYTEK_PORT=80
DRAYTEK_USERNAME=admin
DRAYTEK_PASSWORD=your_router_password
```

> The `.env` file is listed in `.gitignore` and will never be committed.

**Step 2 — run the integration tests**

```bash
pytest tests/test_integration.py -v
```

Expected output when the router is reachable and credentials are correct:

```
tests/test_integration.py::test_router_is_reachable PASSED
tests/test_integration.py::test_login_succeeds PASSED
tests/test_integration.py::test_dsl_speeds_are_returned PASSED
tests/test_integration.py::test_dsl_speeds_are_plausible PASSED
```

**Run everything at once**

```bash
pytest -v
```

Unit tests always run; integration tests are skipped if `.env` is absent.

---

## Tested Firmware

| Model | Firmware | Status |
|-------|----------|--------|
| Vigor 2862 | 3.9.x | Supported |

Contributions for other Vigor models welcome — please open a PR or issue.
