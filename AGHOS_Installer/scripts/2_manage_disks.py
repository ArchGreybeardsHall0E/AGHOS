#!/usr/bin/env python3

import sys
import os
import subprocess
import re
import importlib.util

from math import floor
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QComboBox, QPushButton,
    QHBoxLayout, QLineEdit, QMessageBox, QFormLayout, QCheckBox
)
from PySide6.QtGui import QPainter, QColor
from PySide6.QtCore import Qt

# Pełne sekcje „translations” dla PL, EN, FR, DE i ES
translations = {
    "pl": {
        "format_question": "Czy sformatować?",
        "title": "Zarządzanie dyskiem",
        "select_disk": "Wybierz dysk do instalacji:",
        "mode_question": "Czy wyczyścić cały dysk i zastosować domyślny schemat?",
        "early_warning": "Instalator jest we wczesnej wersji — partycjonowanie wykonaj w GParted.",
        "launch_gparted": "OK, uruchamiam GParted",
        "usage": "Wykorzystanie dysku",
        "ptable": "Rodzaj tablicy partycji:",
        "gpt": "GPT",
        "mbr": "MBR",
        "gpt_comment": (
            "Dla GPT potrzebna jest partycja /boot sformatowana w VFAT min. 256M, "
            "optymalnie 2GB dla wielu kerneli.\n"
            "Partycja root (/) to główna partycja systemowa. Jeśli wiesz, co robisz, "
            "możesz to zmienić.\n"
            "Jeśli nie jesteś pewien, partycja root nie powinna mieć mniej niż 50GB.\n"
            "Partycja /home to partycja na Twoje dane (Twój katalog domowy).\n"
            "Tam będą Twoje dokumenty, gry i wszystkie Twoje pliki – przeznacz na nią "
            "najwięcej miejsca."
        ),
        "add": "Dodaj partycję",
        "delete": "Usuń partycję",
        "mount": "Punkt montowania",
        "fs": "System plików",
        "name": "Nazwa partycji",
        "size": "Rozmiar (np. 500M, 2G, 1T, 10%)",
        "mount_button": "Zamontuj",
        "mount_done": "Montowanie zakończone",
        "mount_done_msg": "Wszystkie partycje zostały zamontowane.",
        "mount_error": "Błąd montowania",
        "mount_error_msg": "Nie udało się zamontować {dev} → {mp}:\n{err}",
        "commit": "Zapisz zmiany na dysku",
        "commit_warning": "⚠️ Zaraz zapiszę zmiany: utrata danych! Kontynuować?",
        "commit_done": "✅ Zmiany zapisane.",
        "continue": "Kontynuuj",
        "cancel": "Anuluj",
        "free_space": "Wolne miejsce: {gb:.1f} GB ({pct:.1f}%)"
    },
    "en": {
        "format_question": "Format partitions?",
        "title": "Disk Management",
        "select_disk": "Select disk for installation:",
        "mode_question": "Clear entire disk and apply default layout?",
        "early_warning": "Installer is early-stage—partition using GParted.",
        "launch_gparted": "OK, launching GParted",
        "usage": "Disk usage",
        "ptable": "Partition table type:",
        "gpt": "GPT",
        "mbr": "MBR",
        "gpt_comment": (
            "For GPT, a /boot partition (VFAT) min. 256M, ideally 2G for multiple kernels.\n"
            "The root partition (/) is the main system partition. If you know what you're doing, feel free to change it.\n"
            "Otherwise, the root partition should not be smaller than 50GB.\n"
            "The /home partition is for your personal data (your home directory).\n"
            "This is where your documents, games, and all your files will be stored – allocate the most space here."
        ),
        "add": "Add partition",
        "delete": "Delete partition",
        "mount": "Mount point",
        "fs": "Filesystem",
        "name": "Partition name",
        "size": "Size (e.g. 500M, 2G, 1T, 10%)",
        "mount_button": "Mount",
        "mount_done": "Mounting finished",
        "mount_done_msg": "All partitions have been mounted.",
        "mount_error": "Mount error",
        "mount_error_msg": "Failed to mount {dev} → {mp}:\n{err}",
        "commit": "Write changes to disk",
        "commit_warning": "⚠️ About to write changes: data lost! Continue?",
        "commit_done": "✅ Changes written.",
        "continue": "Continue",
        "cancel": "Cancel",
        "free_space": "Free space: {gb:.1f} GB ({pct:.1f}%)"
    },
    "fr": {
        "format_question": "Formater les partitions ?",
        "title": "Gestion du disque",
        "select_disk": "Sélectionnez le disque pour l'installation :",
        "mode_question": "Effacer tout le disque et appliquer le schéma par défaut ?",
        "early_warning": "L'installateur en est à un stade précoce – partitionnez avec GParted.",
        "launch_gparted": "OK, lancement de GParted",
        "usage": "Utilisation du disque",
        "ptable": "Type de table de partitions :",
        "gpt": "GPT",
        "mbr": "MBR",
        "gpt_comment": (
            "Pour GPT, une partition /boot (VFAT) d'au moins 256 M, idéalement 2 G pour plusieurs noyaux.\n"
            "La partition root (/) est la partition système principale. Si vous savez ce que vous faites, vous pouvez la modifier.\n"
            "Sinon, la partition root ne doit pas être inférieure à 50 Go.\n"
            "La partition /home est destinée à vos données personnelles (votre répertoire personnel).\n"
            "C'est là que seront stockés vos documents, jeux et tous vos fichiers – allouez-lui le plus d'espace possible."
        ),
        "add": "Ajouter une partition",
        "delete": "Supprimer la partition",
        "mount": "Point de montage",
        "fs": "Système de fichiers",
        "name": "Nom de la partition",
        "size": "Taille (ex. 500M, 2G, 1T, 10%)",
        "mount_button": "Monter",
        "mount_done": "Montage terminé",
        "mount_done_msg": "Toutes les partitions ont été montées.",
        "mount_error": "Erreur de montage",
        "mount_error_msg": "Impossible de monter {dev} → {mp}:\n{err}",
        "commit": "Appliquer les modifications",
        "commit_warning": "⚠️ Vous allez appliquer les modifications : perte de données ! Continuer ?",
        "commit_done": "✅ Modifications appliquées.",
        "continue": "Continuer",
        "cancel": "Annuler",
        "free_space": "Espace libre: {gb:.1f} GB ({pct:.1f}%)"
    },
    "de": {
        "format_question": "Partitionen formatieren?",
        "title": "Datenträgerverwaltung",
        "select_disk": "Wählen Sie die Festplatte zur Installation:",
        "mode_question": "Gesamte Festplatte löschen und Standardlayout anwenden?",
        "early_warning": "Installer ist noch in der frühen Phase – partitionieren Sie mit GParted.",
        "launch_gparted": "OK, GParted wird gestartet",
        "usage": "Datenträgernutzung",
        "ptable": "Partitionstabellentyp:",
        "gpt": "GPT",
        "mbr": "MBR",
        "gpt_comment": (
            "Für GPT wird eine /boot-Partition (VFAT) von mindestens 256 MB benötigt, idealerweise 2 GB für mehrere Kernel.\n"
            "Die Root-Partition (/) ist die Hauptsystempartition. Wenn Sie wissen, was Sie tun, können Sie sie ändern.\n"
            "Andernfalls sollte die Root-Partition nicht kleiner als 50 GB sein.\n"
            "Die /home-Partition ist für Ihre persönlichen Daten (Ihr Home-Verzeichnis) vorgesehen.\n"
            "Hier werden Ihre Dokumente, Spiele und alle Ihre Dateien gespeichert – reservieren Sie hierfür den meisten Speicherplatz."
        ),
        "add": "Partition hinzufügen",
        "delete": "Partition löschen",
        "mount": "Einhängepunkt",
        "fs": "Dateisystem",
        "name": "Partitionsname",
        "size": "Größe (z. B. 500M, 2G, 1T, 10%)",
        "mount_button": "Einbinden",
        "mount_done": "Einhängen abgeschlossen",
        "mount_done_msg": "Alle Partitionen wurden eingehängt.",
        "mount_error": "Einbindungsfehler",
        "mount_error_msg": "Konnte {dev} → {mp} nicht einhängen:\n{err}",
        "commit": "Änderungen schreiben",
        "commit_warning": "⚠️ Änderungen werden geschrieben: Datenverlust! Fortfahren?",
        "commit_done": "✅ Änderungen geschrieben.",
        "continue": "Fortfahren",
        "cancel": "Abbrechen",
        "free_space": "Freier Speicher: {gb:.1f} GB ({pct:.1f}%)"
    },
    "es": {
        "format_question": "¿Formatear particiones?",
        "title": "Gestión de disco",
        "select_disk": "Seleccione el disco para la instalación:",
        "mode_question": "¿Borrar todo el disco and aplicar esquema por defecto?",
        "early_warning": "El instalador está en una etapa temprana – particione con GParted.",
        "launch_gparted": "OK, iniciando GParted",
        "usage": "Uso del disco",
        "ptable": "Tipo de tabla de particiones:",
        "gpt": "GPT",
        "mbr": "MBR",
        "gpt_comment": (
            "Para GPT se necesita una partición /boot (VFAT) de al menos 256 MB, idealmente 2 GB para múltiples núcleos.\n"
            "La partición root (/) es la partición principal del sistema. Si sabes lo que haces, puedes cambiarla.\n"
            "De lo contrario, la partición root no debe ser inferior a 50 GB.\n"
            "La partición /home es para tus datos personales (tu directorio personal).\n"
            "Aquí se almacenarán tus documentos, juegos y todos tus archivos: asigna la mayor cantidad de espacio posible."
        ),
        "add": "Agregar partición",
        "delete": "Eliminar partición",
        "mount": "Punto de montaje",
        "fs": "Sistema de archivos",
        "name": "Nombre de la partición",
        "size": "Tamaño (p. ej. 500M, 2G, 1T, 10%)",
        "mount_button": "Montar",
        "mount_done": "Montaje terminado",
        "mount_done_msg": "Todas las particiones han sido montadas.",
        "mount_error": "Error de montaje",
        "mount_error_msg": "No se pudo montar {dev} → {mp}:\n{err}",
        "commit": "Escribir cambios en disco",
        "commit_warning": "⚠️ A punto de escribir cambios: ¡pérdida de datos! ¿Continuar?",
        "commit_done": "✅ Cambios escritos.",
        "continue": "Continuar",
        "cancel": "Cancelar",
        "free_space": "Espacio libre: {gb:.1f} GB ({pct:.1f}%)"
    }
}


def is_root():
    return os.geteuid() == 0


class UsageBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.partitions = []

    def set_partitions(self, parts):
        total = sum(size for _, size in parts)
        from random import sample
        self.partitions = [
            (name, size, QColor(*sample(range(50, 200), 3)))
            for name, size in parts
        ]
        self.total = total if total else 1
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        w, h = self.width(), self.height()
        x = 0
        for _, size, color in self.partitions:
            pw = w * size / self.total
            painter.fillRect(x, 0, pw, h, color)
            x += pw


class PartitionRow(QWidget):
    def __init__(self, lang, tr, free, ptype, manager):
        super().__init__(manager)
        self.manager = manager
        self.size = 0
        layout = QHBoxLayout(self)

        self.size_edit = QLineEdit()
        self.size_edit.setPlaceholderText(str(floor(free / 1024**2)))
        self.size_edit.editingFinished.connect(self.update_size)
        layout.addWidget(self.size_edit)

        self.mount_edit = QLineEdit()
        self.mount_edit.setPlaceholderText(tr['mount'])
        layout.addWidget(self.mount_edit)

        self.fs_combo = QComboBox()
        for fs in ['vfat', 'ext2', 'ext3', 'ext4', 'btrfs', 'swap']:
            self.fs_combo.addItem(fs)
        layout.addWidget(self.fs_combo)

        if ptype == tr['gpt']:
            self.name_edit = QLineEdit()
            self.name_edit.setPlaceholderText(tr['name'])
            layout.addWidget(self.name_edit)

        btn_add = QPushButton(tr['add'])
        btn_del = QPushButton(tr['delete'])
        btn_add.clicked.connect(manager.add_row)
        btn_del.clicked.connect(lambda _, r=self: manager.remove_row(r))
        layout.addWidget(btn_add)
        layout.addWidget(btn_del)

    def update_size(self):
        txt = self.size_edit.text().strip().upper()
        if txt.endswith('%'):
            try:
                pct = float(txt.strip('%'))
                dev = f"/dev/{self.manager.disk_combo.currentData()}"
                total = int(subprocess.getoutput(f"lsblk -b -n -l -o SIZE {dev}").splitlines()[0])
                self.size = int(pct/100 * total)
            except ValueError:
                self.size = 0
        else:
            m = re.match(r'^(\d+(?:\.\d+)?)([MGT]B?)?$', txt)
            if m:
                num, suf = m.groups()
                mul = {'M':1024**2,'MB':1024**2,'G':1024**3,'GB':1024**3,'T':1024**4,'TB':1024**4,None:1}
                self.size = int(float(num)*mul[suf])
            else:
                try:
                    self.size = int(txt)
                except ValueError:
                    self.size = 0
        self.manager.update_free()

    def set_free(self, free):
        self.size_edit.setPlaceholderText(str(floor(free / 1024**2)))

    def get_index(self):
        return str(self.manager.rows.index(self) + 1)


class DiskManager(QWidget):
    def __init__(self, lang, console):
        super().__init__()
        if not is_root():
            QMessageBox.critical(None, 'Error', 'Run as root!')
            sys.exit(1)
        self.lang = lang
        self.console = console
        self.tr = translations[lang]
        self.mode = None
        self.fs_selector = {}
        self.rows = []
        self.total_size = 0
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(self.tr['title'])
        self.resize(1000, 800)
        self.layout = QVBoxLayout(self)

        # Disk select
        self.layout.addWidget(QLabel(self.tr['select_disk']))
        self.disk_combo = QComboBox()
        self.disk_combo.addItem("", "")
        out = subprocess.getoutput("lsblk -nd -b -o NAME,SIZE,MODEL")
        for line in out.splitlines():
            parts = re.split(r"\s+", line, maxsplit=2)
            if len(parts) != 3:
                continue
            name, size_str, model = parts
            size_gb = int(size_str)/(1024**3) if size_str.isdigit() else 0
            self.disk_combo.addItem(f"/dev/{name} – {model.strip()} – {size_gb:.1f} GB", name)
        self.layout.addWidget(self.disk_combo)

        # Flow container
        self.flow = QWidget()
        self.flow_layout = QVBoxLayout(self.flow)
        self.layout.addWidget(self.flow)

        # Free space label (dodane z drugiego skryptu)
        self.free_label = QLabel(self.tr["free_space"].format(gb=0.0, pct=100.0))
        self.layout.addWidget(self.free_label)

        # Buttons
        btn_box = QHBoxLayout()
        self.cancel_btn = QPushButton(self.tr['cancel'])
        self.cancel_btn.clicked.connect(self._on_cancel)
        self.cont_btn = QPushButton(self.tr['continue'])
        self.cont_btn.setEnabled(False)
        self.cont_btn.clicked.connect(lambda: launch_next(self.lang, self.console))
        btn_box.addWidget(self.cancel_btn)
        btn_box.addWidget(self.cont_btn)
        self.layout.addLayout(btn_box)

        self.disk_combo.currentIndexChanged.connect(self.on_disk_selected)

    def _on_cancel(self):
        # Unmount in reverse order
        for mp in ['/home', '/boot', '/']:
            tgt = '/mnt'+mp if mp != '/' else '/mnt'
            subprocess.run(['umount', '-R', tgt], check=False)
            self.console.append(f"🔄 Odmontowano {tgt}")
        self.close()

    def on_disk_selected(self):
        dev = self.disk_combo.currentData()
        if not dev:
            self.clear_flow()
            return
        resp = QMessageBox.question(
            self, self.tr['title'], self.tr['mode_question'],
            QMessageBox.Yes | QMessageBox.No
        )
        if resp == QMessageBox.Yes:
            self.mode = 'full'
            self.init_full_flow()
        else:
            self.mode = 'partial'
            self.init_partial_flow()

    def clear_flow(self):
        while self.flow_layout.count():
            w = self.flow_layout.takeAt(0).widget()
            if w:
                w.deleteLater()
        self.cont_btn.setEnabled(False)

    def init_full_flow(self):
        self.clear_flow()
        self.scan_and_build_default()

    def scan_and_build_default(self):
        dev = f"/dev/{self.disk_combo.currentData()}"
        parts = []
        out = subprocess.getoutput(f"lsblk -b -n -l -o NAME,TYPE,SIZE {dev}")
        total = int(subprocess.getoutput(f"lsblk -b -n -l -o SIZE {dev}").splitlines()[0])
        self.total_size = total  # Dodane z drugiego skryptu

        for line in out.splitlines():
            cols = re.split(r"\s+", line)
            if len(cols)>=3 and cols[1]=='part':
                parts.append((cols[0],int(cols[2])))
        ub = UsageBar(); ub.setFixedHeight(30); ub.set_partitions(parts)
        self.flow_layout.addWidget(QLabel(self.tr['usage']))
        self.flow_layout.addWidget(ub)

        self.flow_layout.addWidget(QLabel(self.tr['ptable']))
        self.pt = QComboBox(); self.pt.addItems([self.tr['gpt'],self.tr['mbr']])
        self.flow_layout.addWidget(self.pt)
        comment = QLabel(self.tr['gpt_comment']); comment.setWordWrap(True)
        self.flow_layout.addWidget(comment)

        self.table = QVBoxLayout()
        self.flow_layout.addLayout(self.table)
        self.rows = []

        # Domyślny układ z partycją SWAP
        for sz, mp, fs, nm in [
            ("1G", "/boot", "vfat", "boot"),
            ("40G", "/", "btrfs", "root"),
            ("8G", "swap", "swap", "swap"),
            ("20G", "/home", "btrfs", "home")
        ]:
            row = PartitionRow(self.lang, self.tr, total, self.pt.currentText(), self)
            row.size_edit.setText(sz)
            row.mount_edit.setText(mp)
            row.fs_combo.setCurrentText(fs)
            if hasattr(row,'name_edit'):
                row.name_edit.setText(nm)
            row.update_size()
            self.table.addWidget(row)
            self.rows.append(row)

        # Dodanie przycisku commit
        commit_btn = QPushButton(self.tr['commit'])
        commit_btn.clicked.connect(self.commit_changes)
        self.flow_layout.addWidget(commit_btn)

        # Aktualizacja wolnego miejsca (dodane z drugiego skryptu)
        self.update_free()

    def add_row(self):
        dev = f"/dev/{self.disk_combo.currentData()}"
        total = int(subprocess.getoutput(f"lsblk -b -n -l -o SIZE {dev}").splitlines()[0])
        used = sum(r.size for r in self.rows)
        free = total - used
        row = PartitionRow(self.lang, self.tr, free, self.pt.currentText(), self)
        self.table.addWidget(row)
        self.rows.append(row)
        self.update_free()  # Dodane z drugiego skryptu

    def remove_row(self, row):
        if row in self.rows:
            self.rows.remove(row)
            row.deleteLater()
            self.update_free()  # Dodane z drugiego skryptu

    # Funkcja update_free z drugiego skryptu
    def update_free(self):
        used = sum(r.size for r in self.rows)
        free = self.total_size - used
        pct = max(0, free / self.total_size * 100)
        gb = max(0, free / 1024**3)
        self.free_label.setText(self.tr["free_space"].format(gb=gb, pct=pct))
        for r in self.rows:
            r.set_free(free)
        if free < 0:
            self.free_label.setStyleSheet("color: red;")
        else:
            self.free_label.setStyleSheet("color: green;")

    def build_mkfs_cmd(self, device, fstype):
        fstype = fstype.lower()
        if fstype in ('swap', 'linux-swap', 'swapspace'):
            return ['mkswap', device]
        elif fstype == 'btrfs':
            return ['mkfs.btrfs', '-f', device]
        elif fstype == 'vfat':
            return ['mkfs.vfat', '-F', '32', device]
        elif fstype in ('ext2','ext3','ext4'):
            return ['mkfs.'+fstype, '-F', device]
        elif fstype == 'xfs':
            return ['mkfs.xfs', '-f', device]
        elif fstype == 'f2fs':
            return ['mkfs.f2fs', '-f', device]
        else:
            return ['mkfs.ext4', '-F', device]

    def commit_changes(self):
        if QMessageBox.question(
            self, self.tr['commit'], self.tr['commit_warning'],
            QMessageBox.Yes | QMessageBox.No
        ) != QMessageBox.Yes:
            return

        dev = f"/dev/{self.disk_combo.currentData()}"
        ptype = self.pt.currentText().lower()

        # 1. Partition table
        self.console.append(f"parted -s {dev} mklabel {ptype}")
        result = subprocess.run(['parted','-s',dev,'mklabel',ptype], capture_output=True, text=True)
        if result.returncode != 0:
            QMessageBox.critical(self, "Błąd", f"Nie udało się utworzyć tablicy partycji: {result.stderr}")
            return

        # 2. Create parts - poprawione obliczenia
        start_mb = 1  # Zaczynamy od 1MB (zostawiamy miejsce na MBR/GPT)

        for r in self.rows:
            # Konwertuj rozmiar z bajtów na MB
            size_mb = max(1, floor(r.size / (1024**2)))
            end_mb = start_mb + size_mb

            fs = r.fs_combo.currentText().lower()

            # mapowanie typu do parted
            if fs.startswith('vfat'):
                part_fs = 'fat32'
            elif fs in ('swap', 'linux-swap', 'swapspace'):
                part_fs = 'linux-swap'
            else:
                part_fs = fs

            self.console.append(f"Tworzenie partycji: {start_mb}MiB - {end_mb}MiB ({size_mb}MB)")

            # Sprawdź czy rozmiar jest poprawny
            if end_mb <= start_mb:
                QMessageBox.critical(self, "Błąd", f"Nieprawidłowy rozmiar partycji: {size_mb}MB")
                return

            try:
                result = subprocess.run([
                    'parted', '-s', dev, 'mkpart', 'primary', part_fs,
                    f"{start_mb}MiB", f"{end_mb}MiB"
                ], capture_output=True, text=True, check=True)
                self.console.append(result.stdout)
            except subprocess.CalledProcessError as e:
                error_msg = f"Błąd tworzenia partycji: {e.stderr}\nCommand: {e.cmd}"
                QMessageBox.critical(self, "Błąd", error_msg)
                return

            idx = r.get_index()

            # Ustaw flagę ESP dla partycji /boot w GPT
            if r.mount_edit.text().strip() == '/boot' and ptype == 'gpt':
                try:
                    result = subprocess.run(['parted','-s',dev,'set',idx,'esp','on'],
                                        capture_output=True, text=True, check=True)
                    self.console.append(f"Ustawiono flagę ESP: {result.stdout}")
                except subprocess.CalledProcessError as e:
                    self.console.append(f"Ostrzeżenie: Nie udało się ustawić flagi ESP: {e.stderr}")

            # Flaga swap dla GPT
            if fs in ('swap','linux-swap','swapspace') and ptype == 'gpt':
                try:
                    result = subprocess.run(['parted','-s',dev,'set',idx,'swap','on'],
                                        capture_output=True, text=True, check=True)
                    self.console.append(f"Ustawiono flagę swap: {result.stdout}")
                except subprocess.CalledProcessError as e:
                    self.console.append(f"Ostrzeżenie: Nie udało się ustawić flagi swap: {e.stderr}")

            # Ustaw nazwę partycji dla GPT
            if ptype == 'gpt' and hasattr(r, 'name_edit') and r.name_edit.text().strip():
                try:
                    result = subprocess.run(['parted','-s',dev,'name',idx,r.name_edit.text().strip()],
                                        capture_output=True, text=True, check=True)
                    self.console.append(f"Ustawiono nazwę: {result.stdout}")
                except subprocess.CalledProcessError as e:
                    self.console.append(f"Ostrzeżenie: Nie udało się ustawić nazwy: {e.stderr}")

            start_mb = end_mb + 1  # Zostaw 1MB przerwy między partycjami

        # 3. Odczekaj chwilę aby system wykrył nowe partycje
        import time
        time.sleep(2)

        # 4. Sformatuj i zamontuj partycje
        os.makedirs('/mnt', exist_ok=True)

        # root
        root = next((r for r in self.rows if r.mount_edit.text().strip() == '/'), None)
        if not root:
            QMessageBox.critical(self, self.tr['mount_error'], "Nie znaleziono partycji root (/)")
            return

        root_idx = root.get_index()
        root_dev = f"/dev/{self.disk_combo.currentData()}{root_idx}"
        root_fs = root.fs_combo.currentText().lower()

        # Sprawdź czy urządzenie istnieje
        if not os.path.exists(root_dev):
            self.console.append(f"Oczekiwanie na urządzenie {root_dev}...")
            time.sleep(3)
            if not os.path.exists(root_dev):
                QMessageBox.critical(self, "Błąd", f"Urządzenie {root_dev} nie istnieje!")
                return

        cmd = self.build_mkfs_cmd(root_dev, root_fs)
        self.console.append(' '.join(cmd))
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            self.console.append(result.stdout + result.stderr)
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, "Błąd formatowania", f"Nie udało się sformatować {root_dev}: {e.stderr}")
            return

        try:
            result = subprocess.run(['mount', root_dev, '/mnt'], capture_output=True, text=True, check=True)
            self.console.append(result.stdout + result.stderr)
            self.console.append(f"✅ {root_dev} → /")
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, "Błąd montowania", f"Nie udało się zamontować {root_dev}: {e.stderr}")
            return

        # Utwórz katalogi i zamontuj pozostałe partycje
        for sub in ('boot', 'home'):
            os.makedirs(f"/mnt/{sub}", exist_ok=True)

        # --- SWAP: sformatuj i aktywuj ---
        for r in self.rows:
            mp_txt = r.mount_edit.text().strip().lower()
            fs_txt = r.fs_combo.currentText().lower()
            if mp_txt == 'swap' or fs_txt in ('swap', 'linux-swap', 'swapspace'):
                idx = r.get_index()
                devn = f"/dev/{self.disk_combo.currentData()}{idx}"

                # upewnij się, że urządzenie istnieje
                if not os.path.exists(devn):
                    self.console.append(f"Oczekiwanie na urządzenie {devn}...")
                    time.sleep(2)

                # sformatuj na swap
                cmd = self.build_mkfs_cmd(devn, 'swap')
                self.console.append(' '.join(cmd))
                try:
                    subprocess.run(cmd, capture_output=True, text=True, check=True)
                except subprocess.CalledProcessError as e:
                    self.console.append(f"⚠️ Błąd mkswap {devn}: {e.stderr}")
                    continue

                # włącz swap
                try:
                    res = subprocess.run(['swapon', devn], capture_output=True, text=True, check=True)
                    self.console.append(res.stdout + res.stderr)
                    self.console.append(f"✅ {devn} → swap (aktywowany)")
                except subprocess.CalledProcessError as e:
                    self.console.append(f"⚠️ Błąd swapon {devn}: {e.stderr}")

        for mp in ('/boot', '/home'):
            part = next((r for r in self.rows if r.mount_edit.text().strip() == mp), None)
            if not part:
                continue

            part_idx = part.get_index()
            devn = f"/dev/{self.disk_combo.currentData()}{part_idx}"
            fs = part.fs_combo.currentText().lower()

            # Sprawdź czy urządzenie istnieje
            if not os.path.exists(devn):
                self.console.append(f"Oczekiwanie na urządzenie {devn}...")
                time.sleep(2)
                if not os.path.exists(devn):
                    self.console.append(f"⚠️ Urządzenie {devn} nie istnieje, pomijam...")
                    continue

            cmd = self.build_mkfs_cmd(devn, fs)
            self.console.append(' '.join(cmd))
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                self.console.append(result.stdout + result.stderr)
            except subprocess.CalledProcessError as e:
                self.console.append(f"⚠️ Błąd formatowania {devn}: {e.stderr}")
                continue

            try:
                result = subprocess.run(['mount', devn, f"/mnt{mp}"], capture_output=True, text=True, check=True)
                self.console.append(result.stdout + result.stderr)
                self.console.append(f"✅ {devn} → {mp}")
            except subprocess.CalledProcessError as e:
                self.console.append(f"⚠️ Błąd montowania {devn}: {e.stderr}")

        QMessageBox.information(self, self.tr['mount_done'], self.tr['mount_done_msg'])
        self.cont_btn.setEnabled(True)

    def init_partial_flow(self):
        self.clear_flow()
        dlg = QMessageBox(self)
        dlg.setWindowTitle(self.tr['title'])
        dlg.setText(self.tr['early_warning'])
        dlg.addButton(self.tr['launch_gparted'], QMessageBox.AcceptRole)
        dlg.exec_()
        subprocess.Popen(['gparted']).wait()
        self.show_mount_ui()

    def show_mount_ui(self):
        dev = f"/dev/{self.disk_combo.currentData()}"
        out = subprocess.getoutput(f"lsblk -b -n -l -o NAME,TYPE,SIZE {dev}")
        form = QFormLayout()
        self.rows_exist = []
        self.fs_selector = {}
        for line in out.splitlines():
            cols = re.split(r"\s+", line)
            if len(cols)>=3 and cols[1]=='part':
                name = cols[0]
                size_mb = int(cols[2])//(1024**2)
                mount_input = QLineEdit()
                mount_input.setPlaceholderText(self.tr['mount'])
                fs_combo = QComboBox()
                for fs in ['vfat','ext2','ext3','ext4','btrfs','swap']:
                    fs_combo.addItem(fs)
                self.rows_exist.append((name, mount_input))
                self.fs_selector[name] = fs_combo
                row_w = QWidget()
                row_l = QHBoxLayout(row_w)
                row_l.addWidget(mount_input)
                row_l.addWidget(fs_combo)
                form.addRow(QLabel(f"/dev/{name} — {size_mb} MB"), row_w)
        self.flow_layout.addLayout(form)
        self.format_checkbox = QCheckBox(self.tr['format_question'])
        self.format_checkbox.setChecked(True)
        self.flow_layout.addWidget(self.format_checkbox)
        mbtn = QPushButton(self.tr['mount_button'])
        mbtn.clicked.connect(self.do_mount)
        self.flow_layout.addWidget(mbtn)

    def do_mount(self):
        os.makedirs('/mnt', exist_ok=True)
        parts = {}
        for name, inp in self.rows_exist:
            mp = inp.text().strip()
            if not mp: continue
            parts[mp] = (f"/dev/{name}", self.fs_selector[name].currentText().lower())

        if '/' not in parts:
            QMessageBox.critical(self, self.tr['mount_error'], "Nie wybrano partycji root (/)")
            return

        # root
        dev_node, fstype = parts.pop('/')
        if self.format_checkbox.isChecked():
            cmd = self.build_mkfs_cmd(dev_node, fstype)
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode:
                QMessageBox.critical(self, 'Błąd formatowania', res.stderr.strip())
                return
        res = subprocess.run(['mount', dev_node, '/mnt'], capture_output=True, text=True)
        if res.returncode:
            QMessageBox.critical(self, 'Błąd montowania', res.stderr.strip())
            return
        self.console.append(f"✅ {dev_node} → /")

        # Utwórz katalogi
        for sub in ('boot', 'home'):
            os.makedirs(f"/mnt/{sub}", exist_ok=True)

        # Pozostałe MP (w tym SWAP)
        for mp in sorted(parts.keys(), key=len):
            # SWAP: specjalna ścieżka
            if mp.lower() == 'swap':
                dev_node, fstype = parts[mp]
                if self.format_checkbox.isChecked():
                    cmd = self.build_mkfs_cmd(dev_node, 'swap')
                    res = subprocess.run(cmd, capture_output=True, text=True)
                    if res.returncode:
                        QMessageBox.critical(self, 'Błąd mkswap', res.stderr.strip())
                        return
                res = subprocess.run(['swapon', dev_node], capture_output=True, text=True)
                if res.returncode:
                    QMessageBox.critical(self, 'Błąd swapon', res.stderr.strip())
                    return
                self.console.append(f"✅ {dev_node} → swap (aktywowany)")
                continue

            dev_node, fstype = parts[mp]
            tgt = f"/mnt{mp}"
            os.makedirs(tgt, exist_ok=True)
            if self.format_checkbox.isChecked():
                cmd = self.build_mkfs_cmd(dev_node, fstype)
                res = subprocess.run(cmd, capture_output=True, text=True)
                if res.returncode:
                    QMessageBox.critical(self, 'Błąd formatowania', res.stderr.strip())
                    return
            res = subprocess.run(['mount', dev_node, tgt], capture_output=True, text=True)
            if res.returncode:
                QMessageBox.critical(self, f'Błąd montowania {mp}', res.stderr.strip())
                return
            self.console.append(f"✅ {dev_node} → {mp}")

        QMessageBox.information(self, self.tr['mount_done'], self.tr['mount_done_msg'])
        self.cont_btn.setEnabled(True)


def launch_next(lang, console):
    script_dir = os.path.dirname(__file__)
    files = sorted(f for f in os.listdir(script_dir) if re.match(r'^\d+_.*\.py$', f))
    current = os.path.basename(__file__)
    if current in files:
        idx = files.index(current)
        if idx+1 < len(files):
            path = os.path.join(script_dir, files[idx+1])
            spec = importlib.util.spec_from_file_location('mod', path)
            mod  = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            if hasattr(mod, 'run'):
                mod.run(lang, console)
            else:
                console.append(f"❌ Brak funkcji run() w {files[idx+1]}")


def run(lang, console):
    # Otwórz plik HTML w domyślnej przeglądarce
    script_dir = os.path.dirname(__file__)
    html_file = os.path.join(script_dir, f"{lang}.html")

    if os.path.exists(html_file):
        try:
            console.append(f"📖 Otwieram dokumentację: {html_file}")

            if sys.platform == "win32":
                # Windows
                os.startfile(html_file)
            elif sys.platform == "darwin":
                # macOS
                subprocess.run(["open", html_file])
            else:
                # Linux i inne systemy uniksowe
                subprocess.run(["xdg-open", html_file])

            console.append("✅ Dokumentacja otwarta w przeglądarce")
            console.append("ℹ️ Możesz zamknąć przeglądarkę - instalator będzie kontynuował działanie")

        except Exception as e:
            console.append(f"❌ Błąd przy otwieraniu dokumentacji: {str(e)}")
            console.append("ℹ️ Kontynuuję instalację bez dokumentacji")
    else:
        console.append(f"⚠️ Plik dokumentacji nie istnieje: {html_file}")
        console.append("ℹ️ Kontynuuję instalację bez dokumentacji")

    # Kontynuuj z głównym interfejsem zarządzania dyskiem
    app = QApplication.instance() or QApplication(sys.argv)
    w = DiskManager(lang, console)
    w.show()
    app.exec_()


if __name__ == '__main__':
    class DummyConsole:
        def append(self, txt): print(txt)
    run('pl', DummyConsole())
