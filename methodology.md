Now I present Somaek Maker, an automated drink-mixing robot that detects your emotional state and pours a custom drink based on how you're feeling.

The system has one PC and two LEGO hubs. The bottle hub sits above the bottles and controls the valves that pour each drink. The cup hub drives a motorized rail that carries the cup to each bottle in sequence. The PC is the brain -- it handles emotion detection, computes the recipe, and tells both hubs what to do and when.

The PC talks to both hubs over BLE. The protocol is simple: the hub sends "READY", the PC sends a text command, the hub executes and sends a response back. One thing worth mentioning is that BLE packets can arrive fragmented, so the PC assembles incoming bytes into a buffer and splits on newlines to reconstruct complete messages. It's a small detail but it's what makes the communication reliable in practice.

When it's time to pour, the bottle hub opens a valve by rotating a motor to a calibrated angle, holds it for a calculated amount of time, then closes it. The time comes from a flow rate value for each bottle -- how many ml per second it actually pours. To get that value, we built a calibration script that opens and closes the valve while you measure the real volume that came out. You repeat this a few times with different amounts, and the script fits a linear regression over those measurements to give you an accurate flow rate. That value goes directly into the config.

The cup hub works similarly. Position is tracked by dead-reckoning from a home endstop. We have a separate calibration script that lets you nudge the rail interactively, millimeter by millimeter, until the cup is sitting exactly under each bottle. Confirm the position, and it writes those distances back into the config automatically.

For the recipe, the system supports two modes. In face mode, DeepFace analyzes webcam frames in the background and picks the dominant emotion when triggered. Each emotion has a baseline ratio across soda, beer, and soju -- happy skews beer-heavy, sad pushes toward more soju. The emotion intensity then shifts that ratio further; a stronger reading means a stronger drink. In voice mode, keyword matching on the transcribed speech feeds into the same recipe logic.

After all ingredients are poured, the cup moves to a mixing station where a spoon lowers, spins, and lifts back out.

Now you have a drink made exactly for how you feel.
