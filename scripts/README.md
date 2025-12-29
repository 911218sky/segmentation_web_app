# Scripts

This directory contains utility scripts organized by purpose.

## Directory Structure

```
scripts/
├── ci/           # CI/CD related scripts
├── docker/       # Docker operation scripts
├── internal/     # Internal scripts (used inside container)
└── local/        # Local development scripts
```

## CI Scripts (`ci/`)

| Script | Description | Usage |
|--------|-------------|-------|
| `release.sh` | Create GitHub Release with wheels and models | `bash scripts/ci/release.sh v1.0.0` |
| `docker-release.sh` | Trigger Docker image build with auto version bump | `bash scripts/ci/docker-release.sh` |

## Docker Scripts (`docker/`)

| Script | Description | Usage |
|--------|-------------|-------|
| `start.sh` | Start services with docker-compose | `bash scripts/docker/start.sh [foreground\|background]` |
| `clean.sh` | Clean up Docker resources | `bash scripts/docker/clean.sh [--dry-run] [--aggressive]` |

## Internal Scripts (`internal/`)

These scripts are used inside the Docker container and should not be run directly.

| Script | Description |
|--------|-------------|
| `entrypoint.sh` | Container entrypoint |
| `web.sh` | Start Streamlit web server |

## Local Scripts (`local/`)

| Script | Description | Usage |
|--------|-------------|-------|
| `dev.sh` | Start local development server (without Docker) | `bash scripts/local/dev.sh` |

## Prerequisites

- **GitHub CLI (`gh`)**: Required for `release.sh` and `docker-release.sh`
  - Install: https://cli.github.com/
  - Login: `gh auth login`
- **Docker & Docker Compose v2**: Required for docker scripts
- **Streamlit**: Required for local development
