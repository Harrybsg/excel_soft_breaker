import os
import zipfile
import shutil
import logging
import pandas as pd

class FileProcessor:
    """
    Class to handle file processing tasks such as extracting, modifying, and compressing files.
    """
    ext_zip = '.zip'
    ext_xlsx = '.xlsx'

    def process_single_file(self, file_path, range_sheets=None):
        """
        Processes a single file to unlock specified sheets.

        Args:
            file_path (str): Path to the file to be processed.
            range_sheets (str): Range of sheets to be unlocked.

        Returns:
            list: List of unlocked sheets.
        """
        try:
            if not os.path.exists(file_path):
                msg = f"El archivo {file_path} no existe."
                logging.error(msg)
                return [], msg
            if range_sheets is None or range_sheets == "":
                range_sheets = ",".join(map(str, range(1, self.sheetsLength(file_path) + 1)))
                logging.info(f"range_sheets: {range_sheets}")
            if self.inputFormatValidator(range_sheets):
                if self.inputRangeValidator(range_sheets) and self.rangeSheetsValidator(file_path, range_sheets):
                    logging.info("Validations passed")
                    file_path_zip = self.changeExtension(file_path, FileProcessor.ext_zip)
                    if file_path_zip != -1:
                        logging.info("Extension changed")
                        unzipped_directory = self.extractZip(file_path_zip)
                        logging.info("Extraction completed")
                        self.modifySheets(unzipped_directory, range_sheets)
                        logging.info("Sheets modified")
                        file_compressed_zip_format = self.compressandcreate(file_path_zip, unzipped_directory)
                        file_unlocked_xlsx_format = self.changeExtension(file_compressed_zip_format,
                                                                         FileProcessor.ext_xlsx)
                        self.copyAndDelete(file_unlocked_xlsx_format, file_path)
                        msg = f"El archivo {file_path} ha sido desbloqueado con éxito."
                        logging.info(msg)
                        return self.process_string(range_sheets), msg
                    else:
                        msg = f"Se detectó que quiere volver a desbloquear el archivo {file_path}. Primero elimine el archivo {FileProcessor.ext_zip}"
                        logging.error(msg)
                        return [], msg
            else:
                msg = "Error en la validación del formato de entrada."
                logging.error(msg)
                return [], msg
        except Exception as e:
            msg = f"Error al desbloquear el archivo {file_path}: {e}"
            logging.error(msg)
            return [], msg

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
            if not os.path.exists(extraction_path):
                os.makedirs(extraction_path)
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                zip_ref.extractall(extraction_path)
            return extraction_path
        except Exception as e:
            logging.error(f"Error extracting zip file: {e}")
            return ""

    def compressandcreate(self, zip_file_name, directory):
        """
        Compresses a directory into a zip file.

        Args:
            zip_file_name (str): Name of the zip file to be created.
            directory (str): Directory to be compressed.

        Returns:
            str: Path to the created zip file.
        """
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
        """
        Copies the unlocked file to the original path and deletes the temporary directory.

        Args:
            unlocked_file (str): Path to the unlocked file.
            original_path (str): Original path of the file.
        """
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

    def sheetsLength(self, file):
        """
        Gets the number of sheets in an Excel file.

        Args:
            file (str): Path to the Excel file.

        Returns:
            int: Number of sheets in the file.
        """
        logging.info(f"Getting sheet length for file: {file}")
        if not os.path.exists(file):
            logging.error(f"File does not exist: {file}")
            return 0
        try:
            xl = pd.ExcelFile(file)
            logging.info(f"xl.sheet_names:  {xl.sheet_names}")
            npag = len(xl.sheet_names)
            logging.info(f"npag:  {npag}")
            return npag
        except Exception as e:
            logging.error(f"Error reading Excel file: {e}")
            return 0

    def process_string(self, input_string):
        """
        Processes the input string to generate a list of sheet numbers.

        Args:
            input_string (str): Input string containing sheet ranges.

        Returns:
            list: List of sheet numbers.
        """
        logging.info("Processing input string")
        logging.info(f"input_string: {input_string}")
        input_list = input_string.split(",")
        processed_list = []
        logging.info("antes del for process_string")
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

    def rangeSheetsValidator(self, file_path, range_sheets):
        """
        Validates if the range of sheets is within the actual number of sheets in the file.

        Args:
            file_path (str): Path to the file.
            range_sheets (str): Range of sheets to be validated.

        Returns:
            bool: True if the range is valid, False otherwise.
        """
        logging.info("Validating range sheets")
        npag = self.sheetsLength(file_path)
        logging.info(f"npag: {npag}")
        logging.info(f"Values: {range_sheets}")
        output_values = self.process_string(range_sheets)
        logging.info(f"output_values: {output_values}")
        logging.info(f"output_values_type:  {type(output_values)}")
        logging.info(f"Págs:  {output_values}")
        last_page = int(output_values[-1])
        logging.info(f"last_page:  {type(last_page)}")
        logging.info(f"npag:  {type(npag)}")
        if last_page > npag:
            logging.error(
                f"Alguna página ingresada excede la cantidad real de páginas del documento. Cant. Pág. del Doc: {npag}")
            return False
        return True

    def inputRangeValidator(self, range_sheets):
        """ Verifica si la entrada del rango de páginas termina en '-' o en ','.
        Args:
            range_sheets: Entrada de texto. Ejemplo: 1,3,5-8
        Returns:
            False si la entrada termina en '-' o en ',' y True si no.
        """
        logging.info("Validating input range")
        if range_sheets.endswith(",") or range_sheets.endswith("-"):
            logging.error("Se detectó una ',' o un '-' al final del intervalo de hojas. Borre para continuar.")
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

    def modifySheets(self, zip_directory, range_sheets):
        """
        Modifies the sheets in the extracted directory based on the specified range.

        Args:
            zip_directory (str): Path to the extracted directory.
            range_sheets (str): Range of sheets to be modified.
        """
        logging.info(f"Modifying sheets in directory: {zip_directory}")
        try:
            zip_directory_path = zip_directory + "/xl/worksheets"
            sheets = self.process_string(range_sheets)
            files = os.listdir(zip_directory_path)
            xml_files = [file for file in files if file.endswith(".xml")]
            logging.info(f"xml_files sheets: {xml_files}")
            for sheet in sheets:
                found = False
                for nsheet in range(len(xml_files)):
                    result = xml_files[nsheet].split('sheet')[1].split('.xml')[0]
                    logging.info(f"Hoja n°: {result}")
                    if result.isdigit() and int(result) == sheet:
                        logging.info("coincide")
                        mfile = xml_files[nsheet]
                        logging.info(f"mfile: {mfile}")
                        found = True
                        break
                if not found:
                    logging.error(f"Sheet {sheet} not found in the directory")
                    raise ValueError(f"Sheet {sheet} not found in the directory")
                full_path = zip_directory_path + "/" + mfile
                with open(full_path, "r") as f:
                    content = f.read()
                    content = content.replace('sheet="1"', 'sheet="0"')
                with open(full_path, "w") as f:
                    f.write(content)
        except Exception as e:
            logging.error(f"Error modifying sheets: {e}")