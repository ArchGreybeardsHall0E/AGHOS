import sys
import os
import socket
import subprocess
import importlib.util
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QComboBox,
    QLineEdit, QPushButton, QRadioButton, QButtonGroup, QHBoxLayout
)
from PySide6.QtCore import Qt

translations = {
    "pl": {
        "title": "Konfiguracja sieci",
        "connected": "✅ Połączono z internetem",
        "not_connected": "❌ Brak połączenia z internetem",
        "select_iface": "Wybierz interfejs:",
        "select_wifi": "Wybierz sieć WiFi:",
        "password": "Hasło:",
        "dhcp": "Użyj DHCP",
        "static": "Statyczne IP",
        "ip": "Adres IP:",
        "mask": "Maska podsieci:",
        "gateway": "Brama:",
        "dns": "DNS (oddzielone spacją):",
        "connect": "Połącz",
        "connecting": "Łączenie...",
        "connected_ok": "✅ Połączenie udane.",
        "error": "❌ Błąd połączenia:",
        "continue": "Kontynuuj"
    },
    "en": {
        "title": "Network Configuration",
        "connected": "✅ Connected to the internet",
        "not_connected": "❌ No internet connection",
        "select_iface": "Select interface:",
        "select_wifi": "Select WiFi network:",
        "password": "Password:",
        "dhcp": "Use DHCP",
        "static": "Static IP",
        "ip": "IP Address:",
        "mask": "Netmask:",
        "gateway": "Gateway:",
        "dns": "DNS (space separated):",
        "connect": "Connect",
        "connecting": "Connecting...",
        "connected_ok": "✅ Connected successfully.",
        "error": "❌ Connection failed:",
        "continue": "Continue"
    }
    # Add other languages as needed...
}

def is_connected():
    try:
        socket.create_connection(("1.1.1.1", 53), timeout=2)
        return True
    except OSError:
        return False

def launch_next(lang, console):
    try:
        # Use the same directory as this script
        script_dir = os.path.dirname(__file__)
        files = sorted(f for f in os.listdir(script_dir) if f.endswith(".py"))
        # Skip this script itself
        if len(files) > 1:
            next_script = files[1]
            console.append(f"➡️ [{lang}] Uruchamiam skrypt: {next_script}")
            path = os.path.join(script_dir, next_script)
            spec = importlib.util.spec_from_file_location("next_mod", path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            if hasattr(mod, "run"):
                mod.run(lang, console)
            else:
                console.append(f"❌ [{lang}] Brak funkcji run() w {next_script}")
        else:
            console.append(f"⚠️ [{lang}] Brak kolejnych skryptów w folderze.")
    except Exception as e:
        console.append(f"❌ [{lang}] Błąd uruchamiania kolejnego skryptu: {e}")

class NetConfigurator(QWidget):
    def __init__(self, lang, console):
        super().__init__()
        self.lang = lang
        self.console = console
        self.tr = translations.get(lang, translations["en"])
        self.init_ui()
        self.post_init()

    def init_ui(self):
        self.setWindowTitle(self.tr["title"])
        self.resize(1000, 700)
        layout = QVBoxLayout(self)

        self.status = QLabel("", alignment=Qt.AlignCenter)
        layout.addWidget(self.status)

        self.iface_combo = QComboBox()
        layout.addWidget(self.iface_combo)

        self.dynamic_layout = QVBoxLayout()
        layout.addLayout(self.dynamic_layout)

        self.connect_btn = QPushButton(self.tr["connect"])
        self.connect_btn.setEnabled(False)
        self.connect_btn.clicked.connect(self.connect_network)
        layout.addWidget(self.connect_btn)

        self.cont_btn = QPushButton(self.tr["continue"])
        self.cont_btn.setEnabled(False)
        self.cont_btn.clicked.connect(lambda: (self.close(), launch_next(self.lang, self.console)))
        layout.addWidget(self.cont_btn)

    def post_init(self):
        if is_connected():
            self.status.setText(self.tr["connected"])
            self.console.append(f"[{self.lang}] {self.tr['connected']}")
            self.cont_btn.setEnabled(True)
        else:
            self.status.setText(self.tr["not_connected"])
            self.console.append(f"[{self.lang}] {self.tr['not_connected']}")
            ifaces = [i for i in os.listdir("/sys/class/net") if i != "lo"]
            self.iface_combo.addItems(ifaces)
            self.iface_combo.currentTextChanged.connect(self.on_iface_changed)
            if ifaces:
                self.iface_combo.setCurrentIndex(0)

    def on_iface_changed(self, iface):
        # Clear previous widgets
        while self.dynamic_layout.count():
            w = self.dynamic_layout.takeAt(0).widget()
            if w: w.deleteLater()
        self.connect_btn.setEnabled(False)

        if iface.startswith("wl"):
            self.dynamic_layout.addWidget(QLabel(self.tr["select_wifi"]))
            self.ssid_combo = QComboBox()
            out = subprocess.getoutput(f"nmcli -t -f SSID dev wifi list ifname {iface}")
            self.ssid_combo.addItems([s for s in out.splitlines() if s])
            self.dynamic_layout.addWidget(self.ssid_combo)
            self.dynamic_layout.addWidget(QLabel(self.tr["password"]))
            self.pwd_edit = QLineEdit(echoMode=QLineEdit.Password)
            self.dynamic_layout.addWidget(self.pwd_edit)
            self.connect_btn.setEnabled(True)
        else:
            box = QHBoxLayout()
            rd_dhcp = QRadioButton(self.tr["dhcp"])
            rd_static = QRadioButton(self.tr["static"])
            rd_dhcp.setChecked(True)
            grp = QButtonGroup(self); grp.addButton(rd_dhcp); grp.addButton(rd_static)
            box.addWidget(rd_dhcp); box.addWidget(rd_static)
            self.dynamic_layout.addLayout(box)
            self.ip_edit = QLineEdit(); self.ip_edit.setPlaceholderText(self.tr["ip"])
            self.mask_edit = QLineEdit(); self.mask_edit.setPlaceholderText(self.tr["mask"])
            self.gw_edit = QLineEdit(); self.gw_edit.setPlaceholderText(self.tr["gateway"])
            self.dns_edit = QLineEdit(); self.dns_edit.setPlaceholderText(self.tr["dns"])
            for w in (self.ip_edit, self.mask_edit, self.gw_edit, self.dns_edit):
                w.setVisible(False)
                self.dynamic_layout.addWidget(w)
            rd_dhcp.toggled.connect(lambda checked: [w.setVisible(not checked) for w in (self.ip_edit, self.mask_edit, self.gw_edit, self.dns_edit)])
            self.connect_btn.setEnabled(True)

    def connect_network(self):
        iface = self.iface_combo.currentText()
        self.console.append(f"[{self.lang}] {self.tr['connecting']}")
        if iface.startswith("wl"):
            ssid = self.ssid_combo.currentText()
            pwd = self.pwd_edit.text()
            subprocess.run(["nmcli","dev","wifi","connect",ssid,"password",pwd,"ifname",iface], capture_output=True)
        else:
            # find DHCP radio
            use_dhcp = any(btn.isChecked() for btn in self.findChildren(QRadioButton) if btn.text()==self.tr["dhcp"])
            if use_dhcp:
                subprocess.run(["nmcli","con","up",iface], capture_output=True)
            else:
                subprocess.run(["nmcli","con","mod",iface,
                                "ipv4.addresses",self.ip_edit.text(),
                                "ipv4.gateway",self.gw_edit.text(),
                                "ipv4.dns",self.dns_edit.text(),
                                "ipv4.method","manual"], capture_output=True)
                subprocess.run(["nmcli","con","up",iface], capture_output=True)
        if is_connected():
            self.status.setText(self.tr["connected_ok"])
            self.console.append(f"[{self.lang}] {self.tr['connected_ok']}")
            self.cont_btn.setEnabled(True)
        else:
            self.status.setText(self.tr["error"])
            self.console.append(f"[{self.lang}] {self.tr['error']}")

def run(lang, console):
    app = QApplication.instance() or QApplication(sys.argv)
    win = NetConfigurator(lang, console)
    win.show()

if __name__ == "__main__":
    class DummyConsole:
        def append(self, txt): print(txt)
    run("pl", DummyConsole())
