import sys
import logging
from PyQt6.QtWidgets import QApplication, QStackedWidget
from ui_main_window import MainWindow

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """
    Main function to initialize and run the application.
    Sets up the main window and starts the event loop.
    """
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    widget = QStackedWidget()
    widget.addWidget(mainWindow)
    widget.setFixedWidth(550)
    widget.setFixedHeight(500)
    widget.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()