# APEXLINE — Driver Intelligence

APEXLINE is a motorsport driver-development platform concept with two separate workflows:

- **Live sim-racing engineer:** a future Windows companion reads simulator telemetry locally and provides spoken coaching.
- **Real-world onboard review:** a separate upload workflow for onboard video and optional synced GPS/vehicle telemetry.

## Website

This repository is configured for GitHub Pages. The current website is a front-end prototype. Simulator connection buttons are explanatory placeholders, and the radio feed is explicitly labelled as example content.

## What is not live yet

The website does not currently connect to Assetto Corsa, iRacing, Le Mans Ultimate or rFactor 2. It does not currently run AI lap analysis or generate live race-engineer speech. A static GitHub Pages website cannot read a running simulator's local telemetry by itself.

To make live coaching real, the project still needs:

1. A Windows companion application with a separate telemetry adapter for each simulator.
2. A local authenticated bridge between that companion and the browser.
3. A secure AI service integration. API keys must be stored in environment variables on a backend or companion service, never in public website JavaScript.
4. Voice output, rate limiting and safety rules so radio messages are short and do not distract the driver.
5. Verified telemetry handling for incidents, lap/sector deltas, fuel, tyres and pit strategy.

## Simulator integration notes

Simulator support is not account OAuth. The companion should read each game's supported local telemetry/shared-memory interface and should never request the user's game password.

## Local preview

Open `index.html` in a browser, or use the published GitHub Pages URL once the Pages build is ready.

## Security

Do not commit API keys, passwords, access tokens, personal telemetry files or other secrets.
