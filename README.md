# Medusa

Medusa notices when someone is looking at your screen and covers for you. The moment it spots a snooper, your laptop jumps to an empty Google Doc, and a small spotlight swings over and follows them until they look away.

Built at Hack Western 13 for the QNX track.

## How it works

1. **Two cameras watch for onlookers.** A USB webcam on a Raspberry Pi (running QNX) watches the room. The laptop's own webcam watches from the screen's point of view.
2. **AI decides if someone is looking.** Each camera runs a face and gaze model to tell "someone is looking at this screen" apart from "someone walked past".
3. **Your screen covers for you.** The laptop switches to a fresh blank Google Doc (`docs.new`).
4. **The spotlight follows them.** An LED on a small motor turns toward the onlooker and tracks them for as long as they keep staring. It aims at their body, not their eyes, and uses a low-power LED, never a laser.
5. **It stops when they do.** Once nobody is looking, the light switches off and the motor returns to rest.

## Hardware

- Raspberry Pi 5 running QNX
- Logitech C270 USB webcam
- Laptop with a built-in webcam
- Arduino UNO Q (motor control and a safety cut-off if the Pi stops responding)
- Stepper motor or micro servo, plus an LED for the spotlight

## Status

Early. Nothing is built yet; this README describes the plan.
