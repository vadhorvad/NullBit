# Changelog

## 1.1.0 — 2026-11-03

### Fixed
- Portrait photos no longer come out sideways after cleaning: the EXIF orientation is now baked into the pixels before the metadata is destroyed.
- A single unreadable or corrupted file no longer aborts the whole batch — it is skipped and counted.
- Existing files in the target folder are never overwritten: copies are named `_nullbit`, `_nullbit_1`, `_nullbit_2`, …
- Pixel formats the target format cannot store (e.g. CMYK, alpha) are converted automatically instead of failing.

### Changed
- Images are processed in a background thread: the window no longer freezes, with live progress (`3 / 12`).
- JPEG copies are saved with 4:4:4 chroma (no chroma subsampling).
- The selected language is remembered between sessions.
- File dialogs are localized.

### Added
- GitHub Actions workflow that builds the `.exe` and attaches it to a GitHub Release on every `v*` tag.
- Offline test suite for the cleaning core (`tests/test_cleaning.py`).
- `.gitignore` for Python and PyInstaller artifacts.
