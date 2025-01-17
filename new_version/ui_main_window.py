import os
from PyQt6 import uic
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QDialog, QFileDialog
from PyQt6.QtCore import QRegularExpression
from PyQt6.QtGui import QRegularExpressionValidator
from file_processor import FileProcessor
import logging

class MainWindow(QDialog):
    """
    Main window class for the application.
    Inherits from QDialog and sets up the UI components and event handlers.
    """
    def __init__(self):
        """
        Initializes the main window, sets up the UI components and connects signals to slots.
        """
        super(MainWindow, self).__init__()
        uic.loadUi("ui/unlockFile.ui", self)
        self.file_processor = FileProcessor()
        self.setup_ui()

    def setup_ui(self):
        """
        Sets up the user interface components.
        """
        self.sheetValidator()
        self.continuar.clicked.connect(self.setFileSettings)
        self.cleanOptionFiles.clicked.connect(self.clean)
        self.uploadChoice.clicked.connect(self.browsefiles)
        self.unlockFile.clicked.connect(self.unlock)

    def sheetValidator(self):
        """ Función que verifica la entrada del rango de páginas, solo se permite números seguido de (,) o (-)
            No permite que una (,) y (-) esten juntos.
        """
        noSpaceValidator = QRegularExpressionValidator(QRegularExpression("^(?!0)[1-9][0-9]*(?:,[1-9][0-9]*|-[1-9][0-9]*)+$"), self.rangeSheets)
        self.rangeSheets.setValidator(noSpaceValidator)

    def clean(self):
        """ Limpia los campos de entrada, habilita e inhabilita los grupos de contenido dentro de la GUI. """
        logging.info("Cleaning input fields")
        self.optionFiles.setEnabled(True)
        self.unlockFile.setEnabled(False)
        self.fileGroup.setEnabled(False)
        self.cleanOptionFiles.setEnabled(False)
        self.continuar.setEnabled(True)

    def setFileSettings(self):
        """ Habilita o deshabilita las opciones de la GUI dependiendo de la primer elección de opciones como:
        desbloquear un archivo, varios archivos o un conjunto de archivos."""
        logging.info("Setting file options")
        self.optionFiles.setEnabled(False)
        self.unlockFile.setEnabled(True)
        self.fileGroup.setEnabled(True)
        self.cleanOptionFiles.setEnabled(True)
        self.continuar.setEnabled(False)
        if self.manyFiles.isChecked():
            self.intervalLabel.setEnabled(False)
            self.rangeSheets.setEnabled(False)
            self.clearInputRange.setEnabled(False)
        elif self.multipleFiles.isChecked():
            self.intervalLabel.setEnabled(True)
            self.rangeSheets.setEnabled(True)
            self.clearInputRange.setEnabled(True)
        else:
            self.intervalLabel.setEnabled(True)
            self.rangeSheets.setEnabled(True)
            self.clearInputRange.setEnabled(True)

    def browsefiles(self):
        try:
            if self.oneFile.isChecked():
                fname = QFileDialog.getOpenFileName(self, caption="Abrir archivo", filter="Archivos XLSX (*.xlsx)")
                self.inputFile.setText(fname[0])
                logging.info(f"Selected file: {fname[0]}")
            elif self.manyFiles.isChecked():
                directory = QFileDialog.getExistingDirectory(self, caption="Seleccionar directorio")
                self.inputFile.setText(directory)
                logging.info(f"Selected directory: {directory}")
            elif self.multipleFiles.isChecked():
                fnames, _ = QFileDialog.getOpenFileNames(self, caption="Abrir archivo", filter="Archivos XLSX (*.xlsx)")
                self.inputFile.setText(";".join(fnames))
                logging.info(f"Selected files: {fnames}")
        except Exception as e:
            logging.error(f"Error browsing files: {e}")

    def unlock(self):
        """
        Handles the unlock button click event.
        Processes the input file(s) and displays the result to the user.
        """
        self.unlockFile.setEnabled(False)
        try:
            file_path = self.inputFile.text()
            range_sheets = self.rangeSheets.text()
            if self.oneFile.isChecked() and (not file_path or not range_sheets):
                self.messageText.setText("Complete los campos")
                return
            if self.manyFiles.isChecked() and not file_path:
                self.messageText.setText("Seleccione un directorio")
                return
            if self.multipleFiles.isChecked() and not file_path:
                self.messageText.setText("Seleccione los archivos")
                return
            if self.oneFile.isChecked() and (file_path != "" or range_sheets != ""):
                if not self.file_processor.rangeSheetsValidator(file_path, range_sheets):
                    self.messageText.setText(
                        "Alguna página ingresada excede la cantidad real de páginas del documento.")
                    return
                unlocked_sheets, msg = self.file_processor.process_single_file(file_path, range_sheets)
                self.messageText.setText(msg)
            elif self.manyFiles.isChecked():
                all_unlocked = True
                for root, _, files in os.walk(file_path):
                    for file in files:
                        if file.endswith(".xlsx"):
                            full_path = os.path.join(root, file)
                            if not self.file_processor.rangeSheetsValidator(full_path, range_sheets):
                                self.messageText.setText(
                                    "Alguna página ingresada excede la cantidad real de páginas del documento.")
                                return
                            unlocked_sheets, msg = self.file_processor.process_single_file(full_path)
                            if not unlocked_sheets:
                                all_unlocked = False
                if all_unlocked:
                    self.messageText.setText(
                        f"Todos los archivos en el directorio {file_path} han sido desbloqueados con éxito.")
                else:
                    self.messageText.setText("Ocurrió un error al intentar desbloquear algunos archivos.")
            elif self.multipleFiles.isChecked():
                files = file_path.split(";")
                all_unlocked = True
                for file in files:
                    if not self.file_processor.rangeSheetsValidator(file, range_sheets):
                        self.messageText.setText(
                            "Alguna página ingresada excede la cantidad real de páginas del documento.")
                        return
                    unlocked_sheets, msg = self.file_processor.process_single_file(file, range_sheets)
                    if not unlocked_sheets:
                        all_unlocked = False
                if all_unlocked:
                    self.messageText.setText("Todos los archivos seleccionados han sido desbloqueados con éxito.")
                else:
                    self.messageText.setText("Ocurrió un error al intentar desbloquear algunos archivos.")
        except Exception as e:
            logging.error(f"Error unlocking files: {e}")
            self.messageText.setText("Ocurrió un error al intentar desbloquear los archivos.")
        finally:
            self.unlockFile.setEnabled(True)