"""
Fleet Scan Screen — distributed multi-node scanning
Runs from the master node: loads a node inventory, triggers a
digital-hygiene + hardening scan on every connected node concurrently,
and shows a fleet-wide grade governed by the weakest reachable machine.
"""

import datetime
import threading
from tkinter import filedialog

import customtkinter as ctk

from src.gui.screens.business_info import _header
from src.gui.screens._cancellable import CancellableScreenMixin
from src.gui.theme import (
    BTN_H,
    BTN_R,
    CLR_ACCENT,
    CLR_ACCENT_HOV,
    CLR_BG,
    CLR_BLUE,
    CLR_BORDER,
    CLR_DANGER,
    CLR_DIVIDER,
    CLR_MUTED,
    CLR_SUCCESS,
    CLR_SURFACE,
    CLR_SURFACE_ALT,
    CLR_SURFACE_HVR,
    CLR_TEXT,
    CLR_TEXT_SEC,
    CLR_WARNING,
    FONT_BODY,
    FONT_CAPTION,
    FONT_HEADING,
    FONT_SMALL,
    FONT_SUBHEAD,
    NAV_H,
    PAD,
)
from src.agents.master_coordinator import (
    DEFAULT_PORT,
    DEFAULT_SCHEME,
    FleetReport,
    Node,
    discover_nodes,
    local_ipv4,
    scan_fleet,
)

GRADE_STYLE = {
    "HARDENED": {
        "icon": "🛡️", "colour": CLR_SUCCESS, "title": "FLEET HARDENED",
        "msg": "Every reachable node meets server-grade hygiene standards. "
               "The infrastructure behind your services is sound.",
    },
    "NEEDS ATTENTION": {
        "icon": "⚠️", "colour": CLR_WARNING, "title": "FLEET NEEDS ATTENTION",
        "msg": "The weakest reachable node has hardening gaps. A business is "
               "only as safe as its least hygienic machine — fix the weakest "
               "link first.",
    },
    "AT RISK": {
        "icon": "🚨", "colour": CLR_DANGER, "title": "FLEET AT RISK",
        "msg": "At least one reachable node is seriously exposed. Users of "
               "every service on this network are at risk until it is fixed.",
    },
    "INCOMPLETE": {
        "icon": "❓", "colour": CLR_WARNING, "title": "FLEET INCOMPLETE",
        "msg": "One or more nodes could not be reached. An unknown node is an "
               "unmanaged risk — bring every node online before certifying "
               "the fleet.",
    },
    "NO DATA": {
        "icon": "ℹ️", "colour": CLR_MUTED, "title": "NO DATA",
        "msg": "No node could be scanned. Check that the node agents are "
               "running and the inventory tokens are correct.",
    },
}

STATUS_STYLE = {
    "online":       ("●", CLR_SUCCESS),
    "offline":      ("○", CLR_DANGER),
    "unauthorized": ("⚠", CLR_WARNING),
    "error":        ("!", CLR_DANGER),
    "busy":         ("◐", CLR_WARNING),
}

NODE_GRADE_CLR = {
    "HARDENED": CLR_SUCCESS,
    "NEEDS ATTENTION": CLR_WARNING,
    "AT RISK": CLR_DANGER,
}


class FleetScanScreen(CancellableScreenMixin, ctk.CTkFrame):
    """Master-node screen: scan a fleet of connected nodes."""

    def __init__(self, master, on_back):
        super().__init__(master, fg_color=CLR_BG, corner_radius=0)
        self._on_back = on_back
        self._scanning = False
        self._discovering = False
        self._report: FleetReport | None = None
        self._nodes = []
        # Discovered / manually-added candidate nodes, each a dict with a
        # BooleanVar for its checkbox. Keyed by url to dedupe.
        self._entries: dict[str, dict] = {}
        self._token_var = ctk.StringVar(value="")
        self._port_var = ctk.StringVar(value=str(DEFAULT_PORT))
        self._manual_var = ctk.StringVar(value="")
        self._build()

    # ------------------------------------------------------------------ build
    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        _header(self, "Fleet Scan — Multi-Node", "Tools", 0.0)

        # ── Controls bar: token + port + discover + scan ──────────────
        ctrl = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0,
                            height=58)
        ctrl.grid(row=1, column=0, sticky="ew")
        ctrl.grid_columnconfigure(1, weight=1)
        ctrl.grid_propagate(False)

        ctk.CTkLabel(ctrl, text="Token:", font=FONT_SMALL,
                     text_color=CLR_MUTED,
                     ).grid(row=0, column=0, padx=(PAD, 6), pady=14)
        ctk.CTkEntry(
            ctrl, textvariable=self._token_var, show="•",
            placeholder_text="shared node-agent secret",
            font=FONT_SMALL, fg_color=CLR_SURFACE_ALT,
            border_color=CLR_BORDER, border_width=1,
            text_color=CLR_TEXT, height=32, corner_radius=8,
        ).grid(row=0, column=1, padx=(0, 8), pady=14, sticky="ew")

        ctk.CTkLabel(ctrl, text="Port:", font=FONT_SMALL,
                     text_color=CLR_MUTED,
                     ).grid(row=0, column=2, padx=(0, 6), pady=14)
        ctk.CTkEntry(
            ctrl, textvariable=self._port_var, width=64,
            font=FONT_SMALL, fg_color=CLR_SURFACE_ALT,
            border_color=CLR_BORDER, border_width=1,
            text_color=CLR_TEXT, height=32, corner_radius=8,
        ).grid(row=0, column=3, padx=(0, 8), pady=14)

        self._discover_btn = ctk.CTkButton(
            ctrl, text="🔍  Discover", font=("Segoe UI", 12, "bold"),
            fg_color=CLR_SURFACE_ALT, hover_color=CLR_SURFACE_HVR,
            border_color=CLR_BORDER, border_width=1, text_color=CLR_TEXT,
            height=34, corner_radius=BTN_R, width=110,
            command=self._start_discovery,
        )
        self._discover_btn.grid(row=0, column=4, padx=(0, 8), pady=14)

        self._scan_btn = ctk.CTkButton(
            ctrl, text="▶  Scan Selected",
            font=("Segoe UI", 12, "bold"),
            fg_color=CLR_ACCENT, hover_color=CLR_ACCENT_HOV,
            text_color="#FFFFFF", height=34, corner_radius=BTN_R,
            state="disabled", command=self._start_scan,
        )
        self._scan_btn.grid(row=0, column=5, padx=(0, PAD), pady=14)

        # ── Body ──────────────────────────────────────────────────────
        body = ctk.CTkScrollableFrame(self, fg_color=CLR_BG, corner_radius=0)
        body.grid(row=2, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        self._body = body

        self._progress = ctk.CTkProgressBar(
            self, fg_color=CLR_DIVIDER, progress_color=CLR_ACCENT,
            height=3, corner_radius=0)
        self._progress.set(0)
        self._progress.grid(row=2, column=0, sticky="new")
        self._progress.grid_remove()

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
            nav, text="📄  Export Report", font=FONT_SMALL,
            fg_color=CLR_SURFACE_ALT, hover_color=CLR_SURFACE_HVR,
            border_color=CLR_BORDER, border_width=1, text_color=CLR_TEXT_SEC,
            height=BTN_H, corner_radius=BTN_R,
            state="disabled", command=self._export_html,
        )
        self._export_btn.grid(row=0, column=2, padx=(0, PAD), pady=14)

        self._render_selection()

    # -------------------------------------------------------- node selection
    def _port(self) -> int:
        try:
            return int(self._port_var.get().strip())
        except (TypeError, ValueError):
            return DEFAULT_PORT

    def _render_selection(self):
        """Draw the discover/select view (candidate nodes with checkboxes)."""
        for w in self._body.winfo_children():
            w.destroy()

        row = 0
        subnet = local_ipv4()
        subnet_txt = (f"Your network: {'.'.join(subnet.split('.')[:3])}.0/24"
                      if subnet else "Network subnet could not be determined")
        ctk.CTkLabel(
            self._body,
            text=f"🔍  Auto-detect node agents on your network and pick which "
                 f"to scan.   ({subnet_txt})",
            font=FONT_SMALL, text_color=CLR_MUTED, anchor="w", justify="left",
            wraplength=820,
        ).grid(row=row, column=0, padx=PAD, pady=(PAD, 6), sticky="w")
        row += 1

        # Select-all + count header (only when we have candidates)
        if self._entries:
            hdr = ctk.CTkFrame(self._body, fg_color="transparent")
            hdr.grid(row=row, column=0, padx=PAD, pady=(2, 4), sticky="ew")
            hdr.grid_columnconfigure(1, weight=1)
            self._select_all_var = ctk.BooleanVar(value=True)
            ctk.CTkCheckBox(
                hdr, text="Select all", variable=self._select_all_var,
                font=FONT_SMALL, text_color=CLR_TEXT_SEC,
                fg_color=CLR_ACCENT, hover_color=CLR_ACCENT_HOV,
                checkbox_width=18, checkbox_height=18,
                command=self._toggle_all,
            ).grid(row=0, column=0, sticky="w")
            self._count_lbl = ctk.CTkLabel(
                hdr, text="", font=FONT_CAPTION, text_color=CLR_MUTED)
            self._count_lbl.grid(row=0, column=2, sticky="e")
            row += 1

            for url, entry in self._entries.items():
                self._render_node_row(row, entry)
                row += 1
        else:
            ctk.CTkLabel(
                self._body,
                text="No nodes yet.\n\nClick  🔍 Discover  to find node agents "
                     "running on your network,\nor add one manually below.\n\n"
                     "On each node run:  cli.py node-agent --port 8765 --token <secret>",
                font=FONT_BODY, text_color=CLR_MUTED, justify="center",
            ).grid(row=row, column=0, pady=36)
            row += 1

        # Manual add row
        add = ctk.CTkFrame(self._body, fg_color=CLR_SURFACE, corner_radius=12,
                           border_width=1, border_color=CLR_BORDER)
        add.grid(row=row, column=0, padx=PAD, pady=(10, PAD), sticky="ew")
        add.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(add, text="Add host:", font=FONT_SMALL,
                     text_color=CLR_TEXT_SEC,
                     ).grid(row=0, column=0, padx=(12, 6), pady=10)
        ctk.CTkEntry(
            add, textvariable=self._manual_var,
            placeholder_text="e.g.  192.168.1.50   or   192.168.1.50:8765",
            font=FONT_SMALL, fg_color=CLR_SURFACE_ALT,
            border_color=CLR_BORDER, border_width=1,
            text_color=CLR_TEXT, height=32, corner_radius=8,
        ).grid(row=0, column=1, padx=(0, 8), pady=10, sticky="ew")
        ctk.CTkButton(
            add, text="＋ Add", font=FONT_SMALL, width=80,
            fg_color=CLR_SURFACE_ALT, hover_color=CLR_SURFACE_HVR,
            border_color=CLR_BORDER, border_width=1, text_color=CLR_TEXT,
            height=32, corner_radius=8, command=self._add_manual_host,
        ).grid(row=0, column=2, padx=(0, 12), pady=10)

        self._update_selection_count()

    def _render_node_row(self, grid_row, entry):
        online = entry.get("reachable", True)
        dot_clr = CLR_SUCCESS if online else CLR_WARNING
        card = ctk.CTkFrame(self._body, fg_color=CLR_SURFACE, corner_radius=10,
                            border_width=1, border_color=CLR_BORDER)
        card.grid(row=grid_row, column=0, padx=PAD, pady=3, sticky="ew")
        card.grid_columnconfigure(1, weight=1)
        ctk.CTkCheckBox(
            card, text="", variable=entry["var"], width=24,
            fg_color=CLR_ACCENT, hover_color=CLR_ACCENT_HOV,
            checkbox_width=18, checkbox_height=18,
            command=self._update_selection_count,
        ).grid(row=0, column=0, padx=(12, 4), pady=10)

        info = ctk.CTkFrame(card, fg_color="transparent")
        info.grid(row=0, column=1, sticky="w", pady=8)
        title = entry.get("hostname") or entry["host"]
        ctk.CTkLabel(info, text=f"● {title}",
                     font=FONT_SUBHEAD, text_color=dot_clr, anchor="w",
                     ).pack(anchor="w")
        sub = f"{entry['host']}:{entry['port']}"
        if entry.get("agent_version"):
            sub += f"   ·   agent v{entry['agent_version']}"
        if entry.get("manual"):
            sub += "   ·   added manually"
        ctk.CTkLabel(info, text=sub, font=FONT_CAPTION, text_color=CLR_MUTED,
                     anchor="w").pack(anchor="w")

        ctk.CTkButton(
            card, text="✕", width=28, font=FONT_SMALL,
            fg_color="transparent", hover_color=CLR_SURFACE_HVR,
            text_color=CLR_MUTED, command=lambda u=entry["url"]: self._remove(u),
        ).grid(row=0, column=2, padx=(0, 10), pady=10)

    def _add_entry(self, host, port, hostname=None, agent_version=None,
                   reachable=True, manual=False, selected=True):
        url = f"{DEFAULT_SCHEME}://{host}:{port}"
        if url in self._entries:
            return False
        self._entries[url] = {
            "host": host, "port": port, "url": url,
            "hostname": hostname, "agent_version": agent_version,
            "reachable": reachable, "manual": manual,
            "var": ctk.BooleanVar(value=selected),
        }
        return True

    def _add_manual_host(self):
        raw = self._manual_var.get().strip()
        if not raw:
            return
        host = raw
        port = self._port()
        if ":" in raw:
            host, _, p = raw.partition(":")
            try:
                port = int(p)
            except ValueError:
                pass
        host = host.strip()
        if not host:
            return
        if self._add_entry(host, port, hostname=host, manual=True):
            self._manual_var.set("")
            self._render_selection()

    def _remove(self, url):
        self._entries.pop(url, None)
        self._render_selection()

    def _toggle_all(self):
        val = self._select_all_var.get()
        for entry in self._entries.values():
            entry["var"].set(val)
        self._update_selection_count()

    def _selected_entries(self):
        return [e for e in self._entries.values() if e["var"].get()]

    def _update_selection_count(self):
        n = len(self._selected_entries())
        total = len(self._entries)
        if hasattr(self, "_count_lbl") and self._count_lbl.winfo_exists():
            self._count_lbl.configure(text=f"{n} of {total} selected")
        if not self._scanning and not self._discovering:
            self._scan_btn.configure(
                state="normal" if n else "disabled")

    # ---------------------------------------------------------- discovery
    def _start_discovery(self):
        if self._discovering or self._scanning:
            return
        self._discovering = True
        self._discover_btn.configure(state="disabled", text="Discovering…")
        self._scan_btn.configure(state="disabled")

        for w in self._body.winfo_children():
            w.destroy()
        self._progress.grid()
        self._progress.set(0)
        self._disc_lbl = ctk.CTkLabel(
            self._body, text="Scanning your network for node agents…",
            font=FONT_SMALL, text_color=CLR_MUTED)
        self._disc_lbl.grid(row=0, column=0, pady=(20, 4))

        threading.Thread(target=self._run_discovery, daemon=True).start()

    def _run_discovery(self):
        port = self._port()

        def _progress(done, total, found):
            self._safe_after(0, self._progress.set, done / total if total else 1)
            if found:
                self._safe_after(
                    0, lambda f=found: self._disc_lbl.configure(
                        text=f"Found {f.get('hostname', f['host'])} "
                             f"({f['host']})…"))

        try:
            results = discover_nodes(port=port, timeout=0.7, progress=_progress)
        except Exception as exc:
            results = []
            # Bind the message now — the except alias is gone by the time
            # the deferred lambda runs on the Tk main loop.
            msg = f"Discovery failed: {exc}"
            self._safe_after(0, lambda: self._show_message(msg, CLR_DANGER))
        self._safe_after(0, lambda: self._finish_discovery(results))

    def _finish_discovery(self, results):
        self._discovering = False
        self._progress.grid_remove()
        self._discover_btn.configure(state="normal", text="🔍  Discover")
        added = 0
        for r in results:
            if self._add_entry(r["host"], r["port"],
                               hostname=r.get("hostname"),
                               agent_version=r.get("agent_version"),
                               reachable=True, manual=False, selected=True):
                added += 1
        self._render_selection()
        if not results:
            # Keep the selection view but flag the empty result.
            hint = ctk.CTkLabel(
                self._body,
                text="No node agents answered on this network/port. "
                     "Check the agents are running and the port is correct, "
                     "or add a host manually.",
                font=FONT_SMALL, text_color=CLR_WARNING, wraplength=780,
                justify="center")
            hint.grid(row=99, column=0, pady=(4, 0))

    # ------------------------------------------------------------------- scan
    def _start_scan(self):
        if self._scanning or self._discovering:
            return
        selected = self._selected_entries()
        if not selected:
            self._show_message("Select at least one node to scan.", CLR_WARNING)
            return
        token = self._token_var.get().strip()
        self._nodes = [
            Node(name=e.get("hostname") or e["host"], url=e["url"], token=token)
            for e in selected
        ]

        self._scanning = True
        self._report = None
        self._scan_btn.configure(state="disabled", text="Scanning…")
        self._discover_btn.configure(state="disabled")
        self._export_btn.configure(state="disabled")

        for w in self._body.winfo_children():
            w.destroy()
        self._progress.grid()
        self._progress.set(0)
        self._status_lbl = ctk.CTkLabel(
            self._body, text=f"Scanning {len(self._nodes)} node(s)…",
            font=FONT_SMALL, text_color=CLR_MUTED)
        self._status_lbl.grid(row=0, column=0, pady=(16, 4))

        threading.Thread(target=self._run_scan, daemon=True).start()

    def _run_scan(self):
        def _progress(done, tot, result):
            self._safe_after(0, self._progress.set, done / tot if tot else 1)
            self._safe_after(0, lambda: self._status_lbl.configure(
                text=f"Scanned {done}/{tot} — {result.name} ({result.status})"))

        report = scan_fleet(self._nodes, timeout=90, max_workers=10,
                            progress=_progress)
        self._report = report
        self._safe_after(0, self._show_results)

    def _show_message(self, text, colour):
        for w in self._body.winfo_children():
            w.destroy()
        ctk.CTkLabel(self._body, text=text, font=FONT_BODY,
                     text_color=colour, justify="center",
                     ).grid(row=0, column=0, pady=48)

    # ---------------------------------------------------------------- results
    def _show_results(self):
        self._scanning = False
        self._scan_btn.configure(state="normal", text="▶  Re-scan Selected")
        self._discover_btn.configure(state="normal", text="🔍  Discover")
        self._export_btn.configure(state="normal")
        self._progress.grid_remove()

        report = self._report
        if report is None:
            return

        # Persist to fleet history (best-effort)
        try:
            from src.utils.local_db import save_fleet_report
            save_fleet_report(report.to_dict())
        except Exception:
            import logging
            logging.getLogger(__name__).warning(
                "could not save fleet report to history", exc_info=True)

        gs = GRADE_STYLE.get(report.fleet_grade, GRADE_STYLE["NO DATA"])

        for w in self._body.winfo_children():
            w.destroy()

        row = [0]

        def next_row():
            r = row[0]
            row[0] += 1
            return r

        # ── Fleet grade hero ──────────────────────────────────────────
        hero = ctk.CTkFrame(self._body, fg_color=CLR_SURFACE,
                            corner_radius=16, border_width=2,
                            border_color=gs["colour"])
        hero.grid(row=next_row(), column=0, padx=PAD, pady=(PAD, 10),
                  sticky="ew")
        hero.grid_columnconfigure(0, weight=1)
        ctk.CTkFrame(hero, fg_color=gs["colour"], height=4,
                     corner_radius=0).grid(row=0, column=0, sticky="ew")

        inner = ctk.CTkFrame(hero, fg_color="transparent")
        inner.grid(row=1, column=0, padx=PAD, pady=14, sticky="ew")
        inner.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(inner, text=gs["icon"], font=("Segoe UI Emoji", 40),
                     ).grid(row=0, column=0, rowspan=2, padx=(0, 18), pady=4)
        ctk.CTkLabel(inner, text=gs["title"], font=("Segoe UI", 18, "bold"),
                     text_color=gs["colour"],
                     ).grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(inner, text=gs["msg"], font=FONT_SMALL,
                     text_color=CLR_TEXT_SEC, wraplength=600, justify="left",
                     ).grid(row=1, column=1, sticky="w")

        s = report.to_dict()["summary"]
        ctk.CTkLabel(inner,
                     text=f"{s['online']}/{s['total_nodes']}\nonline",
                     font=("Segoe UI", 14, "bold"),
                     text_color=gs["colour"], justify="center",
                     ).grid(row=0, column=2, rowspan=2, padx=(PAD, 0))

        # ── Summary strip ─────────────────────────────────────────────
        strip = ctk.CTkFrame(self._body, fg_color=CLR_SURFACE,
                             corner_radius=14, border_width=1,
                             border_color=CLR_BORDER)
        strip.grid(row=next_row(), column=0, padx=PAD, pady=(0, 12), sticky="ew")
        weakest = report.weakest_node
        cells = [
            ("Nodes",     s["total_nodes"],              CLR_BLUE),
            ("At Risk",   s["nodes_at_risk"],            CLR_DANGER),
            ("Unreach.",  s["unreachable"],              CLR_WARNING),
            ("Critical",  s["total_critical_failures"],  CLR_DANGER),
            ("Avg Score", f"{s['average_hardening_score']}%", CLR_SUCCESS),
            ("Weakest",   weakest.name if weakest else "—", CLR_WARNING),
        ]
        strip.grid_columnconfigure(tuple(range(len(cells))), weight=1)
        for col_i, (label, value, clr) in enumerate(cells):
            cell = ctk.CTkFrame(strip, fg_color="transparent")
            cell.grid(row=0, column=col_i, padx=10, pady=14)
            ctk.CTkLabel(cell, text=label, font=FONT_CAPTION,
                         text_color=CLR_MUTED).pack()
            ctk.CTkLabel(cell, text=str(value), font=("Segoe UI", 14, "bold"),
                         text_color=clr).pack()

        # ── Per-node cards ────────────────────────────────────────────
        ctk.CTkLabel(self._body, text="Nodes", font=FONT_HEADING,
                     text_color=CLR_TEXT,
                     ).grid(row=next_row(), column=0, padx=PAD, pady=(4, 6),
                            sticky="w")

        grade_rank = {"AT RISK": 0, "NEEDS ATTENTION": 1, "HARDENED": 2}
        status_rank = {"online": 0, "busy": 1, "unauthorized": 2,
                       "error": 3, "offline": 4}
        ordered = sorted(
            report.results,
            key=lambda r: (status_rank.get(r.status, 4),
                           grade_rank.get(r.hardening_grade or "", 5)))
        for r in ordered:
            self._make_node_card(self._body, next_row(), r,
                                 is_weakest=(weakest is not None
                                             and r.name == weakest.name))

    def _make_node_card(self, parent, row_idx, r, is_weakest=False):
        icon, status_clr = STATUS_STYLE.get(r.status, ("?", CLR_MUTED))
        border = CLR_WARNING if is_weakest else CLR_BORDER

        card = ctk.CTkFrame(parent, fg_color=CLR_SURFACE, corner_radius=12,
                            border_width=2 if is_weakest else 1,
                            border_color=border)
        card.grid(row=row_idx, column=0, padx=PAD, pady=3, sticky="ew")
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkFrame(card, fg_color=status_clr, width=4,
                     corner_radius=0).grid(row=0, column=0, rowspan=2,
                                           sticky="ns")

        ctk.CTkLabel(card, text=icon, font=("Segoe UI", 14),
                     text_color=status_clr, width=26,
                     ).grid(row=0, column=1, padx=(10, 4), pady=(10, 2),
                            sticky="n")

        name_f = ctk.CTkFrame(card, fg_color="transparent")
        name_f.grid(row=0, column=2, sticky="w", pady=(10, 2))
        title = f"{r.name}"
        if r.hostname and r.hostname != r.name:
            title += f"  ({r.hostname})"
        ctk.CTkLabel(name_f, text=title, font=FONT_SUBHEAD,
                     text_color=CLR_TEXT).pack(side="left")
        if is_weakest and r.reachable:
            ctk.CTkLabel(name_f, text="  ⬅ weakest link",
                         font=FONT_CAPTION, text_color=CLR_WARNING,
                         ).pack(side="left")

        # Right-side grade / status badge
        if r.reachable and r.hardening_grade:
            badge_txt = f"{r.hardening_grade}  {r.hardening_score}%"
            badge_clr = NODE_GRADE_CLR.get(r.hardening_grade, CLR_MUTED)
        else:
            badge_txt = r.status.upper()
            badge_clr = status_clr
        ctk.CTkLabel(card, text=badge_txt, font=("Segoe UI", 9, "bold"),
                     text_color=badge_clr, fg_color=CLR_SURFACE_ALT,
                     corner_radius=6, height=20,
                     ).grid(row=0, column=3, padx=(0, 12), pady=(10, 2),
                            sticky="ne")

        # Detail line
        if r.reachable:
            detail = (f"Certification: {r.cert_level or '—'}  ·  "
                      f"Readiness: {r.readiness_verdict or '—'}  ·  "
                      f"Critical failures: {r.critical_failures}  ·  {r.url}")
        else:
            detail = f"{r.error or 'Unreachable'}  ·  {r.url}"
        ctk.CTkLabel(card, text=detail, font=FONT_SMALL,
                     text_color=CLR_TEXT_SEC, anchor="w", wraplength=760,
                     justify="left",
                     ).grid(row=1, column=1, columnspan=3, padx=(10, 12),
                            pady=(0, 10), sticky="w")

    # ---------------------------------------------------------------- export
    def _export_html(self):
        report = self._report
        if report is None:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML Report", "*.html"), ("All files", "*.*")],
            initialfile=f"fleet_scan_{datetime.date.today().isoformat()}.html",
        )
        if not path:
            return

        gs = GRADE_STYLE.get(report.fleet_grade, GRADE_STYLE["NO DATA"])
        s = report.to_dict()["summary"]
        weakest = report.weakest_node

        rows_html = ""
        for r in report.results:
            clr = {"online": "#3BB273", "offline": "#E84040",
                   "unauthorized": "#F0A500", "error": "#E84040"
                   }.get(r.status, "#A0B4C8")
            grade_clr = {"HARDENED": "#3BB273", "NEEDS ATTENTION": "#F0A500",
                         "AT RISK": "#E84040"}.get(r.hardening_grade or "", "#A0B4C8")
            weak = " ⬅ weakest" if (weakest and r.name == weakest.name
                                    and r.reachable) else ""
            rows_html += (
                f"<tr>"
                f"<td><b>{r.name}</b>{weak}</td>"
                f"<td>{r.hostname or '—'}</td>"
                f"<td style='color:{clr};font-weight:bold'>{r.status}</td>"
                f"<td style='color:{grade_clr};font-weight:bold'>"
                f"{r.hardening_grade or '—'}</td>"
                f"<td>{str(r.hardening_score) + '%' if r.hardening_score is not None else '—'}</td>"
                f"<td>{r.cert_level or '—'}</td>"
                f"<td>{r.readiness_verdict or '—'}</td>"
                f"<td>{r.critical_failures if r.reachable else '—'}</td>"
                f"<td style='font-size:11px;color:#A0B4C8'>{r.error or ''}</td>"
                f"</tr>"
            )

        html = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8">
<title>Fleet Scan — {datetime.date.today()}</title>
<style>
 body{{font-family:'Segoe UI',sans-serif;background:#0B1622;
  color:#ECF4FF;margin:0;padding:32px}}
 h1{{color:{gs['colour']}}}
 .badge{{background:#132236;border-radius:16px;padding:24px;margin-bottom:28px;
  border:2px solid {gs['colour']};display:flex;align-items:center;gap:20px}}
 .big{{font-size:42px}}
 .verdict{{font-size:22px;font-weight:bold;color:{gs['colour']}}}
 .msg{{font-size:12px;color:#A0B4C8;margin-top:6px;max-width:640px}}
 .score{{font-size:28px;font-weight:bold;color:{gs['colour']};margin-left:auto}}
 table{{width:100%;border-collapse:collapse;background:#132236;
  border-radius:10px;overflow:hidden}}
 th{{background:#1A2D42;padding:10px 14px;text-align:left;font-size:11px;
  color:#5A7490;text-transform:uppercase}}
 td{{padding:8px 14px;border-bottom:1px solid #0B1622;font-size:12px}}
 h2{{color:#2485E8;border-bottom:1px solid #1A2D42;padding-bottom:6px}}
 footer{{margin-top:40px;color:#5A7490;font-size:10px;text-align:center}}
</style></head><body>
<h1>🖧 Distributed Fleet Scan</h1>
<div class="badge">
 <div class="big">{gs['icon']}</div>
 <div>
  <div class="verdict">{gs['title']}</div>
  <div class="msg">{gs['msg']}</div>
  <div style="margin-top:8px;font-size:11px;color:#5A7490">
   {s['online']}/{s['total_nodes']} online · {s['nodes_at_risk']} at risk ·
   {s['total_critical_failures']} critical failures ·
   avg hardening {s['average_hardening_score']}% ·
   Scanned: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}
  </div>
 </div>
 <div class="score">{report.fleet_grade}</div>
</div>
<h2>Nodes</h2>
<table><thead><tr>
 <th>Node</th><th>Host</th><th>Status</th><th>Hardening</th><th>Score</th>
 <th>Cert</th><th>Readiness</th><th>Critical</th><th>Error</th>
</tr></thead><tbody>{rows_html}</tbody></table>
<footer>Zambia Digital Hygiene Certification Programme
  · Distributed Fleet Scan · University of Zambia</footer>
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
        dlg.geometry("420x120")
        dlg.resizable(False, False)
        dlg.configure(fg_color=CLR_SURFACE)
        dlg.grab_set()
        ctk.CTkLabel(dlg, text="✔  Report saved!", font=FONT_SUBHEAD,
                     text_color=CLR_SUCCESS).pack(pady=(20, 4))
        ctk.CTkLabel(dlg, text=path, font=FONT_CAPTION, text_color=CLR_MUTED,
                     wraplength=380).pack(pady=(0, 12))
        ctk.CTkButton(dlg, text="OK", fg_color=CLR_ACCENT, text_color="#FFFFFF",
                      height=BTN_H, corner_radius=BTN_R,
                      command=dlg.destroy).pack()
