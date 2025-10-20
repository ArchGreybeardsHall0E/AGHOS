"""
AGHOS Installer - Graphical installer for AGH-customized Arch Linux
Author: Łukasz Gołek
Contact: aghos@agh.edu.pl
Website: https://aghos.agh.edu.pl
Organization: SKN "Ceramit", AGH University of Krakow
License: Open Source, provided under the MIT License.

"""

import sys
import os
import glob
import importlib.util
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel,
    QComboBox, QPushButton, QDialog, QTextEdit
)
from PySide6.QtGui import QPixmap, QPalette, QColor
from PySide6.QtCore import Qt

LANGUAGES = {
    "Polski": "pl",
    "English": "en",
    "Deutsch": "de",
    "Español": "es",
    "Français": "fr"
}

class ConsoleWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Konsola")
        self.setGeometry(300, 200, 800, 400)
        layout = QVBoxLayout()
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        layout.addWidget(self.console_output)
        
        

        
        # Author and licensing info


        
        # Author and licensing info
        author_label = QLabel("Autor: Łukasz Gołek  •  Kontakt: aghos@agh.edu.pl  •  Projekt: https://aghos.agh.edu.pl")
        author_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(author_label)

        self.setLayout(layout)

    def append(self, text):
        self.console_output.append(text)

class AghOsInstaller(QMainWindow):
    def __init__(self):
        super().__init__()
        self.lang_code = "pl"
        self.console_window = ConsoleWindow(self)
        self.script_queue = []

        self.setWindowTitle("AGHOS Installer")
        self.setGeometry(100, 100, 1000, 700)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        # Logo AGHOS
        self.logo = QLabel()
        pixmap = QPixmap("logo.png")
        self.logo.setPixmap(pixmap.scaledToWidth(900, Qt.SmoothTransformation))
        self.logo.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.logo)

        # Wybór języka
        self.lang_label = QLabel()
        self.lang_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.lang_label)

        self.lang_combo = QComboBox()
        self.lang_combo.addItems(list(LANGUAGES.keys()))
        self.lang_combo.currentTextChanged.connect(self.set_language)
        self.layout.addWidget(self.lang_combo)

        # Przycisk uruchamiania instalacji
        self.install_button = QPushButton()
        self.install_button.clicked.connect(self.run_first_script)
        self.layout.addWidget(self.install_button)

        # Przycisk pokazania konsoli
        self.console_btn = QPushButton()
        self.console_btn.clicked.connect(self.console_window.show)
        self.layout.addWidget(self.console_btn)
        author_label = QLabel("Autor: Łukasz Gołek  •  Kontakt: aghos@agh.edu.pl  •  Projekt: https://aghos.agh.edu.pl")
        author_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(author_label)

        self.set_language("Polski")
        self.index_scripts()

    def set_language(self, lang_display):
        self.lang_code = LANGUAGES.get(lang_display, "pl")
        self.lang_label.setText({
            "pl": "Wybierz język:",
            "en": "Select language:",
            "de": "Sprache auswählen:",
            "es": "Seleccione idioma:",
            "fr": "Choisissez la langue:"
        }.get(self.lang_code, "Wybierz język:"))
        self.install_button.setText({
            "pl": "Zainstaluj AGHOS",
            "en": "Install AGHOS",
            "de": "AGHOS installieren",
            "es": "Instalar AGHOS",
            "fr": "Installer AGHOS"
        }.get(self.lang_code, "Zainstaluj AGHOS"))
        self.console_btn.setText({
            "pl": "Pokaż konsolę",
            "en": "Show console",
            "de": "Konsole anzeigen",
            "es": "Mostrar consola",
            "fr": "Afficher la console"
        }.get(self.lang_code, "Pokaż konsolę"))

    def index_scripts(self):
        script_folder = os.path.join(os.path.dirname(__file__), "scripts")
        if not os.path.exists(script_folder):
            os.makedirs(script_folder)
        script_files = sorted(glob.glob(os.path.join(script_folder, "*.py")))
        self.script_queue = sorted(script_files, key=lambda x: int(os.path.basename(x).split("_")[0]))

    def run_first_script(self):
        if not self.script_queue:
            self.console_window.append("⚠️ Brak skryptów do uruchomienia.")
            return

        script_path = self.script_queue[0]
        module_name = os.path.splitext(os.path.basename(script_path))[0]
        spec = importlib.util.spec_from_file_location(module_name, script_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(module)
                if hasattr(module, "run"):
                    module.run(self.lang_code, self.console_window)
                else:
                    self.console_window.append(f"⚠️ Skrypt {module_name} nie zawiera funkcji run().\n")
            except Exception as e:
                self.console_window.append(f"❌ Błąd w {module_name}:\n{str(e)}\n")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    dark_palette = QPalette()

    # Aktywne kolory
    dark_palette.setColor(QPalette.Window, QColor(30, 30, 30))
    dark_palette.setColor(QPalette.WindowText, Qt.white)
    dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
    dark_palette.setColor(QPalette.ToolTipText, Qt.white)
    dark_palette.setColor(QPalette.Text, Qt.white)
    dark_palette.setColor(QPalette.Button, QColor(45, 45, 45))
    dark_palette.setColor(QPalette.ButtonText, Qt.white)
    dark_palette.setColor(QPalette.BrightText, Qt.red)
    dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.Highlight, QColor(70, 130, 180))
    dark_palette.setColor(QPalette.HighlightedText, Qt.black)

    # Nieaktywne (disabled) kolory - to kluczowe!
    dark_palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(127, 127, 127))
    dark_palette.setColor(QPalette.Disabled, QPalette.Text, QColor(127, 127, 127))
    dark_palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(127, 127, 127))
    dark_palette.setColor(QPalette.Disabled, QPalette.Highlight, QColor(80, 80, 80))
    dark_palette.setColor(QPalette.Disabled, QPalette.HighlightedText, QColor(127, 127, 127))

    # Możesz też ustawić inne stany dla spójności
    dark_palette.setColor(QPalette.Inactive, QPalette.Highlight, QColor(60, 110, 160))
    dark_palette.setColor(QPalette.Inactive, QPalette.HighlightedText, Qt.white)

    app.setPalette(dark_palette)
    app.setStyle('Fusion')

    app.setPalette(dark_palette)

    # Jeśli chcesz, możesz też dodać .qss
    # with open("darkstyle.qss", "r") as f:
    #     app.setStyleSheet(f.read())

    window = AghOsInstaller()
    window.show()
    sys.exit(app.exec())
