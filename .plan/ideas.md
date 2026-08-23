# Ideas (parking lot)

## Hardware
- Battery pack (LiPo + TP4056 charger) for portable vPet
- 3D-printed case in Digivice style (vertical grip + 2 buttons + screen)
- Alternate screen: 1.8" TFT (160×128) for more detail
- ESP32-S3 with TFT + audio (v2, future)
- IR or NFC for pet-to-pet battles (cute but complex)

## Software
- **Pygame simulator**: run vPet on Mac without Pico. Use the same `src/` modules with a pygame backend instead of displayio. Lets us iterate fast.
- **Web simulator**: even better, browser-based, can share the vPet
- **Tamagotchi-style mini-games** in the Fight menu (rock-paper-scissors, timing)
- **Pet-to-pet trading** via serial (connect 2 Picos)
- **Save state** to a website (REST API on Pico W)

## Game design
- Personality traits (aggressive / playful / lazy) that affect stat growth
- Evolution branches: Greymon can become either MetalGreymon or SkullGreymon (depending on care quality)
- Time-of-day mechanics (pets sleep at night, more active during day)
- Illness from low HP for too long
- Death (after 24h at 0 HP without heal)
- Daycare mode (regression if neglected)

## Polish
- Custom boot logo (not CircuitPython's default)
- Sound: tiny piezo buzzer for feedback beeps
- Vibration motor for "feed" feedback
- Multiple languages (ES, EN, JP)
- Custom themes (user-selectable palette)
- Stats history graph (last 24h shown as mini sparkline)

## Process
- Github Actions: run pytest on every push
- Pre-commit hook: validate JSON files
- Discord/Slack bot that watches the Pico serial and pings on critical events
- Auto-deploy on `git push` via mpremote (Pico W needs to be plugged in)
