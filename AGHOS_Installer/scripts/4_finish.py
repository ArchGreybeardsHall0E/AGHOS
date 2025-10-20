#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import random
import subprocess

from PySide6.QtCore import Qt, QTimer, QRectF, QSize
from PySide6.QtGui import QPainter, QColor, QFont, QFontDatabase
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout, QMessageBox
)

# ---- Tłumaczenia tekstów UI ----
TR = {
    "pl": {
        "title": "Instalacja zakończona",
        "subtitle": "AGHOS został zainstalowany pomyślnie.",
        "hint": "Możesz teraz uruchomić ponownie komputer lub odmontować punkty montowania instalacji.",
        "reboot": "Uruchom ponownie teraz",
        "unmount": "Odmontuj i zostań w Live",
        "close": "Zamknij instalator",
        "syncing": "Kończę zapisy na dysk…",
        "flushed": "Zapisy zakończone.",
        "ask_reboot": "Czy na pewno chcesz teraz uruchomić ponownie komputer?",
        "unmounting": "Odmontowuję punkty montowania…",
        "unmounted_ok": "✅ Odmontowano wszystko co było zamontowane do /mnt.",
        "unmount_warn": "⚠️ Część punktów nie dała się odmontować (mogą być w użyciu).",
        "busy_processes": "Niektóre punkty są w użyciu. Zamknij procesy lub użyj lazy umount.",
        "anim_banner": "AGHOS — witamy na pokładzie!",
    },
    "en": {
        "title": "Installation complete",
        "subtitle": "AGHOS has been successfully installed.",
        "hint": "You can reboot now or unmount the installation targets.",
        "reboot": "Reboot now",
        "unmount": "Unmount and stay in Live",
        "close": "Close installer",
        "syncing": "Flushing file system buffers…",
        "flushed": "Flush complete.",
        "ask_reboot": "Are you sure you want to reboot now?",
        "unmounting": "Unmounting targets…",
        "unmounted_ok": "✅ Everything under /mnt unmounted.",
        "unmount_warn": "⚠️ Some mount points could not be unmounted (busy).",
        "busy_processes": "Some targets are busy. Close processes or use lazy umount.",
        "anim_banner": "AGHOS — welcome aboard!",
    },
    "de": {
        "title": "Installation abgeschlossen",
        "subtitle": "AGHOS wurde erfolgreich installiert.",
        "hint": "Du kannst jetzt neu starten oder die Installations-Ziele aushängen.",
        "reboot": "Jetzt neu starten",
        "unmount": "Aushängen und im Live-System bleiben",
        "close": "Installer beenden",
        "syncing": "Schreibe Puffer auf Datenträger…",
        "flushed": "Schreiben abgeschlossen.",
        "ask_reboot": "Möchtest du jetzt wirklich neu starten?",
        "unmounting": "Hänge Mountpoints aus…",
        "unmounted_ok": "✅ Alles unter /mnt ausgehängt.",
        "unmount_warn": "⚠️ Einige Mountpoints sind belegt.",
        "busy_processes": "Einige Ziele sind belegt. Prozesse beenden oder Lazy-Umount nutzen.",
        "anim_banner": "AGHOS — willkommen an Bord!",
    },
    "es": {
        "title": "Instalación completa",
        "subtitle": "AGHOS se ha instalado correctamente.",
        "hint": "Puedes reiniciar ahora o desmontar los puntos de instalación.",
        "reboot": "Reiniciar ahora",
        "unmount": "Desmontar y permanecer en Live",
        "close": "Cerrar instalador",
        "syncing": "Vaciando buffers al disco…",
        "flushed": "Vaciado completado.",
        "ask_reboot": "¿Seguro que quieres reiniciar ahora?",
        "unmounting": "Desmontando puntos…",
        "unmounted_ok": "✅ Todo lo de /mnt desmontado.",
        "unmount_warn": "⚠️ Algunos puntos no pudieron desmontarse (ocupados).",
        "busy_processes": "Algunos destinos están ocupados. Cierra procesos o usa umount perezoso.",
        "anim_banner": "AGHOS — ¡bienvenido a bordo!",
    },
    "fr": {
        "title": "Installation terminée",
        "subtitle": "AGHOS a été installé avec succès.",
        "hint": "Vous pouvez redémarrer maintenant ou démonter les cibles d'installation.",
        "reboot": "Redémarrer maintenant",
        "unmount": "Démonter et rester en Live",
        "close": "Fermer l’installateur",
        "syncing": "Vidage des buffers sur le disque…",
        "flushed": "Vidage terminé.",
        "ask_reboot": "Voulez-vous vraiment redémarrer maintenant ?",
        "unmounting": "Démontage…",
        "unmounted_ok": "✅ Tout ce qui est sous /mnt a été démonté.",
        "unmount_warn": "⚠️ Certains points n'ont pas pu être démontés (occupés).",
        "busy_processes": "Certaines cibles sont occupées. Fermez les processus ou utilisez le démontage paresseux.",
        "anim_banner": "AGHOS — bienvenue à bord !",
    },
}

AGHOS_BG = QColor(12, 15, 18)            # tło
AGHOS_NEON = QColor(80, 180, 255)        # niebieski neon
AGHOS_NEON_GLOW = QColor(80, 180, 255, 70)

# ---- Generator runicznych linii ----

RUNES = list("ᚠᚢᚦᚨᚱᚲᚷᚹᚺᚾᛁᛃᛇᛈᛉᛊᛏᛒᛖᛗᛚᛜᛟᛞᛠᛡᛣᛥ")
RUNE_PUNCT = list("᛫᛬᛭·•")
ICONS = ["✧", "⚙", "◆", "▣", "⛓", "⌁", "※", "☼", "⌘", "☯", "➤", "➣", "➟"]

LATIN_TO_RUNE = {
    **{c: RUNES[i % len(RUNES)] for i, c in enumerate("abcdefghijklmnopqrstuvwxyz")},
    **{c.upper(): RUNES[(i+7) % len(RUNES)] for i, c in enumerate("abcdefghijklmnopqrstuvwxyz")},
    **{d: RUNES[(i*3) % len(RUNES)] for i, d in enumerate("0123456789")},
    " ": " ",
    "-": random.choice(RUNE_PUNCT),
    "_": random.choice(RUNE_PUNCT),
    ".": random.choice(RUNE_PUNCT),
    "/": random.choice(RUNE_PUNCT),
    ":": random.choice(RUNE_PUNCT),
    "[": "ᛝ", "]": "ᛝ", "(": "ᛝ", ")": "ᛝ",
}

def runeify(s: str) -> str:
    return "".join(LATIN_TO_RUNE.get(ch, random.choice(RUNES + RUNE_PUNCT)) for ch in s)

class RuneStream:
    """Tworzy pacmanopodobne linie, ale runiczne i z pseudo-progressem."""
    def __init__(self):
        self.step = 0
        self.pkg_idx = 0
        self.progress = 0
        self.pkgs = [
            "kernel-shard", "wyrd-lib", "mead-utils", "stone-driver",
            "mithril-core", "hugin", "munin", "futhark-db", "ragnar-ui",
            "valkyrie-net", "heimdall", "yggdrasil"
        ]

    def next_line(self) -> str:
        self.step += 1
        icon = random.choice(ICONS)

        # Co kilka kroków — pseudo pasek postępu
        if self.step % 5 == 0:
            self.progress = (self.progress + random.randint(3, 12)) % 101
            bar_len = 28
            filled = int(bar_len * self.progress / 100)
            bar = "█" * filled + "░" * (bar_len - filled)
            base = f"[{bar}] {self.progress:3d}%  {self.pkgs[self.pkg_idx % len(self.pkgs)]}"
            return f"{icon} {runeify(base)}"

        actions = [
            "synchronizing rune databases",
            "resolving dependencies",
            "installing",
            "checking integrity",
            "upgrading",
            "linking shared totems",
            "verifying signatures",
            "assembling shards",
        ]
        action = random.choice(actions)
        pkg = self.pkgs[self.pkg_idx % len(self.pkgs)]
        self.pkg_idx += random.choice([0, 1])  # czasem ten sam „pakiet”
        base = f":: {action} {pkg}"
        if random.random() < 0.4:
            sp = f"{random.uniform(2.0, 42.0):0.1f} MiB/s"
            base += f"  ({sp})"
        return f"{icon} {runeify(base)}"

# ---- Widget: przewijający się, świecący „terminal runiczny” ----

class RuneTerminal(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(260)
        self.setAutoFillBackground(True)

        self.font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        self.font.setPointSize(12)
        self.font.setStyleStrategy(QFont.PreferDefault)

        self.stream = RuneStream()
        self.lines = []
        self.line_h = None
        self.offset = 0.0
        self.speed = 0.8  # px/tick
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(16)  # ~60 FPS

        self._fill_initial()

    def sizeHint(self):
        return QSize(720, 320)

    def _fill_initial(self):
        fm = self.fontMetrics()
        self.line_h = fm.lineSpacing()
        visible = max(5, int(self.height() / self.line_h) + 3)
        self.lines = [self.stream.next_line() for _ in range(visible)]

    def resizeEvent(self, _):
        self._fill_initial()
        self.update()

    def _tick(self):
        self.offset += self.speed
        if self.offset >= self.line_h:
            self.offset -= self.line_h
            self.lines.pop(0)
            self.lines.append(self.stream.next_line())
        self.update()

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.fillRect(self.rect(), AGHOS_BG)
        painter.setFont(self.font)

        y_base = self.height() - self.offset
        for i in range(len(self.lines)-1, -1, -1):
            y = y_base - (len(self.lines)-1 - i) * self.line_h
            if y < -self.line_h or y > self.height() + self.line_h:
                continue
            self._draw_glow_text(painter, 16, int(y), self.lines[i])

    def _draw_glow_text(self, painter: QPainter, x: int, y: int, text: str):
        painter.setPen(AGHOS_NEON_GLOW)
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (0, 0), (2, 1), (-2, -1)):
            painter.drawText(x + dx, y + dy, text)
        painter.setPen(AGHOS_NEON)
        painter.drawText(x, y, text)

# ---- Okno końcowe z przyciskami ----

class FinishWindow(QWidget):
    def __init__(self, lang="pl", console=None):
        super().__init__()
        self.lang = lang if lang in TR else "en"
        self.tr = TR[self.lang]
        self.console = console

        self.setWindowTitle(self.tr["title"])
        self.resize(780, 520)

        v = QVBoxLayout(self)
        v.setSpacing(10)

        title = QLabel(self.tr["subtitle"])
        title.setAlignment(Qt.AlignCenter)
        f2 = QFont(); f2.setPointSize(16); f2.setBold(True)
        title.setFont(f2)
        title.setStyleSheet("color: rgb(200,200,200);")
        v.addWidget(title)

        hint = QLabel(self.tr["hint"])
        hint.setAlignment(Qt.AlignCenter)
        hint.setWordWrap(True)
        hint.setStyleSheet("color: rgb(150,150,150);")
        v.addWidget(hint)

        self.terminal = RuneTerminal()
        v.addWidget(self.terminal)

        banner = QLabel(self.tr["anim_banner"])
        banner.setAlignment(Qt.AlignCenter)
        fb = QFont(); fb.setPointSize(12); fb.setBold(True)
        banner.setFont(fb)
        banner.setStyleSheet("color: rgb(120,180,255);")
        v.addWidget(banner)

        btns = QHBoxLayout()
        self.btn_reboot = QPushButton(self.tr["reboot"])
        self.btn_unmount = QPushButton(self.tr["unmount"])
        self.btn_close = QPushButton(self.tr["close"])
        for b in (self.btn_reboot, self.btn_unmount, self.btn_close):
            b.setMinimumHeight(36)
        btns.addWidget(self.btn_reboot)
        btns.addWidget(self.btn_unmount)
        btns.addWidget(self.btn_close)
        v.addLayout(btns)

        self.btn_reboot.clicked.connect(self._on_reboot)
        self.btn_unmount.clicked.connect(self._on_unmount)
        # Zamykamy CAŁY instalator:
        self.btn_close.clicked.connect(QApplication.instance().quit)

        # estetyka tła
        self.setStyleSheet("""
            QWidget { background: rgb(20,23,27); }
            QPushButton { background: rgb(40,44,52); color: white; border: 1px solid rgb(70,80,90); border-radius: 6px; }
            QPushButton:hover { background: rgb(55,60,70); }
            QPushButton:pressed { background: rgb(30,34,40); }
        """)

    def _flush_writes(self):
        if self.console: self.console.append(self.tr["syncing"])
        try:
            subprocess.run(["sync"], check=False)
            t0 = time.time()
            while time.time() - t0 < 30:
                dirty = writeback = 0
                with open("/proc/meminfo") as f:
                    for line in f:
                        if line.startswith("Dirty:"):
                            dirty = int(line.split()[1])
                        elif line.startswith("Writeback:"):
                            writeback = int(line.split()[1])
                if dirty <= 4 and writeback <= 4:
                    break
                time.sleep(0.3)
            subprocess.run(["udevadm", "settle"], check=False)
        except Exception as e:
            if self.console: self.console.append(f"⚠️ flush: {e}")
        if self.console: self.console.append(self.tr["flushed"])

    def _umount_all_under_mnt(self):
        if self.console: self.console.append(self.tr["unmounting"])
        targets = []
        try:
            out = subprocess.run(
                ["findmnt", "-Rrno", "TARGET", "/mnt"],
                capture_output=True, text=True, check=False
            ).stdout.strip().splitlines()
            extras = ["/mnt/tmp", "/mnt/run", "/mnt/dev", "/mnt/sys", "/mnt/proc",
                      "/mnt/boot/efi", "/mnt/boot/EFI", "/mnt/boot", "/mnt/efi", "/mnt/home", "/mnt"]
            for t in extras:
                if t not in out:
                    out.append(t)
            targets = sorted(set(filter(os.path.exists, out)), key=lambda p: (-len(p), p))
        except Exception:
            targets = ["/mnt/tmp", "/mnt/run", "/mnt/dev", "/mnt/sys", "/mnt/proc",
                       "/mnt/boot/efi", "/mnt/boot/EFI", "/mnt/boot", "/mnt/efi", "/mnt/home", "/mnt"]

        failed = []
        for t in targets:
            res = subprocess.run(["umount", "-R", t], capture_output=True, text=True)
            if res.returncode != 0:
                if t != "/mnt":
                    res2 = subprocess.run(["umount", "-l", t], capture_output=True, text=True)
                    if res2.returncode != 0:
                        failed.append((t, res.stderr or res2.stderr))
                else:
                    failed.append((t, res.stderr))
        return failed

    def _on_reboot(self):
        if QMessageBox.question(self, self.tr["title"], self.tr["ask_reboot"],
                                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        self._flush_writes()
        self._umount_all_under_mnt()
        try:
            rc = subprocess.run(["systemctl", "reboot", "-i"]).returncode
            if rc != 0:
                subprocess.run(["reboot"])
        except Exception:
            subprocess.run(["reboot"])

    def _on_unmount(self):
        self._flush_writes()
        failed = self._umount_all_under_mnt()
        if failed:
            if self.console:
                for t, err in failed:
                    self.console.append(f"⚠️ umount {t}: {err.strip() if err else 'busy'}")
            QMessageBox.warning(self, self.tr["title"], f"{self.tr['unmount_warn']}\n{self.tr['busy_processes']}")
        else:
            QMessageBox.information(self, self.tr["title"], self.tr["unmounted_ok"])

def run(lang, console):
    app = QApplication.instance() or QApplication(sys.argv)
    w = FinishWindow(lang, console)
    w.show()
    if hasattr(console, "append"):
        console.append("✅ Instalacja zakończona — ekran finałowy gotowy.")
    return w

if __name__ == "__main__":
    class DummyConsole:
        def append(self, txt): print(txt)
    app = QApplication(sys.argv)
    w = FinishWindow("pl", DummyConsole())
    w.show()
    sys.exit(app.exec())
