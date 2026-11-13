#!/usr/bin/env python3
"""Create a private deployment environment without replacing existing secrets."""

import argparse
import ipaddress
import os
from pathlib import Path
import re
import secrets
import sys
from urllib.parse import urlsplit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--public-url", required=True, help="HTTPS hostname without a URL prefix")
    parser.add_argument("--public-ip", required=True, help="VPS public IPv4 address")
    parser.add_argument("--http-port", type=int, default=18080, help="Loopback backend port")
    args = parser.parse_args()

    try:
        url = urlsplit(args.public_url)
        hostname = url.hostname or ""
        valid_hostname = all(
            re.fullmatch(r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?", label)
            for label in hostname.split(".")
        )
        if (
            url.scheme != "https"
            or not valid_hostname
            or "." not in hostname
            or len(hostname) > 253
            or url.netloc.lower() != hostname.lower()
            or url.path not in ("", "/")
            or url.query
            or url.fragment
        ):
            raise ValueError("Use https://hostname with no credentials, port, query, or URL prefix. Jitsi subdirectory routing needs a separate decision.")
        public_ip = ipaddress.IPv4Address(args.public_ip)
        if not public_ip.is_global:
            raise ValueError("--public-ip must be the VPS's globally routable IPv4 address.")
        if not 1024 <= args.http_port <= 65535:
            raise ValueError("--http-port must be between 1024 and 65535.")
        if sys.platform.startswith("linux") and os.geteuid() not in (0, 1000):
            raise ValueError("Run this script with sudo so persistent storage can be owned by container uid 1000.")
    except ValueError as error:
        parser.error(str(error))

    root = Path(__file__).resolve().parent.parent
    env_path = root / ".env"
    if env_path.exists():
        parser.exit(1, "Existing .env preserved. Edit its public URL/IP manually; keep service passwords unchanged.\n")
    values = {
        "PUBLIC_URL": "https://" + hostname.lower(),
        "JVB_ADVERTISE_IPS": str(public_ip),
        "HTTP_PORT": str(args.http_port),
        "JICOFO_AUTH_PASSWORD": secrets.token_hex(32),
        "JVB_AUTH_PASSWORD": secrets.token_hex(32),
    }
    lines = []
    for line in (root / ".env.example").read_text().splitlines():
        key, separator, _ = line.partition("=")
        lines.append(key + "=" + values[key] if separator and key in values else line)

    for directory in (
        "web", "storage/web", "prosody/config", "prosody/prosody-plugins-custom",
        "storage/prosody", "tmp/web-load-test", "jicofo", "jvb",
    ):
        path = root / "data" / directory
        path.mkdir(parents=True, exist_ok=True)
        path.chmod(0o755)
    # Upstream images run as uid/gid 1000 and must be able to write state.
    for directory in ("storage/web", "storage/prosody", "tmp/web-load-test"):
        path = root / "data" / directory
        if sys.platform.startswith("linux") and os.geteuid() == 0:
            os.chown(path, 1000, 1000)
        path.chmod(0o700)
    try:
        fd = os.open(env_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        parser.exit(1, "Existing .env preserved. Edit its public URL/IP manually; keep service passwords unchanged.\n")
    with os.fdopen(fd, "w") as env_file:
        env_file.write("\n".join(lines) + "\n")
    print("Created private .env and persistent data directories. No containers started.")


if __name__ == "__main__":
    main()
