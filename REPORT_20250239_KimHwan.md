# CS270 Final Individual Report

**Name:** Kim Hwan
**Student ID:** 20250239
**Project:** Somaek Maker
**Date:** June 13, 2025

---

## My Role

I served as the primary software developer for the Somaek Maker project, a robot that automatically mixes *somaek* (a blend of soju and beer) based on the user's detected emotion or voice command. Our team of five built the complete system using LEGO SPIKE Prime hubs, Bluetooth Low Energy (BLE), Python, and computer vision / speech recognition.

---

## Contributions

### 1. Ideation

During the early brainstorming phase, our teammate Hyunjae Chun initially proposed the concept of an automated dispenser. Building on that foundation, I proposed several thematic directions — including a Squid Game-inspired machine and the Somaek Maker concept that the team ultimately pursued. I also proposed the physical architecture for how the cup would move along a rail system between dispensing stations, which became the structural backbone of the robot's hardware design.

### 2. Communication Protocol Design

One of my key architectural contributions was designing the PC–Hub communication protocol. The system operates on a strict **request-response handshake**: the PC sends a command to a hub, the hub executes the action, and only then does it send back a completion signal (e.g., `DISPENSE_DONE`, `ARRIVED:home`, `CONFIG_OK`). This ensures the PC never issues the next command before the previous one finishes, preventing race conditions between hardware actions.

The original architecture used two PCs and two hubs. After Ethan demonstrated that a single PC could maintain two simultaneous BLE connections, I refactored the entire codebase around that topology — one PC managing both the `Bottle Hub` (dispensers + mixer) and the `Cup Hub` (rail movement) over BLE in a single async event loop.

A key implementation detail was BLE packet fragmentation: BLE payloads can arrive split across multiple callbacks. I handled this by accumulating incoming bytes in a buffer and splitting on newlines to reconstruct complete messages, which is what makes the communication reliable in practice.

### 3. Full Software Implementation

I implemented nearly the entire software stack:

- **`pc1/main.py`** — The main orchestrator. An async event loop supporting two operating modes (face recognition and voice command), keyboard input on a background thread, and the full drink-making sequence coordinating both hubs.
- **`pc1/hub_client.py`** — The BLE communication layer. Implements the READY-based handshake: the hub signals `READY` when waiting for a command, and the PC waits for that signal before sending. This eliminates dropped commands from timing mismatches.
- **`pc1/dispenser.py` / `pc1/rail.py`** — High-level abstractions over the two hubs, translating drink recipes into timed motor commands (dispenser) and millimeter-precise movement sequences (rail).
- **`hub1/main.py` / `hub2/main.py`** — MicroPython firmware running on the LEGO hubs themselves. The Bottle Hub handles valve control and spoon mixing; the Cup Hub drives the robot base along the rail using encoder-based odometry.
- **`pc1/emotion/`** — Face detection using DeepFace and emotion-to-recipe mapping. Each emotion (happy, sad, angry, stressed, surprised, neutral) has a baseline soda/beer/soju ratio, and the detected intensity linearly shifts that ratio.
- **`pc1/voice/`** — Voice command listener (Google STT / Whisper), TTS speaker feedback, and clap detector for hands-free triggering.
- **`pc1/calibrate_dispenser.py` / `pc1/calibrate_distance.py`** — Interactive calibration tools described below.

### 4. Solving Key Engineering Challenges

**Challenge 1: USB vs. BLE Integration**

Early in development, Ethan and I each independently implemented a working connection between the PC and the hubs — mine over USB serial, his over BLE. Merging both approaches into a unified codebase required significant refactoring and extended discussion. We ultimately standardized on BLE for its wireless flexibility, and the `HubClient` class abstracts the connection so the rest of the codebase remains connection-agnostic.

**Challenge 2: Dispenser Accuracy**

The dispenser motors cannot directly measure volume. To solve this, I built `calibrate_dispenser.py`, an interactive calibration tool that repeatedly opens and closes each valve while the user measures the actual volume dispensed. The tool applies **linear regression** across multiple measurements to derive a precise flow rate (ml/s) per bottle, targeting R² ≥ 0.995. This approach is far more reliable than using a fixed constant, since flow rate varies with liquid viscosity and remaining bottle pressure.

**Challenge 3: Cup Positioning**

Accurately moving the cup to each station proved difficult. We initially attached a color sensor to the underside of the robot to detect station markers, but the approach was too unreliable in practice. I replaced it with **encoder-based odometry**: the cup hub's drive motors track exactly how far the robot has traveled in millimeters from the home endstop. `calibrate_distance.py` lets us interactively nudge the robot by small increments and confirm each station's distance, which is then written back automatically into `config.py`. This eliminated the dependency on external sensors entirely.

---

## Reflection

This project gave me hands-on experience designing a real-time hardware communication protocol, building a full async software pipeline in Python, and closing the gap between software correctness and physical reliability. The most valuable lesson was that a system can be logically correct in code yet fail completely in the physical world — and that **calibration tooling is just as important as the main application itself**. Knowing when to discard an approach (color sensor) and replace it with a fundamentally more robust one (encoder odometry) was the kind of engineering judgment that no amount of reading can fully prepare you for.
