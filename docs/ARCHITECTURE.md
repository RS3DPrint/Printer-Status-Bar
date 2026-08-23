# Architecture

Printer connectors normalize every manufacturer into one structure:

- state
- progress
- remaining_minutes
- job_name
- detail

The controller maps the normalized state to a light-bar message. The ESP32 does not need to know whether the source printer is Klipper, Bambu, or another manufacturer.

This separation is intentional: new printer brands are added to the Windows controller without changing the light-bar hardware.
