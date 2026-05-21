"""
Network Architecture Scanner
Discovers all devices on the local network, port-scans each one,
assesses risk and draws an interactive topology map.
"""

import threading
import socket
import subprocess
import math
import re
import datetime
import tkinter as tk
import customtkinter as ctk
from dataclasses import dataclass, field
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from tkinter import filedialog

from src.gui.theme import (
    CLR_BG, CLR_SURFACE, CLR_SURFACE_ALT, CLR_SURFACE_HVR,
    CLR_ACCENT, CLR_ACCENT_HOV, CLR_BLUE,
    CLR_TEXT, CLR_TEXT_SEC, CLR_MUTED,
    CLR_SUCCESS, CLR_WARNING, CLR_DANGER, CLR_BORDER, CLR_DIVIDER,
    FONT_TITLE, FONT_HEADING, FONT_SUBHEAD, FONT_BODY, FONT_SMALL, FONT_CAPTION,
    PAD, PAD_SM, NAV_H, BTN_H, BTN_R,
)
from src.gui.screens.business_info import _header

# ── Port catalogue ────────────────────────────────────────────────────────────
SCAN_PORTS = [21, 22, 23, 25, 53, 80, 135, 139, 443, 445,
              1433, 3306, 3389, 5432, 8080, 8443]

PORT_INFO = {
    21:   ("FTP",        "HIGH",     "Unencrypted file transfer — use SFTP"),
    22:   ("SSH",        "INFO",     "Secure remote access"),
    23:   ("Telnet",     "CRITICAL", "Unencrypted remote access — disable now"),
    25:   ("SMTP",       "MEDIUM",   "Mail relay — verify not open to internet"),
    53:   ("DNS",        "INFO",     "DNS resolver"),
    80:   ("HTTP",       "LOW",      "Unencrypted web — redirect to HTTPS"),
    135:  ("MS-RPC",     "HIGH",     "Windows RPC — restrict to internal only"),
    139:  ("NetBIOS",    "HIGH",     "Legacy Windows sharing — disable if unused"),
    443:  ("HTTPS",      "INFO",     "Secure web server"),
    445:  ("SMB",        "CRITICAL", "Windows file sharing — prime ransomware vector"),
    1433: ("MS-SQL",     "HIGH",     "SQL Server exposed — restrict access"),
    3306: ("MySQL",      "HIGH",     "MySQL database exposed to network"),
    3389: ("RDP",        "CRITICAL", "Remote Desktop — critical ransomware risk"),
    5432: ("PostgreSQL", "HIGH",     "PostgreSQL database exposed"),
    8080: ("HTTP-alt",   "LOW",      "Alternative web server"),
    8443: ("HTTPS-alt",  "INFO",     "Alternative HTTPS server"),
}

RISK_COLOUR = {
    "CRITICAL": "#E84040",
    "HIGH":     "#E87000",
    "MEDIUM":   "#F0A500",
    "LOW":      "#78C840",
    "SAFE":     "#00C896",
    "SCANNING": "#5A7490",
    "UNKNOWN":  "#5A7490",
}

RISK_ORDER = {
    "CRITICAL": 5, "HIGH": 4, "MEDIUM": 3,
    "LOW": 2, "SAFE": 1, "UNKNOWN": 0, "SCANNING": 0,
}


# ── Data model ────────────────────────────────────────────────────────────────
@dataclass
class DeviceInfo:
    ip: str
    hostname: str = "Resolving…"
    mac: str = ""
    open_ports: list = field(default_factory=list)
    risk_level: str = "SCANNING"
    is_gateway: bool = False

    @property
    def risk_colour(self) -> str:
        return RISK_COLOUR.get(self.risk_level, "#5A7490")

    def compute_risk(self) -> None:
        if not self.open_ports:
            self.risk_level = "SAFE"
            return
        severities = [PORT_INFO.get(p, ("?", "LOW", ""))[1]
                      for p in self.open_ports]
        for level in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
            if level in severities:
                self.risk_level = level
                return
        self.risk_level = "SAFE"

    @property
    def risky_ports(self) -> list:
        return [p for p in self.open_ports
                if PORT_INFO.get(p, ("", "INFO", ""))[1]
                in ("CRITICAL", "HIGH")]

    def port_label(self) -> str:
        if not self.open_ports:
            return "No open ports"
        parts = []
        for p in sorted(self.open_ports):
            name = PORT_INFO.get(p, (str(p), "", ""))[0]
            parts.append(f"{p}/{name}")
        return "  ·  ".join(parts[:6]) + ("…" if len(self.open_ports) > 6 else "")


# ── Helper functions ──────────────────────────────────────────────────────────
def _get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 53))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"


def _get_subnet_prefix(ip: str) -> str:
    parts = ip.split(".")
    return ".".join(parts[:3])


def _resolve_hostname(ip: str) -> str:
    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return ip


def _get_arp_devices(prefix: str) -> dict:
    """Return {ip: mac} from the system ARP cache."""
    devices = {}
    try:
        result = subprocess.run(
            ["arp", "-a"], capture_output=True, text=True, timeout=5)
        for line in result.stdout.splitlines():
            m = re.search(
                r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
                r"\s+([\da-fA-F\-:]{11,17})",
                line)
            if m:
                ip, mac = m.group(1), m.group(2)
                if ip.startswith(prefix):
                    devices[ip] = mac
    except Exception:
        pass
    return devices


def _ping(ip: str, timeout_ms: int = 400) -> bool:
    try:
        result = subprocess.run(
            ["ping", "-n", "1", "-w", str(timeout_ms), ip],
            capture_output=True, timeout=3)
        return result.returncode == 0
    except Exception:
        return False


def _scan_port(ip: str, port: int, timeout: float = 0.6) -> bool:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        result = s.connect_ex((ip, port))
        s.close()
        return result == 0
    except Exception:
        return False


# ── Screen ────────────────────────────────────────────────────────────────────
class NetworkScannerScreen(ctk.CTkFrame):
    """Discover and assess all devices on the local network."""

    def __init__(self, master, on_back):
        super().__init__(master, fg_color=CLR_BG, corner_radius=0)
        self._on_back = on_back
        self._devices: dict[str, DeviceInfo] = {}
        self._scanning = False
        self._scan_total = 0
        self._scan_done = 0
        self._local_ip = _get_local_ip()
        self._gateway_ip = ""
        self._lock = threading.Lock()
        self._build()

    # ------------------------------------------------------------------ layout
    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        _header(self, "Network Architecture Scanner", "Tools", 0.0)

        # ── Scan controls bar ─────────────────────────────────────────
        ctrl = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0,
                            height=56)
        ctrl.grid(row=1, column=0, sticky="ew")
        ctrl.grid_columnconfigure(2, weight=1)
        ctrl.grid_propagate(False)

        self._subnet_var = ctk.StringVar(
            value=f"{_get_subnet_prefix(self._local_ip)}.0/24")
        ctk.CTkLabel(ctrl, text="Subnet:", font=FONT_SMALL,
                     text_color=CLR_MUTED,
                     ).grid(row=0, column=0, padx=(PAD, 6), pady=14)
        ctk.CTkEntry(
            ctrl, textvariable=self._subnet_var,
            font=FONT_BODY, fg_color=CLR_SURFACE_ALT,
            border_color=CLR_BORDER, border_width=1,
            text_color=CLR_TEXT, height=32, width=180, corner_radius=8,
        ).grid(row=0, column=1, pady=14)

        self._status_var = ctk.StringVar(
            value=f"Local IP: {self._local_ip}  ·  Ready to scan")
        ctk.CTkLabel(ctrl, textvariable=self._status_var,
                     font=FONT_CAPTION, text_color=CLR_MUTED,
                     ).grid(row=0, column=2, padx=PAD, sticky="w")

        self._progress = ctk.CTkProgressBar(
            ctrl, fg_color=CLR_DIVIDER, progress_color=CLR_ACCENT,
            height=3, corner_radius=0, width=200)
        self._progress.set(0)
        self._progress.grid(row=0, column=3, padx=(0, 12))

        self._scan_btn = ctk.CTkButton(
            ctrl, text="🔍  Scan Network",
            font=("Segoe UI", 12, "bold"),
            fg_color=CLR_ACCENT, hover_color=CLR_ACCENT_HOV,
            text_color="#000000", height=34, corner_radius=BTN_R,
            command=self._start_scan,
        )
        self._scan_btn.grid(row=0, column=4, padx=(0, PAD))

        # ── Main body: left canvas + right device list ────────────────
        body = ctk.CTkFrame(self, fg_color=CLR_BG, corner_radius=0)
        body.grid(row=2, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=0)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        # Left: topology canvas
        canvas_frame = ctk.CTkFrame(body, fg_color=CLR_SURFACE,
                                    corner_radius=0, width=460,
                                    border_width=0)
        canvas_frame.grid(row=0, column=0, sticky="nsew")
        canvas_frame.grid_propagate(False)
        canvas_frame.grid_rowconfigure(1, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(canvas_frame, text="Network Topology",
                     font=FONT_SUBHEAD, text_color=CLR_TEXT,
                     ).grid(row=0, column=0, padx=PAD, pady=(12, 0),
                            sticky="w")

        self._canvas = tk.Canvas(
            canvas_frame, bg=CLR_SURFACE,
            highlightthickness=0, cursor="hand2")
        self._canvas.grid(row=1, column=0, sticky="nsew",
                          padx=8, pady=(4, 8))
        self._canvas.bind("<Configure>", lambda _e: self._draw_topology())
        self._canvas.bind("<Button-1>", self._on_canvas_click)

        # Legend
        legend = ctk.CTkFrame(canvas_frame, fg_color=CLR_SURFACE_ALT,
                              corner_radius=8)
        legend.grid(row=2, column=0, padx=PAD, pady=(0, 12), sticky="ew")
        legend.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)
        for col, (label, clr) in enumerate([
            ("Safe",     RISK_COLOUR["SAFE"]),
            ("Low",      RISK_COLOUR["LOW"]),
            ("Medium",   RISK_COLOUR["MEDIUM"]),
            ("High",     RISK_COLOUR["HIGH"]),
            ("Critical", RISK_COLOUR["CRITICAL"]),
        ]):
            f = ctk.CTkFrame(legend, fg_color="transparent")
            f.grid(row=0, column=col, padx=6, pady=6)
            ctk.CTkFrame(f, fg_color=clr, width=10, height=10,
                         corner_radius=5).pack(side="left", padx=(0, 4))
            ctk.CTkLabel(f, text=label, font=FONT_CAPTION,
                         text_color=CLR_MUTED).pack(side="left")

        # Right: device cards list
        right = ctk.CTkFrame(body, fg_color=CLR_BG, corner_radius=0)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        # Summary bar
        self._summary_frame = ctk.CTkFrame(
            right, fg_color=CLR_SURFACE, corner_radius=0, height=56)
        self._summary_frame.grid(row=0, column=0, sticky="ew")
        self._summary_frame.grid_propagate(False)
        self._summary_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)
        self._build_summary_empty()

        self._scroll = ctk.CTkScrollableFrame(
            right, fg_color=CLR_BG, corner_radius=0)
        self._scroll.grid(row=1, column=0, sticky="nsew")
        self._scroll.grid_columnconfigure(0, weight=1)

        self._placeholder = ctk.CTkLabel(
            self._scroll,
            text="Click  🔍 Scan Network  to discover all devices\n"
                 "on your local network and assess their security posture.",
            font=FONT_BODY, text_color=CLR_MUTED, justify="center",
        )
        self._placeholder.grid(row=0, column=0, pady=60)

        # Nav
        nav = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0,
                           height=NAV_H)
        nav.grid(row=3, column=0, sticky="ew")
        nav.grid_columnconfigure(1, weight=1)
        nav.grid_propagate(False)

        ctk.CTkButton(
            nav, text="← Back", font=FONT_BODY,
            fg_color="transparent", border_color=CLR_BORDER, border_width=1,
            text_color=CLR_TEXT_SEC, hover_color=CLR_SURFACE_ALT,
            width=100, height=BTN_H, corner_radius=BTN_R,
            command=self._on_back,
        ).grid(row=0, column=0, padx=PAD, pady=14)

        self._export_btn = ctk.CTkButton(
            nav, text="📄  Export Report",
            font=FONT_SMALL,
            fg_color=CLR_SURFACE_ALT, hover_color=CLR_SURFACE_HVR,
            border_color=CLR_BORDER, border_width=1,
            text_color=CLR_TEXT_SEC,
            height=BTN_H, corner_radius=BTN_R,
            state="disabled", command=self._export_html,
        )
        self._export_btn.grid(row=0, column=2, padx=(0, PAD), pady=14)

    def _build_summary_empty(self):
        for w in self._summary_frame.winfo_children():
            w.destroy()
        ctk.CTkLabel(self._summary_frame,
                     text="No scan results yet",
                     font=FONT_SMALL, text_color=CLR_MUTED,
                     ).grid(row=0, column=0, columnspan=5,
                            padx=PAD, pady=18)

    def _build_summary(self):
        for w in self._summary_frame.winfo_children():
            w.destroy()
        total = len(self._devices)
        counts = {k: 0 for k in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "SAFE")}
        for d in self._devices.values():
            counts[d.risk_level] = counts.get(d.risk_level, 0) + 1

        for col, (label, val, clr) in enumerate([
            ("Devices",  str(total),              CLR_TEXT),
            ("Critical", str(counts["CRITICAL"]), RISK_COLOUR["CRITICAL"]),
            ("High",     str(counts["HIGH"]),      RISK_COLOUR["HIGH"]),
            ("Medium",   str(counts["MEDIUM"]),    RISK_COLOUR["MEDIUM"]),
            ("Safe",     str(counts["SAFE"] + counts.get("LOW", 0)),
             RISK_COLOUR["SAFE"]),
        ]):
            cell = ctk.CTkFrame(self._summary_frame,
                                fg_color="transparent")
            cell.grid(row=0, column=col, padx=8, pady=10)
            ctk.CTkLabel(cell, text=val,
                         font=("Segoe UI", 18, "bold"),
                         text_color=clr).pack()
            ctk.CTkLabel(cell, text=label,
                         font=FONT_CAPTION,
                         text_color=CLR_MUTED).pack()

    # ------------------------------------------------------------------ scan
    def _start_scan(self):
        if self._scanning:
            return
        self._scanning = True
        self._devices.clear()
        self._scan_done = 0
        self._scan_total = 0
        self._scan_btn.configure(state="disabled", text="Scanning…")
        self._export_btn.configure(state="disabled")
        self._progress.set(0)
        self._status_var.set("Discovering devices…")
        for w in self._scroll.winfo_children():
            w.destroy()
        self._draw_topology()
        threading.Thread(target=self._run_scan, daemon=True).start()

    def _run_scan(self):
        # Step 1: Get ARP cache (instant) + detect gateway
        local_ip = self._local_ip
        prefix = _get_subnet_prefix(local_ip)

        # Guess gateway (usually .1)
        self._gateway_ip = f"{prefix}.1"
        arp_devices = _get_arp_devices(prefix)

        # Always include gateway and local machine
        seed_ips = set(arp_devices.keys())
        seed_ips.add(self._gateway_ip)
        seed_ips.add(local_ip)

        # Step 2: Ping sweep to find more live hosts
        self.after(0, self._status_var.set,
                   f"Pinging {prefix}.0/24 …  ({len(seed_ips)} known devices)")

        # Ping common host range (1-50 + known from ARP)
        ping_targets = set(range(1, 51))
        for ip in seed_ips:
            try:
                last = int(ip.split(".")[-1])
                ping_targets.add(last)
            except ValueError:
                pass

        live_ips = set(seed_ips)
        with ThreadPoolExecutor(max_workers=30) as ex:
            futures = {
                ex.submit(_ping, f"{prefix}.{i}", 350): i
                for i in ping_targets
            }
            for fut in as_completed(futures):
                octet = futures[fut]
                try:
                    if fut.result():
                        live_ips.add(f"{prefix}.{octet}")
                except Exception:
                    pass

        self._scan_total = len(live_ips)
        self.after(0, self._status_var.set,
                   f"Scanning {self._scan_total} live devices…")

        # Step 3: Port-scan each live IP in parallel
        with ThreadPoolExecutor(max_workers=12) as ex:
            futures = {
                ex.submit(self._scan_device, ip,
                          arp_devices.get(ip, ""),
                          ip == local_ip,
                          ip == self._gateway_ip): ip
                for ip in live_ips
            }
            for fut in as_completed(futures):
                try:
                    device = fut.result()
                    with self._lock:
                        self._devices[device.ip] = device
                        self._scan_done += 1
                    pct = self._scan_done / max(self._scan_total, 1)
                    self.after(0, self._progress.set, pct)
                    self.after(0, self._on_device_found, device)
                except Exception:
                    pass

        self.after(0, self._scan_complete)

    def _scan_device(self, ip: str, mac: str,
                     is_self: bool, is_gateway: bool) -> DeviceInfo:
        dev = DeviceInfo(ip=ip, mac=mac, is_gateway=is_gateway)
        dev.hostname = _resolve_hostname(ip)

        # Port scan
        with ThreadPoolExecutor(max_workers=8) as ex:
            futs = {ex.submit(_scan_port, ip, port): port
                    for port in SCAN_PORTS}
            for fut in as_completed(futs):
                port = futs[fut]
                try:
                    if fut.result():
                        dev.open_ports.append(port)
                except Exception:
                    pass

        dev.open_ports.sort()
        if is_gateway:
            dev.risk_level = "LOW" if dev.open_ports else "SAFE"
        else:
            dev.compute_risk()
        return dev

    def _on_device_found(self, device: DeviceInfo):
        """Called on the UI thread each time a device completes scanning."""
        self._status_var.set(
            f"Scanned {self._scan_done} / {self._scan_total}  ·  "
            f"Found {len(self._devices)} device(s)")
        self._refresh_device_card(device)
        self._draw_topology()

    def _scan_complete(self):
        self._scanning = False
        self._scan_btn.configure(state="normal", text="🔍  Rescan")
        self._export_btn.configure(state="normal")
        self._progress.set(1.0)
        critical = sum(1 for d in self._devices.values()
                       if d.risk_level == "CRITICAL")
        high = sum(1 for d in self._devices.values()
                   if d.risk_level == "HIGH")
        self._status_var.set(
            f"Scan complete  ·  {len(self._devices)} devices  ·  "
            f"{critical} critical  ·  {high} high risk")
        self._build_summary()
        self._draw_topology()

    # ---------------------------------------------------------------- UI update
    def _refresh_device_card(self, device: DeviceInfo):
        """Add or refresh the device's card in the scroll list."""
        tag = f"card_{device.ip.replace('.', '_')}"
        risk_clr = device.risk_colour
        is_local = device.ip == self._local_ip

        # Remove existing card for this IP
        existing = getattr(self, f"_card_{tag}", None)
        if existing:
            try:
                existing.destroy()
            except Exception:
                pass

        # Hide placeholder
        if hasattr(self, "_placeholder") and self._placeholder.winfo_exists():
            self._placeholder.grid_remove()

        # Determine row position (sorted by risk severity desc, then IP)
        row_idx = sorted(
            self._devices.values(),
            key=lambda d: (-RISK_ORDER.get(d.risk_level, 0),
                           [int(x) for x in d.ip.split(".")])
        ).index(device)

        card = ctk.CTkFrame(self._scroll, fg_color=CLR_SURFACE,
                            corner_radius=12, border_width=1,
                            border_color=CLR_BORDER)
        card.grid(row=row_idx, column=0, padx=PAD_SM,
                  pady=3, sticky="ew")
        card.grid_columnconfigure(1, weight=1)

        # Risk stripe
        ctk.CTkFrame(card, fg_color=risk_clr, width=5,
                     corner_radius=0).grid(row=0, column=0,
                                           rowspan=3, sticky="ns")

        # IP + hostname
        lbl = (f"{device.hostname}"
               + (" (This device)" if is_local else "")
               + ("  🌐 Gateway" if device.is_gateway else ""))
        ctk.CTkLabel(card, text=lbl, font=FONT_SUBHEAD,
                     text_color=CLR_TEXT, anchor="w",
                     ).grid(row=0, column=1, padx=(10, 8),
                            pady=(10, 1), sticky="w")

        ctk.CTkLabel(card, text=device.ip,
                     font=FONT_CAPTION, text_color=CLR_MUTED, anchor="w",
                     ).grid(row=1, column=1, padx=(10, 8),
                            pady=(0, 1), sticky="w")

        # Ports
        port_txt = device.port_label()
        ctk.CTkLabel(card, text=port_txt,
                     font=FONT_CAPTION, text_color=CLR_TEXT_SEC, anchor="w",
                     wraplength=380,
                     ).grid(row=2, column=1, padx=(10, 8),
                            pady=(0, 10), sticky="w")

        # Risk badge
        ctk.CTkLabel(card,
                     text=device.risk_level,
                     font=("Segoe UI", 9, "bold"), text_color=risk_clr,
                     fg_color=CLR_SURFACE_ALT, corner_radius=8,
                     width=72, height=22,
                     ).grid(row=0, column=2, padx=(0, 10), pady=(10, 2))

        # MAC
        if device.mac:
            ctk.CTkLabel(card, text=device.mac,
                         font=FONT_CAPTION, text_color=CLR_MUTED,
                         ).grid(row=1, column=2, padx=(0, 10), pady=(0, 2))

        # Expand button
        ctk.CTkButton(
            card, text="Details", font=FONT_CAPTION,
            fg_color="transparent", hover_color=CLR_SURFACE_HVR,
            border_color=CLR_BORDER, border_width=1,
            text_color=CLR_TEXT_SEC,
            width=64, height=24, corner_radius=6,
            command=lambda d=device: self._show_device_details(d),
        ).grid(row=2, column=2, padx=(0, 10), pady=(0, 10))

        setattr(self, f"_card_{tag}", card)

    # -------------------------------------------------------------- topology
    def _draw_topology(self):
        c = self._canvas
        try:
            W = c.winfo_width() or 450
            H = c.winfo_height() or 400
        except Exception:
            return
        c.delete("all")

        if not self._devices:
            c.create_text(W // 2, H // 2,
                          text="Scan the network to see the topology",
                          font=("Segoe UI", 11), fill=CLR_MUTED)
            return

        cx, cy = W // 2, 60

        # Draw gateway
        gw = self._devices.get(self._gateway_ip)
        gw_clr = gw.risk_colour if gw else CLR_BLUE
        self._draw_node(c, cx, cy, 26, gw_clr,
                        "🌐", "Gateway", self._gateway_ip)

        # Arrange device nodes in rows
        devices = [d for d in self._devices.values()
                   if not d.is_gateway]
        devices.sort(key=lambda d: (
            -RISK_ORDER.get(d.risk_level, 0),
            [int(x) for x in d.ip.split(".")]))

        cols = max(1, min(6, W // 80))
        row_h = 80
        col_w = min(80, (W - 40) // cols)

        for idx, dev in enumerate(devices):
            row = idx // cols
            col = idx % cols
            n_in_row = min(cols, len(devices) - row * cols)
            start_x = cx - (n_in_row - 1) * col_w / 2
            dx = int(start_x + col * col_w)
            dy = int(cy + 80 + row * row_h)

            # Connector line
            c.create_line(cx, cy + 28, dx, dy - 20,
                          fill=CLR_BORDER, width=1, dash=(4, 3))

            # Node
            last_octet = dev.ip.split(".")[-1]
            short_host = (dev.hostname.split(".")[0][:8]
                          if dev.hostname != dev.ip else "")
            self._draw_node(c, dx, dy, 20, dev.risk_colour,
                            f".{last_octet}", short_host, dev.ip)

    def _draw_node(self, canvas, x, y, r, colour, line1,
                   line2="", tooltip_ip=""):
        # Outer glow ring
        canvas.create_oval(x - r - 3, y - r - 3,
                           x + r + 3, y + r + 3,
                           fill="", outline=colour, width=1.5)
        # Filled circle
        canvas.create_oval(x - r, y - r, x + r, y + r,
                           fill=colour, outline="")
        # Labels
        canvas.create_text(x, y, text=line1,
                           font=("Segoe UI", 8, "bold"), fill="#0B1622")
        if line2:
            canvas.create_text(x, y + r + 9, text=line2,
                               font=("Segoe UI", 7), fill=CLR_TEXT_SEC)
        # Store hitbox data for click detection
        tag = f"node_{tooltip_ip.replace('.', '_')}"
        canvas.create_oval(x - r, y - r, x + r, y + r,
                           fill="", outline="", tags=tag)
        canvas.tag_bind(tag, "<Button-1>",
                        lambda e, ip=tooltip_ip: self._on_node_click(ip))

    def _on_canvas_click(self, _event):
        pass  # Handled by individual node tags

    def _on_node_click(self, ip: str):
        device = self._devices.get(ip)
        if device:
            self._show_device_details(device)

    # --------------------------------------------------------- details dialog
    def _show_device_details(self, device: DeviceInfo):
        dlg = ctk.CTkToplevel(self)
        dlg.title(f"Device Details — {device.ip}")
        dlg.geometry("560x520")
        dlg.configure(fg_color=CLR_BG)
        dlg.grab_set()

        risk_clr = device.risk_colour

        # Header
        hdr = ctk.CTkFrame(dlg, fg_color=CLR_SURFACE, corner_radius=0,
                           height=64)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkFrame(hdr, fg_color=risk_clr, width=5,
                     corner_radius=0).pack(side="left", fill="y")
        ctk.CTkLabel(hdr,
                     text=f"{device.hostname}  ({device.ip})",
                     font=FONT_SUBHEAD, text_color=CLR_TEXT,
                     ).pack(side="left", padx=14, pady=18)
        ctk.CTkLabel(hdr,
                     text=device.risk_level,
                     font=("Segoe UI", 10, "bold"), text_color=risk_clr,
                     ).pack(side="right", padx=14)

        scroll = ctk.CTkScrollableFrame(dlg, fg_color=CLR_BG,
                                        corner_radius=0)
        scroll.pack(fill="both", expand=True)
        scroll.grid_columnconfigure(0, weight=1)

        # Info card
        info = ctk.CTkFrame(scroll, fg_color=CLR_SURFACE,
                            corner_radius=12, border_width=1,
                            border_color=CLR_BORDER)
        info.grid(row=0, column=0, padx=12, pady=(10, 6), sticky="ew")
        info.grid_columnconfigure(1, weight=1)

        for row_i, (label, val) in enumerate([
            ("IP Address",    device.ip),
            ("Hostname",      device.hostname),
            ("MAC Address",   device.mac or "—"),
            ("Risk Level",    device.risk_level),
            ("Type",          "Gateway" if device.is_gateway else "Host"),
            ("Open Ports",    str(len(device.open_ports))),
        ]):
            ctk.CTkLabel(info, text=label + ":",
                         font=("Segoe UI", 10, "bold"),
                         text_color=CLR_MUTED, width=110, anchor="w",
                         ).grid(row=row_i, column=0,
                                padx=(14, 6), pady=4, sticky="w")
            clr = risk_clr if label == "Risk Level" else CLR_TEXT
            ctk.CTkLabel(info, text=val,
                         font=FONT_SMALL, text_color=clr, anchor="w",
                         ).grid(row=row_i, column=1,
                                padx=(0, 14), pady=4, sticky="w")

        # Port findings
        if device.open_ports:
            ctk.CTkLabel(scroll, text="Port Findings",
                         font=FONT_SUBHEAD, text_color=CLR_TEXT,
                         ).grid(row=1, column=0, padx=12,
                                pady=(10, 4), sticky="w")

            for pi, port in enumerate(sorted(device.open_ports)):
                name, severity, desc = PORT_INFO.get(
                    port, (str(port), "INFO", "Unknown service"))
                sev_clr = RISK_COLOUR.get(severity, CLR_MUTED)

                pf = ctk.CTkFrame(scroll, fg_color=CLR_SURFACE,
                                  corner_radius=10, border_width=1,
                                  border_color=CLR_BORDER)
                pf.grid(row=2 + pi, column=0, padx=12,
                        pady=3, sticky="ew")
                pf.grid_columnconfigure(1, weight=1)

                ctk.CTkFrame(pf, fg_color=sev_clr, width=4,
                             corner_radius=0).grid(row=0, column=0,
                                                   sticky="ns")
                ctk.CTkLabel(pf,
                             text=f"{port}/{name}",
                             font=("Segoe UI", 11, "bold"),
                             text_color=sev_clr, width=110, anchor="w",
                             ).grid(row=0, column=1,
                                    padx=(10, 6), pady=8, sticky="w")
                ctk.CTkLabel(pf,
                             text=f"[{severity}]  {desc}",
                             font=FONT_CAPTION, text_color=CLR_TEXT_SEC,
                             anchor="w",
                             ).grid(row=0, column=2,
                                    padx=(0, 12), pady=8, sticky="w")
        else:
            ctk.CTkLabel(scroll,
                         text="✔  No open ports detected — device appears secure",
                         font=FONT_SMALL, text_color=CLR_SUCCESS,
                         ).grid(row=1, column=0, padx=12,
                                pady=10, sticky="w")

        # Recommendations
        recs = self._device_recommendations(device)
        if recs:
            ctk.CTkLabel(scroll, text="Recommendations",
                         font=FONT_SUBHEAD, text_color=CLR_TEXT,
                         ).grid(row=2 + len(device.open_ports),
                                column=0, padx=12, pady=(10, 4), sticky="w")
            for ri, rec in enumerate(recs):
                rf = ctk.CTkFrame(scroll, fg_color=CLR_SURFACE,
                                  corner_radius=8)
                rf.grid(row=3 + len(device.open_ports) + ri,
                        column=0, padx=12, pady=2, sticky="ew")
                rf.grid_columnconfigure(1, weight=1)
                ctk.CTkLabel(rf, text="→", font=FONT_BODY,
                             text_color=CLR_ACCENT, width=20,
                             ).grid(row=0, column=0, padx=(10, 4), pady=8)
                ctk.CTkLabel(rf, text=rec, font=FONT_CAPTION,
                             text_color=CLR_TEXT_SEC, wraplength=440,
                             justify="left", anchor="w",
                             ).grid(row=0, column=1,
                                    padx=(0, 10), pady=8, sticky="w")

        ctk.CTkButton(dlg, text="Close",
                      height=BTN_H, corner_radius=BTN_R,
                      fg_color=CLR_SURFACE_ALT, hover_color=CLR_BORDER,
                      text_color=CLR_TEXT, font=FONT_BODY,
                      command=dlg.destroy,
                      ).pack(pady=10)

    # ------------------------------------------------------ recommendations
    def _device_recommendations(self, device: DeviceInfo) -> list:
        recs = []
        if 23 in device.open_ports:
            recs.append("Disable Telnet (port 23) immediately — use SSH instead.")
        if 445 in device.open_ports:
            recs.append("SMB (port 445) is open — disable if not needed or restrict "
                        "to trusted IPs. This is the primary ransomware entry point.")
        if 3389 in device.open_ports:
            recs.append("RDP (port 3389) is exposed — enable Network Level "
                        "Authentication, restrict to a VPN, and use strong passwords.")
        if 135 in device.open_ports or 139 in device.open_ports:
            recs.append("Windows RPC/NetBIOS ports are open — restrict access "
                        "using Windows Firewall rules.")
        for p in (3306, 5432, 1433):
            if p in device.open_ports:
                name = PORT_INFO[p][0]
                recs.append(f"{name} (port {p}) is network-accessible — bind the "
                             f"database to localhost only unless remote access is required.")
        if 21 in device.open_ports:
            recs.append("FTP (port 21) transmits data unencrypted — replace with SFTP.")
        if 80 in device.open_ports and 443 not in device.open_ports:
            recs.append("HTTP (port 80) is open but HTTPS (443) is not — "
                        "configure a valid TLS certificate.")
        if not device.open_ports:
            recs.append("No open ports detected — ensure firewall rules are in place "
                        "and review regularly.")
        return recs

    # -------------------------------------------------------------- export
    def _export_html(self):
        if not self._devices:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML Report", "*.html"), ("All files", "*.*")],
            initialfile=f"network_scan_{datetime.date.today().isoformat()}.html",
        )
        if not path:
            return

        rows_html = ""
        for dev in sorted(self._devices.values(),
                          key=lambda d: (
                              -RISK_ORDER.get(d.risk_level, 0),
                              [int(x) for x in d.ip.split(".")])):
            rc = dev.risk_colour
            ports_txt = dev.port_label()
            rows_html += (
                f"<tr>"
                f"<td style='color:{rc};font-weight:bold'>"
                f"{dev.risk_level}</td>"
                f"<td>{dev.ip}</td>"
                f"<td>{dev.hostname}</td>"
                f"<td>{dev.mac or '—'}</td>"
                f"<td style='font-size:11px'>{ports_txt}</td>"
                f"</tr>"
            )

        critical = sum(1 for d in self._devices.values()
                       if d.risk_level == "CRITICAL")
        high = sum(1 for d in self._devices.values()
                   if d.risk_level == "HIGH")

        html = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8">
<title>Network Security Scan — {datetime.date.today()}</title>
<style>
 body{{font-family:'Segoe UI',sans-serif;background:#0B1622;
  color:#ECF4FF;margin:0;padding:32px}}
 h1{{color:#00C896}} h2{{color:#2485E8;border-bottom:1px solid #1A2D42;
  padding-bottom:6px}}
 .summary{{display:grid;grid-template-columns:repeat(4,1fr);
  gap:16px;margin-bottom:28px}}
 .card{{background:#132236;border-radius:12px;padding:20px;
  text-align:center}}
 .big{{font-size:36px;font-weight:bold}}
 table{{width:100%;border-collapse:collapse;background:#132236;
  border-radius:10px;overflow:hidden}}
 th{{background:#1A2D42;padding:10px 14px;text-align:left;
  font-size:11px;color:#5A7490;text-transform:uppercase}}
 td{{padding:10px 14px;border-bottom:1px solid #0B1622;font-size:12px}}
 footer{{margin-top:40px;color:#5A7490;font-size:10px;text-align:center}}
</style></head><body>
<h1>🌐 Network Security Scan Report</h1>
<p style="color:#5A7490">Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}
  &nbsp;·&nbsp; Subnet: {self._subnet_var.get()}</p>
<div class="summary">
 <div class="card">
  <div class="big" style="color:#ECF4FF">{len(self._devices)}</div>
  <div style="color:#5A7490">Devices Found</div>
 </div>
 <div class="card">
  <div class="big" style="color:{RISK_COLOUR['CRITICAL']}">{critical}</div>
  <div style="color:#5A7490">Critical Risk</div>
 </div>
 <div class="card">
  <div class="big" style="color:{RISK_COLOUR['HIGH']}">{high}</div>
  <div style="color:#5A7490">High Risk</div>
 </div>
 <div class="card">
  <div class="big" style="color:#00C896">
   {sum(1 for d in self._devices.values() if d.risk_level in ("SAFE","LOW"))}
  </div>
  <div style="color:#5A7490">Safe / Low Risk</div>
 </div>
</div>
<h2>Device Inventory</h2>
<table>
 <thead><tr>
  <th>Risk</th><th>IP Address</th><th>Hostname</th>
  <th>MAC</th><th>Open Ports</th>
 </tr></thead>
 <tbody>{rows_html}</tbody>
</table>
<footer>Zambia Digital Hygiene Certification Programme
  · Network Architecture Scanner
  · University of Zambia</footer>
</body></html>"""

        with open(path, "w", encoding="utf-8") as f:
            f.write(html)

        try:
            import os
            os.startfile(path)  # type: ignore
        except AttributeError:
            import subprocess as sp
            sp.Popen(["xdg-open", path])

        dlg = ctk.CTkToplevel(self)
        dlg.title("Saved")
        dlg.geometry("400x120")
        dlg.resizable(False, False)
        dlg.configure(fg_color=CLR_SURFACE)
        dlg.grab_set()
        ctk.CTkLabel(dlg, text="✔  Network report saved!",
                     font=FONT_SUBHEAD, text_color=CLR_SUCCESS,
                     ).pack(pady=(20, 4))
        ctk.CTkLabel(dlg, text=path, font=FONT_CAPTION,
                     text_color=CLR_MUTED, wraplength=370,
                     ).pack(pady=(0, 12))
        ctk.CTkButton(dlg, text="OK",
                      fg_color=CLR_ACCENT, text_color="#000000",
                      height=BTN_H, corner_radius=BTN_R,
                      command=dlg.destroy).pack()
