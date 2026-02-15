# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.2] - 2026-02-15

### Fixed

- Project migrated to https://github.com/ewoks-kit/ewoksdask.

## [2.0.1] - 2025-12-30

### Fixed

- Adapt to `ewokscore>=4` test utility API change.

## [2.0.0] - 2025-07-25

### Added

- Add `ewoks.engines` entry point and implement the `WorkflowEngine` interface.
- Add `ewoksdask local` and `ewoksdask slurm` CLI to start a Dask cluster (Local or SLURM).

### Changed

- Drop support for Python 3.6 and 3.7.

## [1.0.0] - 2024-12-25

## [0.2.0] - 2024-11-08

### Added

- Add `task_options` to `execute_graph`.

## [0.1.4] - 2024-09-16

### Fixed

- Remove deprecated ewoks_jsonload_hook.

## [0.1.3] - 2024-06-22

### Fixed

- Support pip 24.1 and avoid pyyaml 6.0.2rc1.

## [0.1.2] - 2023-05-15

### Changed

- Remove deprecated ewokscore Task properties.

## [0.1.1] - 2023-03-09

### Changed

- Use new "engine" argument instead of the deprecated "binding".

## [0.1.0] - 2022-12-03

### Added

- Execute ewoks graph with dask.

[unreleased]: https://github.com/ewoks-kit/ewoksdask/compare/v2.0.2...HEAD
[2.0.2]: https://github.com/ewoks-kit/ewoksdask/compare/v2.0.1...v2.0.2
[2.0.1]: https://github.com/ewoks-kit/ewoksdask/compare/v2.0.0...v2.0.1
[2.0.0]: https://github.com/ewoks-kit/ewoksdask/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/ewoks-kit/ewoksdask/compare/v0.2.0...v1.0.0
[0.2.0]: https://github.com/ewoks-kit/ewoksdask/compare/v0.1.4...v0.2.0
[0.1.4]: https://github.com/ewoks-kit/ewoksdask/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/ewoks-kit/ewoksdask/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/ewoks-kit/ewoksdask/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/ewoks-kit/ewoksdask/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/ewoks-kit/ewoksdask/releases/tag/v0.1.0
