# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project aims to follow Semantic Versioning once we cut the first stable release.

## [Unreleased]

### Changed
- Waveform-only increase: use up to 1000 VT points when IBIS version >= 4.0. VI tables remain capped at 100 points.
- Refined transient sampling to improve waveform resolution and parity with commercial tools.
- Added an info log noting the 100 → 1000 waveform point change for IBIS >= 4.0.

### Notes
- Writer behavior unchanged: it emits all waveform samples provided by analysis; no additional truncation is applied.
- Backward compatibility: for IBIS < 4.0, waveform tables remain at 100 points.

## [0.0.0] - Initial scaffolding
- Project structure, packaging, and CLI/GUI foundations.

[Unreleased]: https://github.com/simon9721/s2ibispy/compare/sec...HEAD
[0.0.0]: https://github.com/simon9721/s2ibispy/tree/sec