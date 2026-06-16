"""Infrastructure scanner: port and TLS checks for external hosts."""
from __future__ import annotations

import socket
import ssl
from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class PortCheck:
    port: int
    open: bool
    banner: str | None = None


@dataclass
class TLSCheck:
    port: int
    valid: bool
    expires: str | None = None
    subject: str | None = None
    cipher: str | None = None


def scan_ports(host: str, ports: List[int], timeout: float = 0.5) -> List[PortCheck]:
    results: List[PortCheck] = []
    for p in ports:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(timeout)
                r = s.connect_ex((host, p))
                if r == 0:
                    try:
                        s.sendall(b"\r\n")
                        banner = s.recv(1024).decode('utf-8', errors='ignore').strip()
                    except Exception:
                        banner = None
                    results.append(PortCheck(port=p, open=True, banner=banner))
                else:
                    results.append(PortCheck(port=p, open=False))
        except Exception:
            results.append(PortCheck(port=p, open=False))
    return results


def check_tls(host: str, port: int = 443, timeout: float = 3.0) -> TLSCheck:
    ctx = ssl.create_default_context()
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssl_sock:
                cert = ssl_sock.getpeercert()
                cipher_info = ssl_sock.cipher()
                cipher = cipher_info[0] if cipher_info else None
                if not cert:
                    return TLSCheck(port=port, valid=True, cipher=cipher)
                not_after: str | None = (
                    str(cert['notAfter']) if 'notAfter' in cert else None
                )
                subject_cn: str | None = None
                for rdn in cert.get('subject', ()):
                    for attr, val in rdn:
                        if attr == 'commonName':
                            subject_cn = str(val)
                return TLSCheck(
                    port=port, valid=True,
                    expires=not_after, subject=subject_cn, cipher=cipher,
                )
    except Exception:
        return TLSCheck(port=port, valid=False)


def scan_host_services(host: str, ports: List[int] | None = None) -> Dict[str, Any]:
    if ports is None:
        ports = [80, 443, 22, 3389, 3306, 5432]
    port_results = scan_ports(host, ports)
    tls = None
    if any(p.port == 443 and p.open for p in port_results):
        tls = check_tls(host, 443)

    return {
        'host': host,
        'ports': [p.__dict__ for p in port_results],
        'tls': tls.__dict__ if tls else None,
    }
