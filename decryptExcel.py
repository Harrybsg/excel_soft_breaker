import os
import sys
import pandas as pd
import zipfile
from PyQt6 import QtWidgets, uic
from PyQt6.QtCore import QRegularExpression
from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtWidgets import QDialog, QApplication, QFileDialog
import shutil
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MainWindow(QDialog):
    ext_zip = '.zip'
    ext_xlsx = '.xlsx'

    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi("unlockFile.ui", self)
        self.sheetValidator()
        self.continuar.clicked.connect(self.setFileSettings)
        self.cleanOptionFiles.clicked.connect(self.clean)
        self.uploadChoice.clicked.connect(self.browsefiles)
        self.unlockFile.clicked.connect(self.unlock)

    # region Botones de acción
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
        desbloquear un archivo o varios archivos."""
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
        else:
            self.intervalLabel.setEnabled(True)
            self.rangeSheets.setEnabled(True)
            self.clearInputRange.setEnabled(True)

    def browsefiles(self):
        try:
            if self.oneFile.isChecked():
                fname = QFileDialog.getOpenFileName(self, caption=caption, filter=filterSheet)
                self.inputFile.setText(fname[0])
                logging.info(f"Selected file: {fname[0]}")
            if self.manyFiles.isChecked():
                directory = QFileDialog.getExistingDirectory(self, caption="Seleccionar directorio")
                self.inputFile.setText(directory)
                logging.info(f"Selected directory: {directory}")
        except Exception as e:
            logging.error(f"Error browsing files: {e}")

    def unlock(self):
        try:
            file_path = self.inputFile.text()
            range_sheets = self.rangeSheets.text()
            if self.oneFile.isChecked() and (not file_path or not range_sheets):
                self.messageText.setText("Complete los campos")
                return
            if self.manyFiles.isChecked() and not file_path:
                self.messageText.setText("Seleccione un directorio")
                return
            if self.oneFile.isChecked() and (file_path != "" or range_sheets != ""):
                self.process_single_file(file_path, range_sheets)
            elif self.manyFiles.isChecked():
                for root, _, files in os.walk(file_path):
                    for file in files:
                        if file.endswith(".xlsx"):
                            full_path = os.path.join(root, file)
                            self.process_single_file(full_path, range_sheets)
                self.messageText.setText(
                    f"Todos los archivos en el directorio {file_path} han sido desbloqueados con éxito.")
        except Exception as e:
            logging.error(f"Error unlocking files: {e}")
            self.messageText.setText("Ocurrió un error al intentar desbloquear los archivos.")

    def process_single_file(self, file_path, range_sheets):
        try:
            if not os.path.exists(file_path):
                self.messageText.setText(f"El archivo {file_path} no existe.")
                return
            if self.inputFormatValidator(range_sheets):
                if self.inputRangeValidator(range_sheets) and self.rangeSheetsValidator(file_path, range_sheets):
                    logging.info("Validations passed")
                    file_path_zip = self.changeExtension(file_path, MainWindow.ext_zip)
                    if file_path_zip != -1:
                        logging.info("Extension changed")
                        unzipped_directory = self.extractZip(file_path_zip)
                        logging.info("Extraction completed")
                        self.modifySheets(unzipped_directory)
                        logging.info("Sheets modified")
                        file_compressed_zip_format = self.compressandcreate(file_path_zip, unzipped_directory)
                        file_unlocked_xlsx_format = self.changeExtension(file_compressed_zip_format,
                                                                         MainWindow.ext_xlsx)
                        self.copyAndDelete(file_unlocked_xlsx_format, file_path)
                        logging.info(f"El archivo {file_path} ha sido desbloqueado con éxito.")
                    else:
                        self.messageText.setText(
                            f"Se detectó que quiere volver a desbloquear el archivo {file_path}. \n "
                            "Primero elimine el siguiente archivo antes de continuar: " +
                            os.path.splitext(file_path)[0] + MainWindow.ext_zip)
        except Exception as e:
            logging.error(f"Error unlocking file {file_path}: {e}")
            self.messageText.setText(f"Ocurrió un error al intentar desbloquear el archivo {file_path}.")

    # endregion

    # region Funciones de validación de entrada
    def sheetValidator(self):
        """ Función que verifica la entrada del rango de páginas, solo se permite números seguido de (,) o (-)
            No permite que una (,) y (-) esten juntos.
        """
        noSpaceValidator = QRegularExpressionValidator(QRegularExpression("^(?!0)[1-9][0-9]*(?:,[1-9][0-9]*|-[1-9][0-9]*)+$"), self.rangeSheets)
        self.rangeSheets.setValidator(noSpaceValidator)

    def inputRangeValidator(self, range_sheets):
        """ Verifica si la entrada del rango de páginas termina en '-' o en ','.
        Args:
            range_sheets: Entrada de texto. Ejemplo: 1,3,5-8
        Returns:
            False si la entrada termina en '-' o en ',' y True si no.
        """
        logging.info("Validating input range")
        if range_sheets.endswith(",") or range_sheets.endswith("-"):
            self.messageText.setText("Se detectó una ',' o un '-' al final del intervalo de hojas. Borre para continuar.")
            return False
        return True

    def inputFormatValidator(self, range_sheets):
        """ Verifica si la entrada del rango de páginas en caso de contener un valor con el formato:
            n-m, n sea menor que m.
        Args:
            range_sheets: Entrada de texto. Ejemplo: 1,3,5-8
        Returns:
            False si la entrada contiene un valor n-m, donde n > m. True si n < m.
        """
        logging.info("Validating input format")
        valores = range_sheets.split(",")
        for valor in valores:
            if "-" in valor:
                num1, num2 = map(int, valor.split("-"))
                if num1 > num2:
                    return False
        return True
    # endregion

    # region Funciones de acción
    def changeExtension(self, file_path, ext):
        """ Cambia la extensión del archivo al pasado por parámetro.
        Args:
            file_path: Ruta entera del archivo, incluido el archivo.
            ext: Extensión a la cual se quiere cambiar el archivo. Ejm.- .zip, .xlsx.
        Returns:
            La ruta completa del archivo con la nueva extensión.
        """
        logging.info(f"Changing extension of {file_path} with {ext}")
        try:
            new_file_path = os.path.splitext(file_path)[0] + ext
            if os.path.exists(new_file_path):
                return -1
            else:
                os.rename(file_path, new_file_path)
                return new_file_path
        except Exception as e:
            logging.error(f"Error changing file extension: {e}")
            return -1

    def extractZip(self, zip_file_path):
        """ Extrae el contenido del archivo en la ruta especificada, si no existe la ruta esta se crea con el nombre
        del archivo sin extensión.
        Args:
            zip_file_path: Ruta del archivo .zip.
        Returns:
            La ruta del directorio donde se extrajo el archivo .zip.
        """
        logging.info(f"Extracting zip file: {zip_file_path}")
        try:
            extraction_path = os.path.splitext(zip_file_path)[0]
            logging.info(f"extraction_path: : {extraction_path}")
            # Verificar si el directorio existe
            if not os.path.exists(extraction_path):
                os.makedirs(extraction_path)
            logging.info(f"pasa la extracción: {os.path.exists(extraction_path)}")
            # Extraer en el directorio
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                zip_ref.extractall(extraction_path)
            return extraction_path
        except Exception as e:
            logging.error(f"Error extracting zip file: {e}")
            return ""
    # endregion

    def process_string(self, input_string):
        logging.info("Processing input string")
        logging.info(f"input_string: {input_string}")
        input_list = input_string.split(",")
        processed_list = []
        for i in input_list:
            if "-" in i:
                start, end = map(int, i.split("-"))
                processed_list += [str(x) for x in range(start, end + 1)]
            else:
                if i.isdigit():
                    processed_list.append(i)
        processed_list = sorted(list(set(processed_list)))
        processed_list = ",".join(processed_list)
        processed_list = [int(x) for x in processed_list.split(",")]
        processed_list.sort()
        logging.info(f"processed_list: {processed_list}")
        return processed_list

    def sheetsLength(self, file):
        logging.info(f"Getting sheet length for file: {file}")
        if not os.path.exists(file):
            logging.error(f"File does not exist: {file}")
            return 0
        try:
            xl = pd.ExcelFile(file)
            print("xl.sheet_names: ", xl.sheet_names)
            npag = len(xl.sheet_names)
            print("npag: ", npag)
            return npag
        except Exception as e:
            logging.error(f"Error reading Excel file: {e}")
            return 0

    def rangeSheetsValidator(self, file_path, range_sheets):
        logging.info("Validating range sheets")
        npag = self.sheetsLength(file_path)
        print(npag)
        print("Values: ", range_sheets)
        output_values = self.process_string(range_sheets)
        print("output_values: ", output_values)
        print("output_values_type: ", type(output_values))
        print("Págs: ", output_values)
        last_page = int(output_values[-1])
        print("last_page: ", type(last_page))
        print("npag: ", type(npag))
        if last_page > npag:
            self.messageText.setText(
                "Alguna página ingresada excede la cantidad real de páginas del documento.\n Cant. Pág. del Doc: " + str(npag))
            return False
        return True

    def modifySheets(self, zip_directory):
        logging.info(f"Modifying sheets in directory: {zip_directory}")
        try:
            zip_directory_path = zip_directory + "/xl/worksheets"
            logging.info(f"modifySheets zip_directory_path: {zip_directory_path}")
            range_sheets = self.rangeSheets.text()
            sheets = self.process_string(range_sheets)
            logging.info(f"modify sheets: {sheets}")
            files = os.listdir(zip_directory_path)
            xml_files = [file for file in files if file.endswith(".xml")]
            logging.info(f"xml_files sheets: {xml_files}")
            mfile = ""
            found = False
            for sheet in sheets: #3,5,6
                for nsheet in range(len(xml_files)):
                    result = xml_files[nsheet].split('sheet')[1].split('.xml')[0]
                    logging.info(f"Hoja n°: {result}")
                    if int(result) == sheet:
                        logging.info("coincide")
                        mfile = xml_files[nsheet]
                        logging.info(f"mfile: {mfile}")
                        found = True
                        break
                if not found:
                    logging.error(f"Sheet {sheet} not found in the directory")
                    raise ValueError(f"Sheet {sheet} not found in the directory")
                logging.info("salgo del segundo for")
                full_path = zip_directory_path + "/" + mfile
                with open(full_path, "r") as f:
                    content = f.read()
                    # Modificación del contenido
                    content = content.replace('sheet="1"', 'sheet="0"')
                with open(full_path, "w") as f:
                    f.write(content)
            logging.info("salgo del primer for")
        except Exception as e:
            logging.error(f"Error modifying sheets: {e}")

    def compressandcreate(self, zip_file_name, directory):
        logging.info(f"Compressing and creating zip file: {zip_file_name}")
        try:
            zip_base_name = os.path.basename(zip_file_name)
            logging.info(f"compressandcreate zip_file_name: {zip_base_name}")
            directory = directory.replace("/", "\\")
            logging.info(f"compressandcreate directory: {directory}")
            full_zip_file_name = os.path.join(directory, zip_base_name)
            logging.info(f"compressandcreate zip_file_name 2: {full_zip_file_name}")
            logging.info(f"compressandcreate os.listdir(directory): {os.listdir(directory)}")

            with zipfile.ZipFile(full_zip_file_name, "w") as zip_file:
                for root, dirs, files in os.walk(directory):
                    for filename in files:
                        if filename == zip_base_name:
                            continue
                        file_path = os.path.join(root, filename)
                        zip_file.write(file_path, arcname=os.path.relpath(file_path, directory))

            logging.info(f"Ruta archivo unlocked: {full_zip_file_name}")
            return full_zip_file_name
        except Exception as e:
            logging.error(f"Error compressing and creating zip file: {e}")
            return ""

    def copyAndDelete(self, unlocked_file, original_path):
        logging.info(f"Copying and deleting files: {unlocked_file} to {original_path}")
        try:
            old_path = os.path.dirname(unlocked_file)
            original_path = original_path.replace("/", "\\")
            logging.info(f"os.path.dirname(original_path): {os.path.dirname(original_path)}")
            logging.info(f"os.path.basename(original_path): {os.path.basename(original_path)}")
            # Path de destino = nombre de directorio original + nombre del archivo.xlsx
            dst_path = os.path.dirname(original_path) + "\\" + os.path.basename(original_path)
            logging.info(f"old_path: {old_path}")
            logging.info(f"dst_path: {dst_path}")
            shutil.copy2(unlocked_file, dst_path)
            shutil.rmtree(old_path)
        except Exception as e:
            logging.error(f"Error copying and deleting files: {e}")


filterSheet = "Archivos XLSX (*.xlsx)"
caption = "Abrir archivo"
values = ""
app = QApplication(sys.argv)
mainWindow = MainWindow()
widget = QtWidgets.QStackedWidget()
widget.addWidget(mainWindow)
widget.setFixedWidth(550)
widget.setFixedHeight(500)
widget.show()
sys.exit(app.exec())
