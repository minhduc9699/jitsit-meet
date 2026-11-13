# Jitsi Docker deployment

Date: 2026-11-13
Status: core preparation reviewed and statically validated; final public URL and existing reverse proxy need confirmation.

## Context

- New project in `/Users/ducpm/jitsi-meet`; no existing project files or deployment configuration.
- Target VPS: 3 vCPUs, 4 GB RAM, 15 GB free disk; four participants; no recording.
- Requested URL: `https://statsb.io.vn/jitsi`.
- Upstream explicitly cautions against subdirectory deployment. Do not silently replace the requested URL.
- Local Docker CLI is available, but the daemon is stopped. Shell network access is unavailable; upstream documentation is accessible through web tools.

## Steps

1. Done: prepare pinned Jitsi web, Prosody, Jicofo, and Videobridge containers; provide service-credential generation, persisted accounts/configuration, rotated logs, and a generic Nginx locations snippet.
2. Pending user: confirm root-hostname/redirect versus strict subdirectory requirement and existing reverse proxy. Add the matching TLS and WebSocket integration without replacing existing website routes.
3. Partial: Compose and credential setup statically validated; core/snippet reviewed and setup/call checks documented. Nginx syntax, container startup, DNS/TLS, account recreation, and four-person call verification await the target environment and final routing decision.

## Verification

- Generator AST, five invalid-input cases, secret mode 0600, state mode 0700, and repeated-run preservation passed in a temporary project copy.
- `docker compose config --format json` passed; checked pinned image tags, internal shared credentials, authentication, disabled recording, intended published ports, log rotation, read-only/tmpfs layout, total memory limit, and explicit screen-sharing frame-rate settings.
- Scoped reviewer checked pinned upstream init/templates, Prosody persistence, XMPP routing, rootless permissions, and Nginx WebSocket/forwarded headers. Corrected the screen-sharing auto-frame-rate override identified in review; final static checks passed.
- No real environment file or credentials were generated in this project. No containers were started and no remote server was changed.

## Acceptance criteria

- Only the web backend on loopback TCP and Videobridge UDP are published by the base stack.
- Host authentication is required to create meetings; guests can join after the host.
- No recording services; Java heap and container memory budgets suit a small VPS.
- Credentials are generated with restrictive permissions, never printed, and not overwritten on a repeated setup.
- Proxy preserves HTTPS origin and WebSocket upgrades; media goes directly to VPS UDP 10000.
- Existing website routing is preserved; URL changes require the user's decision.
- Report static validation separately from actual runtime/call verification.

## Boundaries and rollback

Create local deployment files only. No VPS connection, DNS change, firewall change, certificate issuance, or live proxy reload has been requested with connection details yet.
Stop with `docker compose down`; preserve `.env` and `data/` for recovery. Do not remove shared proxy configuration or Docker resources belonging to other apps.

## Sources

- [Jitsi Docker guide](https://jitsi.github.io/handbook/docs/devops-guide/devops-guide-docker/)
- [Pinned upstream release](https://github.com/jitsi/docker-jitsi-meet/releases/tag/stable-11248-3)
