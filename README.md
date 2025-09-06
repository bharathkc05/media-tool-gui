# Media Tool GUI

A Python (Tkinter) desktop GUI that wraps common media command-line utilities used in Dolby Vision and general video workflows:

- **dovi_tool** (Dolby Vision metadata)
- **mp4muxer**
- **MKVToolNix suite**: `mkvmerge`, `mkvextract`, `mkvinfo`, `mkvpropedit`
- **FFmpeg**

It provides a single window with themed tabs, async process logging, and a preset system.

---
## Features
- Unified GUI for multiple external tools
- Asynchronous execution with live log + cancel
- Light & Dark themes
- Multi-size icon handling (.ico + PNG fallbacks)
- Preset save/load (`tool_gui_presets.json`)
- Auto-detects tool paths (PATH / current / subdirectories)
- Collapsible advanced sections
- Raw extra args fields for power users

---
## Files
| File | Purpose |
|------|---------|
| `1.py` | Main Tkinter application |
| `tool_gui_presets.json` | Created on demand to store presets |
| `favicon.ico` / PNG icons | Window & executable icons |

---
## External Tools (Not Bundled)
| Tool | URL |
|------|-----|
| dovi_tool | https://github.com/quietvoid/dovi_tool/releases |
| mp4muxer | https://github.com/DolbyLaboratories/dlb_mp4base/blob/master/bin/mp4muxer.exe |
| MKVToolNix (mkvmerge, etc.) | https://mkvtoolnix.download/downloads.html |
| FFmpeg | https://ffmpeg.org/download.html |

Startup dialog offers download links if missing.

---
## Requirements
- Python 3.9+
- Tkinter (bundled with CPython)
- Windows primary target; should work on Linux/macOS if tools installed

No third-party Python deps (pure stdlib + Tk).

---
## Run From Source
```powershell
python 1.py
```

Virtual environment (optional):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python 1.py
```

Enable icon debug:
```powershell
$env:DEBUG_ICONS='1'
python 1.py
```

---
## Presets
Saved in `tool_gui_presets.json`. Use File menu -> Save / Load presets.

---
## Build (PyInstaller)
Install:
```powershell
pip install pyinstaller
```

One-folder build:
```powershell
pyinstaller .\1.py --name MediaToolGUI --icon .\favicon.ico --noconsole ^
	--add-data "apple-touch-icon.png;." ^
	--add-data "favicon-16x16.png;." ^
	--add-data "favicon-32x32.png;." ^
	--add-data "android-chrome-192x192.png;." ^
	--add-data "android-chrome-512x512.png;." ^
	--add-data "favicon.ico;."
```

One-file build:
```powershell
pyinstaller .\1.py --onefile --name MediaToolGUI --icon .\favicon.ico --noconsole ^
	--add-data "apple-touch-icon.png;." ^
	--add-data "favicon-16x16.png;." ^
	--add-data "favicon-32x32.png;." ^
	--add-data "android-chrome-192x192.png;." ^
	--add-data "android-chrome-512x512.png;." ^
	--add-data "favicon.ico;."
```

Add `--version-file version_info.txt` if you create one.

---
## Icons
Place beside `1.py`:
- `favicon.ico`
- `apple-touch-icon.png`
- `favicon-16x16.png`, `favicon-32x32.png`
- Optional: `android-chrome-192x192.png`, `android-chrome-512x512.png`

Runtime logic prefers `.ico` (Windows) then stacks PNGs with `iconphoto`.

---
## Theming
Switch between Light / Dark via the Theme menu. Extend palettes in the `THEMES` dictionary.

---
## Troubleshooting
| Issue | Fix |
|-------|-----|
| Icon missing | Ensure `favicon.ico` present; set `DEBUG_ICONS=1` |
| Tool not detected | Add executable to PATH or browse manually |
| Slow first start (one-file) | Use one-folder build |
| AV false positive | Rebuild or exclude dist folder |
| venv creation hangs | Use `--without-pip` + bootstrap, or Python 3.12 |

---
## Roadmap Ideas
- Drag & drop files
- Batch queue
- FFmpeg progress parsing
- Log font customization
- Auto-update checker

---
## Contributing
1. Fork
2. Branch: `feat/your-feature`
3. Commit & push
4. Open PR

Maintain minimal UI & consistent theming.

---
## License
MIT License (recommended). Add `LICENSE` file with full MIT text:
```
MIT License
Copyright (c) 2025 <Your Name>
Permission is hereby granted, free of charge, to any person obtaining a copy...
```

---
## Attribution
All external tools retain their own licenses; this project only orchestrates them.

---
## Quick Start
```powershell
python 1.py
```

Enjoy streamlined media workflows.
