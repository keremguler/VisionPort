import os
import platform
import tkinter as tk
from datetime import datetime

# ============================================================
# PILLOW ENTEGRASYONU (Anti-Aliasing için)
# ============================================================
try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# ============================================================
# TEMA VE RENK YÖNETİMİ
# ============================================================
class Theme:
    BG        = "#06060F"
    BG1       = "#0D0D1A"
    BG2       = "#131325"
    BG3       = "#1A1A30"
    LINE      = "#1E1E38"
    GLASS     = "#12122099"
    FW        = "#F0F0FF"
    FG        = "#6060A0"
    FL        = "#9090C0"
    GRN       = "#00E5A0"
    GRN2      = "#002E22"
    RED       = "#FF3060"
    RED2      = "#280010"
    BLU       = "#4D9FFF"
    BLU2      = "#00122E"
    ORN       = "#FFBB00"
    ORN2      = "#241A00"
    PRP       = "#B060FF"
    PRP2      = "#1A0035"
    GLD       = "#FFD700"
    GOLD_DIM  = "#806800"
    ACT       = "#1E1E38"
    SEL_BG    = "#1A1A38"
    SEL_BG_HL = "#004D40" 
    SEL_FG_HL = "#FFD700" 
    CYAN      = "#00D4FF"
    ROSE      = "#FF6090"
    CURSOR    = "" 

    @staticmethod
    def get_font():
        s = platform.system()
        if s == "Darwin": return "Helvetica"
        elif s == "Windows": return "Segoe UI"
        else: return "DejaVu Sans"

F = Theme.get_font()

BANKALAR = [
    {"isim": "Ziraat Bankası",  "kod": "ZRT", "renk": "#EF5350", "bg": "#B71C1C", "ikon": "🌾", "dosya": "ziraat.png"},
    {"isim": "İş Bankası",      "kod": "ISB", "renk": "#42A5F5", "bg": "#0D47A1", "ikon": "💼", "dosya": "isbankasi.png"},
    {"isim": "Garanti BBVA",    "kod": "GNT", "renk": "#26A69A", "bg": "#004D40", "ikon": "🍀", "dosya": "garanti.png"},
    {"isim": "Akbank",          "kod": "AKB", "renk": "#EF5350", "bg": "#B71C1C", "ikon": "❤️", "dosya": "akbank.png"},
    {"isim": "Yapı Kredi",      "kod": "YKB", "renk": "#5C6BC0", "bg": "#1A237E", "ikon": "🏛️", "dosya": "yapikredi.png"},
    {"isim": "QNB Finansbank",  "kod": "QNB", "renk": "#FFA726", "bg": "#BF360C", "ikon": "🌐", "dosya": "qnb.png"},
    {"isim": "Vakıfbank",       "kod": "VKF", "renk": "#FFCA28", "bg": "#F57F17", "ikon": "🛡️", "dosya": "vakifbank.png"},
    {"isim": "Halkbank",        "kod": "HLK", "renk": "#42A5F5", "bg": "#0D47A1", "ikon": "🤝", "dosya": "halkbank.png"},
    {"isim": "DenizBank",       "kod": "DNZ", "renk": "#26A69A", "bg": "#004D40", "ikon": "⚓", "dosya": "denizbank.png"},
    {"isim": "TEB",             "kod": "TEB", "renk": "#29B6F6", "bg": "#01579B", "ikon": "🌟", "dosya": "teb.png"},
    {"isim": "Tom Bank (Hadi)", "kod": "TOM", "renk": "#00D4FF", "bg": "#0077B6", "ikon": "📱", "dosya": "tombank.png"},
    {"isim": "Kişisel Borç",    "kod": "KSL", "renk": "#78909C", "bg": "#37474F", "ikon": "👤", "dosya": "kisisel.png"},
]

BANKA_LOGOLARI_CACHE = {}

def banka_bul(isim):
    for b in BANKALAR:
        if b["isim"] in isim or isim in b["isim"]: return b
    return {"isim": isim, "kod": "???", "renk": Theme.FG, "bg": Theme.BG2, "ikon": "💳", "dosya": ""}

import sys 

def get_cached_logo(bk, size=24):
    import sys # Fonksiyonun içinde çağırabilirsin, sorun olmaz
    dosya = bk.get("dosya", "")
    
    # --- YOL BULUCU GÜNCELLEMESİ ---
    if getattr(sys, 'frozen', False):
        # Eğer uygulama paketlenmişse (App olarak çalışıyorsa)
        ana_dizin = sys._MEIPASS
    else:
        # Eğer uygulama normal python dosyası olarak çalışıyorsa
        ana_dizin = os.path.dirname(os.path.abspath(__file__))
    
    logo_path = os.path.join(ana_dizin, "logos", dosya) if dosya else ""
    # ------------------------------
    
    cache_key = f"{logo_path}_{size}"
    
    if logo_path and os.path.exists(logo_path):
        if cache_key not in BANKA_LOGOLARI_CACHE:
            try:
                if HAS_PIL:
                    pil_img = Image.open(logo_path).convert("RGBA")
                    pil_img.thumbnail((size, size), Image.Resampling.LANCZOS)
                    img = ImageTk.PhotoImage(pil_img)
                else:
                    img = tk.PhotoImage(file=logo_path)
                    w, h = img.width(), img.height()
                    if w > size or h > size:
                        fact = int(max(w/size, h/size))
                        if fact > 1: img = img.subsample(fact, fact)
                BANKA_LOGOLARI_CACHE[cache_key] = img
            except Exception: pass
    return BANKA_LOGOLARI_CACHE.get(cache_key, None)

def para(x):
    try: return f"{x:,.0f} ₺".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError): return f"{x} ₺"

def sayi(t):
    if not t: return None
    t = str(t).lower().strip()
    c = 1
    if t.endswith('m'): c = 1_000_000; t = t[:-1]
    elif t.endswith('k'): c = 1000; t = t[:-1]
    t = t.replace('.', '').replace(',', '').replace(' ', '')
    try: return float(t) * c
    except ValueError: return None

def gun_eki(gun):
    ekler = { 1: "i", 2: "si", 3: "ü", 4: "ü", 5: "i", 6: "sı", 7: "si", 8: "i", 9: "u", 10: "u", 11: "i", 12: "si", 13: "ü", 14: "ü", 15: "i", 16: "sı", 17: "si", 18: "i", 19: "u", 20: "si", 21: "i", 22: "si", 23: "ü", 24: "ü", 25: "i", 26: "sı", 27: "si", 28: "i", 29: "u", 30: "u", 31: "i" }
    try: g = int(gun); return f"{g}'{ekler.get(g, 'i')}"
    except ValueError: return f"{gun}"

def tarih_formatla(tarih_str):
    try:
        d = datetime.strptime(tarih_str.split()[0], "%Y-%m-%d")
        return f"{d.day:02d}.{d.month:02d}.{d.year}"
    except: return tarih_str