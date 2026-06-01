# Xiaomi Pet Fountain — Home Assistant HACS Integration

Control and monitor your Xiaomi/MMGG pet fountain from Home Assistant.

Supported models: `xiaomi.pet_waterer.iv02`, `mmgg.pet_waterer.wi11` (and variants matching `pet_waterer`).

## Entities

| Platform | Entity | Description |
|---|---|---|
| `switch` | Pump | Turn pump on/off |
| `sensor` | Battery | Battery level (%) |
| `sensor` | Filter Life | Filter remaining life (%) |
| `sensor` | Filter Days Remaining | Days before filter change |
| `sensor` | Fault | Current fault code (enum) |
| `binary_sensor` | Water Shortage | True when water is low |
| `binary_sensor` | Pump Blocked | True when pump is obstructed |
| `binary_sensor` | Filter Expired | True when filter needs replacement |
| `binary_sensor` | Lid Removed | True when lid is off |
| `select` | Flow Mode | `sensor` / `intermittent` / `continuous` |
| `button` | Reset Filter | Reset filter life counter after replacement |

## Installation

1. Install via HACS (custom repository) or copy `custom_components/xiaomi_pet_fountain` into your HA `custom_components` folder.
2. Restart Home Assistant.
3. Go to **Settings → Integrations → Add Integration** → search **Xiaomi Pet Fountain**.
4. Enter your Xiaomi account email, password, and region (`de` for EU, `cn` for China, `us` for US…).
5. Complete 2FA if prompted.

## Regions

| Region | Value |
|---|---|
| Europe | `de` |
| China | `cn` |
| US | `us` |
| Russia | `ru` |
| Taiwan | `tw` |
| Singapore | `sg` |
| India | `in` |

## Automations

Example — notify when water is low:
```yaml
automation:
  trigger:
    platform: state
    entity_id: binary_sensor.fontaine_water_shortage
    to: "on"
  action:
    service: notify.mobile_app
    data:
      message: "Fontaine: remplis l'eau !"
```

Example — alert when filter expires:
```yaml
automation:
  trigger:
    platform: state
    entity_id: binary_sensor.fontaine_filter_expired
    to: "on"
  action:
    service: notify.mobile_app
    data:
      message: "Fontaine: remplace le filtre !"
```
