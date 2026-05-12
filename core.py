import json
import os
import platform
import copy
import csv
import threading
from datetime import date
from tkinter import filedialog
from config import gun_eki # config.py'den yardımcı fonksiyonu çekiyoruz

# ============================================================
# SES SİSTEMİ
# ============================================================
class SoundManager:
    @staticmethod
    def _play_win(freqs):
        try: import winsound; [winsound.Beep(f, d) for f, d in freqs]
        except Exception: pass

    @staticmethod
    def _play_mac(sound_file):
        try: os.system(f"afplay /System/Library/Sounds/{sound_file} &")
        except Exception: pass

    @classmethod
    def play_success(cls):
        if platform.system() == "Windows": threading.Thread(target=cls._play_win, args=([(1200, 100), (1600, 150)],), daemon=True).start()
        elif platform.system() == "Darwin": cls._play_mac("Glass.aiff")

    @classmethod
    def play_error(cls):
        if platform.system() == "Windows": threading.Thread(target=cls._play_win, args=([(200, 100), (150, 120)],), daemon=True).start()
        elif platform.system() == "Darwin": cls._play_mac("Basso.aiff")

    @classmethod
    def play_cash(cls):
        if platform.system() == "Windows": threading.Thread(target=cls._play_win, args=([(3000, 60), (4500, 250)],), daemon=True).start()
        elif platform.system() == "Darwin": cls._play_mac("Glass.aiff")

    @classmethod
    def play_delete(cls):
        if platform.system() == "Windows": threading.Thread(target=cls._play_win, args=([(300, 50), (200, 50)],), daemon=True).start()
        elif platform.system() == "Darwin": cls._play_mac("Pop.aiff")

    @classmethod
    def play_add(cls):
        if platform.system() == "Windows": threading.Thread(target=cls._play_win, args=([(800, 60), (1200, 90)],), daemon=True).start()
        elif platform.system() == "Darwin": cls._play_mac("Purr.aiff")

    @classmethod
    def play_save(cls):
        if platform.system() == "Windows": threading.Thread(target=cls._play_win, args=([(1000, 50)],), daemon=True).start()
        elif platform.system() == "Darwin": cls._play_mac("Tink.aiff")

# ============================================================
# VERİ YÖNETİMİ
# ============================================================
class DataManager:
    def __init__(self):
        self.app_name = "GelisimPlani"
        self.data_dir = self._get_data_dir()
        self.file_path = os.path.join(self.data_dir, "gelisim_plani.json")
        self.backup_path = os.path.join(self.data_dir, "gelisim_plani_backup.json")
        self.veriler = { 
            "temiz_tarihler": [], "borclar": [], "alinacaklar": [], 
            "gecmis_durumlar": {}, "gunluk_notlar": {}, "tema": "dark", 
            "odeme_gecmisi": [],
            "hizli_miktarlar": [1000, 5000, 10000, 20000, 50000],
            "gecmis_ai_tavsiye": ""
        }
        self.load()

    def _get_data_dir(self):
        if platform.system() == "Windows": data_dir = os.path.join(os.environ["LOCALAPPDATA"], self.app_name)
        elif platform.system() == "Darwin": data_dir = os.path.join(os.path.expanduser("~"), "Library", "Application Support", self.app_name)
        else: data_dir = os.path.join(os.path.expanduser("~"), f".{self.app_name}")
        if not os.path.exists(data_dir): os.makedirs(data_dir)
        return data_dir

    def load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    for k in saved: self.veriler[k] = saved[k]
            except Exception:
                if os.path.exists(self.backup_path):
                    try:
                        with open(self.backup_path, "r", encoding="utf-8") as f:
                            saved = json.load(f)
                            for k in saved: self.veriler[k] = saved[k]
                    except Exception: pass
        
        if "hizli_miktarlar" not in self.veriler or not self.veriler["hizli_miktarlar"]:
            self.veriler["hizli_miktarlar"] = [1000, 5000, 10000, 20000, 50000]

    def save(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f: data = f.read()
                with open(self.backup_path, "w", encoding="utf-8") as f: f.write(data)
            except Exception: pass
        with open(self.file_path, "w", encoding="utf-8") as f: json.dump(self.veriler, f, ensure_ascii=False, indent=2)

    def snapshot(self):
        bugun = str(date.today())
        self.veriler["gecmis_durumlar"][bugun] = { "borclar": copy.deepcopy(self.veriler["borclar"]), "alinacaklar": copy.deepcopy(self.veriler["alinacaklar"]) }
        self.save()

    def export_to_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Dosyası", "*.csv")], title="Verileri Dışa Aktar")
        if not path: return False
        try:
            with open(path, "w", newline='', encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["BÖLÜM", "VERİ", "DETAY", "MİKTAR", "EK DETAY"])
                for b in self.veriler["borclar"]:
                    tur = b.get("tur", "-")
                    sot = f"Ayın {gun_eki(b['son_odeme_gunu'])}" if b.get("son_odeme_gunu") else "-"
                    writer.writerow(["BORÇ", b["isim"], tur, b["kalan"], sot])
                for a in self.veriler["alinacaklar"]: 
                    writer.writerow(["HEDEF", a["isim"], a.get("kategori", "-"), "-", ""])
                for g in self.veriler["odeme_gecmisi"]: writer.writerow(["ÖDEME GEÇMİŞİ", g["isim"], g["tarih"], g["miktar"], ""])
                for d in self.veriler["temiz_tarihler"]: writer.writerow(["İŞARETLİ GÜN", d, "", "", ""])
            return True
        except Exception: return False

    def reset_all(self):
        self.veriler = {"temiz_tarihler": [], "borclar": [], "alinacaklar": [], "gecmis_durumlar": {}, "gunluk_notlar": {}, "tema": "dark", "odeme_gecmisi": [], "hizli_miktarlar": [1000, 5000, 10000, 20000, 50000], "gecmis_ai_tavsiye": ""}
        self.save()