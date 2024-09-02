import logging


class Log:

# Untuk inisialisasi, kelas Log menerima 3 argumen: path, logic, file_mode.
# path:
#  - False - tidak melakukan logging. Tidak akan menyimpan apa pun ke file dan tidak akan mencetak apa pun ke stdout.
#  - True - akan mencetak output yang lebih detail ke stdout.
#  - string - akan menyimpan output yang lebih detail ke file dengan nama sesuai string ini.
# logic:
#  - 'OR' - jika path berupa string, hanya menyimpan output detail ke file;
#  - 'AND' - jika path berupa string, mencetak output detail ke stdout dan menyimpannya ke file.
# file_mode:
#  - 'a' - menambahkan log ke file yang sudah ada
#  - 'w' - membuat file baru untuk logging, jika file dengan nama tersebut sudah ada, file tersebut akan ditimpa.

    def __init__(self, path, logic, file_mode):

        # Jika perlu logging ke file, konfigurasikan terlebih dahulu
        if path is not True and type(path) == str:
            logging.basicConfig(filename=path, filemode=file_mode,
                                format='%(asctime)s - %(message)s', level=logging.DEBUG)

        # Definisikan berbagai aksi log yang dapat digunakan
        def nothing(message):
            pass

        def to_file(message):
            logging.debug(message)

        def to_stdout(message):
            print(message)

        def both(message):
            print(message)
            logging.debug(message)

        # Tetapkan aksi yang sesuai berdasarkan nilai path dan logic
        if not path:
            self.func = nothing

        elif path is True:
            self.func = to_stdout

        elif path is not True and type(path) == str and logic == 'OR':
            self.func = to_file

        elif path is not True and type(path) == str and logic == 'AND':
            self.func = both
        else:
            self.func = to_stdout

    def __call__(self, message):
        self.func(message)
