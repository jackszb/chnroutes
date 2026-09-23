#!/usr/bin/env python3
"""Generate geoip-v4-cn.json / geoip-v4-cn.list.

Merges the aggregated China IPv4 ranges (from chnroutes2) with a fixed set
of private/reserved IPv4 ranges, then dedupes + aggregates + sorts the
combined set before writing the output files.

Usage:
    python3 generate_geoip_v4_cn.py <chnroutes-source-file>
"""

import ipaddress
import json
import sys

# Private / reserved IPv4 ranges to always include alongside the China routes.
EXTRA_CIDRS = [
    "0.0.0.0/8",
    "10.0.0.0/8",
    "100.64.0.0/10",
    "127.0.0.0/8",
    "169.254.0.0/16",
    "172.16.0.0/12",
    "192.0.0.0/24",
    "192.0.2.0/24",
    "192.88.99.0/24",
    "192.168.0.0/16",
    "198.18.0.0/15",
    "198.51.100.0/24",
    "203.0.113.0/24",
    "224.0.0.0/4",
    "240.0.0.0/4",
    "255.255.255.255/32",
]

JSON_OUTPUT = "geoip-v4-cn.json"
LIST_OUTPUT = "geoip-v4-cn.list"


def load_networks_from_file(path):
    nets = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                nets.append(ipaddress.ip_network(line, strict=False))
            except ValueError:
                continue
    return nets


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <chnroutes-source-file>", file=sys.stderr)
        sys.exit(1)

    source_path = sys.argv[1]

    chn_nets = load_networks_from_file(source_path)
    extra_nets = [ipaddress.ip_network(c, strict=False) for c in EXTRA_CIDRS]

    all_nets = set(chn_nets) | set(extra_nets)

    # dedupe + aggregate + sort
    collapsed = sorted(
        ipaddress.collapse_addresses(all_nets),
        key=lambda n: (int(n.network_address), n.prefixlen),
    )
    cidrs = [str(n) for n in collapsed]

    with open(JSON_OUTPUT, "w", encoding="utf-8") as f:
        json.dump({"version": 5, "rules": [{"ip_cidr": cidrs}]}, f, indent=2)
        f.write("\n")

    with open(LIST_OUTPUT, "w", encoding="utf-8") as f:
        for cidr in cidrs:
            f.write(f"IP-CIDR,{cidr},no-resolve\n")

    print(
        f"China routes: {len(chn_nets)}, extra ranges: {len(extra_nets)}, "
        f"merged+aggregated total: {len(cidrs)}"
    )


if __name__ == "__main__":
    main()
