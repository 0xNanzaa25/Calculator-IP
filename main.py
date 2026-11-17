#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════╗
║  IP CALC  —  Kalkulator Jaringan (TUI)   ║
║  developer : AndraxC2                    ║
╚══════════════════════════════════════════╝

Install : pip install textual
Jalankan: python ipcalc.py

Aturan input: setiap IP WAJIB pakai prefix, contoh 192.168.1.10/24
(boleh juga netmask: 192.168.1.10/255.255.255.0)
"""
from __future__ import annotations

import ipaddress
import re
from itertools import islice

from rich.align import Align
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Input,
    Static,
    TabbedContent,
    TabPane,
)

# ──────────────────────────── PALET WARNA ────────────────────────────
PURPLE = "#a855f7"
VIOLET = "#7c3aed"
LILAC = "#c084fc"
PALE = "#e9d5ff"
GRAY = "#9ca3af"
DGRAY = "#6b7280"
RED = "#fca5a5"
GREEN = "#86efac"

G1 = (216, 180, 254)  # lilac terang
G2 = (109, 40, 217)   # ungu tua

MAX_ROWS = 1024


def lerp_color(t: float) -> str:
    t = max(0.0, min(1.0, t))
    return "#%02x%02x%02x" % tuple(int(a + (b - a) * t) for a, b in zip(G1, G2))


# ──────────────────────────── LOGIKA JARINGAN ────────────────────────────
class CalcError(Exception):
    """Error input yang ramah dibaca user."""


def fmt(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def parse_cidr(raw: str) -> ipaddress.IPv4Interface:
    raw = raw.strip()
    if "/" not in raw:
        raise CalcError("Prefix wajib diisi!  Contoh: 192.168.1.10/24")
    ip_s, pfx_s = (p.strip() for p in raw.split("/", 1))
    try:
        ip = ipaddress.IPv4Address(ip_s)
    except ValueError:
        raise CalcError(f"IP '{ip_s}' tidak valid (format: 0-255.0-255.0-255.0-255)") from None
    if not pfx_s:
        raise CalcError("Prefix masih kosong.  Contoh: /24")
    if pfx_s.isdigit():
        prefix = int(pfx_s)
        if not 0 <= prefix <= 32:
            raise CalcError("Prefix harus antara /0 sampai /32")
    else:
        try:
            m = int(ipaddress.IPv4Address(pfx_s))
        except ValueError:
            raise CalcError(f"Prefix/netmask '{pfx_s}' tidak valid") from None
        inv = ~m & 0xFFFFFFFF
        if inv & (inv + 1):
            raise CalcError("Netmask tidak valid (bit 1 harus berurutan)")
        prefix = bin(m).count("1")
    return ipaddress.IPv4Interface(f"{ip}/{prefix}")


def host_range(net: ipaddress.IPv4Network):
    p = net.prefixlen
    if p == 32:
        return net.network_address, net.network_address, 1
    if p == 31:
        return net.network_address, net.broadcast_address, 2
    return net.network_address + 1, net.broadcast_address - 1, net.num_addresses - 2


def ip_class(ip: ipaddress.IPv4Address):
    o = ip.packed[0]
    if o == 0:
        return "—", None, "Reserved (0.0.0.0/8)"
    if o < 128:
        return "A", 8, "1 – 127   (default /8)"
    if o < 192:
        return "B", 16, "128 – 191 (default /16)"
    if o < 224:
        return "C", 24, "192 – 223 (default /24)"
    if o < 240:
        return "D", None, "224 – 239 (Multicast)"
    return "E", None, "240 – 255 (Reserved)"


def ip_kind(ip: ipaddress.IPv4Address) -> str:
    table = [
        ("0.0.0.0/8", "This network (reserved)"),
        ("127.0.0.0/8", "Loopback"),
        ("169.254.0.0/16", "Link-local (APIPA)"),
        ("10.0.0.0/8", "Private (RFC 1918)"),
        ("172.16.0.0/12", "Private (RFC 1918)"),
        ("192.168.0.0/16", "Private (RFC 1918)"),
        ("100.64.0.0/10", "CGNAT (Shared Address Space)"),
        ("224.0.0.0/4", "Multicast"),
        ("255.255.255.255/32", "Limited Broadcast"),
        ("240.0.0.0/4", "Reserved (Class E)"),
    ]
    for cidr, name in table:
        if ip in ipaddress.IPv4Network(cidr):
            return name
    return "Public"


def block_info(net: ipaddress.IPv4Network):
    idx = min(net.prefixlen // 8, 3)
    mask_oct = net.netmask.packed[idx]
    return idx + 1, 256 - mask_oct


def bin_text(value: int, prefix: int) -> Text:
    s = format(value, "032b")
    t = Text()
    for i, b in enumerate(s):
        if i and i % 8 == 0:
            t.append(".", style=DGRAY)
        t.append(b, style=f"bold {LILAC}" if i < prefix else GRAY)
    return t


def kv_table(rows) -> Table:
    t = Table.grid(padding=(0, 2))
    t.add_column(justify="right", style=GRAY, no_wrap=True)
    t.add_column()
    for row in rows:
        if row is None:
            t.add_row("", "")
            continue
        k, v = row
        t.add_row(k, v if isinstance(v, Text) else Text(str(v), style=f"bold {PALE}"))
    return t


def panel(content, title: str) -> Panel:
    return Panel(
        content,
        title=Text(f" ◆ {title} ", style=f"bold {LILAC}"),
        title_align="left",
        border_style=VIOLET,
        padding=(1, 2),
    )


def render_info(iface: ipaddress.IPv4Interface):
    net, ip, p = iface.network, iface.ip, iface.network.prefixlen
    first, last, usable = host_range(net)
    total = net.num_addresses
    cls, dprefix, cls_note = ip_class(ip)
    octet, inc = block_info(net)

    if p < 31 and ip == net.network_address:
        role = Text("Network address — bukan host", style=RED)
    elif p < 31 and ip == net.broadcast_address:
        role = Text("Broadcast address — bukan host", style=RED)
    else:
        role = Text("Host valid", style=GREEN)

    hi = lambda s: Text(str(s), style=f"bold {LILAC}")  # noqa: E731
    rows = [
        ("IP Address", Text(str(ip), style="bold white")),
        ("Prefix", f"/{p}"),
        ("Netmask", net.netmask),
        ("Wildcard", net.hostmask),
        None,
        ("Network ID", hi(net.network_address)),
        ("Broadcast", hi(net.broadcast_address)),
        ("Host pertama", first),
        ("Host terakhir", last),
        None,
        ("Jumlah host", f"{fmt(usable)} host"),
        ("Total alamat", f"{fmt(total)}  (2^{32 - p})"),
        ("Bit network/host", f"{p} / {32 - p}"),
        ("Blok subnet", f"{inc}  (di oktet ke-{octet})"),
        None,
        ("Kelas", f"{cls}   {cls_note}"),
        ("Tipe", ip_kind(ip)),
        ("Peran IP", role),
    ]

    # ── biner ──
    b = Text()
    b.append("IP      ", style=GRAY)
    b.append_text(bin_text(int(ip), p))
    b.append("\nNetmask ", style=GRAY)
    b.append_text(bin_text(int(net.netmask), p))
    b.append("\nNetwork ", style=GRAY)
    b.append_text(bin_text(int(net.network_address), p))
    b.append("\n\n")
    b.append("■ ", style=LILAC)
    b.append("bit network   ", style=GRAY)
    b.append("■ ", style=GRAY)
    b.append("bit host", style=GRAY)

    # ── ringkasan "auto baca" ──
    s = Text(style=GRAY)
    s.append(f"{ip}/{p}", style=f"bold {PALE}")
    s.append(" berada di jaringan ")
    s.append(f"{net.network_address}/{p}", style=f"bold {LILAC}")
    s.append(".\n")
    s.append(f"Dari 32 bit: {p} bit untuk network, {32 - p} bit untuk host → 2^{32 - p} = {fmt(total)} alamat, ")
    s.append(f"{fmt(usable)} bisa dipakai host", style=f"bold {PALE}")
    s.append(".\n")
    s.append(f"Rentang host {first} – {last}, broadcast {net.broadcast_address}.\n")
    s.append(f"Blok subnet = {inc} pada oktet ke-{octet}.")
    if dprefix is not None:
        if p > dprefix:
            s.append(
                f"\nKelas {cls} default /{dprefix} → di-subnet-kan, meminjam {p - dprefix} bit "
                f"= {fmt(2 ** (p - dprefix))} subnet."
            )
        elif p < dprefix:
            s.append(f"\nPrefix lebih kecil dari default kelas {cls} (/{dprefix}) → supernet / CIDR summarization.")
        else:
            s.append(f"\nPrefix sama dengan default kelas {cls} (classful).")

    return Group(panel(kv_table(rows), "HASIL"), panel(b, "BINER"), panel(s, "AUTO BACA"))


def welcome() -> Panel:
    t = Text()
    t.append("Cara pakai\n", style=f"bold {LILAC}")
    t.append("  ▸ Ketik IP + prefix di kolom atas, hasil muncul otomatis (live)\n", style=GRAY)
    t.append("  ▸ Prefix ", style=GRAY)
    t.append("WAJIB", style=f"bold {PALE}")
    t.append(" →  192.168.1.10/24\n", style=GRAY)
    t.append("  ▸ Netmask juga boleh →  192.168.1.10/255.255.255.0\n\n", style=GRAY)
    t.append("Coba contoh\n", style=f"bold {LILAC}")
    for ex in ("10.10.10.5/8", "172.16.5.4/20", "192.168.100.77/26", "192.168.1.1/30"):
        t.append(f"  • {ex}\n", style=PALE)
    t.append("\nTab: ", style=DGRAY)
    t.append("F1 Info  F2 Subnetting  F3 VLSM  F4 Konversi  F5 Referensi", style=GRAY)
    return panel(t, "SELAMAT DATANG")


def reference_view():
    pt = Table(border_style=VIOLET, header_style=f"bold {PALE}", show_edge=True)
    for c in ("Prefix", "Netmask", "Total alamat", "Host usable", "Blok"):
        pt.add_column(c, justify="right")
    for p in range(8, 33):
        n = ipaddress.IPv4Network(f"0.0.0.0/{p}")
        usable = 1 if p == 32 else 2 if p == 31 else n.num_addresses - 2
        _, inc = block_info(n)
        st = f"bold {LILAC}" if p in (8, 16, 24, 30) else GRAY
        pt.add_row(f"/{p}", str(n.netmask), fmt(n.num_addresses), fmt(usable), str(inc), style=st)

    ct = Table(border_style=VIOLET, header_style=f"bold {PALE}")
    for c in ("Kelas", "Oktet 1", "Default mask", "Keterangan"):
        ct.add_column(c)
    ct.add_row("A", "1 – 126", "255.0.0.0 (/8)", "Skala besar", style=GRAY)
    ct.add_row("B", "128 – 191", "255.255.0.0 (/16)", "Skala menengah", style=GRAY)
    ct.add_row("C", "192 – 223", "255.255.255.0 (/24)", "Skala kecil / LAN", style=GRAY)
    ct.add_row("D", "224 – 239", "—", "Multicast", style=GRAY)
    ct.add_row("E", "240 – 255", "—", "Reserved / eksperimen", style=GRAY)

    rt = Table(border_style=VIOLET, header_style=f"bold {PALE}")
    for c in ("Range khusus", "Keterangan"):
        rt.add_column(c)
    for a, b in (
        ("10.0.0.0/8", "Private kelas A"),
        ("172.16.0.0/12", "Private kelas B (172.16 – 172.31)"),
        ("192.168.0.0/16", "Private kelas C"),
        ("127.0.0.0/8", "Loopback"),
        ("169.254.0.0/16", "APIPA / link-local"),
        ("100.64.0.0/10", "CGNAT"),
    ):
        rt.add_row(a, b, style=GRAY)

    return Group(
        panel(pt, "TABEL PREFIX"),
        panel(ct, "KELAS IP"),
        panel(rt, "RANGE PRIVATE & KHUSUS"),
    )


# ──────────────────────────── SPLASH SCREEN ────────────────────────────
def _make_art():
    I = ["██╗", "██║", "██║", "██║", "██║", "╚═╝"]
    P = ["██████╗ ", "██╔══██╗", "██████╔╝", "██╔═══╝ ", "██║     ", "╚═╝     "]
    C = [" ██████╗", "██╔════╝", "██║     ", "██║     ", "╚██████╗", " ╚═════╝"]
    A = [" █████╗ ", "██╔══██╗", "███████║", "██╔══██║", "██║  ██║", "╚═╝  ╚═╝"]
    L = ["██╗     ", "██║     ", "██║     ", "██║     ", "███████╗", "╚══════╝"]
    rows = [I[i] + P[i] + "   " + C[i] + A[i] + L[i] + C[i] for i in range(6)]
    w = max(len(r) for r in rows)
    return [r.ljust(w) for r in rows], w


ART, ART_W = _make_art()
SPLASH_TOTAL = 115  # tick @ 20 fps


class SplashScreen(Screen):
    def compose(self) -> ComposeResult:
        with Vertical(id="splash-box"):
            yield Static(id="sp-art")
            yield Static(id="sp-title")
            yield Static(id="sp-dev")
            yield Static(id="sp-net")
            yield Static(id="sp-bar")
            yield Static(id="sp-hint")

    def on_mount(self) -> None:
        self.t = 0
        self._done = False
        self.set_interval(1 / 20, self._tick)

    # ── input untuk skip ──
    def on_key(self, event) -> None:
        self._finish()

    def on_click(self) -> None:
        self._finish()

    def _finish(self) -> None:
        if not self._done:
            self._done = True
            self.dismiss(None)

    # ── frame ──
    def _tick(self) -> None:
        if self._done:
            return
        self.t += 1
        t = self.t
        self.query_one("#sp-art", Static).update(self._art(t))
        self.query_one("#sp-title", Static).update(self._title(t))
        self.query_one("#sp-dev", Static).update(self._dev(t))
        self.query_one("#sp-net", Static).update(self._net(t))
        self.query_one("#sp-bar", Static).update(self._bar(t))
        if t >= 25:
            hint = Text("tekan sembarang tombol untuk lanjut", style=DGRAY)
            self.query_one("#sp-hint", Static).update(Align.center(hint))
        if t >= SPLASH_TOTAL:
            self._finish()

    def _art(self, t: int) -> Text:
        reveal = int(t * 2.6)
        shimmer = (t * 2) % (ART_W + 24) - 10 if reveal >= ART_W else -99
        out = Text(no_wrap=True)
        for row in ART:
            for x, ch in enumerate(row):
                if x >= reveal or ch == " ":
                    out.append(" ")
                    continue
                if ch == "█":
                    color = lerp_color(x / ART_W)
                    if reveal - 3 <= x < reveal and reveal < ART_W:
                        out.append("▓", style="bold #f5f3ff")
                        continue
                else:
                    color = DGRAY
                if abs(x - shimmer) <= 2:
                    color = "#f5f3ff"
                out.append(ch, style=f"bold {color}" if ch == "█" else color)
            out.append("\n")
        out.rstrip()
        return out

    @staticmethod
    def _typewriter(segments, n: int, t: int) -> Text:
        out = Text()
        left = n
        total = sum(len(s) for s, _ in segments)
        for s, style in segments:
            if left <= 0:
                break
            out.append(s[:left], style=style)
            left -= len(s)
        if n < total and t % 8 < 4:
            out.append("▌", style=PURPLE)
        return out

    def _title(self, t: int) -> Align:
        n = max(0, int((t - 12) * 1.3))
        seg = [("K A L K U L A T O R   I P", f"bold {PALE}")]
        return Align.center(self._typewriter(seg, n, t))

    def _dev(self, t: int) -> Align:
        n = max(0, int((t - 32) * 1.2))
        seg = [("developer  ", GRAY), ("▸  ", PURPLE), ("AndraxC2", f"bold {LILAC}")]
        return Align.center(self._typewriter(seg, n, t))

    def _net(self, t: int) -> Text:
        if t < 18:
            return Text("")
        l1 = l2 = 10
        total = l1 + l2
        p = int((t - 18) * 0.8) % (total + 8)
        out = Text(no_wrap=True)
        out.append("▣ PC ", style=f"bold {PURPLE}")
        for i in range(total):
            if i == p:
                out.append("●", style="bold #f5f3ff")
            elif i == p - 1:
                out.append("•", style=LILAC)
            elif i == p - 2:
                out.append("·", style=VIOLET)
            else:
                out.append("─", style=DGRAY)
            if i == l1 - 1:
                out.append(" ◉ ROUTER ", style=f"bold {LILAC}")
        out.append(" ▣ SERVER", style=f"bold {PURPLE}")
        return out

    def _bar(self, t: int) -> Text:
        if t < 34:
            return Text("")
        prog = min(1.0, (t - 34) / 70)
        w = 34
        f = int(prog * w)
        out = Text(no_wrap=True)
        out.append("▕", style=DGRAY)
        for i in range(w):
            if i < f:
                out.append("█", style=lerp_color(i / w))
            else:
                out.append("░", style="#3b3552")
        out.append("▏", style=DGRAY)
        out.append(f" {int(prog * 100):3d}%", style=f"bold {PALE}")
        msgs = [
            (0.0, "Memuat modul ipaddress..."),
            (0.3, "Menyiapkan engine subnet..."),
            (0.6, "Menghitung tabel VLSM..."),
            (0.95, "Siap digunakan!"),
        ]
        msg = [m for th, m in msgs if prog >= th][-1]
        out.append("\n")
        out.append(msg, style=GRAY if prog < 0.95 else f"bold {LILAC}")
        return out


# ──────────────────────────── LAYAR UTAMA ────────────────────────────
TAB_INPUT = {
    "tab-info": "check-input",
    "tab-sub": "sub-input",
    "tab-vlsm": "vlsm-input",
    "tab-conv": "conv-input",
    "tab-ref": "ip-input",
}


class MainScreen(Screen):
    BINDINGS = [
        Binding("f1", "tab('tab-info')", "Info IP"),
        Binding("f2", "tab('tab-sub')", "Subnetting"),
        Binding("f3", "tab('tab-vlsm')", "VLSM"),
        Binding("f4", "tab('tab-conv')", "Konversi"),
        Binding("f5", "tab('tab-ref')", "Referensi"),
        Binding("ctrl+l", "focus_ip", "Fokus IP"),
        Binding("ctrl+r", "reset", "Reset"),
    ]

    iface: ipaddress.IPv4Interface | None = None

    def compose(self) -> ComposeResult:
        with Vertical(id="root"):
            yield Static(id="title")
            with Horizontal(id="inputbar"):
                yield Input(placeholder="IP/prefix  →  contoh 192.168.1.10/24", id="ip-input")
                yield Button("Hitung ▶", id="calc-btn")
            yield Static(id="status")
            with TabbedContent(id="tabs", initial="tab-info"):
                with TabPane("◆ Info IP", id="tab-info"):
                    with VerticalScroll():
                        yield Static(id="info")
                        yield Input(placeholder="Cek IP lain, satu jaringan? mis. 192.168.1.77", id="check-input")
                        yield Static(id="check-out")
                with TabPane("◆ Subnetting", id="tab-sub"):
                    yield Input(placeholder="Prefix baru (/26)  atau  jumlah subnet (4)", id="sub-input")
                    yield Static(id="sub-note")
                    yield DataTable(id="sub-table", zebra_stripes=True, cursor_type="row")
                with TabPane("◆ VLSM", id="tab-vlsm"):
                    yield Input(placeholder="Kebutuhan host dipisah koma: 100, 50, 25, 10", id="vlsm-input")
                    yield Static(id="vlsm-note")
                    yield DataTable(id="vlsm-table", zebra_stripes=True, cursor_type="row")
                with TabPane("◆ Konversi", id="tab-conv"):
                    with VerticalScroll():
                        yield Input(placeholder="IP (192.168.1.1)  /  prefix (/26)  /  netmask (255.255.255.192)", id="conv-input")
                        yield Static(id="conv-out")
                with TabPane("◆ Referensi", id="tab-ref"):
                    with VerticalScroll():
                        yield Static(reference_view(), id="ref-out")
        yield Footer()

    # ── lifecycle ──
    def on_mount(self) -> None:
        self._tt = 0
        self.query_one("#root").styles.opacity = 0.0
        sub = self.query_one("#sub-table", DataTable)
        sub.add_columns("#", "Network", "Host pertama", "Host terakhir", "Broadcast", "Host")
        vl = self.query_one("#vlsm-table", DataTable)
        vl.add_columns("LAN", "Butuh", "Prefix", "Network", "Netmask", "Range host", "Broadcast", "Host")
        self.set_interval(0.06, self._tick_title)
        self.refresh_all()
        self.refresh_conv()

    def play_intro(self) -> None:
        root = self.query_one("#root")
        root.styles.opacity = 0.0
        root.styles.animate("opacity", 1.0, duration=0.8, easing="out_cubic")
        self.query_one("#ip-input", Input).focus()

    # ── animasi judul ──
    def _tick_title(self) -> None:
        self._tt += 1
        label = "◆  K A L K U L A T O R   I P  ◆"
        pos = (self._tt % (len(label) + 14)) - 7
        l1 = Text()
        for i, ch in enumerate(label):
            d = abs(i - pos)
            style = "bold #f5f3ff" if d <= 1 else f"bold {PALE}" if d <= 3 else f"bold {PURPLE}"
            l1.append(ch, style=style)
        l2 = Text.assemble(("developer ", DGRAY), ("▸ ", PURPLE), ("AndraxC2", f"bold {LILAC}"))
        n = 44
        pos2 = (self._tt * 2) % (n + 16) - 8
        l3 = Text()
        for i in range(n):
            d = abs(i - pos2)
            l3.append("━", style="#f5f3ff" if d <= 1 else lerp_color(i / n) if d > 3 else LILAC)
        self.query_one("#title", Static).update(Group(Align.center(l1), Align.center(l2), Align.center(l3)))

    # ── actions ──
    def action_tab(self, tab_id: str) -> None:
        self.query_one(TabbedContent).active = tab_id
        self.call_after_refresh(lambda: self.query_one("#" + TAB_INPUT[tab_id]).focus())

    def action_focus_ip(self) -> None:
        self.query_one("#ip-input", Input).focus()

    def action_reset(self) -> None:
        for wid in ("ip-input", "check-input", "sub-input", "vlsm-input", "conv-input"):
            self.query_one("#" + wid, Input).value = ""
        self.query_one("#ip-input", Input).focus()

    # ── events ──
    def on_input_changed(self, event: Input.Changed) -> None:
        wid = event.input.id
        if wid == "ip-input":
            self.refresh_all()
        elif wid == "check-input":
            self.refresh_check()
        elif wid == "sub-input":
            self.refresh_sub()
        elif wid == "vlsm-input":
            self.refresh_vlsm()
        elif wid == "conv-input":
            self.refresh_conv()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "ip-input":
            self.refresh_all(flash=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "calc-btn":
            self.refresh_all(flash=True)

    # ── util ──
    def _set(self, wid: str, content) -> None:
        self.query_one(wid, Static).update(content)

    def _flash(self) -> None:
        w = self.query_one("#info")
        w.styles.opacity = 0.2
        w.styles.animate("opacity", 1.0, duration=0.4)

    # ── refresh ──
    def refresh_all(self, flash: bool = False) -> None:
        raw = self.query_one("#ip-input", Input).value
        if not raw.strip():
            self.iface = None
            self._set("#status", Text("○ menunggu input...", style=DGRAY))
            self._set("#info", welcome())
        else:
            try:
                self.iface = parse_cidr(raw)
            except CalcError as e:
                self.iface = None
                self._set("#status", Text(f"✖ {e}", style=RED))
                self._set("#info", welcome())
            else:
                i = self.iface
                self._set(
                    "#status",
                    Text.assemble(
                        ("● ", PURPLE),
                        (f"{i.ip}/{i.network.prefixlen}", f"bold {PALE}"),
                        ("  valid", GRAY),
                    ),
                )
                self._set("#info", render_info(i))
                if flash:
                    self._flash()
        self.refresh_check()
        self.refresh_sub()
        self.refresh_vlsm()

    def refresh_check(self) -> None:
        raw = self.query_one("#check-input", Input).value.strip()
        if not raw:
            self._set("#check-out", Text(""))
            return
        if self.iface is None:
            self._set("#check-out", Text("  Isi IP/prefix utama yang valid dulu.", style=GRAY))
            return
        try:
            other = ipaddress.IPv4Address(raw.split("/")[0].strip())
        except ValueError:
            self._set("#check-out", Text("  ✖ IP pembanding tidak valid", style=RED))
            return
        net = self.iface.network
        if other in net:
            t = Text.assemble(("  ✔ ", f"bold {GREEN}"), (f"{other}", f"bold {PALE}"),
                              (f" SATU jaringan dengan {net}", GRAY))
            if net.prefixlen < 31 and other == net.network_address:
                t.append("  (tapi ini network address)", style=RED)
            elif net.prefixlen < 31 and other == net.broadcast_address:
                t.append("  (tapi ini broadcast address)", style=RED)
        else:
            other_net = ipaddress.IPv4Network(f"{other}/{net.prefixlen}", strict=False)
            t = Text.assemble(("  ✖ ", f"bold {RED}"), (f"{other}", f"bold {PALE}"),
                              (f" BEDA jaringan (network-nya {other_net}) — butuh router", GRAY))
        self._set("#check-out", t)

    def refresh_sub(self) -> None:
        table = self.query_one("#sub-table", DataTable)
        table.clear()
        spec = self.query_one("#sub-input", Input).value.strip()
        if self.iface is None:
            self._set("#sub-note", Text("  Isi IP/prefix valid dulu di kolom atas.", style=GRAY))
            return
        net = self.iface.network
        if not spec:
            self._set("#sub-note", Text.assemble(
                ("  Jaringan induk ", GRAY), (str(net), f"bold {LILAC}"),
                ("  → isi prefix baru (/26) atau jumlah subnet (4)", GRAY)))
            return
        try:
            newp, rounded = self._parse_split(net, spec)
        except CalcError as e:
            self._set("#sub-note", Text(f"  ✖ {e}", style=RED))
            return
        count = 2 ** (newp - net.prefixlen)
        sample = ipaddress.IPv4Network(f"{net.network_address}/{newp}")
        _, _, usable = host_range(sample)
        note = Text.assemble(
            ("  ", ""), (str(net), f"bold {LILAC}"), (f" → /{newp}  ", GRAY),
            (f"{fmt(count)} subnet", f"bold {PALE}"), (f" × {fmt(usable)} host  ", GRAY),
            (f"netmask {sample.netmask}", GRAY),
        )
        if rounded:
            note.append("  (jumlah dibulatkan ke pangkat 2)", style=DGRAY)
        if count > MAX_ROWS:
            note.append(f"  (tampil {MAX_ROWS} pertama)", style=RED)
        self._set("#sub-note", note)
        for i, sn in enumerate(islice(net.subnets(new_prefix=newp), MAX_ROWS), 1):
            f, l, u = host_range(sn)
            table.add_row(
                str(i),
                Text(f"{sn.network_address}/{newp}", style=f"bold {LILAC}"),
                str(f), str(l), str(sn.broadcast_address), fmt(u),
            )

    @staticmethod
    def _parse_split(net, spec: str):
        rounded = False
        try:
            if spec.startswith("/"):
                newp = int(spec[1:])
            else:
                n = int(spec)
                if n < 1:
                    raise ValueError
                bits = (n - 1).bit_length()
                rounded = n != 1 << bits
                newp = net.prefixlen + bits
        except ValueError:
            raise CalcError("Isi /prefix (mis. /26) atau jumlah subnet (mis. 4)") from None
        if newp < net.prefixlen:
            raise CalcError(f"Prefix baru harus ≥ /{net.prefixlen}")
        if newp > 32:
            raise CalcError("Prefix melebihi /32 — bit host tidak cukup")
        return newp, rounded

    def refresh_vlsm(self) -> None:
        table = self.query_one("#vlsm-table", DataTable)
        table.clear()
        raw = self.query_one("#vlsm-input", Input).value.strip()
        if self.iface is None:
            self._set("#vlsm-note", Text("  Isi IP/prefix valid dulu di kolom atas.", style=GRAY))
            return
        net = self.iface.network
        if not raw:
            self._set("#vlsm-note", Text.assemble(
                ("  Jaringan induk ", GRAY), (f"{net}", f"bold {LILAC}"),
                (f" ({fmt(net.num_addresses)} alamat)  → contoh: 100, 50, 25, 10", GRAY)))
            return
        try:
            needs = [int(x) for x in re.split(r"[,\s;]+", raw) if x]
        except ValueError:
            self._set("#vlsm-note", Text("  ✖ Hanya angka, dipisah koma", style=RED))
            return
        if not needs or any(n < 1 for n in needs):
            self._set("#vlsm-note", Text("  ✖ Kebutuhan host harus ≥ 1", style=RED))
            return

        cur, end = int(net.network_address), int(net.broadcast_address)
        used, unfit = 0, []
        for idx, h in sorted(enumerate(needs, 1), key=lambda x: (-x[1], x[0])):
            bits = max(2, (h + 1).bit_length())
            size = 1 << bits
            if bits > 32 or cur + size - 1 > end:
                unfit.append(f"LAN {idx} ({h})")
                continue
            sn = ipaddress.IPv4Network((cur, 32 - bits))
            f, l, u = host_range(sn)
            table.add_row(
                f"LAN {idx}", str(h), f"/{sn.prefixlen}",
                Text(str(sn.network_address), style=f"bold {LILAC}"),
                str(sn.netmask), f"{f} – {l}", str(sn.broadcast_address), fmt(u),
            )
            cur += size
            used += size
        pct = used * 100 / net.num_addresses
        note = Text.assemble(
            ("  Terpakai ", GRAY), (f"{fmt(used)}/{fmt(net.num_addresses)}", f"bold {PALE}"),
            (f" alamat ({pct:.1f}%)  — urut dari kebutuhan terbesar", GRAY),
        )
        if unfit:
            note.append(f"\n  ✖ Tidak muat: {', '.join(unfit)}", style=RED)
        self._set("#vlsm-note", note)

    def refresh_conv(self) -> None:
        raw = self.query_one("#conv-input", Input).value.strip()
        if not raw:
            hint = Text()
            hint.append("Ketik salah satu:\n", style=f"bold {LILAC}")
            hint.append("  • IP        192.168.1.1        → desimal, biner, hex, integer\n", style=GRAY)
            hint.append("  • Prefix    /26                → netmask, wildcard, biner\n", style=GRAY)
            hint.append("  • Netmask   255.255.255.192    → prefix, wildcard, biner", style=GRAY)
            self._set("#conv-out", panel(hint, "KONVERSI"))
            return
        try:
            if raw.startswith("/"):
                if not raw[1:].isdigit() or not 0 <= int(raw[1:]) <= 32:
                    raise CalcError("Prefix harus /0 sampai /32")
                p = int(raw[1:])
                n = ipaddress.IPv4Network(f"0.0.0.0/{p}")
                _, _, usable = host_range(n)
                _, inc = block_info(n)
                rows = [
                    ("Prefix", f"/{p}"),
                    ("Netmask", Text(str(n.netmask), style=f"bold {LILAC}")),
                    ("Wildcard", n.hostmask),
                    ("Netmask biner", bin_text(int(n.netmask), p)),
                    ("Netmask hex", f"0x{int(n.netmask):08X}"),
                    ("Total alamat", fmt(n.num_addresses)),
                    ("Host usable", fmt(usable)),
                    ("Blok subnet", inc),
                ]
            else:
                try:
                    ip = ipaddress.IPv4Address(raw)
                except ValueError:
                    raise CalcError("Bukan IP, /prefix, atau netmask yang valid") from None
                v = int(ip)
                cls, _, _ = ip_class(ip)
                rows = [
                    ("Desimal", Text(str(ip), style=f"bold {LILAC}")),
                    ("Biner", bin_text(v, 0)),
                    ("Hex", f"0x{v:08X}"),
                    ("Integer", fmt(v)),
                    ("Kelas", cls),
                    ("Tipe", ip_kind(ip)),
                ]
                inv = ~v & 0xFFFFFFFF
                if v and not (inv & (inv + 1)):
                    ones = bin(v).count("1")
                    rows.append(("Sebagai netmask", Text(f"valid → /{ones}", style=GREEN)))
            self._set("#conv-out", panel(kv_table(rows), "HASIL KONVERSI"))
        except CalcError as e:
            self._set("#conv-out", Text(f"  ✖ {e}", style=RED))


# ──────────────────────────── APLIKASI ────────────────────────────
class IPCalcApp(App):
    TITLE = "IP CALC"
    BINDINGS = [Binding("ctrl+q", "quit", "Keluar")]

    CSS = """
    Screen { background: #14111c; color: #d1d5db; }
    * {
        scrollbar-color: #7c3aed;
        scrollbar-color-hover: #a855f7;
        scrollbar-background: #1c1828;
        scrollbar-background-hover: #1c1828;
    }

    /* splash */
    SplashScreen { align: center middle; background: #0d0a14; }
    #splash-box { width: 64; max-width: 100%; height: auto; align-horizontal: center; }
    #splash-box Static { width: 100%; height: auto; }
    #sp-art { width: 46; }
    #sp-net { width: 44; margin-top: 1; }
    #sp-bar { width: 44; margin-top: 1; }
    #sp-title { margin-top: 1; }
    #sp-hint { margin-top: 1; }

    /* main */
    #root { padding: 0 2; }
    #title { height: 3; width: 100%; margin-top: 1; }
    #inputbar { height: 3; margin-top: 1; }
    #ip-input { width: 1fr; }
    #calc-btn { width: 14; margin-left: 1; }
    #status { height: 1; margin: 0 0 0 1; }
    #tabs { height: 1fr; margin-top: 1; }
    TabPane { padding: 1 0 0 0; }

    Input {
        background: #1c1828;
        border: tall #4c1d95;
        color: #e9d5ff;
    }
    Input:focus { border: tall #a855f7; }
    Input > .input--placeholder { color: #6b7280; }
    Input > .input--cursor { background: #a855f7; color: #ffffff; }

    Button {
        background: #6d28d9;
        color: #ffffff;
        border: none;
        border-top: tall #8b5cf6;
        border-bottom: tall #4c1d95;
        text-style: bold;
    }
    Button:hover { background: #7c3aed; }
    Button:focus { background: #8b5cf6; }

    Tabs { background: #14111c; }
    Tab { color: #9ca3af; background: #14111c; }
    Tab:hover { color: #e9d5ff; }
    Tab.-active { color: #c084fc; text-style: bold; background: #14111c; }
    Tabs Underline > .underline--bar,
    Tabs:focus Underline > .underline--bar { color: #a855f7; background: #2d2640; }

    DataTable { background: #1c1828; height: 1fr; margin-top: 1; }
    DataTable > .datatable--header { background: #3b2a6b; color: #e9d5ff; text-style: bold; }
    DataTable > .datatable--cursor { background: #6d28d9; color: #ffffff; }
    DataTable > .datatable--odd-row { background: #221d33; }
    DataTable > .datatable--even-row { background: #1c1828; }

    #sub-note, #vlsm-note { height: auto; margin-top: 1; }
    #check-out { height: auto; margin-top: 1; }
    #info { height: auto; }

    Footer { background: #1c1828; color: #9ca3af; }
    """

    def on_mount(self) -> None:
        self.main = MainScreen()
        self.push_screen(self.main)
        self.push_screen(SplashScreen(), self._after_splash)

    def _after_splash(self, _result) -> None:
        self.main.play_intro()


if __name__ == "__main__":
    IPCalcApp().run()
