---
description: "Compile and execute the PlatformIO firmware for the ESP32-C3 Supermini"
name: "Compile and Execute Firmware"
argument-hint: "Optional upload port or execution detail"
agent: "agent"
---
Work with the PlatformIO project in this workspace.

1. Inspect `platformio.ini` and use the configured environment `esp32-c3-supermini`.
2. Compile the firmware with:
   `pio run -e esp32-c3-supermini`
3. If compilation fails, stop and report the first actionable error with its file and line when available. Do not claim that the firmware executed.
4. If compilation succeeds, determine whether an ESP32-C3 device and upload port are available. Use the user-provided port or execution detail when supplied: `${input:executionDetail}`.
5. If a device is available, upload the firmware with:
   `pio run -e esp32-c3-supermini -t upload`
   Then start the serial monitor at the project's configured speed:
   `pio device monitor -e esp32-c3-supermini -b 115200`
6. If no device or port is available, do not upload. State that compilation passed and that execution was skipped because hardware access is unavailable.

Report the result briefly with these headings:
- Build: passed or failed
- Execution: uploaded and monitored, or skipped with the reason
- Next action: only when the user needs to connect hardware, choose a port, or fix an error

Do not modify source code or configuration unless the user explicitly asks for a fix. Do not report success unless the corresponding command completed successfully.