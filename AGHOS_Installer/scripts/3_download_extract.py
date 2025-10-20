#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AGHOS Post-Install Wizard
- Pobranie i weryfikacja RootFS (SHA512 z widocznym postępem)
- Rozpakowanie do /mnt
- Generowanie /etc/fstab (UUID/PARTUUID) + dopisanie SWAP
- timezone, locale, vconsole (FONT/FONT_MAP/KEYMAP)
- hostname/hosts, sudoers dla wheel, hwclock
- instalacja GRUB (UEFI/BIOS) z wykryciem ESP jako mountpointu
- branding os-release (pełny) + symlink /etc/os-release -> /usr/lib/os-release
- wykrycie Windows i dodanie wpisu do GRUB (41_windows)

UWAGA: Zakłada, że partycje docelowe (/, ewent. /boot lub /efi) są
zamontowane pod /mnt przed uruchomieniem. SWAP może być już aktywny
(ze skryptu 2); jeśli nie, spróbujemy go włączyć i dopiszemy do fstab.
"""

import sys
import os
import re
import time
import hashlib
import requests
import urllib.request
import subprocess
from typing import Optional, Tuple, List
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QFormLayout, QGroupBox,
    QLabel, QComboBox, QProgressBar, QPushButton,
    QMessageBox, QLineEdit
)
from PySide6.QtCore import QProcess, QTimer

_post_install_wizard = None

translations = {
    "pl": {
        "download_group": "1. Pobranie RootFS",
        "select_archive": "Wybierz archiwum:",
        "progress": "Postęp:",
        "download_button": "Pobierz i rozpakuj",
        "progress_speed": "Prędkość:",
        "usb_warning": (
            "Jeśli instalujesz system na dysku USB, to rozpakowywanie "
            "archiwum może potrwać nawet koło 10 minut."
        ),
        "config_group": "2. Konfiguracja systemu",
        "timezone": "Strefa czasowa:",
        "locale": "Locale:",
        "font": "Czcionka konsoli:",
        "charset_map": "Mapowanie znaków:",
        "username": "Nazwa użytkownika:",
        "user_pass": "Hasło użytkownika:",
        "root_pass": "Hasło roota:",
        "apply_config": "Zastosuj konfigurację",
        "config_done": "Konfiguracja zakończona.",
        "finish_button": "Usuń machine-id i zakończ",
        "tz_default": "Europe/Warsaw",
        "locale_default": "pl_PL.UTF-8",
        "font_default": "Lat2-Terminus16",
        "map_default": "8859-2"
    },
    "en": {
        "download_group": "1. Download RootFS",
        "select_archive": "Select archive:",
        "progress": "Progress:",
        "download_button": "Download & Extract",
        "progress_speed": "Speed:",
        "usb_warning": (
            "If installing on a USB drive, extraction may take up to 10 minutes."
        ),
        "config_group": "2. System Configuration",
        "timezone": "Timezone:",
        "locale": "Locale:",
        "font": "Console font:",
        "charset_map": "Charset mapping:",
        "username": "Username:",
        "user_pass": "User password:",
        "root_pass": "Root password:",
        "apply_config": "Apply configuration",
        "config_done": "Configuration done.",
        "finish_button": "Clean machine-id & Finish",
        "tz_default": "UTC",
        "locale_default": "en_US.UTF-8",
        "font_default": "Lat1-Terminus16",
        "map_default": "8859-1"
    },
    "fr": {
        "download_group": "1. Téléchargement RootFS",
        "select_archive": "Sélectionnez l'archive :",
        "progress": "Progression :",
        "download_button": "Télécharger et extraire",
        "progress_speed": "Vitesse :",
        "usb_warning": (
            "Si vous installez sur USB, l'extraction peut prendre jusqu'à 10 minutes."
        ),
        "config_group": "2. Configuration du système",
        "timezone": "Fuseau horaire :",
        "locale": "Locale :",
        "font": "Police console :",
        "charset_map": "Codage caractères :",
        "username": "Nom d'utilisateur :",
        "user_pass": "Mot de passe utilisateur :",
        "root_pass": "Mot de passe root :",
        "apply_config": "Appliquer configuration",
        "config_done": "Configuration terminée.",
        "finish_button": "Supprimer machine-id & Terminer",
        "tz_default": "Europe/Paris",
        "locale_default": "fr_FR.UTF-8",
        "font_default": "Lat15-Terminus16",
        "map_default": "8859-15"
    },
    "de": {
        "download_group": "1. RootFS herunterladen",
        "select_archive": "Archiv auswählen:",
        "progress": "Fortschritt:",
        "download_button": "Herunterladen & Entpacken",
        "progress_speed": "Geschwindigkeit:",
        "usb_warning": (
            "Bei USB-Installation kann das Entpacken bis zu 10 Minuten dauern."
        ),
        "config_group": "2. Systemkonfiguration",
        "timezone": "Zeitzone:",
        "locale": "Locale:",
        "font": "Konsolenschriftart:",
        "charset_map": "Zeichensatz Zuordnung:",
        "username": "Benutzername:",
        "user_pass": "Benutzerpasswort:",
        "root_pass": "Root-Passwort:",
        "apply_config": "Konfiguration übernehmen",
        "config_done": "Konfiguration abgeschlossen.",
        "finish_button": "Machine-id löschen & Beenden",
        "tz_default": "Europe/Berlin",
        "locale_default": "de_DE.UTF-8",
        "font_default": "Lat15-Terminus16",
        "map_default": "8859-15"
    },
    "es": {
        "download_group": "1. Descarga RootFS",
        "select_archive": "Selecciona el archivo:",
        "progress": "Progreso:",
        "download_button": "Descargar y extraer",
        "progress_speed": "Velocidad:",
        "usb_warning": (
            "Si instalas en USB, la extracción puede tardar hasta 10 minutos."
        ),
        "config_group": "2. Configuración del sistema",
        "timezone": "Zona horaria:",
        "locale": "Locale:",
        "font": "Fuente de consola:",
        "charset_map": "Mapeo charset:",
        "username": "Usuario:",
        "user_pass": "Contraseña usuario:",
        "root_pass": "Contraseña root:",
        "apply_config": "Aplicar configuración",
        "config_done": "Configuración completada.",
        "finish_button": "Eliminar machine-id y terminar",
        "tz_default": "Europe/Madrid",
        "locale_default": "es_ES.UTF-8",
        "font_default": "Lat15-Terminus16",
        "map_default": "8859-15"
    }
}

class PostInstallWizard(QWidget):
    def __init__(self, lang='pl', console=None):
        super().__init__()
        self.lang = lang
        self.tr = translations.get(lang, translations['en'])
        self.console = console or self

        self.setWindowTitle(self.tr['download_group'])
        self.resize(600, 700)
        self.layout = QVBoxLayout(self)

        # Step 1: Download
        self._build_download_group()
        # USB warning
        self._build_usb_warning()
        # Step 2: Config (disabled until extraction)
        self._build_config_group()
        self.config_group.setEnabled(False)
        # Step 3: Finish (disabled)
        self._build_finish_button()
        self.finish_btn.setEnabled(False)

        # Defaults
        self.tz_combo.setCurrentText(self.tr['tz_default'])
        self.locale_combo.setCurrentText(self.tr['locale_default'])
        self.font_combo.setCurrentText(self.tr['font_default'])
        self.map_combo.setCurrentText(self.tr['map_default'])

    # ---- logging wrapper ----
    def append(self, msg:str):
        print(msg)
    def log(self, msg: str):
        if hasattr(self.console, "append"):
            self.console.append(msg)
        else:
            self.append(msg)

    def _build_download_group(self):
        gb = QGroupBox(self.tr['download_group'])
        form = QFormLayout()

        self.combo = QComboBox()
        try:
            r = requests.get("https://aghos.agh.edu.pl/distro/", timeout=10)
            files = re.findall(r'href=["\']([^"\']+\.tar\.zst)["\']', r.text)
            files = sorted(set(files), reverse=True)
        except Exception:
            files = ['latest-rootfs.tar.zst']
        self.combo.addItems(files)
        idx = self.combo.findText('latest-rootfs.tar.zst')
        if idx != -1:
            self.combo.setCurrentIndex(idx)
        form.addRow(self.tr['select_archive'], self.combo)

        self.progress = QProgressBar(); self.progress.setRange(0,100)
        form.addRow(self.tr['progress'], self.progress)

        self.speed_label = QLabel("0 KB/s")
        form.addRow(self.tr['progress_speed'], self.speed_label)

        self.download_btn = QPushButton(self.tr['download_button'])
        self.download_btn.clicked.connect(self._on_download)
        form.addRow(self.download_btn)

        gb.setLayout(form)
        self.layout.addWidget(gb)

    def _build_usb_warning(self):
        self.info_label = QLabel(self.tr['usb_warning'])
        self.info_label.setWordWrap(True)
        self.info_label.hide()
        self.layout.addWidget(self.info_label)

    def _build_config_group(self):
        self.config_group = QGroupBox(self.tr['config_group'])
        form = QFormLayout()

        # Timezone
        self.tz_combo = QComboBox()
        zones=[]
        for r,d,f in os.walk('/usr/share/zoneinfo'):
            for fn in f:
                rel=os.path.relpath(os.path.join(r,fn), '/usr/share/zoneinfo')
                if not rel.startswith(('posix','right','Etc')):
                    zones.append(rel)
        zones.sort()
        self.tz_combo.addItems(zones)
        form.addRow(self.tr['timezone'], self.tz_combo)

        # Locale (selector for default LANG)
        self.locale_combo=QComboBox()
        for loc in ['en_US.UTF-8','pl_PL.UTF-8','fr_FR.UTF-8','de_DE.UTF-8','es_ES.UTF-8']:
            self.locale_combo.addItem(loc)
        form.addRow(self.tr['locale'], self.locale_combo)

        # Font & charset (vconsole) — poprawne nazwy i szerszy wybór
        self.font_combo=QComboBox()
        for f in [
            "Lat2-Terminus16","Lat2-Terminus14","Lat2-Terminus20",
            "Lat2-TerminusBold16","Terminus16","Lat15-Terminus16","Lat1-Terminus16"
        ]:
            self.font_combo.addItem(f)
        form.addRow(self.tr['font'], self.font_combo)

        self.map_combo=QComboBox()
        for m in ["8859-2", "8859-1", "8859-15", "cp852", "cp1250", "koi8-r"]:
            self.map_combo.addItem(m)
        form.addRow(self.tr['charset_map'], self.map_combo)

        # Users
        self.user_edit=QLineEdit(); form.addRow(self.tr['username'], self.user_edit)
        self.user_pass=QLineEdit(); self.user_pass.setEchoMode(QLineEdit.Password)
        form.addRow(self.tr['user_pass'], self.user_pass)
        self.user_pass_repeat=QLineEdit(); self.user_pass_repeat.setEchoMode(QLineEdit.Password)
        form.addRow(self.tr['user_pass']+" (powtórz):", self.user_pass_repeat)
        self.root_pass=QLineEdit(); self.root_pass.setEchoMode(QLineEdit.Password)
        form.addRow(self.tr['root_pass'], self.root_pass)
        self.root_pass_repeat=QLineEdit(); self.root_pass_repeat.setEchoMode(QLineEdit.Password)
        form.addRow(self.tr['root_pass']+" (powtórz):", self.root_pass_repeat)

        self.config_btn=QPushButton(self.tr['apply_config'])
        self.config_btn.clicked.connect(self._on_config)
        form.addRow(self.config_btn)

        self.config_group.setLayout(form)
        self.layout.addWidget(self.config_group)

    def _build_finish_button(self):
        self.finish_btn=QPushButton(self.tr['finish_button'])
        self.finish_btn.clicked.connect(self._on_finish)
        self.layout.addWidget(self.finish_btn)

    # ===== Helpery =====
    def _sha512sum(self, path: str) -> str:
        h = hashlib.sha512()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(1024*1024), b''):
                h.update(chunk)
        return h.hexdigest()

    def _sha512sum_with_progress(self, path: str) -> str:
        """Wariant z aktualizacją paska postępu i komunikatem."""
        try:
            total = os.path.getsize(path)
        except Exception:
            total = 0
        h = hashlib.sha512()
        done = 0
        self.speed_label.setText("Liczenie sumy… (na wolnym USB może to potrwać kilkanaście minut)")
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(1024*1024), b''):
                h.update(chunk)
                done += len(chunk)
                if total:
                    self.progress.setValue(min(100, int(done * 100 / total)))
                QApplication.processEvents()
        self.progress.setValue(100)
        return h.hexdigest()

    def _get_id_for(self, dev: str) -> Tuple[Optional[str], Optional[str]]:
        # UUID
        r = subprocess.run(['blkid', '-s', 'UUID', '-o', 'value', dev], capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            return 'UUID', r.stdout.strip()
        # PARTUUID
        r = subprocess.run(['blkid', '-s', 'PARTUUID', '-o', 'value', dev], capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            return 'PARTUUID', r.stdout.strip()
        return None, None

    def _is_mount_in_mnt(self, rel: str) -> bool:
        target = os.path.join('/mnt', rel.strip('/'))
        try:
            out = subprocess.run(['findmnt', '-no', 'TARGET', target], capture_output=True, text=True)
            return out.returncode == 0 and out.stdout.strip() == target
        except Exception:
            return False

    def _detect_root_disk_for_mnt(self):
        try:
            part = subprocess.run(
                ['findmnt', '-n', '-o', 'SOURCE', '/mnt'],
                capture_output=True, text=True, check=True
            ).stdout.strip()
            disk = re.sub(r'p?\d+$', '', part)
            return disk if disk.startswith('/dev/') else None
        except Exception:
            return None

    # ===== Akcje =====
    def _on_download(self):
        self.info_label.show()
        file=self.combo.currentText()
        url=f"https://aghos.agh.edu.pl/distro/{file}"
        local=f"/root/{file}"
        chk_url=url+".sha512"

        def want_download() -> bool:
            try:
                rchk = requests.get(chk_url, timeout=10)
                exp = rchk.text.split()[0].strip()
            except Exception:
                self.log("⚠️  Nie mogę pobrać sumy .sha512 – spróbuję pobrać archiwum.")
                return True
            if os.path.exists(local):
                try:
                    self.progress.setRange(0,100); self.progress.setValue(0)
                    self.speed_label.setText("Liczenie sumy…")
                    got = self._sha512sum_with_progress(local)
                except Exception:
                    return True
                if got == exp:
                    self.log("Cache OK, pomijam pobieranie.")
                    return False
                else:
                    try: os.remove(local)
                    except Exception: pass
                    return True
            return True

        need = want_download()
        if need:
            self.log(f"Pobieranie {url}")
            try:
                req=urllib.request.urlopen(url)
                total=int(req.getheader('Content-Length') or 0)
            except Exception as e:
                QMessageBox.critical(self,"Błąd",str(e)); return
            dl=0; start=time.time()
            with open(local,'wb') as f:
                while True:
                    chunk=req.read(8192)
                    if not chunk: break
                    f.write(chunk); dl+=len(chunk)
                    if total:
                        pct=int(dl*100/total)
                        self.progress.setValue(pct)
                    elapsed=max(time.time()-start,0.001)
                    sp=dl/elapsed
                    disp=f"{sp/1024**2:0.2f} MB/s" if sp>1024**2 else f"{sp/1024:0.0f} KB/s"
                    self.speed_label.setText(disp)
                    QApplication.processEvents()
            self.log("Pobieranie zakończone. Liczę sumę SHA-512 — to może potrwać…")
            try:
                rchk = requests.get(chk_url, timeout=10)
                exp = rchk.text.split()[0].strip()
                got = self._sha512sum_with_progress(local)
                if got != exp:
                    QMessageBox.critical(self, "Błąd", "Checksum mismatch po pobraniu"); return
                else:
                    self.log("Suma kontrolna OK.")
            except Exception as e:
                self.log(f"⚠️  Nie udało się sprawdzić sumy: {e}")

        self.log("Rozpakowywanie…")
        self.progress.setRange(0,0)
        proc=QProcess(self)
        proc.finished.connect(self._on_extraction_finished)
        proc.start('bsdtar',['-xpf',local,'-C','/mnt'])

    def _on_extraction_finished(self):
        self.progress.setRange(0,100)
        self.progress.setValue(100)
        self.log("Rozpakowywanie zakończone.")
        self.config_group.setEnabled(True)

    def _on_config(self):
        # wizualny sygnał pracy
        self.progress.setRange(0,0)
        self.speed_label.setText("Zapisywanie ustawień…")

        # fstab – na podstawie findmnt (odporne na Btrfs subvol)
        self.log("Generuję /mnt/etc/fstab (na podstawie UUID/PARTUUID)")
        entries: List[str] = []
        try:
            out = subprocess.run(
                ['findmnt', '-Rrno', 'SOURCE,TARGET,FSTYPE,OPTIONS', '/mnt'],
                capture_output=True, text=True, check=True
            )
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, "Błąd", f"findmnt nie powiodło się:\n{e.stderr}")
            return

        def _clean_src(dev: str) -> str:
            return re.sub(r'\[.*\]$', '', dev)

        for line in out.stdout.strip().splitlines():
            parts = line.split(None, 3)
            if len(parts) < 4:
                continue
            src, target, fstype, options = parts[:4]
            src = _clean_src(src)
            target = re.sub(r'^[├└─│\s]+', '', target).strip()

            if not src.startswith('/dev/'):
                continue

            id_key, uuid = self._get_id_for(src)
            if not uuid:
                self.log(f"⚠️  Pomijam {src}: brak UUID/PARTUUID")
                continue

            if target == '/mnt':
                mountpoint = '/'
            elif target.startswith('/mnt/'):
                mountpoint = target.replace('/mnt', '', 1)
            else:
                mountpoint = target

            if mountpoint == '/' and fstype == 'ext4':
                opts = 'noatime,nodiratime,lazytime,commit=60,errors=remount-ro'
            else:
                opts = ','.join([o for o in options.split(',') if o != 'rw']) or 'defaults'

            dump = 0
            passno = 1 if mountpoint == '/' else 2
            entries.append(f"{id_key}={uuid}\t{mountpoint}\t{fstype}\t{opts}\t{dump} {passno}")

        os.makedirs('/mnt/etc', exist_ok=True)
        if not entries:
            # fallback minimalny
            try:
                root_src = subprocess.run(['findmnt','-n','-o','SOURCE','/mnt'],
                                          capture_output=True, text=True, check=True).stdout.strip()
                root_fst = subprocess.run(['findmnt','-n','-o','FSTYPE','/mnt'],
                                          capture_output=True, text=True, check=True).stdout.strip()
                key, val = self._get_id_for(_clean_src(root_src))
                if key and val and root_fst:
                    entries.append(f"{key}={val}\t/\t{root_fst}\tnoatime\t0 1")
            except Exception as e:
                self.log(f"⚠️  Fallback fstab niepełny: {e}")

        # --- SWAP: dopisz do fstab + upewnij się, że aktywny ---
        swap_lines = []

        # 1) aktywny swap (preferowane) — pomiń zram*
        try:
            r = subprocess.run(['swapon', '--noheadings', '--show=NAME'],
                               capture_output=True, text=True, check=False)
            active_swaps = [d for d in r.stdout.strip().splitlines() if d and not os.path.basename(d).startswith('zram')]
        except Exception:
            active_swaps = []

        # 2) jeśli nic nieaktywne, poszukaj TYPE=swap w blkid
        if not active_swaps:
            try:
                r = subprocess.run(['blkid', '-t', 'TYPE=swap', '-o', 'device'],
                                   capture_output=True, text=True, check=False)
                active_swaps = [d for d in r.stdout.strip().splitlines() if d and not os.path.basename(d).startswith('zram')]
            except Exception:
                active_swaps = []

        # 3) jeśli swapfile w docelowym systemie
        if os.path.exists('/mnt/swapfile'):
            swap_lines.append("/swapfile\tnone\tswap\tdefaults\t0 0")
            # można od razu włączyć:
            subprocess.run(['swapon', '/mnt/swapfile'], check=False)

        # 4) zbuduj wpisy po UUID/PARTUUID i ewentualnie włącz jeśli nieaktywny
        for dev in active_swaps:
            if not dev:
                continue
            if dev.startswith('/dev/'):
                key, val = self._get_id_for(dev)
                if key and val:
                    swap_lines.append(f"{key}={val}\tnone\tswap\tdefaults\t0 0")
                # aktywuj (bezpiecznie – jeśli już aktywny, rc=0)
                subprocess.run(['swapon', dev], check=False)
            elif dev.startswith('/'):  # np. /swapfile spoza /mnt
                # nie dodawaj /swapfile hosta live do fstab docelowego
                pass

        # deduplikacja swap_lines
        seen = set()
        dedup = []
        for ln in swap_lines:
            if ln not in seen:
                seen.add(ln); dedup.append(ln)
        swap_lines = dedup

        if swap_lines:
            entries.extend(swap_lines)
            self.log(f"Dodano wpisy SWAP do fstab (liczba: {len(swap_lines)})")
        else:
            self.log("Brak wykrytego SWAP do dopisania w fstab (OK, jeśli używasz zram lub swapfile tworzony później).")

        with open('/mnt/etc/fstab', 'w') as f:
            f.write("\n".join(entries) + ("\n" if entries else ""))

        self.log(f"Zapisano /mnt/etc/fstab (wpisów: {len(entries)})")

        # montujemy pseudo-fs po fstab, z --make-rslave
        for fs in ('proc','sys','dev','run'):
            dst=f"/mnt/{fs}"; os.makedirs(dst,exist_ok=True)
            if fs=='proc':
                subprocess.run(['mount','-t','proc','proc',dst],check=False)
            else:
                subprocess.run(['mount','--rbind',f"/{fs}",dst],check=False)
                subprocess.run(['mount','--make-rslave',dst],check=False)
        os.makedirs('/mnt/tmp',exist_ok=True)
        subprocess.run(['mount','--rbind','/tmp','/mnt/tmp'],check=False)
        subprocess.run(['mount','--make-rslave','/mnt/tmp'],check=False)

        # timezone
        tz=self.tz_combo.currentText()
        self.log(f"Strefa: {tz}")
        subprocess.run(['arch-chroot','/mnt','ln','-sf',f"/usr/share/zoneinfo/{tz}",'/etc/localtime'])

        # locale
        locales = ["en_US.UTF-8", "pl_PL.UTF-8", "fr_FR.UTF-8", "de_DE.UTF-8", "es_ES.UTF-8"]
        with open('/mnt/etc/locale.gen','w') as f:
            for loc in locales:
                f.write(f"{loc} UTF-8\n")
        subprocess.run(['arch-chroot','/mnt','locale-gen'], check=False)
        with open('/mnt/etc/locale.conf','w') as f:
            f.write(f"LANG={self.locale_combo.currentText()}\n")

        # vconsole: FONT + FONT_MAP + KEYMAP
        font=self.font_combo.currentText(); mp=self.map_combo.currentText()
        lang = self.locale_combo.currentText().split('.')[0][:2]
        keymap = {'pl':'pl','de':'de','fr':'fr','es':'es'}.get(lang,'us')
        self.log(f"vconsole: KEYMAP={keymap} FONT={font} FONT_MAP={mp}")
        subprocess.run(['arch-chroot','/mnt','bash','-c',
            f"printf 'KEYMAP={keymap}\nFONT={font}\nFONT_MAP={mp}\n' > /etc/vconsole.conf"], check=False)

        # branding: os-release (pełny + symlink)
        self.log("Branding systemu jako AGHOS")
        os_release = """NAME="Arch Greybeards Hall Linux"
PRETTY_NAME="AGHOS"
ID=arch
BUILD_ID=rolling
ANSI_COLOR="38;2;0;105;60"
HOME_URL="https://aghos.agh.edu.pl"
DOCUMENTATION_URL="https://aghos.agh.edu.pl"
SUPPORT_URL="https://aghos.agh.edu.pl"
BUG_REPORT_URL="https://aghos.agh.edu.pl"
PRIVACY_POLICY_URL="https://aghos.agh.edu.pl"
LOGO=aghos-logo
"""
        os.makedirs('/mnt/usr/lib', exist_ok=True)
        with open('/mnt/usr/lib/os-release', 'w') as f:
            f.write(os_release)
        os.makedirs('/mnt/etc', exist_ok=True)
        try:
            if os.path.exists('/mnt/etc/os-release') and not os.path.islink('/mnt/etc/os-release'):
                os.remove('/mnt/etc/os-release')
            if os.path.islink('/mnt/etc/os-release'):
                os.unlink('/mnt/etc/os-release')
            os.symlink('/usr/lib/os-release', '/mnt/etc/os-release')
        except Exception as e:
            self.log(f"⚠️  Nie udało się utworzyć symlinku /etc/os-release: {e}")

        # hostname + hosts jeżeli nie istnieją
        if not os.path.exists('/mnt/etc/hostname'):
            with open('/mnt/etc/hostname','w') as f:
                f.write('aghos\n')
        with open('/mnt/etc/hosts','w') as f:
            f.write('127.0.0.1\tlocalhost\n::1\tlocalhost\n127.0.1.1\taghos\n')

        # users
        if self.user_pass.text()!=self.user_pass_repeat.text():
            QMessageBox.critical(self,"Błąd","Hasła użytkownika różne"); return
        if self.root_pass.text()!=self.root_pass_repeat.text():
            QMessageBox.critical(self,"Błąd","Hasła root różne"); return
        usr=self.user_edit.text().strip()
        if usr:
            self.log(f"Tworzę {usr} (kopiuję /etc/skel)…")
            subprocess.run(['arch-chroot','/mnt','useradd','-m','-G','wheel',usr], check=False)
            subprocess.run(['arch-chroot','/mnt','bash','-c', f"echo {usr}:{self.user_pass.text()}|chpasswd"], check=False)
        if self.root_pass.text():
            self.log("Ustawiam hasło roota")
            subprocess.run(['arch-chroot','/mnt','bash','-c', f"echo root:{self.root_pass.text()}|chpasswd"], check=False)
        # włącz sudo dla wheel
        subprocess.run(['arch-chroot','/mnt','bash','-c',
            "install -Dm0640 /dev/stdin /etc/sudoers.d/10-wheel <<<'%wheel ALL=(ALL:ALL) ALL' && chmod 0440 /etc/sudoers.d/10-wheel"], check=False)

        # hwclock
        subprocess.run(['arch-chroot','/mnt','hwclock','--systohc'], check=False)

        # =======================
        # GRUB: instalacja i konfiguracja
        # + wykrywanie Windows i dodanie wpisu
        # =======================
        os.makedirs('/mnt/boot', exist_ok=True)
        os.makedirs('/mnt/boot/EFI/BOOT', exist_ok=True)
        self.log("Instaluję GRUB")

        # wykryj ESP jako istniejący mountpoint wewnątrz chroota
        efi_dir = None
        for cand in ['/boot', '/efi', '/boot/efi', '/boot/EFI']:
            if self._is_mount_in_mnt(cand):
                efi_dir = cand
                break

        # Funkcja pomocnicza: wykrycie Windows
        def detect_windows(efi_dir_: Optional[str]) -> Tuple[bool, bool]:
            """
            Zwraca (windows_uefi, windows_bios).
            - UEFI: sprawdza obecność pliku EFI/Microsoft/Boot/bootmgfw.efi na ESP.
            - BIOS: heurystyka: obecność partycji NTFS w systemie.
            """
            win_uefi = False
            win_bios = False
            try:
                if efi_dir_:
                    candidate = os.path.join('/mnt', efi_dir_.strip('/'), 'EFI', 'Microsoft', 'Boot', 'bootmgfw.efi')
                    if os.path.exists(candidate):
                        win_uefi = True
                # BIOS / MBR – sprawdź, czy są w systemie wolumeny NTFS
                if not win_uefi:
                    r = subprocess.run(['blkid', '-t', 'TYPE=ntfs', '-o', 'device'],
                                       capture_output=True, text=True, check=False)
                    ntfs_parts = [ln.strip() for ln in r.stdout.splitlines() if ln.strip()]
                    if ntfs_parts:
                        win_bios = True
            except Exception as e:
                self.log(f"⚠️  Błąd wykrywania Windows: {e}")
            return win_uefi, win_bios

        windows_uefi, windows_bios = detect_windows(efi_dir)

        if efi_dir:
            # UEFI instalacja
            self.log(f"UEFI: --efi-directory={efi_dir}")
            r = subprocess.run([
                'arch-chroot','/mnt','grub-install',
                '--target=x86_64-efi',
                f'--efi-directory={efi_dir}',
                '--bootloader-id=AGHOS',
                '--removable'
            ], check=False, capture_output=True, text=True)
            if r.returncode != 0:
                self.log(f"⚠️  grub-install (UEFI) rc={r.returncode}: {r.stderr.strip()}")
        else:
            # BIOS instalacja
            disk = self._detect_root_disk_for_mnt()
            if not disk:
                self.log("Nie udało się wykryć dysku dla /mnt – próbuję /dev/sda (fallback).")
                disk = '/dev/sda'
            else:
                self.log(f"Tryb BIOS: instaluję na {disk}")
            r = subprocess.run(['arch-chroot','/mnt','grub-install','--boot-directory=/boot', disk],
                               check=False, capture_output=True, text=True)
            if r.returncode != 0:
                self.log(f"⚠️  grub-install (BIOS) rc={r.returncode}: {r.stderr.strip()}")

        # Branding i ustawienia GRUB
        subprocess.run(['cp', '/boot/logo.png', '/mnt/boot/logo.png'], check=False)
        # Włącz wpis tła i dystrybutora
        subprocess.run(['arch-chroot','/mnt','bash','-c',
            'if grep -qE "^\\s*GRUB_BACKGROUND=" /etc/default/grub; '
            'then sed -i "s|^\\s*GRUB_BACKGROUND=.*|GRUB_BACKGROUND=\\"/boot/logo.png\\"|" /etc/default/grub; '
            'else echo "GRUB_BACKGROUND=\\"/boot/logo.png\\"" >> /etc/default/grub; fi'
        ], check=False)
        subprocess.run(['arch-chroot','/mnt','bash','-c',
            'if grep -qE "^\\s*GRUB_DISTRIBUTOR=" /etc/default/grub; '
            'then sed -i "s|^\\s*GRUB_DISTRIBUTOR=.*|GRUB_DISTRIBUTOR=\\"AGHOS\\"|" /etc/default/grub; '
            'else echo "GRUB_DISTRIBUTOR=\\"AGHOS\\"" >> /etc/default/grub; fi'
        ], check=False)

        # Przygotuj 41_windows (jeśli wykryto Windows)
        if windows_uefi or windows_bios:
            self.log("Wykryto Windows – dodaję wpis do GRUB (41_windows).")
            lines = [
                "#!/bin/sh",
                "exec tail -n +3 $0",
                "# ---- Windows entries added by AGHOS installer ----"
            ]
            if windows_uefi:
                lines += [
                    "menuentry 'Windows Boot Manager (UEFI)' --class windows --class os {",
                    "    insmod part_gpt",
                    "    insmod fat",
                    "    insmod chain",
                    "    search --no-floppy --file --set=root /EFI/Microsoft/Boot/bootmgfw.efi",
                    "    chainloader /EFI/Microsoft/Boot/bootmgfw.efi",
                    "}"
                ]
            if windows_bios:
                lines += [
                    "menuentry 'Windows (BIOS/MBR)' --class windows --class os {",
                    "    insmod part_msdos",
                    "    insmod ntfs",
                    "    insmod chain",
                    "    # Znajdź partycję z bootsectorem Windows (bootmgr)",
                    "    search --no-floppy --file --set=root /bootmgr",
                    "    chainloader +1",
                    "}"
                ]
            content = "\n".join(lines) + "\n"
            try:
                with open('/mnt/etc/grub.d/41_windows', 'w') as f:
                    f.write(content)
                os.chmod('/mnt/etc/grub.d/41_windows', 0o755)
            except Exception as e:
                self.log(f"⚠️  Nie udało się zapisać 41_windows: {e}")
        else:
            self.log("Nie wykryto Windows – pomijam tworzenie 41_windows.")

        # Bezpiecznie wygeneruj grub.cfg po wszystkich zmianach
        self.log("Generuję /boot/grub/grub.cfg…")
        r = subprocess.run(['arch-chroot','/mnt','grub-mkconfig','-o','/boot/grub/grub.cfg'],
                           capture_output=True, text=True, check=False)
        if r.returncode != 0:
            self.log(f"⚠️  grub-mkconfig rc={r.returncode}: {r.stderr.strip()}")
        else:
            self.log("GRUB: wygenerowano /boot/grub/grub.cfg.")

        self.progress.setRange(0,100)
        self.progress.setValue(100)
        self.speed_label.setText("Gotowe")
        QMessageBox.information(self, self.tr['config_done'], self.tr['config_done'])
        self.finish_btn.setEnabled(True)

    def _on_finish(self):
        # Uwaga: nie odmontowujemy od razu bind-mountów – dalsze skrypty mogą potrzebować chroota.
        # Czyszczenie identyfikatorów
        self.log("Czyszczę machine-id i random-seed")
        for p in ['/mnt/etc/machine-id','/mnt/var/lib/systemd/random-seed']:
            try: os.remove(p)
            except Exception: pass

        # ---- POPRAWKA: uruchamianie dokładnie skryptu 4_* z katalogu pliku, z logami ----
        self.log("Uruchamiam kolejny skrypt…")
        base = Path(__file__).resolve().parent
        scripts: List[Tuple[int, Path]] = []
        for p in base.glob('[0-9]*_*.py'):
            m = re.match(r'^(\d+)_', p.name)
            if m:
                try:
                    scripts.append((int(m.group(1)), p))
                except ValueError:
                    pass
        scripts.sort(key=lambda x: x[0])

        target = next((p for n, p in scripts if n == 4), None)

        if not target:
            QMessageBox.warning(self, "Brak skryptu", "Nie znalazłem pliku 4_*.py w katalogu instalatora.")
            # Opcjonalnie: spróbuj „następnego po bieżącym”
        else:
            self.log(f"→ {target.name}")
            try:
                from importlib import util
                spec = util.spec_from_file_location('wizard_next', str(target))
                mod = util.module_from_spec(spec)
                spec.loader.exec_module(mod)
            except Exception as e:
                QMessageBox.critical(self, "Błąd importu", f"{target.name}:\n{e}")
            else:
                # Preferuj run(lang, console); awaryjnie main()
                if hasattr(mod, "run"):
                    mod.run(self.lang, self)
                    QTimer.singleShot(0, self.close)  # zamknij po oddaniu sterowania
                elif hasattr(mod, "main"):
                    mod.main()
                    QTimer.singleShot(0, self.close)
                else:
                    QMessageBox.warning(self, "Uwaga", f"{target.name} nie ma funkcji run() ani main().")

    def _on_finish_umount_all(self):
        """Opcjonalne odmontowanie bind-mountów, gdy ostatni etap zakończony."""
        self.log("Odmontowuję bind-mounty…")
        for fs in ('tmp','run','dev','sys','proc'):
            dst=f"/mnt/{fs}"; subprocess.run(['umount','-R',dst],check=False)

def run(lang, console):
    """Uruchom jako pod-moduł w istniejącej aplikacji Qt."""
    global _post_install_wizard
    app = QApplication.instance() or QApplication(sys.argv)
    _post_install_wizard = PostInstallWizard(lang, console)
    _post_install_wizard.show()
    if hasattr(console, "append"):
        console.append(f"➡️ [{lang}] {_post_install_wizard.tr['download_group']}")
    return _post_install_wizard

if __name__=='__main__':
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        w = PostInstallWizard()
        w.show()
        sys.exit(app.exec())
    else:
        w = PostInstallWizard()
        w.show()
