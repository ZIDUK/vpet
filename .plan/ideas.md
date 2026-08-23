# vPet Ideas Backlog

## M1 — Pet lifecycle
- 4 evolution stages (rookie → champion → ultimate → mega) with different sprites
- Mood system: happy / neutral / tired / sick based on stats
- Death state: dark screen + tombstone sprite for 30s, then auto-revive as rookie
- Persistence: state.json saved on every stats change, restored on boot
- Daily cycle: stats decay faster when "asleep" (button held)

## M2 — Animations
- Eat: sprite plays agumon_eat.bmp for 2s after FEED
- Sleep: sprite plays agumon_sleep.bmp for 3s after HEAL
- Happy: sprite plays agumon_happy.bmp for 2s after PLAY
- Hurt: sprite plays agumon_hurt.bmp when health < 30
- Walk: sprite walks back and forth (already have agumon_walk.bmp, just need to wire it)

## M3 — Sound + light
- PWM on backlight (GP13) to dim during sleep
- Status RGB on future hardware
- Click sound on button press (needs piezo)

## M4 — WiFi
- Captive portal: AP mode on first boot, scan networks, save creds
- Tiny Flask server: GET /feed, /play, /heal, /status
- Phone browser: view stats + trigger actions
- Web UI: simple HTML with 3 buttons + 4 stat bars

## M5 — Hardware
- Migrate to ESP32-S3 with proper thermal management (T-Display died)
- 3D-printed case with belt clip
- Lipo battery with charging circuit
- RGB LED strip on the side for status

## Wild ideas (low priority)
- Two devices talk to each other (Pico battle mode via IR)
- AI-generated daily "mood message" (printed via thermal printer)
- Sound detection: pet reacts to claps
- Voice synthesis: pet says its name when happy
- Multiplayer: two pets visit each other (WiFi sync)
