<!-- Animated header -->
<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=0:4c1d95,50:7c3aed,100:c084fc&height=190&section=header&text=KALKULATOR%20IP&fontSize=46&fontColor=ffffff&fontAlignY=36&desc=IPv4%20Subnetting%20%7C%20VLSM%20%7C%20Network%20Toolkit&descAlignY=60&descSize=16&animation=fadeIn" alt="Kalkulator IP animated header" width="100%" />
</p>

<p align="center">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=18&pause=1000&color=C084FC&center=true&vCenter=true&width=680&lines=Hitung+IPv4+dengan+cepat+dan+jelas;Subnetting+%7C+VLSM+%7C+CIDR;Terminal+UI+bertema+ungu+%F0%9F%92%9C" alt="Animated project tagline" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/UI-Textual-7C3AED?style=for-the-badge" alt="Textual UI" />
  <img src="https://img.shields.io/badge/Output-IPv4%20Network-C084FC?style=for-the-badge" alt="IPv4 network" />
  <img src="https://img.shields.io/badge/License-Not%20specified-gray?style=for-the-badge" alt="License not specified" />
</p>

<p align="center">
  <b>Kalkulator IP</b> adalah aplikasi terminal interaktif (TUI) untuk membantu memahami dan menghitung jaringan IPv4.
  Dilengkapi tampilan live, tabel subnet, perhitungan VLSM, konversi alamat, dan referensi jaringan.
</p>

---

## ✨ Fitur

| Fitur | Keterangan |
|---|---|
| **Info IP** | Network ID, broadcast, netmask, wildcard, rentang host, jumlah alamat, kelas, dan tipe IP |
| **Live calculation** | Hasil diperbarui otomatis saat input IP/prefix berubah |
| **Binary view** | Menampilkan representasi biner IP, netmask, dan network dengan pemisah oktet |
| **Cek satu jaringan** | Memeriksa apakah alamat IP lain berada di subnet yang sama |
| **Subnetting** | Membagi jaringan berdasarkan prefix baru atau jumlah subnet |
| **VLSM** | Mengalokasikan subnet berdasarkan kebutuhan host, dari kebutuhan terbesar |
| **Konversi** | Mengubah IP, prefix, dan netmask ke bentuk desimal, biner, hexadecimal, atau integer |
| **Referensi** | Tabel prefix /8 sampai /32, kelas IP, dan rentang alamat khusus |
| **Tampilan interaktif** | Antarmuka terminal dengan tema ungu, splash screen, dan animasi judul |

## 🧰 Teknologi

- **Python 3.10+** — bahasa pemrograman utama.
- **Textual** — framework untuk membangun antarmuka terminal interaktif.
- **Rich** — komponen tabel, panel, teks berwarna, dan layout terminal.
- **ipaddress** — library standar Python untuk operasi alamat dan jaringan IP.

## 📋 Persyaratan

Sebelum menjalankan aplikasi, siapkan:

- Python **3.10 atau lebih baru**.
- Terminal yang mendukung tampilan teks/Unicode.
- Koneksi internet saat pertama kali memasang dependency.

Cek versi Python:

```bash
python --version
```

Di sebagian sistem Linux/macOS, gunakan:

```bash
python3 --version
```

## 🚀 Instalasi

### 1. Clone repository

```bash
git clone https://github.com/0xNanzaa25/Calculator-IP.git
cd Calculator-IP
```

### 2. Pastikan file aplikasi tersedia

File utama aplikasi adalah `ipcalc.py` dan dijalankan dari direktori repository:

```text
Calculator-IP/
└── ipcalc.py
```

### 3. (Disarankan) Buat virtual environment

**Windows — PowerShell:**

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

Jika PowerShell memblokir aktivasi script, buka terminal Command Prompt lalu jalankan:

```bat
.venv\Scripts\activate.bat
```

**Linux / macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Instal dependency

```bash
python -m pip install --upgrade pip
python -m pip install textual rich
```

### 5. Jalankan aplikasi

**Windows:**

```powershell
python ipcalc.py
```

**Linux / macOS:**

```bash
python3 ipcalc.py
```

> Jalankan perintah dari folder yang berisi `ipcalc.py`. Jika perintah `python` tidak tersedia, coba `python3` (Linux/macOS) atau `py` (Windows).

## 📱 Instalasi di Android (Termux)

Aplikasi ini dapat dicoba melalui terminal Termux selama versi Python dan dependency yang terpasang kompatibel.

```bash
pkg update
pkg install python git
git clone https://github.com/0xNanzaa25/Calculator-IP.git
cd Calculator-IP
python -m pip install --upgrade pip
python -m pip install textual rich
python ipcalc.py
```

Pastikan file `ipcalc.py` sudah ada di folder repository sebelum menjalankan perintah terakhir.

## 🕹️ Cara Penggunaan

### 1. Menghitung informasi IP

Masukkan alamat IPv4 beserta prefix pada kolom utama, lalu tekan Enter atau pilih **Hitung**.

Contoh:

```text
192.168.1.10/24
```

Netmask juga dapat digunakan sebagai pengganti angka prefix:

```text
192.168.1.10/255.255.255.0
```

Hasil akan menampilkan informasi seperti:

- IP address dan prefix.
- Netmask dan wildcard.
- Network ID dan broadcast address.
- Host pertama dan host terakhir.
- Jumlah host usable dan total alamat.
- Pembagian bit network/host.
- Kelas serta tipe alamat IP.
- Representasi biner dan ringkasan hasil perhitungan.

### 2. Memeriksa apakah dua IP satu jaringan

Pada tab **Info IP**, isi kolom pemeriksaan dengan alamat IP lain.

Contoh:

- IP utama: `192.168.1.10/24`
- IP pembanding: `192.168.1.77`

Aplikasi akan memberi tahu apakah IP pembanding termasuk jaringan yang sama. Jika berbeda jaringan, aplikasi juga menampilkan network dari IP pembanding menggunakan prefix yang sama.

### 3. Subnetting

Buka tab **Subnetting**. Masukkan salah satu dari dua format berikut:

**Menggunakan prefix baru:**

```text
/26
```

**Menggunakan jumlah subnet:**

```text
4
```

Aplikasi menghitung jumlah subnet, kapasitas host, netmask, dan menampilkan tabel network hasil pembagian. Jika jumlah subnet bukan pangkat dua, jumlahnya dibulatkan ke pangkat dua berikutnya. Maksimal **1.024 baris subnet pertama** yang ditampilkan agar tabel tetap terkendali.

### 4. VLSM

Buka tab **VLSM**, kemudian masukkan kebutuhan host yang dipisahkan koma, spasi, atau titik koma.

Contoh:

```text
100, 50, 25, 10
```

Aplikasi akan:

1. Mengurutkan kebutuhan host dari yang terbesar.
2. Menentukan prefix subnet yang sesuai untuk setiap kebutuhan.
3. Mengalokasikan subnet secara berurutan dari awal network induk.
4. Menampilkan network, netmask, rentang host, broadcast, dan kapasitas host.
5. Memberi tahu jika ada kebutuhan LAN yang tidak muat di jaringan induk.

**Catatan:** sisakan kapasitas yang cukup pada network induk. Pada subnet IPv4 biasa, alamat network dan broadcast tidak dihitung sebagai host usable.

### 5. Konversi IP, prefix, dan netmask

Buka tab **Konversi**, lalu masukkan salah satu format berikut.

| Input | Contoh | Informasi yang ditampilkan |
|---|---|---|
| IPv4 | `192.168.1.1` | Biner, hexadecimal, integer, kelas, dan tipe IP |
| Prefix | `/26` | Netmask, wildcard, biner, total alamat, dan host usable |
| Netmask | `255.255.255.192` | Prefix, wildcard, dan biner |

### 6. Referensi

Tab **Referensi** menyediakan tabel prefix dari /8 sampai /32, kelas IP, serta rentang private dan alamat khusus.

## ⌨️ Pintasan Keyboard

| Tombol | Fungsi |
|---|---|
| `F1` | Buka Info IP |
| `F2` | Buka Subnetting |
| `F3` | Buka VLSM |
| `F4` | Buka Konversi |
| `F5` | Buka Referensi |
| `Ctrl + L` | Fokus ke input IP utama |
| `Ctrl + R` | Reset seluruh input |
| `Ctrl + Q` | Keluar dari aplikasi |
| Tombol apa saja saat splash screen | Lewati splash screen |

## 🧠 Catatan Perhitungan

- Prefix IPv4 valid berada pada rentang **/0 sampai /32**.
- Aplikasi menerima prefix CIDR maupun netmask IPv4 yang valid.
- Untuk subnet **/31**, kedua alamat dihitung sebagai alamat yang dapat digunakan pada koneksi point-to-point.
- Untuk subnet **/32**, satu alamat dihitung sebagai satu alamat host.
- Untuk prefix /0 sampai /30, perhitungan host usable mengurangi alamat network dan broadcast.
- Pada tab Subnetting, tampilan dibatasi hingga 1.024 subnet pertama.

## ☁️ Menjalankan di Google Colab

Google Colab dapat digunakan untuk menyiapkan Python dan dependency proyek. Namun, aplikasi ini menggunakan **Textual TUI** (antarmuka terminal interaktif). Karena itu, jalankan aplikasinya melalui fitur **Terminal** Colab jika tersedia, bukan melalui cell notebook biasa.

### 1. Buka notebook Colab

Buka [Google Colab](https://colab.research.google.com/) dan buat notebook baru. Pastikan runtime menggunakan Python.

### 2. Clone repository

Jalankan pada satu cell:

```python
!git clone https://github.com/0xNanzaa25/Calculator-IP.git
```

### 3. Masuk ke folder proyek

```python
%cd /content/Calculator-IP
```

### 4. Instal dependency

```python
!python -m pip install --upgrade pip
!python -m pip install textual rich
```

### 5. Jalankan melalui Terminal Colab

1. Buka panel **Terminal** di Colab (jika tersedia pada akun/runtime kamu).
2. Jalankan perintah berikut:

```bash
cd /content/Calculator-IP
python ipcalc.py
```

Jika Terminal tidak tersedia, aplikasi TUI ini tidak dapat digunakan secara penuh dari cell notebook biasa. Cell Colab tidak menyediakan pengalaman terminal interaktif yang dibutuhkan untuk navigasi keyboard dan tampilan Textual.

**Penting:** langkah di atas menyiapkan environment dan menjalankan aplikasi dari terminal. Pastikan file `ipcalc.py` memang tersedia di repository. Instalasi dependency saja tidak akan membuat file aplikasi yang belum ada menjadi tersedia.

---

## 🛠️ Troubleshooting

**Error `ModuleNotFoundError: No module named 'textual'` atau `rich`**

Pasang dependency:

```bash
python -m pip install textual rich
```

**Perintah `python` tidak ditemukan**

Coba gunakan `python3` di Linux/macOS atau `py` di Windows.

**Tampilan karakter tidak rapi**

Gunakan terminal modern dengan dukungan Unicode. Perbesar lebar terminal jika tabel terlihat terpotong.

**Aplikasi tidak bisa dijalankan**

Pastikan:
1. Versi Python minimal 3.10.
2. Dependency Textual dan Rich sudah terpasang pada environment yang sedang digunakan.
3. Perintah dijalankan dari direktori yang berisi `ipcalc.py`.

## 👨‍💻 Developer

<p align="center">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=20&pause=1200&color=A855F7&center=true&vCenter=true&width=420&lines=AndraxC2;Building+with+Python;Learn.+Build.+Understand." alt="Developer animation" />
</p>

<p align="center">
  Dibuat untuk belajar dan mempermudah eksplorasi konsep jaringan IPv4.
</p>

<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=0:4c1d95,50:7c3aed,100:c084fc&height=110&section=footer&animation=fadeIn" alt="Animated footer" width="100%" />
</p>
