import json
import sys
import os
import textwrap

def muat_basis_pengetahuan(nama_file="kb_laptop.json"):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path_lengkap = os.path.join(base_dir, nama_file)
    if not os.path.exists(path_lengkap):
        path_lengkap = nama_file
        
    if not os.path.exists(path_lengkap):
        print(f"Error: File basis pengetahuan '{nama_file}' tidak ditemukan.")
        sys.exit(1)
    with open(path_lengkap, "r", encoding="utf-8") as f:
        return json.load(f)

def cari_fakta_tanya(kb):
    """
    Fakta yang tidak pernah menjadi hasil aturan (maka) adalah fakta input
    yang harus ditanyakan ke pengguna.
    """
    semua_hasil = {aturan["maka"] for aturan in kb["aturan"]}
    fakta_tanya = []
    
    for aturan in kb["aturan"]:
        for premis in aturan["jika"]:
            if premis not in semua_hasil and premis not in fakta_tanya:
                fakta_tanya.append(premis)
    return fakta_tanya

def format_pertanyaan(fakta):
    mapping_teks = {
        "laptop menyala tetapi layar blank hitam tanpa tampilan logo BIOS": "Apakah laptop dapat menyala (indikator power aktif) tetapi layar blank hitam tanpa logo BIOS?",
        "terdengar bunyi beep berulang atau lampu LED CapsLock berkedip": "Apakah terdengar bunyi beep berulang dari motherboard atau lampu LED CapsLock/indikator berkedip?",
        "laptop gagal masuk ke sistem operasi dan restart berulang kali": "Apakah laptop gagal memuat sistem operasi dan terus-menerus restart secara berulang (boot-loop)?",
        "bodi bawah laptop terasa sangat panas menyengat": "Apakah area bodi bawah laptop terasa sangat panas menyengat saat disentuh?",
        "suara kipas pendingin berputar kencang tanpa henti atau terdengar mendengung kasar": "Apakah kipas pendingin internal berputar dengan kecepatan maksimal tanpa henti atau bersuara mendengung kasar?",
        "laptop mati mendadak setelah digunakan beberapa menit saat menjalankan aplikasi berat": "Apakah laptop tiba-tiba mati mendadak (shutdown sendiri) saat menjalankan aplikasi berat/game?",
        "layar menampilkan pesan error No Bootable Device Found atau Operating System Not Found": "Apakah layar menampilkan pesan kesalahan 'No Bootable Device Found' atau 'Operating System Not Found'?",
        "terdengar bunyi ketukan klik berulang pada area storage atau drive tidak terbaca di BIOS": "Apakah terdengar bunyi ketukan 'klik' berulang dari area harddisk atau storage drive tidak terdeteksi di BIOS?",
        "laptop langsung mati seketika saat charger adaptor dilepas": "Apakah laptop langsung mati seketika begitu kabel charger adaptor dicabut?",
        "indikator baterai pada sistem operasi bertuliskan Plugged In Not Charging": "Apakah status ikon baterai di sistem operasi bertuliskan 'Plugged In, Not Charging' walau charger terpasang?"
    }
    return mapping_teks.get(fakta, f"Apakah {fakta}?")

def jalankan_forward_chaining(kb, fakta_awal):
    """
    Mesin inferensi Forward Chaining:
    Mulai dari fakta yang diketahui, cari aturan yang syaratnya terpenuhi,
    tambahkan hasilnya ke memori, catat sumber dan alasan penelusuran.
    """
    memori = set(fakta_awal)
    jejak_alasan = {}
    siklus_log = []
    
    semua_kesimpulan_akhir = {
        aturan["maka"] for aturan in kb["aturan"] 
        if aturan["id"] in ["R3", "R4", "R5", "R6"]
    }
    
    siklus = 1
    while True:
        cocok = []
        for aturan in kb["aturan"]:
            hasil = aturan["maka"]
            if hasil in memori:
                continue
            
            mode = aturan.get("mode", "dan").lower()
            syarat = aturan["jika"]
            
            if mode == "dan":
                terpenuhi = all(s in memori for s in syarat)
            elif mode == "atau":
                terpenuhi = any(s in memori for s in syarat)
            else:
                terpenuhi = False
                
            if terpenuhi:
                cocok.append(aturan)
        
        if not cocok:
            siklus_log.append(f"Siklus {siklus}: tidak ada aturan baru, berhenti")
            break
            
        r = cocok[0]
        hasil_r = r["maka"]
        memori.add(hasil_r)
        
        premis_aktif = [s for s in r["jika"] if s in memori]
        jejak_alasan[hasil_r] = {
            "id": r["id"],
            "premis": premis_aktif,
            "sumber": r["sumber"]
        }
        siklus_log.append(f"Siklus {siklus}: {r['id']} -> {hasil_r}")
        siklus += 1
        
    kesimpulan_ditemukan = [k for k in memori if k in semua_kesimpulan_akhir]
    return kesimpulan_ditemukan, jejak_alasan, siklus_log

def cetak_alasan_rekursif(item, jejak_alasan, indent="  "):
    if item not in jejak_alasan:
        return
    info = jejak_alasan[item]
    premis_str = ", ".join(info["premis"])
    print(f"{indent}{item} <- {info['id']} ({premis_str}) [Sumber: {info['sumber']}]")
    for p in info["premis"]:
        cetak_alasan_rekursif(p, jejak_alasan, indent + "    ")

def main():
    kb = muat_basis_pengetahuan("kb_laptop.json")
    fakta_tanya = cari_fakta_tanya(kb)
    
    print("=" * 76)
    print(textwrap.fill(kb['judul'].upper(), width=76))
    print("=" * 76)
    print("Jawab setiap pertanyaan dengan 'y' (Ya) atau 't' (Tidak).\n")
    
    fakta_awal = []
    
    if len(sys.argv) > 1 and sys.argv[1].startswith("--test="):
        kasus = sys.argv[1].split("=")[1]
        print(f"[MODE PENGUJIAN OTOMATIS: KASUS {kasus}]")
        if kasus == "1":
            jawaban_ya = {
                "laptop menyala tetapi layar blank hitam tanpa tampilan logo BIOS",
                "terdengar bunyi beep berulang atau lampu LED CapsLock berkedip",
                "laptop gagal masuk ke sistem operasi dan restart berulang kali"
            }
        elif kasus == "2":
            jawaban_ya = {
                "bodi bawah laptop terasa sangat panas menyengat",
                "suara kipas pendingin berputar kencang tanpa henti atau terdengar mendengung kasar",
                "laptop mati mendadak setelah digunakan beberapa menit saat menjalankan aplikasi berat"
            }
        elif kasus == "3":
            jawaban_ya = {
                "laptop menyala tetapi layar blank hitam tanpa tampilan logo BIOS"
            }
        else:
            print("Kasus tidak dikenal (pilih 1, 2, atau 3).")
            return
            
        for i, f in enumerate(fakta_tanya, 1):
            tanya = format_pertanyaan(f)
            jawab = "y" if f in jawaban_ya else "t"
            print(f"{i:2d}. {tanya} (y/t) > {jawab}")
            if jawab == "y":
                fakta_awal.append(f)
    else:
        for i, f in enumerate(fakta_tanya, 1):
            tanya = format_pertanyaan(f)
            while True:
                jawab = input(f"{i:2d}. {tanya} (y/t) > ").strip().lower()
                if jawab in ['y', 'ya', 't', 'tidak']:
                    break
                print("   Mohon masukkan 'y' atau 't'.")
            if jawab in ['y', 'ya']:
                fakta_awal.append(f)
                
    print("\n" + "-" * 70)
    print("PROSES INFERENSI FORWARD CHAINING:")
    print("-" * 70)
    print(f"Fakta awal dari indikator gejala fisik ({len(fakta_awal)} gejala teridentifikasi):")
    if fakta_awal:
        for f in fakta_awal:
            print(f"  * {f}")
    else:
        print("  (Tidak ada gejala abnormal yang dilaporkan)")
    print()
    
    kesimpulan, jejak_alasan, siklus_log = jalankan_forward_chaining(kb, fakta_awal)
    
    for log in siklus_log:
        print(log)
    print()
    
    print("=" * 70)
    print("HASIL DIAGNOSIS & REKOMENDASI TROUBLESHOOTING:")
    print("=" * 70)
    if kesimpulan:
        for i, k in enumerate(kesimpulan, 1):
            print(f"{i}. {k}")
    else:
        print("Tidak ada diagnosis kerusakan perangkat keras yang terkonfirmasi.")
        print("Gejala yang dimasukkan tidak memenuhi kriteria kerusakan komponen spesifik.")
        
    print("\n" + "-" * 70)
    print("ALASAN PENELUSURAN ATURAN (EXPLANATION TRACE):")
    print("-" * 70)
    if kesimpulan:
        for k in kesimpulan:
            cetak_alasan_rekursif(k, jejak_alasan)
    else:
        print("Tidak ada rantai aturan yang aktif menghasilkan kesimpulan.")
        
    print("\n" + "=" * 70)
    print("CATATAN BATAS KEBERLAKUAN (DISCLAIMER):")
    print("=" * 70)
    print(kb["batas"])
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()
