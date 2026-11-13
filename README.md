# Jitsi Meet on a small VPS

Docker Compose deployment for four participants, 3 vCPUs, 4 GB RAM, and 15 GB free disk. Recording and transcription are disabled. Cameras start at a maximum requested capture height of 480p; screen sharing is limited to 5 fps. The four service memory limits total 2,944 MiB; leave capacity for the OS, Docker, and other existing applications.

## Public URL decision pending

The requested URL is `https://statsb.io.vn/jitsi`. [Jitsi's official guide](https://jitsi.github.io/handbook/docs/devops-guide/devops-guide-docker/#running-behind-a-reverse-proxy) explicitly says subdirectory deployments do not currently work well. A root-hostname deployment, optionally linked by a `/jitsi` redirect on the existing site, is the recommended option but has not been selected by the user yet. Proxy configuration will be added once that decision and the VPS's existing proxy are known.

This folder currently contains the independent Jitsi container stack. It is not deployed to the VPS and is not yet reachable at the requested URL.

`proxy/nginx-locations.conf` provides the root-hostname HTTP/WebSocket routes for host-installed Nginx. It must be included in a dedicated HTTPS server block once its hostname and certificate are chosen. It does not configure the existing website, TLS, or the requested `/jitsi` path. Do not include its catch-all route in the existing `statsb.io.vn` website's server block.

## Prepare on the VPS

Requirements: Docker Engine with Compose v2, Python 3, a public IPv4 address, and a hostname with HTTPS served by the VPS's reverse proxy. Use a supported Linux VPS; local macOS validation does not prove VPS media routing. Run the following as root on the VPS (or prefix the Python and Docker commands with `sudo`).

After selecting a root hostname, copy this folder to the VPS and run:

```sh
cd jitsi-meet
python3 scripts/configure.py --public-url https://CHOSEN_HOSTNAME --public-ip VPS_PUBLIC_IPV4
docker compose config --quiet
docker compose pull
docker compose up -d
docker compose ps
```

Replace both uppercase placeholders. The configuration script generates two random internal service passwords in `.env` (mode 0600), creates `data/`, and refuses to overwrite an existing `.env`. On Linux, writable storage is owned by the images' uid/gid 1000 with mode 0700; the script requires root or uid 1000. Configuration mounts are read-only, and runtime files use bounded tmpfs mounts. Set the public IPv4 to the VPS address, not a CDN or reverse-proxy address. Do not upload `.env` or `data/` to Git. If the IP changes, update `.env` and recreate containers with `docker compose up -d`; preserve service passwords.

The web backend binds only to `127.0.0.1:18080` on the VPS. A host-installed proxy can reach it there. A containerized proxy needs shared networking configured separately; its own `127.0.0.1` does not refer to the VPS.

Allow inbound UDP 10000 in both the VPS-provider and host firewalls. The reverse proxy handles HTTPS TCP 443; its certificate mechanism may also need TCP 80. An HTTP proxy alone does not carry audio/video. This minimal stack has no TURN relay: participants on networks that block direct UDP may need a TURN service later.

## Create the meeting host

Once Prosody is running, use its interactive account creation command so the meeting password is not placed in shell history:

```sh
docker compose exec prosody prosodyctl --config /run/prosody/config/prosody.cfg.lua adduser host@meet.jitsi
```

Host authentication is enabled; guests wait for a host and do not need accounts. Generated service credentials are separate from this meeting-host account.

## Verify before relying on it

- Confirm the final HTTPS hostname loads without certificate errors and `config.js` refers to that hostname.
- Check browser developer tools for a successful `/xmpp-websocket` connection.
- Create a meeting as the host, then join from a guest browser.
- Test all four participants on different networks, including camera, microphone, and screen sharing. A two-person call can bypass the bridge, so it does not prove four-person routing.
- Watch `docker stats`, `docker compose logs --tail=100`, and `df -h` during a normal-length call. Container logs rotate at 10 MB per file, three files per service. Also check persistent application files in `data/` periodically.

## Stop, backup, and update

`docker compose down` stops this project and preserves its bind-mounted data. Back up `.env` and `data/` privately while stopped, especially Prosody's account storage. Restart with `docker compose up -d`. Never run a system-wide Docker prune as part of maintaining this project.

All four Jitsi images are pinned to [stable-11248-3](https://github.com/jitsi/docker-jitsi-meet/releases/tag/stable-11248-3), the release checked on 2026-11-13. Back up first, review upstream release notes, change `JITSI_IMAGE_VERSION` consistently in `.env`, pull, and recreate the stack. Restoring a backup may be required to roll back a data-format change.
