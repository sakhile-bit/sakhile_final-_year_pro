"""CLI tools to run agent and infra scanner locally."""
from __future__ import annotations

import argparse
import json
from src.agents.windows_agent import collect_local_report
from src.security.infra_scanner import scan_host_services


def main():
    p = argparse.ArgumentParser(description='Agent utilities')
    sp = p.add_subparsers(dest='cmd')

    a_agent = sp.add_parser('agent', help='Run local Windows agent')
    a_agent.add_argument('--name', default='local-host')

    a_scan = sp.add_parser('scan', help='Scan host services')
    a_scan.add_argument('host')
    a_scan.add_argument('--ports', help='Comma separated ports', default='80,443')

    args = p.parse_args()
    if args.cmd == 'agent':
        r = collect_local_report(args.name)
        print(json.dumps(r['report'], indent=2))
    elif args.cmd == 'scan':
        ports = [int(p.strip()) for p in args.ports.split(',') if p.strip()]
        r = scan_host_services(args.host, ports)
        print(json.dumps(r, indent=2))
    else:
        p.print_help()


if __name__ == '__main__':
    main()
