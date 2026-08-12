"""Point d'entrée de l'application MT5 Set Editor."""
import sys

from PySide6.QtWidgets import QApplication

from main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("MT5 Set Editor")
    window = MainWindow()
    window.show()

    # Si l'application est lancée en double-cliquant sur un fichier .set
    # (association de fichier Windows), le chemin est passé en argument.
    if len(sys.argv) > 1:
        window.load_file(sys.argv[1])

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
