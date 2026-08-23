# vPet Roadmap

## Vision
A pocket-sized Digimon-style virtual pet keychain. Real Agumon on a 128x128
color display, 2 buttons, autoplay + care mechanics. The pet dies if neglected,
evolves through 4 stages, and has a web admin panel for remote feeding.

## Hardware targets
- **Primary**: Waveshare Pico-LCD-1.44 (Raspberry Pi Pico W + ST7735S 128x128)
- **Future**: ESP32-S3 with better display + battery + RGB LED + piezo

## Milestones

### M0 — Prototype (✅ done)
- [x] Agumon idle sprite renders on Pico-LCD-1.44
- [x] Jungle background visible behind sprite
- [x] 4 action buttons (FEED/HEAL/PLAY/EVO) with white selector ring
- [x] Auto-decay stats (hunger/energy/happiness/health)
- [x] Manual button triggers an action
- [x] Repo + deployment script in place

### M1 — Pet lifecycle (current sprint)
- [ ] Stats actually drive sprite mood (happy/sad/hurt/sick)
- [ ] 4 evolution stages: rookie → champion → ultimate → mega
- [ ] Evolution triggered by stats + age
- [ ] Death by neglect (health = 0 for too long)
- [ ] Persistence: stats survive reboot (state.json)

### M2 — More animations
- [ ] Agumon walk cycle (left-right idle/walk alternation)
- [ ] Eat animation on FEED
- [ ] Sleep animation on HEAL
- [ ] Happy animation on PLAY
- [ ] Hurt animation when health low

### M3 — Sound + light feedback
- [ ] Backlight PWM based on mood
- [ ] Simple beep on actions (no piezo yet, just for testing)

### M4 — WiFi admin (deferred)
- [ ] Captive portal for initial WiFi config
- [ ] Flask web server with feed/play buttons (web-based remote care)

### M5 — Hardware iteration (long-term)
- [ ] Migrate to ESP32-S3 with proper display + battery
- [ ] Add RGB LED for status
- [ ] Add piezo for beeps
- [ ] 3D-print keychain case

## Current focus
M1 — Pet lifecycle. See `.plan/current-sprint.md`.
