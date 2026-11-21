# Design

## What each part does

- **Laptop:** its webcam watches for someone other than you looking at the screen. When it sees one, it switches Chrome to a blank Google Doc and tells the Pi "someone is looking".
- **Raspberry Pi 5 (QNX):** the brain. It watches the dummy through the C270, finds the paper marker and the face, works out where to point, and sends angles to the UNO Q. Two programs run here: one that sees (AI) and one that decides (plain rules). If either is killed, it restarts on its own.
- **C270 webcam:** the turret's eye. Sits on the base plate, just above the turret.
- **UNO Q:** the hands and the safety guard. It moves the servos, switches the light, and refuses anything outside safe limits. If the Pi goes quiet for 0.3 s, it turns the light off and parks the turret.
- **Two servos:** one turns the turret left and right, the other tilts it up and down.
- **Light:** a finger light held in a printed clamp on the turret. It stays dark unless the UNO Q switches it on.
- **Paper marker:** a black and white square on the dummy's forehead. The turret only ever aims at a face with this marker. Anyone else in view just switches the light off.

## How they connect

- **Laptop ↔ Pi:** Wi-Fi (phone hotspot). The laptop sends "looking / not looking" about 15 times a second.
- **C270 → Pi:** USB.
- **Pi ↔ UNO Q:** three wires (send, receive, ground), each data wire through a 1 kΩ resistor. The 3.3 V pins are never joined.
- **UNO Q → servos:** pin D9 to the left-right servo, pin D10 to the up-down servo.
- **UNO Q → light:** pin D5 drives a transistor that sits in the light's battery loop. A foil-and-card insert in the light lets the transistor do the switching.

## Power

- Pi: Apple charger.
- UNO Q: laptop USB.
- Servos: their own 5 V supply, never shared with the Pi or UNO Q.
- Light: its own batteries.
- **Kill plug:** one pull tab that cuts both servo power and the light at once.

## When something fails

- **Pi unplugged:** the UNO Q notices within 0.3 s, turns the light off and parks the turret.
- **Camera unplugged, or a program killed:** the light goes off, and the program restarts by itself.
- **Laptop gone:** after 0.5 s with no news, the light goes off.
- **UNO Q unplugged:** resistors hold the light off and the servos still.
- **Kill plug pulled:** servos and light lose power, no software involved.
