# Meshtastic Satellite Weather Station
### A Hack Club Stasis Project

A self-contained, fully off-grid deployable kit that receives real-time weather data directly from GOES satellites and serves it on demand to any nearby Meshtastic mesh node — no internet, no cell service, no infrastructure required.

> Built for [Hack Club Stasis](https://stasis.hackclub.com)

---

## The Problem

Weather stations are common on urban LoRa meshes, but they rely on local sensors or internet-connected APIs. In a natural disaster, exactly when weather data matters most, power and internet go down first. A mesh node that can only tell you the temperature outside your window isn't very useful when a tornado is 40 miles away.

## The Solution

This kit receives structured meteorological data broadcasts directly from NOAA's GOES-East geostationary satellite using a software defined radio and a 3D printed helical antenna. It stores a rolling 7-day database of weather data and exposes a query bot on the Meshtastic mesh. Anyone within radio range can request a weather report with a simple command, no app, no internet, no setup on their end.

The entire system runs on solar power and a 3-cell 18650 battery pack, capable of operating for multiple days without sunlight.

---

## Query Interface

Any Meshtastic user within range can query the bot using plain text commands:

```
!wx 30.26 -97.74          → current conditions at coordinates
!wx 30.26 -97.74 3        → 3-day forecast
!fc AUS                   → forecast by airport/station ID
!warn TX                  → active NWS warnings for a state
!help                     → list available commands
```

Responses are formatted to stay under 200 characters, well within LoRa packet limits.

---

## System Architecture

```
GOES-East Satellite (1692.7 MHz EMWIN broadcast)
        |
3D Printed Helical Antenna (RHCP, tuned 1692.7 MHz)
        │
Nooelec SAWbird+ GOES LNA (powered via RTL-SDR bias tee)
        │
RTL-SDR Blog V3 (USB SDR dongle)
        │ USB
Raspberry Pi Zero 2W
 > goestools EMWIN decoder
 > SQLite database (7-day rolling store)
 > Meshtastic bot daemon (Python)
        │ USB serial
RAKWireless RAK4631 + RAK19007
        │ 915 MHz LoRa
Meshtastic mesh network
```

---

## Hardware

### Satellite Receive Chain
The GOES EMWIN signal at 1692.7 MHz broadcasts structured NWS text products: forecasts, warnings, METARs, and observations, in an unencrypted digital format receivable with commodity SDR hardware. The key components are:

- **3D Printed Helical Antenna** — custom designed in Fusion 360, printed on an Elegoo Centauri Carbon, wound with 18 AWG solid copper wire. Axial-mode helix provides natural right-hand circular polarization (RHCP) matching the satellite downlink. Aimed at GOES-East (~35° elevation, due south from Texas).
- **Nooelec SAWbird+ GOES LNA** — inline low-noise amplifier with SAW filter centered at 1688 MHz, providing >20 dB gain. Powered directly from the RTL-SDR V3 bias tee — no separate power required.
- **RTL-SDR Blog V3** — the industry standard hobbyist SDR dongle. Tunes up to ~1.7 GHz with excellent sensitivity.

### Mesh Radio
- **RAKWireless RAK4631** (nRF52840) + **RAK19007 base board** — low power Meshtastic node running stock Meshtastic firmware. Communicates with the Pi over USB serial using the Meshtastic Python library. The nRF52840 chipset draws significantly less power than ESP32-based alternatives, extending battery life.
- **Generic 915 MHz 5.8 dBi fiberglass antenna** — panel mounted to the exterior of the case with the included hardware mount. Omnidirectional, suitable for multi-day high-density mesh operation.

### Computing & Power
- **Raspberry Pi Zero 2W** — runs Raspberry Pi OS Lite, goestools, SQLite, and the bot daemon. Draws ~1.5W under load.
- **TP4056 charge controller** — manages charging of the 3-cell 18650 pack from the solar panels.
- **3x 18650 Li-Ion cells** (~10Ah) — provides ~48 hours of runtime without solar input.
- **2x ALLPOWERS 2.5W 5V solar panels** — wired in parallel, magnetically mounted to the case lid for deployment. Provides realistic 2-3W in partial sun, enough to sustain the system indefinitely in typical conditions.

### The Case
An IP67-rated 11×8×5" hard case serves as the foundation for the entire kit. Interior layout:

- **Left half** — 3D printed brain enclosure housing all electronics, with a magnetic front plate featuring an SSD1306 OLED display and 4 toggle switches
- **Right half** — 3D printed storage trays for the antenna, cables, and mast sections

External hardware includes SMA bulkheads, a cable gland for the solar panel, and the antenna mount — everything needed to go from closed case to fully deployed in under 2 minutes.

### Front Plate Controls
| Switch | Function |
|--------|----------|
| 1 | System power on/off |
| 2 | Mesh TX enable/disable |
| 3 | Display mode (system status / last query) |
| 4 | Force EMWIN data refresh |

The OLED display shows a split view: system status (satellite lock, battery, node count) on the top half, and the last mesh query and response on the bottom half.

---

## Software Stack

| Component | Technology |
|-----------|------------|
| EMWIN decoder | goestools |
| Database | SQLite (7-day rolling window) |
| Bot daemon | Python, Meshtastic library |
| Display driver | Python, luma.oled |
| Auto-start | systemd services with watchdog |

---

## Deployment

1. Open case, prop lid open
2. Peel solar panels off lid interior stow frame, stick to exterior lid mount
3. Point helical antenna south (~175° azimuth, ~35° elevation) toward GOES-East
4. Flip power switch
5. Within ~60 seconds the Meshtastic node appears on the mesh and the bot is live

---

## BOM

Full bill of materials with pricing and links:
[Google Sheets BOM](https://docs.google.com/spreadsheets/d/1USlBK-dkPbo43bPHNxUITIbZjwFQk0WdP9H-Rfz2vz8/edit?usp=sharing)

**Approximate total: ~$294**

---

## Project Status

- [x] System architecture designed
- [x] BOM finalized
- [x] Front plate modeled in Fusion 360
- [ ] Parts on order
- [ ] EMWIN receive pipeline (goestools + SQLite)
- [ ] Meshtastic bot daemon
- [x] Brain enclosure modeled
- [ ] Helical antenna former modeled and wound
- [ ] Assembly
- [ ] Field test

---

## License

MIT
