# Mikrotik API Boot Attack
Mikrotik API Boot Attack adalah tool sederhana untuk melakukan pengujian pada kredensial login admin Router Mikrotik dengan tekhnik Brute Force.

Tool ini hanya boleh digunakan untuk edukasi saja atau pengujian saja terutama bagi para pemilik admin Mikrotik yang membuka akses API pada port 8728 yang biasa digunakan untuk membuat akun "Mikhmon" (Mikrotik Hotspot Monitor) untuk jualan Wi-Fi voucheran.

#
<b>[ Cara Install MikrotikBot ]</b>

1. Download dan instal python (minimum python 3.x.x):
https://www.python.org/downloads/

2. Download dan instal git:
https://git-scm.com/downloads

3. Jalankan CMD (Command Prompt) git/Termux
   ```git clone https://github.com/MichaelJorky/Mikrotik-API-Boot-Attack.git .MikrotikBot```

4. Instal Colorama:
   ```python -m pip install colorama``` 

   Dokumentasi lengkap colorama -> https://pypi.org/project/colorama/

4. Instal Laiarturs Ros API
   ```python -m pip install laiarturs-ros-api``` 

   Dokumentasi lengkap laiarturs ros api -> https://pypi.org/project/laiarturs-ros-api/

5. Jalankan scrypt python lewat ```cd .MikrotikBot```

6. Lalu pastekan kode ini:

   ```python MikrotikBot.py -t 10.10.10.1 -d password.txt```
   10.10.10.1 ganti dulu dengan target tujuan.

#
<b>[ Contoh Penggunaan Kode MikrotikBot lainnya ]</b>

```
python MikrotikBot.py -t 10.10.10.1 -d password.txt
python MikrotikBot.py -t 10.10.10.1 -d password.txt -a save.json
python MikrotikBot.py -t 10.10.10.1 -d password.txt -s 3
python MikrotikBot.py -t 10.10.10.1 -d password.txt -s 3 -a save.json
python MikrotikBot.py -t 10.10.10.1 -u admin -p 80 -d password.txt
python MikrotikBot.py -t 10.10.10.1 -u admin -p 80 -d password.txt -a save.json
python MikrotikBot.py -t 10.10.10.1 -u admin -p 80 -d password.txt -s 3
python MikrotikBot.py -t 10.10.10.1 -u admin -p 80 -d password.txt -s 3 -a save.json
```

#
<b>[ Penjelasan Lengkap Kode pada MikrotikBot ]</b>

   -t 10.10.10.1: ganti dengan target ip address tujuan misalkan 192.168.1.1

   -u admin: anda bisa mengganti target username "admin" dengan misal: root, superadmin, user, support, public, debug, tech, administrator, sysadm, manager, apc, device, superuser, customer, operator, cusadmin, guest, useradmin dll

   -p 80: anda bisa mengganti port "80" dengan port lainnya, port umum pada mikrotik: 21 (ftp), 22 (ssh), 23 (telnet), 80 (http), 443 (ssl), 8291 (winbox), 8728 (api), 8729 (api ssl). port umum lainnya yang mungkin anda butuhkan: 25 (smtp), 53 (dns), 110 (pop3), 115 (sftp), 135 (rpc), 139 (netbios), 143 (imap), 194 (irc), 445 (smb), 1433 (mssql), 3306 (mysql), 3389 (rdp), 5632 (pcanywhere), 5900 (vnc), 25565 (minecraft).
   
   -d password.txt: Anda bisa menambahkan atau mengurangi jumlah daftar password pada password.txt
   
   -s 3: anda bisa mengganti delay 3 detik menjadi misal -s 2 (2 detik), -s 4 (4 detik), default 1 detik
   
   -a save.json: secara otomatis menyimpan kemajuan saat ini ke file, dan membacanya kembali saat startup
   
   Petunjuk lengkapnya: ```python MikrotikBot.py -h```
