# BLE Visibility And WiFi Deferral

## Goal

Make the TTGO T-Display discoverable from a mobile phone through Bluetooth Low
Energy (BLE), while removing WiFi from the product until mobile provisioning is
implemented as a later feature.

## User Flow

1. In Options, `NEXT` moves to `BLUETOOTH: OFF`.
2. `ACTION` changes it to `BLUETOOTH: ADVERTISING` and starts BLE advertising.
3. A phone can discover the peripheral as `vPet-XXXX`, where `XXXX` is the
   final four hexadecimal digits of the ESP32 eFuse MAC address.
4. When a phone connects, the row displays `BLUETOOTH: CONNECTED`.
5. `ACTION` again stops advertising and disconnects any central; the row
   becomes `BLUETOOTH: OFF`.
6. The preference persists in NVS and is restored on boot.

## Scope

- Use NimBLE only, not Bluetooth Classic.
- Advertise the standard Device Information service with model, firmware
  version, and serial identifier characteristics. This lets common BLE scanner
  apps validate the device without a custom mobile app.
- Keep the radio on only while the setting is enabled.
- Remove WiFi scan, password input, auto-connect, Internet verification, and
  WiFi status from the T-Display firmware and its Options UI.
- Preserve any existing WiFi credentials in NVS, but do not read or use them.
- Shrink Options to language, sound, save, load, Bluetooth, date, time, and
  back so it remains readable on the 240x135 screen.

## Architecture

`BleService` is a T-Display platform adapter. It owns NimBLE lifecycle and
reports `Off`, `Advertising`, `Connected`, or `Error` to `App` and `Panels`.
The portable `Settings` model owns only the persisted enable preference; it
does not depend on Arduino or NimBLE.

The simulator mirrors the user-facing option and status, without attempting to
emulate a host BLE radio. Board-only tests compile the adapter; portable tests
cover persisted settings and option navigation.

## Constraints And Verification

- BLE and WiFi are intentionally mutually exclusive in this release because
  WiFi is disabled, avoiding shared-radio and heap pressure on the ESP32 with
  no PSRAM.
- Deployment must measure startup heap and show the selected BLE state in
  serial telemetry without exposing any secret.
- `make test`, `make native-test`, firmware build, and board deploy must pass.
