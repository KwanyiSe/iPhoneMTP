# iPhone MTP for Windows

**Makes your iPhone appear in File Explorer like an Android device.**  
Plug & play – no separate app to open.

## Features (Planned)
- [x] Device detection and AFC listing (core)
- [ ] Browse photos, videos, books, voice memos (AFC)
- [ ] Access app‑shared files (VLC, Documents, etc.) via House Arrest
- [ ] Selective backup for WhatsApp, Telegram (paid)
- [ ] Windows Service (background)
- [ ] Explorer namespace integration
- [ ] One‑click installer

## Getting Started
1. **Get the DLLs** – Download the required `libimobiledevice` Windows DLLs (from [jrjr/libimobiledevice-windows](https://github.com/jrjr/libimobiledevice-windows/releases)) and place them in a `libs` folder at the root (this folder is ignored by git).
2. **Install Python dependencies** – `pip install -r requirements.txt` (or use `pipenv install` if you have a Pipfile).
3. **Run the test** – `python tests/test_wrapper.py` to verify device detection.

## Project Structure
- `src/core/` – low‑level libimobiledevice wrapper
- `src/device/`, `src/afc/`, `src/house_arrest/`, `src/backup/` – higher‑level managers
- `src/explorer/` – Windows Explorer integration
- `src/service/` – Windows Service
- `src/utils/` – helpers, registry, logging
- `tests/` – test scripts

## License
MIT