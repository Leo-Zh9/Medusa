# Medusa build plan

Agreed plan for the Hack Western 13 build. Written by one agent, attacked by a second over three rounds, then approved. Times are durations from the start of the build, not clock times.

## What we are building

When someone looks at the laptop screen, the laptop jumps to a blank Google Doc, and a small pan-tilt turret swings a flashlight onto the onlooker and follows them until they look away. For the demo the onlooker is a realistic dummy head carrying a paper marker. The light is a dollar-store finger light or mini flashlight. No laser, ever.

## 1. Architecture

**Raspberry Pi 5 (QNX)**
- `medusa_ai` (C++, a fork of QNX's [ai-camera-app](https://gitlab.com/qnx/projects/ai-camera-app)): reads C270 frames, finds the ArUco marker (ID 7) in the 640×360 frame, then runs BlazeFace (TFLite) on a 192×192 crop around it. If the face is missed, the eye point comes from a fixed offset below the marker, scaled by marker size. Publishes `{seq, t_cap, camera_ok, faces[], marker}` over UDP to 127.0.0.1:9001.
- `medusa_ctl` (Python standard library, no AI): picks the target, applies the aim mode, predicts motion, applies every safety rule, and sends commands to the MCU over UART.

**Arduino UNO Q (MCU side, powered from the laptop's USB)**
- Servo PWM, light switching, angle and slew limits, watchdog, arm button, rail sense, optional LCD.

**Laptop (macOS)**
- MediaPipe decides whether someone is looking at the screen, raises a pre-opened `docs.new` tab in Chrome, and shows the Pi's "tracking error (model)".

**Messages**

| From → to | Channel | Rate | Content | Safe after |
|---|---|---|---|---|
| Laptop → Pi | UDP :9000 | 15 Hz | `{seq, t, looking, conf}` | stale > 500 ms |
| AI → controller | UDP 127.0.0.1:9001 | per frame | boxes and marker | stale > 250 ms |
| Pi → MCU | UART 115200 | 30 Hz | `$M,seq,pan_d10,tilt_d10,light_pct,mode*CRC8` | watchdog 300 ms |
| MCU → Pi | UART | 5 Hz | `$S,state,rail*CRC` | — |
| Pi → laptop | UDP | — | `{err_deg, state}` | — |

**Who decides what:** the AI only reports boxes and the looking state. Deterministic code decides where to aim, whether the light is on and when. The MCU re-checks every limit.

## 2. Hardware

**In hand:** Pi 5 + cooler, C270 (blue USB3 port), 2× UNO Q (one spare), jumper wires, Apple USB-C charger, Grove LCD (optional, cut without a Grove cable). Not used: stepper, DC motors, touch sensor.

**From the friend:**
- 2× SG90 micro servos (only one → pan-only, tilt set by hand)
- 2N2222A transistor
- Resistors: 1 kΩ ×3, 330 Ω, 10 kΩ ×4, 20 kΩ
- Breadboard, MB102 (distribution only), push button
- DC supply giving 5 V at ≥1.5 A (fallback: 4×AA holder)
- Multimeter (required); ≥470 µF capacitor if available

**Bought (the only purchase):** one pack of finger lights or one mini flashlight. Free alternative: the Canada Life flashlight from the prize table.

**3D printed:** pan-tilt bracket with a tilt stop; clamp ring for the light (centre of mass within 5 mm of the tilt axis); base plate holding the C270 above the pan axis; handle or mount for the dummy so the holder grips it from below or behind at arm's length; optional snoot.

**Target:** the realistic dummy head with a 4 cm matte paper ArUco marker (ID 7) on its forehead. Fallbacks: a life-size face photo on matte card, then a tablet at full brightness tilted so glare goes away from the camera.

**Light switching**
- A two-sided battery interrupter (foil on both faces of thin card, a lead on each face, foil 1.5 mm back from every edge, edges taped) sits between the battery's negative end and the light's contact. The light's own switch stays on.
- Light lead → kill plug → 2N2222A collector; emitter → battery-negative lead and common GND.
- MCU D5 → base resistor → base, with 10 kΩ from base to GND so the light is dark whenever the MCU isn't driving it.
- Measure the light's current first, across the open interrupter:

| Current | Base resistor | Result |
|---|---|---|
| ≤ 60 mA (finger light) | 1 kΩ | saturated |
| 60–300 mA (AAA light) | 330 Ω | ~0.4 V drop, fine |
| > 400 mA | — | reject the light |

- **Fail-open check:** with the base held low, the light draws 0 mA and stays dark. Run it in P0 and after any battery or cap handling.

**Load on the servos** (SG90: 1.8 kg·cm rated, ~0.5 usable)

| Light | Weight | Torque | Share of usable |
|---|---|---|---|
| Finger light, 1 cm off axis | ~15 g | 0.015 kg·cm | 3% |
| AAA flashlight, 2 cm off axis | ~48 g | ~0.1 kg·cm | 20% |

**Wiring**
- Pi GPIO14 (pin 8) → 1 kΩ → MCU D0; MCU D1 → 1 kΩ → Pi GPIO15 (pin 10); common GND. Never connect the 3V3 rails.
- MCU D9 (pan) and D10 (tilt) to the servos, each with a 10 kΩ pull-down.
- Rail sense: rail → 20 kΩ → A2 → 10 kΩ → GND (1.67 V at 5 V, 2.13 V at 6.4 V); "on" above 1.3 V.
- Servo rail source, in order: bench supply at 5.0 V with a 1.5 A limit; MB102 fed 5 V through its USB input; 4×AA. The rail never connects to the Pi's or the MCU's 5 V.
- **Kill plug:** two jumpers taped into one pull tab, one in the servo rail's +5 V and one in the light's switched lead. Pulling it cuts both, and they stay cut.

## 3. Build order (14 h; S1 = Pi software, S2 = laptop, then hardware)

| Phase | Time | Work | Checkpoint |
|---|---|---|---|
| P0 | 0:00–1:30 | S1: QNX shell, C270 viewfinder, UART loopback, hotspot Wi-Fi, `ls` for libopencv_aruco, `which slm`, Docker build. S2: start the print, Servo library from GitHub master on D9/D10, IWDG, measure light current, foil fail-open check, MediaPipe and BlazeFace on the dummy | Go/no-go table |
| P1/P2 | 1:30–5:00 | S1: AI in stages (unmodified app + `sendto`, then the model, then ArUco) at ≥25 fps; controller prints angles. S2: laptop trigger, firmware, turret, light clamp | Doc opens; turret follows a test script; light toggles from the MCU |
| P3 | 5:00–7:30 | Measure the spot at 1 m and set the cone from it; 5-point calibration at 1 m; lead prediction; fix exposure with the light on the dummy; 30 s hold with no stale frames | Full loop works |
| P4 | 7:30–9:30 | Failure drills (kill each process and supervisor in turn), restart supervision, autostart | Every failure safe in < 0.5 s and recovers by itself |
| P5 | 9:30–10:30 | Tuning; grid card on the dummy at 1 m, record real spot error for 20 s each still / slow / by hand; confirm unmarked faces are never targeted | Three measured precision numbers |
| P6 | 10:30–14:00 | 1.5 h buffer, then demo script and rehearsal | — |

**P0 fallbacks**
- Camera: C270 in MJPEG mode, else the laptop streams frames to the Pi so inference stays on QNX.
- UART: the Pi's debug UART, else the UNO Q's Linux side plus Bridge.
- Servo library: Zephyr PWM API with a 20 ms period. Never bit-bang.
- ArUco missing: face only, inside a fixed region of interest.
- Face detection fails on the dummy: marker-only eye point, and marker pose as "looking".

## 4. Fail-safes (each one demonstrated)

| What happens | Response |
|---|---|
| Pi unplugged | MCU watchdog turns the light off and parks the servos; the laptop still covers the screen |
| Camera unplugged | `camera_ok=false` → light off, turret rests; retry every 1 s |
| `slay` on either process or a supervisor | Stale data or the MCU watchdog makes it safe; SLM, or the surviving partner supervisor, restarts what was killed |
| Laptop gone | Looking state stale after 500 ms → light off |
| Kill plug pulled | Light and servos lose power in hardware; MCU shows KILLED |
| MCU hung | IWDG resets it; base pull-down keeps the light dark |
| UNO Q unplugged | Pull-downs keep the light dark and the servos still |

## 5. AI, safety rules and precision

- **Aim mode (config):** `aim_mode = eye | torso`. Eye aims 0.38 of the face height down from the top of the box; torso aims 1.5 face heights below.
- **Hard limits in code (not config):** no laser; light duty ≤ 60%; pan ±60°; tilt within the calibrated range; slew ≤ 200°/s; only the marker-tagged face can ever be a target (nearest face box within 1.5 face widths of the marker); light off if any unmarked face, box grown by 20%, is inside the measured cone + 3°; light off on stale data.
- **Laptop "looking":** a face outside a fixed bottom-centre "owner" box, yaw and pitch under 20°, held 400 ms, with 800 ms hysteresis.
- **Precision:** the dummy's eye region (6–8 cm) is about 3.5–4.5° at 1 m.

| Error source | Size |
|---|---|
| SG90 backlash | 1–2° |
| Marker noise | ~0.15° |
| Face-box noise | ~0.5° |
| Latency | ~2°, ~0.7° with lead prediction |
| Calibration | ~0.7° |

- Expected: ±1.5–2° still or slow, ±2–3° by hand, 3–6° for ~0.2 s on sudden jerks. These are estimates; the figure we quote is the P5 measurement.
- The on-screen "tracking error (model)" only compares command with detection. It can't see backlash, calibration error or where the beam actually points.
- **Stretch (cut first):** parallax correction from marker range; spot-feedback correction.

## 6. Risks

1. The C270 fails under QNX's camera framework.
2. The QNX toolchain is late.
3. The Pi's UART doesn't work.
4. The servo supply gives < 1.5 A → use 4×AA.
5. The Servo library doesn't work on the UNO Q.
6. The light draws too much or misbehaves when switched → prefer the finger light; switch on/off without PWM.
7. The beam is too wide → snoot.
8. A print fails → cardboard.
9. Glare or dropouts at the target → matte target, fixed exposure, 30 s hold test.

**Cut order if late:** LCD, then tilt (set by hand), then the error overlay.

## 7. Decisions made for the team

SG90 servos (one → pan-only); the MCU owns PWM, the light and the watchdog; Pi–MCU over the GPIO UART; fixed camera; fail-closed (the turret acts only when the laptop reports looking); marker-only targeting; the dummy with a matte marker is the primary target; finger light by default; kill plug as the hardware kill; SLM or paired supervisors restart processes; no automatic return from the doc; no camera frames saved.

**Only the team can do:**
1. Create a QNX account at https://www.qnx.com/account, install the QNX Software Center, then install SDP 8.0 and "QNX SDP Host Tools (Linux 64-bit)".
2. Sign in to Google in Chrome.
3. macOS System Settings → Privacy & Security → Camera, and Automation: allow Terminal.

## 8. Not included

Lasers, any other purchases, multiple targets, a camera on the turret, owner identification, gaze tracking on the Pi, cloud or LLM AI, storing images.

## Sources

- [UNO Q: Linux and STM32](https://mischianti.org/arduino-uno-q-getting-started-with-linux-and-stm32/)
- [QNX Pi 5 BSP drivers](https://www.qnx.com/developers/docs/BSP8.0/com.qnx.doc.bsp_raspberrypi.bcm2712.rpi5_8.0/topic/driver_commands.html)
- [QNX GPIO UART on the Pi](https://www.qnx.com/developers/docs/qnxeverywhere/com.qnx.doc.interfacing/topic/rpi/rpi_GPIO_UART.html)
- [QNX quick start target image](https://www.qnx.com/developers/docs/qnxeverywhere/com.qnx.doc.target_images/topic/qsti/next-steps.html)
- [ai-camera-app](https://gitlab.com/qnx/projects/ai-camera-app)
- [QNX on macOS](https://devblog.qnx.com/how-to-use-macos-to-develop-for-qnx-8-0/)
- [Servo library issue on UNO Q](https://forum.arduino.cc/t/servo-library-issue/1412429)
