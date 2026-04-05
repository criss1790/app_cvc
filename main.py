import sys

from PySide6.QtWidgets import QApplication

from app.bootstrap import AppContainer
from app.ui.main_window import MainWindow
from app.utils.logger import setup_logging


def main():
    setup_logging()
    container = AppContainer()

    app = QApplication(sys.argv)
    window = MainWindow(container)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
