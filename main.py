import tkinter as tk
from tkinter import messagebox
import random
import webbrowser
from datetime import date, datetime, timedelta
import calendar

# Kendi yazdığımız modülleri içeri aktarıyoruz
from config import Theme, F, para, sayi, gun_eki, tarih_formatla, BANKALAR, get_cached_logo
from core import DataManager, SoundManager
from components import ToolTip, ContextMenu, CustomDropdown, Components, CustomScrollableFrame, GridPatternCanvas

# ============================================================
# ANA UYGULAMA
# ============================================================
class DashboardApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.dm = DataManager()
        self.withdraw()
        self.title("Finans & Vizyon  ·  Kişisel Portföy")
        self.configure(bg=Theme.BG)
        self.attributes("-fullscreen", True)

        self.gosterilen_yil, self.gosterilen_ay, self.secili_tarih = date.today().year, date.today().month, str(date.today())
        self.takvim_gun_lbls = {}
        self.borc_toplu_mod, self.borc_secili, self.borc_selected_idx = False, set(), None
        self.hedef_toplu_mod, self.hedef_secili, self.hedef_selected_idx = False, set(), None

        self._build_ui()
        self._init_data()

        def toggle_fs(e=None):
            if self.attributes("-fullscreen"):
                self.attributes("-fullscreen", False)
                sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
                self.geometry(f"{sw//2}x{sh//2}+{sw//4}+{sh//4}")
            else: self.attributes("-fullscreen", True)

        def close_fs(e=None):
            self.attributes("-fullscreen", False)
            sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
            self.geometry(f"{sw//2}x{sh//2}+{sw//4}+{sh//4}")

        self.bind('<F11>', toggle_fs); self.bind('<Escape>', close_fs); self.toggle_fs_cmd = toggle_fs

        def clear_focus(event):
            try:
                if self.focus_get() == self.not_text and event.widget != self.not_text:
                    self.not_kaydet(auto=True); self.focus_set()
            except Exception: pass
                
        self.bind_all("<Button-1>", clear_focus, add="+")
        self.update_idletasks()
        self.deiconify()
        self.attributes("-alpha", 1.0)
        self.mainloop()

    def btn_hedef_update_colors(self):
        is_gelecek, is_temiz, is_bugun = self.secili_tarih > str(date.today()), self.secili_tarih in self.dm.veriler["temiz_tarihler"], self.secili_tarih == str(date.today())
        if is_gelecek: self.btn_hedef.config(bg="#0A1510", fg="#2A4A3A")
        elif is_temiz: self.btn_hedef.config(bg=Theme.GRN2, fg=Theme.GRN)
        elif is_bugun: self.btn_hedef.config(bg=Theme.GRN, fg="#000")
        else: self.btn_hedef.config(bg="#00402E", fg=Theme.GRN)

    def _build_ui(self):
        topbar = tk.Frame(self, bg=Theme.BG1, height=58); topbar.pack(fill=tk.X)
        tk.Frame(self, bg=Theme.GLD, height=1).pack(fill=tk.X); tk.Frame(self, bg=Theme.LINE, height=1).pack(fill=tk.X)

        logo_c = tk.Frame(topbar, bg=Theme.BG1); logo_c.pack(side=tk.LEFT, padx=20, pady=12)
        tk.Label(logo_c, text="◈", font=(F,18), bg=Theme.BG1, fg=Theme.GLD).pack(side=tk.LEFT, padx=(0,10))
        self.lbl_selam = tk.Label(logo_c, text="", font=(F,20,"bold"), bg=Theme.BG1, fg=Theme.FW); self.lbl_selam.pack(side=tk.LEFT)

        saat_c = tk.Frame(topbar, bg=Theme.BG1); saat_c.pack(side=tk.RIGHT, padx=20, pady=16)
        
        fs_btn = tk.Label(saat_c, text="⛶", font=(F,16), bg=Theme.BG1, fg=Theme.FG, cursor=Theme.CURSOR, padx=8)
        fs_btn.bind("<Button-1>", lambda e: self.toggle_fs_cmd()); fs_btn.bind("<Enter>", lambda e: fs_btn.config(fg=Theme.GLD), add="+"); fs_btn.bind("<Leave>", lambda e: fs_btn.config(fg=Theme.FG), add="+")
        fs_btn.pack(side=tk.RIGHT, padx=(8,0))
        fs_tt = ToolTip(fs_btn, "Tam Ekran / Pencere (F11)")
        fs_btn.bind("<Enter>", lambda e: fs_tt.show(e), add="+"); fs_btn.bind("<Leave>", lambda e: fs_tt.hide(e), add="+")
        
        self.lbl_saat = tk.Label(saat_c, text="", font=(F,11,"bold"), bg=Theme.BG1, fg=Theme.FL); self.lbl_saat.pack(side=tk.RIGHT)
        self.lbl_tarih = tk.Label(saat_c, text="", font=(F,10), bg=Theme.BG1, fg=Theme.FG); self.lbl_tarih.pack(side=tk.RIGHT, padx=(0,12))

        stat_band = tk.Frame(self, bg=Theme.BG2); stat_band.pack(fill=tk.X)
        tk.Frame(self, bg=Theme.LINE, height=1).pack(fill=tk.X)

        def _stat(p, title, col):
            f = tk.Frame(p, bg=Theme.BG2); f.pack(side=tk.LEFT, padx=20, pady=8)
            tk.Label(f, text=title, font=(F,7,"bold"), bg=Theme.BG2, fg=Theme.FG).pack(anchor="w")
            v = tk.Label(f, text="—", font=(F,11,"bold"), bg=Theme.BG2, fg=col); v.pack(anchor="w"); return v

        self.lbl_stat1 = _stat(stat_band, "TOPLAM BORÇ", Theme.RED)
        tk.Frame(stat_band, bg=Theme.LINE, width=1).pack(side=tk.LEFT, fill=tk.Y, pady=8)
        self.lbl_stat2 = _stat(stat_band, "AKTİF HEDEF", Theme.BLU)
        tk.Frame(stat_band, bg=Theme.LINE, width=1).pack(side=tk.LEFT, fill=tk.Y, pady=8)
        self.lbl_stat3 = _stat(stat_band, "TOPLAM İŞARETLİ GÜN", Theme.GRN)
        tk.Frame(stat_band, bg=Theme.LINE, width=1).pack(side=tk.LEFT, fill=tk.Y, pady=8)
        self.lbl_stat4 = _stat(stat_band, "MEVCUT SERİ", Theme.ORN)
        tk.Label(stat_band, text="F11 Tam Ekran  ·  Esc Çıkış", font=(F,9), bg=Theme.BG2, fg=Theme.GOLD_DIM).pack(side=tk.RIGHT, padx=16, pady=12)

        body = tk.Frame(self, bg=Theme.BG); body.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)
        self.dot_bg = GridPatternCanvas(body); self.dot_bg.place(relx=0, rely=0, relwidth=1, relheight=1)

        sol = tk.Frame(body, bg=Theme.BG, width=400); sol.pack(side=tk.LEFT, fill=tk.BOTH, expand=False); sol.pack_propagate(False)
        self._build_left_panel(sol)
        tk.Frame(body, bg=Theme.LINE, width=1).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        sag = tk.Frame(body, bg=Theme.BG); sag.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self._build_right_panel(sag)

        self.bind('<Control-s>', lambda e: self.not_kaydet())
        self.bind('<Command-s>', lambda e: self.not_kaydet())
        self.saat_guncelle()

    def _build_left_panel(self, parent):
        sk = Components.create_card(parent, accent=Theme.ORN); sk.pack(side=tk.TOP, fill=tk.X, pady=(0,8))
        sk_ic = tk.Frame(sk, bg=Theme.BG1, padx=18, pady=14); sk_ic.pack(fill=tk.X)
        tk.Label(sk_ic, text="BAŞARI SERİSİ", font=(F,8,"bold"), bg=Theme.BG1, fg=Theme.GOLD_DIM).pack(anchor="w")

        sk_orta = tk.Frame(sk_ic, bg=Theme.BG1); sk_orta.pack(fill=tk.X, pady=(8,2))
        self.lbl_streak_e = tk.Label(sk_orta, text="💤", font=(F,28), bg=Theme.BG1, fg=Theme.FW); self.lbl_streak_e.pack(side=tk.LEFT)
        self.lbl_streak_n = tk.Label(sk_orta, text="0", font=(F,42,"bold"), bg=Theme.BG1, fg=Theme.ORN); self.lbl_streak_n.pack(side=tk.LEFT, padx=8)
        sk_r = tk.Frame(sk_orta, bg=Theme.BG1); sk_r.pack(side=tk.LEFT, padx=4)
        tk.Label(sk_r, text="TOPLAM İŞARETLİ GÜN", font=(F,12,"bold"), bg=Theme.BG1, fg=Theme.FW).pack(anchor="sw")
        self.lbl_streak_maks = tk.Label(sk_r, text="", font=(F,12,"bold"), bg=Theme.BG1, fg="#D0D0E0", justify=tk.LEFT); self.lbl_streak_maks.pack(anchor="nw", pady=(4,0))

        self.btn_hedef_frame = tk.Frame(sk, bg=Theme.BG1); self.btn_hedef_frame.pack(fill=tk.X)
        self.btn_hedef = tk.Label(self.btn_hedef_frame, text="", font=(F,10,"bold"), cursor=Theme.CURSOR, padx=16, pady=13); self.btn_hedef.pack(fill=tk.X)
        self.hedef_btn_tt = ToolTip(self.btn_hedef, "")

        def btn_hedef_enter(e):
            bg = self.btn_hedef.cget('bg')
            if bg == Theme.GRN: Components.animate_bg_color(self.btn_hedef, '#00B870', 150)
            elif bg == Theme.GRN2: Components.animate_bg_color(self.btn_hedef, '#00503a', 150)
            elif bg == '#00402E': Components.animate_bg_color(self.btn_hedef, '#005A42', 150)
            if self.secili_tarih > str(date.today()): self.hedef_btn_tt.show(e)

        def btn_hedef_leave(e): self.btn_hedef_update_colors(); self.hedef_btn_tt.hide(e)
        def on_hedef_btn_click(e): SoundManager.play_error() if self.secili_tarih > str(date.today()) else self.hedef_toggle()

        self.btn_hedef.bind("<Button-1>", on_hedef_btn_click); self.btn_hedef.bind("<Enter>", btn_hedef_enter, add="+"); self.btn_hedef.bind("<Leave>", btn_hedef_leave, add="+")

        tk_c = Components.create_card(parent); tk_c.pack(side=tk.TOP, fill=tk.X, pady=(0,8))
        self.takvim_ic = tk.Frame(tk_c, bg=Theme.BG1, padx=10, pady=12, width=380, height=370); self.takvim_ic.pack_propagate(False); self.takvim_ic.grid_propagate(False); self.takvim_ic.pack(fill=tk.BOTH, expand=True)
        for r in range(8): self.takvim_ic.grid_rowconfigure(r, minsize=30)
        for c in range(7): self.takvim_ic.grid_columnconfigure(c, minsize=46)

        not_c = Components.create_card(parent, accent=Theme.PRP); not_c.pack(side=tk.TOP, fill=tk.BOTH, expand=False, pady=(0,8))
        not_ust = tk.Frame(not_c, bg=Theme.BG1, padx=14, pady=10); not_ust.pack(fill=tk.X)
        tk.Label(not_ust, text="📝  GÜNLÜK NOT", font=(F,11,"bold"), bg=Theme.BG1, fg=Theme.PRP).pack(side=tk.LEFT)
        self.btn_n_kaydet = tk.Label(not_ust, text="💾 Kaydet", font=(F,9,"bold"), bg=Theme.BG2, fg=Theme.PRP, cursor=Theme.CURSOR, padx=10, pady=4); self.btn_n_kaydet.pack(side=tk.RIGHT)
        self.btn_n_kaydet.bind("<Button-1>", lambda e: self.not_kaydet()); 
        self.btn_n_kaydet.bind("<Enter>", lambda e: (Components.animate_bg_color(self.btn_n_kaydet, Theme.BG3, 150), self.btn_n_kaydet.config(fg=Theme.FW))); 
        self.btn_n_kaydet.bind("<Leave>", lambda e: (Components.animate_bg_color(self.btn_n_kaydet, Theme.BG2, 150), self.btn_n_kaydet.config(fg=Theme.PRP)))
        ToolTip(self.btn_n_kaydet, "Yazdığınız notu kaydeder, uygulama içerisinde farklı bir yere tıklarsanız otomatik kaydedilir.")
        tk.Frame(not_c, bg=Theme.LINE, height=1).pack(fill=tk.X, padx=10)

        not_ic = tk.Frame(not_c, bg=Theme.BG1); not_ic.pack(fill=tk.BOTH, expand=True, padx=14, pady=(8,12))
        
        n_bg = tk.Frame(not_ic, bg=Theme.LINE, highlightthickness=0, bd=0); n_bg.pack(fill=tk.BOTH, expand=True)
        n_in = tk.Frame(n_bg, bg=Theme.BG1, highlightthickness=0, bd=0); n_in.pack(padx=1, pady=1, fill=tk.BOTH, expand=True)
        self.not_text = tk.Text(n_in, bg=Theme.BG1, fg=Theme.FW, font=(F,11), relief="flat", insertbackground=Theme.FW, bd=0, highlightthickness=0, highlightcolor=Theme.BG1, highlightbackground=Theme.BG1, height=2, wrap=tk.WORD, padx=8, pady=8, selectbackground=Theme.SEL_BG)
        self.not_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=0); self.not_text.bind("<FocusOut>", lambda e: self.not_kaydet(auto=True))

        alt = tk.Frame(parent, bg=Theme.BG); alt.pack(side=tk.BOTTOM, fill=tk.X, pady=(8,0))
        sl = tk.Label(alt, text="⟳ Sıfırla", bg=Theme.BG, fg=Theme.FG, font=(F,10,"bold"), cursor=Theme.CURSOR, padx=10, pady=8)
        sl.bind("<Button-1>", lambda *args: self.sifirla()); sl.bind("<Enter>", lambda e: (Components.animate_bg_color(sl, Theme.BG1, 150), sl.config(fg=Theme.RED))); sl.bind("<Leave>", lambda e: (Components.animate_bg_color(sl, Theme.BG, 150), sl.config(fg=Theme.FG))); sl.pack(side=tk.LEFT)
        ex = tk.Label(alt, text="📥 Dışa Aktar", bg=Theme.BG, fg=Theme.FG, font=(F,10,"bold"), cursor=Theme.CURSOR, padx=10, pady=8)
        ex.bind("<Button-1>", lambda *args: self.dm.export_to_csv()); ex.bind("<Enter>", lambda e: (Components.animate_bg_color(ex, Theme.BG1, 150), ex.config(fg=Theme.BLU))); ex.bind("<Leave>", lambda e: (Components.animate_bg_color(ex, Theme.BG, 150), ex.config(fg=Theme.FG))); ex.pack(side=tk.RIGHT)
        
        self.ozet_c = Components.create_card(parent, accent=Theme.CYAN)
        self.ozet_c.pack(side=tk.BOTTOM, fill=tk.X, pady=(8,0))
        
        self.alt_ozet_f = tk.Frame(self.ozet_c, bg=Theme.BG1, padx=14, pady=12)
        self.alt_ozet_f.pack(fill=tk.BOTH, expand=True)

        tk.Label(self.alt_ozet_f, text="Toplam Borç:", font=(F,9), bg=Theme.BG1, fg=Theme.FL).pack(side=tk.LEFT)
        self.lbl_alt_borc = tk.Label(self.alt_ozet_f, text="0 ₺", font=(F,11,"bold"), bg=Theme.BG1, fg=Theme.RED)
        self.lbl_alt_borc.pack(side=tk.LEFT, padx=(4,15))
        
        tk.Label(self.alt_ozet_f, text="Son 7 Günde Ödenen:", font=(F,9), bg=Theme.BG1, fg=Theme.FL).pack(side=tk.LEFT)
        self.lbl_alt_odenen = tk.Label(self.alt_ozet_f, text="0 ₺", font=(F,11,"bold"), bg=Theme.BG1, fg=Theme.GRN)
        self.lbl_alt_odenen.pack(side=tk.LEFT, padx=(4,0))

        ai_c = Components.create_card(parent, accent="#FF007F"); ai_c.pack(side=tk.BOTTOM, fill=tk.X, expand=False, pady=(0,0))
        ai_btn = tk.Frame(ai_c, bg=Theme.BG1, cursor=Theme.CURSOR, padx=14, pady=12); ai_btn.pack(fill=tk.BOTH, expand=True)
        tk.Label(ai_btn, text="🤖 YAPAY ZEKA DANIŞMANIM", font=(F,10,"bold"), bg=Theme.BG1, fg="#FF007F", cursor=Theme.CURSOR).pack(side=tk.LEFT)
        tk.Label(ai_btn, text="Analiz Et →", font=(F,9,"bold"), bg=Theme.BG1, fg=Theme.FL, cursor=Theme.CURSOR).pack(side=tk.RIGHT)
        
        def ai_hover_in(*args): Components.animate_bg_color(ai_btn, Theme.BG2, 150)
        def ai_hover_out(*args): Components.animate_bg_color(ai_btn, Theme.BG1, 150)
        
        ai_btn.bind("<Button-1>", lambda *args: self.yapay_zeka_analizi())
        ai_btn.bind("<Enter>", ai_hover_in); ai_btn.bind("<Leave>", ai_hover_out)
        for child in ai_btn.winfo_children():
            child.bind("<Button-1>", lambda *args: self.yapay_zeka_analizi())
            child.bind("<Enter>", ai_hover_in); child.bind("<Leave>", ai_hover_out)

    def tarihe_git_dialog(self):
        d = tk.Toplevel(self); d.title("Tarihe Git"); d.attributes("-alpha", 0.0); Components.fade_in(d); Components.center_window(d, 320, 260); d.configure(bg=Theme.BG1); d.transient(self); d.grab_set()
        tk.Frame(d, bg=Theme.BLU, height=3).pack(fill=tk.X)
        tk.Label(d, text="📅 Tarih Seçimi", font=(F, 14, "bold"), bg=Theme.BG1, fg=Theme.BLU).pack(pady=(15, 5))
        
        self.temp_yil, self.temp_ay = self.gosterilen_yil, self.gosterilen_ay
        aylar = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
        
        ctrl_frame = tk.Frame(d, bg=Theme.BG1); ctrl_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        yil_f = tk.Frame(ctrl_frame, bg=Theme.BG1); yil_f.pack(pady=5); tk.Label(yil_f, text="YIL:", font=(F,9,"bold"), bg=Theme.BG1, fg=Theme.FL, width=4, anchor="e").pack(side=tk.LEFT, padx=(0,10))
        
        def ay_degis(delta):
            self.temp_ay += delta
            if self.temp_ay > 12: self.temp_ay = 1; self.temp_yil += 1
            elif self.temp_ay < 1: self.temp_ay = 12; self.temp_yil -= 1
            lbl_yil_val.config(text=str(self.temp_yil)); lbl_ay_val.config(text=aylar[self.temp_ay])

        def yil_degis(delta): self.temp_yil += delta; lbl_yil_val.config(text=str(self.temp_yil))

        y_btn_geri = tk.Label(yil_f, text="◄", bg=Theme.BG2, fg=Theme.FW, font=(F,12,"bold"), cursor=Theme.CURSOR, padx=10, pady=4); y_btn_geri.pack(side=tk.LEFT); y_btn_geri.bind("<Button-1>", lambda *args: yil_degis(-1))
        lbl_yil_val = tk.Label(yil_f, text=str(self.temp_yil), font=(F,14,"bold"), bg=Theme.BG1, fg=Theme.FW, width=6); lbl_yil_val.pack(side=tk.LEFT, padx=5)
        y_btn_ileri = tk.Label(yil_f, text="►", bg=Theme.BG2, fg=Theme.FW, font=(F,12,"bold"), cursor=Theme.CURSOR, padx=10, pady=4); y_btn_ileri.pack(side=tk.LEFT); y_btn_ileri.bind("<Button-1>", lambda *args: yil_degis(1))
        
        ay_f = tk.Frame(ctrl_frame, bg=Theme.BG1); ay_f.pack(pady=10); tk.Label(ay_f, text="AY:", font=(F,9,"bold"), bg=Theme.BG1, fg=Theme.FL, width=4, anchor="e").pack(side=tk.LEFT, padx=(0,10))
        a_btn_geri = tk.Label(ay_f, text="◄", bg=Theme.BG2, fg=Theme.FW, font=(F,12,"bold"), cursor=Theme.CURSOR, padx=10, pady=4); a_btn_geri.pack(side=tk.LEFT); a_btn_geri.bind("<Button-1>", lambda *args: ay_degis(-1))
        lbl_ay_val = tk.Label(ay_f, text=aylar[self.temp_ay], font=(F,14,"bold"), bg=Theme.BG1, fg=Theme.FW, width=6); lbl_ay_val.pack(side=tk.LEFT, padx=5)
        a_btn_ileri = tk.Label(ay_f, text="►", bg=Theme.BG2, fg=Theme.FW, font=(F,12,"bold"), cursor=Theme.CURSOR, padx=10, pady=4); a_btn_ileri.pack(side=tk.LEFT); a_btn_ileri.bind("<Button-1>", lambda *args: ay_degis(1))

        def git():
            self.gosterilen_yil, self.gosterilen_ay = self.temp_yil, self.temp_ay
            if self.temp_yil == date.today().year and self.temp_ay == date.today().month: self.tarih_sec(str(date.today()))
            else: self.tarih_sec(f"{self.temp_yil}-{self.temp_ay:02d}-01")
            Components.fade_out(d)
        
        btn_frame = tk.Frame(d, bg=Theme.BG1, padx=30, pady=15); btn_frame.pack(fill=tk.X, side=tk.BOTTOM)
        Components.create_btn(btn_frame, "🔄 SEÇİLİ TARİHE GİT", Theme.BLU, "#000", git, py=10, hbg="#2277CC", hfg="#FFF").pack(fill=tk.X)

    def _build_right_panel(self, parent):
        footer = tk.Frame(parent, bg=Theme.BG); footer.pack(side=tk.BOTTOM, fill=tk.X, pady=(4, 0))
        tk.Label(footer, text="© 2026 KEREM GÜLER   —   TÜM HAKLARI SAKLIDIR", font=(F, 8, "bold"), bg=Theme.BG, fg=Theme.FG).pack(side=tk.LEFT, padx=4)

        li = tk.Label(footer, text="LinkedIn", font=(F, 10, "bold"), bg=Theme.BG, fg=Theme.FW, cursor=Theme.CURSOR); li.pack(side=tk.RIGHT, padx=4)
        li.bind("<Button-1>", lambda *args: webbrowser.open("https://linkedin.com/in/keremguler")); li.bind("<Enter>", lambda e: li.config(fg=Theme.BLU)); li.bind("<Leave>", lambda e: li.config(fg=Theme.FW))
        gh = tk.Label(footer, text="GitHub", font=(F, 10, "bold"), bg=Theme.BG, fg=Theme.FW, cursor=Theme.CURSOR); gh.pack(side=tk.RIGHT, padx=14)
        gh.bind("<Button-1>", lambda *args: webbrowser.open("https://github.com/keremguler")); gh.bind("<Enter>", lambda e: gh.config(fg=Theme.BLU)); gh.bind("<Leave>", lambda e: gh.config(fg=Theme.FW))

        self.banner_c = tk.Frame(parent, bg=Theme.BG); self.banner_c.pack(side=tk.TOP, fill=tk.X, pady=(0,8))

        self.bk_c = Components.create_card(parent, accent=Theme.RED); self.bk_c.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(0,8))
        bk_ust = tk.Frame(self.bk_c, bg=Theme.BG1, padx=14, pady=11); bk_ust.pack(fill=tk.X)
        self.lbl_borc_baslik = tk.Label(bk_ust, text="💳  BORÇ DURUMUNUZ", font=(F,11,"bold"), bg=Theme.BG1, fg=Theme.RED); self.lbl_borc_baslik.pack(side=tk.LEFT)
        info_b_lbl = tk.Label(bk_ust, text="ⓘ", bg=Theme.BG1, fg=Theme.FG, font=(F,10,"bold"), cursor=Theme.CURSOR); info_b_lbl.pack(side=tk.LEFT, padx=8)
        ToolTip(info_b_lbl, "Mevcut tüm borçlarınızı buradan görüntüleyebilir ve yönetebilirsiniz.") 

        g_lbl = tk.Label(bk_ust, text="📊 GRAFİK", bg=Theme.BLU2, fg=Theme.BLU, font=(F,9,"bold"), cursor=Theme.CURSOR, padx=14, pady=6)
        g_lbl.bind("<Button-1>", lambda *args: self.show_chart()); g_lbl.bind("<Enter>", lambda e: (Components.animate_bg_color(g_lbl, Theme.BLU, 150), g_lbl.config(fg=Theme.FW))); g_lbl.bind("<Leave>", lambda e: (Components.animate_bg_color(g_lbl, Theme.BLU2, 150), g_lbl.config(fg=Theme.BLU))); g_lbl.pack(side=tk.RIGHT)

        self.borc_progress_frame = tk.Frame(self.bk_c, bg=Theme.BG2, height=4); self.borc_progress_frame.pack(fill=tk.X, padx=14, pady=(0,2)); self.borc_progress_frame.pack_propagate(False)

        borc_frame = tk.Frame(self.bk_c, bg=Theme.BG1); borc_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 5))
        self.borc_list_frame = CustomScrollableFrame(borc_frame, bg_color=Theme.BG1); self.borc_list_frame.pack(fill=tk.BOTH, expand=True)

        self.borc_butonlar = tk.Frame(self.bk_c, bg=Theme.BG1); self.borc_butonlar.pack(fill=tk.X, padx=14, pady=8)
        self.btn_b_ekle = Components.create_btn(self.borc_butonlar, " + Ekle ", "#142B28", "#FFFFFF", self.borc_islem_modal, py=7, hbg="#1C453C", hfg="#FFFFFF")
        self.btn_b_ekle.pack(side=tk.LEFT, padx=(0,5))
        
        self.btn_b_duzenle = Components.create_btn(self.borc_butonlar, " 📝 Düzenle ", "#1E1E38", "#A0A0C0", lambda: self.borc_islem_modal(self.borc_selected_idx), py=7, hbg="#2A2A4A", hfg="#FFFFFF")
        self.btn_b_duzenle.pack(side=tk.LEFT, padx=(0,5))
        self.btn_b_duzenle.set_state("disabled")
        
        self.btn_b_ode = Components.create_btn(self.borc_butonlar, "💳 Ödeme Yap", "#3B1822", "#FF6090", self.borc_ode, py=7, hbg="#5A2030", hfg="#FFFFFF"); self.btn_b_ode.pack(side=tk.LEFT, padx=(0,5))
        self.btn_b_sil = Components.create_btn(self.borc_butonlar, "🗑 Sil", "#20202A", "#A0A0C0", self.borc_sil, py=7, hbg="#303045", hfg="#FFFFFF"); self.btn_b_sil.pack(side=tk.LEFT, padx=(0,5))
        self.btn_b_gecmis = Components.create_btn(self.borc_butonlar, "💸 Geçmiş", "#182A40", "#4D9FFF", self.odenenler_goster, py=7, hbg="#203D60", hfg="#FFFFFF"); self.btn_b_gecmis.pack(side=tk.LEFT)
        self.btn_b_toplu = Components.create_btn(self.borc_butonlar, "✅  Toplu İşlem", "#281A3A", "#B060FF", self.toggle_borc_toplu, py=7, hbg="#402060", hfg="#FFFFFF"); self.btn_b_toplu.pack(side=tk.RIGHT, padx=(5,0))

        hk_c = Components.create_card(parent, accent=Theme.BLU); hk_c.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(0,8))
        hk_ust = tk.Frame(hk_c, bg=Theme.BG1, padx=14, pady=11); hk_ust.pack(fill=tk.X)
        self.lbl_hedef_baslik = tk.Label(hk_ust, text="🎯  ALINACAK VE YAPILACAK HEDEFLERİNİZ", font=(F,11,"bold"), bg=Theme.BG1, fg=Theme.BLU); self.lbl_hedef_baslik.pack(side=tk.LEFT)
        info_h_lbl = tk.Label(hk_ust, text="ⓘ", bg=Theme.BG1, fg=Theme.FG, font=(F,10,"bold"), cursor=Theme.CURSOR); info_h_lbl.pack(side=tk.LEFT, padx=8)
        ToolTip(info_h_lbl, "Alınacak ve yapılacak hedeflerinizi ekleyin, tamamlandıkça işaretleyin.") 

        hedef_frame = tk.Frame(hk_c, bg=Theme.BG1); hedef_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 5))
        self.hedef_list_frame = CustomScrollableFrame(hedef_frame, bg_color=Theme.BG1); self.hedef_list_frame.pack(fill=tk.BOTH, expand=True)

        self.hedef_butonlar = tk.Frame(hk_c, bg=Theme.BG1); self.hedef_butonlar.pack(fill=tk.X, padx=14, pady=8)
        self.btn_h_ekle = Components.create_btn(self.hedef_butonlar," + Ekle ", "#142B28", "#FFFFFF", self.hedef_islem_modal, py=7, hbg="#1C453C", hfg="#FFFFFF"); self.btn_h_ekle.pack(side=tk.LEFT, padx=(0,5))
        
        self.btn_h_duzenle = Components.create_btn(self.hedef_butonlar, " 📝 Düzenle ", "#1E1E38", "#A0A0C0", lambda: self.hedef_islem_modal(self.hedef_selected_idx), py=7, hbg="#2A2A4A", hfg="#FFFFFF")
        self.btn_h_duzenle.pack(side=tk.LEFT, padx=(0,5))
        self.btn_h_duzenle.set_state("disabled")
        
        self.btn_h_tamam = Components.create_btn(self.hedef_butonlar,"✅ Tamamlandı", "#182A40", "#4D9FFF", self.hedef_tamamla, py=7, hbg="#203D60", hfg="#FFFFFF"); self.btn_h_tamam.pack(side=tk.LEFT, padx=(0,5))
        self.btn_h_sil = Components.create_btn(self.hedef_butonlar,"🗑 Sil", "#20202A", "#A0A0C0", self.hedef_sil, py=7, hbg="#303045", hfg="#FFFFFF"); self.btn_h_sil.pack(side=tk.LEFT)
        self.btn_h_toplu = Components.create_btn(self.hedef_butonlar, "✅  Toplu İşlem", "#281A3A", "#B060FF", self.toggle_hedef_toplu, py=7, hbg="#402060", hfg="#FFFFFF"); self.btn_h_toplu.pack(side=tk.RIGHT, padx=(5,0))

    def yapay_zeka_analizi(self):
        if self.secili_tarih != str(date.today()): SoundManager.play_error(); return
        d = tk.Toplevel(self); d.title("Yapay Zeka Danışman"); Components.center_window(d, 800, 460); d.configure(bg=Theme.BG1); d.transient(self); d.grab_set()
        d.attributes("-alpha", 0.0); Components.fade_in(d)
        
        tk.Frame(d, bg="#FF007F", height=3).pack(fill=tk.X)
        hdr = tk.Frame(d, bg=Theme.BG1, padx=22, pady=16); hdr.pack(fill=tk.X)
        tk.Label(hdr, text="🤖 Yapay Zeka Finansal Danışmanım", font=(F,16,"bold"), bg=Theme.BG1, fg="#FF007F").pack(anchor="w")
        Components.create_sep(d, c=Theme.LINE, py=0)

        content = tk.Frame(d, bg=Theme.BG1, padx=24, pady=10); content.pack(fill=tk.BOTH, expand=True)
        lbl_status = tk.Label(content, text="Verileriniz taranıyor ve analiz ediliyor...", font=(F,12,"italic"), bg=Theme.BG1, fg=Theme.FL)
        lbl_status.pack(pady=40)
        
        def goster():
            lbl_status.destroy()
            toplam_borc = sum(b["kalan"] for b in self.dm.veriler["borclar"])
            m, _ = self.streak_hesapla()
            son_7_gun = [str(date.today() - timedelta(days=i)) for i in range(7)]
            odenenler_7_gun = sum(g["miktar"] for g in self.dm.veriler.get("odeme_gecmisi", []) if g["tarih"] in son_7_gun)
            
            if toplam_borc == 0: tahmini_bitis = "Borcunuz bulunmuyor 🎉"
            elif odenenler_7_gun > 0:
                gunluk_hiz = odenenler_7_gun / 7.0
                kalan_gun = int(toplam_borc / gunluk_hiz)
                if kalan_gun < 3650: tahmini_bitis = (date.today() + timedelta(days=kalan_gun)).strftime("%d.%m.%Y")
                else: tahmini_bitis = "10+ Yıl (Ödemelerinizi artırmalısınız)"
            else: tahmini_bitis = "Hesaplanamıyor (Geçen hafta hiç ödeme yapmadınız.)"

            col_left = tk.Frame(content, bg=Theme.BG1); col_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0,10))
            col_right = tk.Frame(content, bg=Theme.BG1); col_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10,0))

            tk.Label(col_left, text="📊 Finansal Özetiniz", font=(F,12,"bold"), bg=Theme.BG1, fg=Theme.CYAN).pack(anchor="w", pady=(0,10))
            
            def st_c(parent, lbl, val):
                f = tk.Frame(parent, bg=Theme.BG2, padx=15, pady=12, highlightthickness=1, highlightbackground=Theme.LINE); f.pack(fill=tk.X, pady=4)
                tk.Label(f, text=lbl, bg=Theme.BG2, fg=Theme.FL, font=(F,10,"bold")).pack(side=tk.LEFT)
                tk.Label(f, text=val, bg=Theme.BG2, fg=Theme.FW, font=(F,11,"bold")).pack(side=tk.RIGHT)

            st_c(col_left, "Son 7 Günde Ödenen", para(odenenler_7_gun))
            st_c(col_left, "Güncel Toplam Borç", para(toplam_borc))
            st_c(col_left, "Başarı Serisi", f"{m} gün")
            st_c(col_left, "Tahmini Borç Bitiş", tahmini_bitis)
            
            tk.Label(col_right, text="💡 AI Strateji & Tavsiye", font=(F,12,"bold"), bg=Theme.BG1, fg="#FF007F").pack(anchor="w", pady=(0,10))
            
            tavsiyeler_borcsuz = [
                "Artık geçmişi değil geleceği finanse ediyorsunuz. Düzenli yatırımlarla portföyünüzü büyütmeye başlamanın tam vakti.",
                "Borçsuz uyanmak en büyük zenginliktir! Bu huzuru koruyun ve yeni hedefleriniz için birikim yapmaya devam edin.",
                "Eksi bakiyeler geride kaldı! Eğer henüz yapmadıysanız, 3-6 aylık masraflarınızı kapsayacak bir acil durum fonu oluşturmayı hedefleyin."
            ]
            tavsiyeler_odeme_yok = [
                "Ödemeleri ertelemek, faiz yükünü artırmaktan başka işe yaramaz. Hemen bugün bütçenizi gözden geçirip ufak bir adım atın.",
                "Finansal yolculuğunuzda duraklamak yok! En azından asgari tutarı ödeyerek borçlarınızın kontrolden çıkmasını engelleyin."
            ]
            tavsiyeler_iyi_seri = [
                "Harika gidiyorsunuz! Disiplinli ödemeleriniz ve hedeflerinize bağlılığınız finansal stresinizi büyük ölçüde azaltacak. Serinizi bozmayın!",
                "Müthiş bir istikrar yakaladınız! Bu alışkanlık kalıcı hale geldiğinde sizi kimse tutamaz. Aynen devam!"
            ]
            tavsiyeler_genel = [
                "Ödemelerinizi düzene sokmaya başlamışsınız. Kalan borçlarınızı en yüksek faizliden başlayarak sırayla kapatmayı ('Çığ Yöntemi') hedefleyin.",
                "Eğer çok fazla borç kaleminiz varsa, önce en küçük borcu bitirip motivasyon kazanmayı ('Kar Topu Yöntemi') deneyebilirsiniz."
            ]
            
            tavsiye = ""
            if toplam_borc == 0: tavsiye = random.choice(tavsiyeler_borcsuz)
            elif odenenler_7_gun == 0: tavsiye = random.choice(tavsiyeler_odeme_yok)
            elif m >= 7: tavsiye = random.choice(tavsiyeler_iyi_seri)
            else: tavsiye = random.choice(tavsiyeler_genel)
            
            gecmis_tavsiye = self.dm.veriler.get("gecmis_ai_tavsiye", "")
            if gecmis_tavsiye:
                gf = tk.Frame(col_right, bg=Theme.BG2, padx=15, pady=10, highlightthickness=1, highlightbackground=Theme.LINE); gf.pack(fill=tk.X, pady=(0,8))
                tk.Label(gf, text="Geçen Haftanın Analizi", font=(F,9,"bold"), bg=Theme.BG2, fg=Theme.FG).pack(anchor="w")
                tk.Label(gf, text=f"\"{gecmis_tavsiye}\"", font=(F,9,"italic"), bg=Theme.BG2, fg=Theme.FL, wraplength=320, justify=tk.LEFT).pack(anchor="w", pady=(4,0))

            nf = tk.Frame(col_right, bg=Theme.PRP2, padx=15, pady=15, highlightthickness=1, highlightbackground=Theme.PRP); nf.pack(fill=tk.X, pady=(0,8))
            tk.Label(nf, text="Haftanın Stratejisi", font=(F,10,"bold"), bg=Theme.PRP2, fg=Theme.PRP).pack(anchor="w")
            tk.Label(nf, text=tavsiye, font=(F,11,"italic"), bg=Theme.PRP2, fg=Theme.FW, wraplength=320, justify=tk.LEFT).pack(anchor="w", pady=(6,0))

            self.dm.veriler["gecmis_ai_tavsiye"] = tavsiye
            self.dm.save()

        d.after(1000, goster)
        
        btn_f = tk.Frame(d, bg=Theme.BG1, padx=24, pady=20); btn_f.pack(fill=tk.X, side=tk.BOTTOM)
        Components.create_btn(btn_f, "ANLADIM", Theme.BG2, Theme.FW, lambda: Components.fade_out(d), py=10, hbg=Theme.BG3).pack(fill=tk.X)

    def _reset_toplu_mod(self, is_borc):
        if is_borc:
            self.borc_toplu_mod, self.borc_selected_idx = False, None; self.borc_secili.clear()
            self.btn_b_toplu.config(bg="#281A3A"); self.btn_b_toplu.l.config(bg="#281A3A", fg="#B060FF")
            self.btn_b_toplu._bg, self.btn_b_toplu._fg, self.btn_b_toplu._hbg = "#281A3A", "#B060FF", "#402060"
        else:
            self.hedef_toplu_mod, self.hedef_selected_idx = False, None; self.hedef_secili.clear()
            self.btn_h_toplu.config(bg="#281A3A"); self.btn_h_toplu.l.config(bg="#281A3A", fg="#B060FF")
            self.btn_h_toplu._bg, self.btn_h_toplu._fg, self.btn_h_toplu._hbg = "#281A3A", "#B060FF", "#402060"

    def toggle_borc_toplu(self):
        if self.secili_tarih != str(date.today()): SoundManager.play_error(); return
        if not self.dm.veriler["borclar"]: return
        self.borc_toplu_mod = not self.borc_toplu_mod; self.borc_secili.clear()
        if self.borc_toplu_mod:
            SoundManager.play_add()
            self.btn_b_toplu.config(bg=Theme.PRP); self.btn_b_toplu.l.config(bg=Theme.PRP, fg=Theme.FW)
            self.btn_b_toplu._bg, self.btn_b_toplu._fg, self.btn_b_toplu._hbg = Theme.PRP, Theme.FW, "#9933FF"
        else: SoundManager.play_delete(); self._reset_toplu_mod(True)
        self.borc_listesi_guncelle()
        self.sag_panel_guncelle()
        
    def toggle_hedef_toplu(self):
        if self.secili_tarih != str(date.today()): SoundManager.play_error(); return
        if not self.dm.veriler["alinacaklar"]: return
        self.hedef_toplu_mod = not self.hedef_toplu_mod; self.hedef_secili.clear()
        if self.hedef_toplu_mod:
            SoundManager.play_add()
            self.btn_h_toplu.config(bg=Theme.PRP); self.btn_h_toplu.l.config(bg=Theme.PRP, fg=Theme.FW)
            self.btn_h_toplu._bg, self.btn_h_toplu._fg, self.btn_h_toplu._hbg = Theme.PRP, Theme.FW, "#9933FF"
        else: SoundManager.play_delete(); self._reset_toplu_mod(False)
        self.hedef_listesi_guncelle()
        self.sag_panel_guncelle()

    def _init_data(self): self.dm.snapshot(); self.streak_guncelle(); self.takvim_ciz(); self.sag_panel_guncelle()
    def saat_guncelle(self):
        aylar = ["","Ocak","Şubat","Mart","Nisan","Mayıs","Haziran","Temmuz","Ağustos","Eylül","Ekim","Kasım","Aralık"]; gunler = ["Pzt","Sal","Çar","Per","Cum","Cmt","Paz"]
        now = datetime.now()
        self.lbl_tarih.config(text=f"{now.day} {aylar[now.month]} {now.year}  {gunler[now.weekday()]}"); self.lbl_saat.config(text=now.strftime("%H:%M:%S"))
        selamlama = "İyi Geceler 🌙" if now.hour < 6 else "Günaydın ☀️" if now.hour < 12 else "İyi Günler ☕" if now.hour < 18 else "İyi Akşamlar 🌆"
        self.lbl_selam.config(text=selamlama); self.after(1000, self.saat_guncelle)

    def streak_hesapla(self):
        bugun = date.today(); m = 0; temiz = self.dm.veriler["temiz_tarihler"]
        if str(bugun) in temiz:
            k = bugun
            while str(k) in temiz: m += 1; k -= timedelta(days=1)
        else:
            k = bugun - timedelta(days=1)
            while str(k) in temiz: m += 1; k -= timedelta(days=1)
        tarihler = sorted(temiz); maks = tmp = 0
        for i,t in enumerate(tarihler):
            if i==0: tmp=1
            else:
                d1 = datetime.strptime(tarihler[i-1],"%Y-%m-%d").date(); d2 = datetime.strptime(t,"%Y-%m-%d").date()
                tmp = tmp+1 if (d2-d1).days==1 else 1
            maks = max(maks,tmp)
        return m, maks

    def streak_guncelle(self):
        m, maks = self.streak_hesapla(); toplam = len(self.dm.veriler["temiz_tarihler"])
        self.lbl_streak_n.config(text=str(toplam)); self.lbl_streak_maks.config(text=f"Mevcut Seri: {m} gün  ·  En Uzun: {maks} gün")
        if str(date.today()) in self.dm.veriler["temiz_tarihler"] and m >= 2:
            self.lbl_streak_e.config(text="👑" if m>=100 else "💎" if m>=30 else "⚡" if m>=7 else "🔥"); self.lbl_streak_n.config(fg=Theme.GLD if m>=30 else Theme.GRN if m>=7 else Theme.ORN)
        else: self.lbl_streak_e.config(text="💤"); self.lbl_streak_n.config(fg=Theme.FG)
        self.ozet_guncelle()

    def ozet_guncelle(self):
        toplam_borc = sum(b["kalan"] for b in self.dm.veriler["borclar"])
        toplam_hedef = len(self.dm.veriler["alinacaklar"])
        toplam_gun = len(self.dm.veriler["temiz_tarihler"])
        m, _ = self.streak_hesapla()
        
        self.lbl_stat1.config(text=f"{para(toplam_borc)}")
        self.lbl_stat2.config(text=f"{toplam_hedef} hedef")
        self.lbl_stat3.config(text=f"{toplam_gun} gün")
        self.lbl_stat4.config(text=f"{m} seri")
        
        son_7_gun = [str(date.today() - timedelta(days=i)) for i in range(7)]
        odenenler_7_gun = sum(g["miktar"] for g in self.dm.veriler.get("odeme_gecmisi", []) if g["tarih"] in son_7_gun)
        
        def animate_lbl(lbl, target_val, color):
            if not lbl.winfo_exists(): return
            if hasattr(lbl, '_anim_id') and lbl._anim_id:
                lbl.after_cancel(lbl._anim_id)
                
            steps = 15
            delay = 300 // steps
            
            start_val = getattr(lbl, '_last_val', target_val)
            
            def step(i):
                if not lbl.winfo_exists(): return
                current_val = start_val + (target_val - start_val) * (i / float(steps))
                lbl.config(text=f"{para(current_val)}", fg=color)
                
                if i < steps:
                    lbl._anim_id = lbl.after(delay, lambda: step(i + 1))
                else:
                    lbl.config(text=f"{para(target_val)}", fg=color)
                    lbl._anim_id = None
                    lbl._last_val = target_val
                    
            step(1)

        if getattr(self, '_prev_alt_borc', None) != toplam_borc:
            animate_lbl(self.lbl_alt_borc, toplam_borc, Theme.RED)
            self._prev_alt_borc = toplam_borc
        
        if getattr(self, '_prev_alt_odenen', None) != odenenler_7_gun:
            animate_lbl(self.lbl_alt_odenen, odenenler_7_gun, Theme.GRN)
            self._prev_alt_odenen = odenenler_7_gun

    def takvim_ciz(self):
        for w in self.takvim_ic.winfo_children(): w.destroy()
        bugun_str = str(date.today()); self.takvim_gun_lbls.clear()
        nav = tk.Frame(self.takvim_ic, bg=Theme.BG1); nav.grid(row=0, column=0, columnspan=7, sticky="ew", pady=(0,12))

        def ybtn(p, t, cmd):
            c = tk.Frame(p, bg=Theme.BG2, padx=1, pady=1); l = tk.Label(c, text=t, bg=Theme.BG2, fg=Theme.FL, font=(F,12,"bold"), cursor=Theme.CURSOR, padx=4, pady=4); l.pack()
            l.bind("<Enter>", lambda e: (Components.animate_bg_color(c, Theme.BG3, 150), l.config(bg=Theme.BG3))); l.bind("<Leave>", lambda e: (Components.animate_bg_color(c, Theme.BG2, 150), l.config(bg=Theme.BG2))); l.bind("<Button-1>", lambda *args: cmd()); return c
        def nbtn(p, t, cmd):
            c = tk.Frame(p, bg=Theme.BG2, padx=1, pady=1); l = tk.Label(c, text=t, bg=Theme.BG2, fg=Theme.FL, font=(F,12,"bold"), cursor=Theme.CURSOR, padx=6, pady=4); l.pack()
            l.bind("<Enter>", lambda e: (Components.animate_bg_color(c, Theme.BG3, 150), l.config(bg=Theme.BG3))); l.bind("<Leave>", lambda e: (Components.animate_bg_color(c, Theme.BG2, 150), l.config(bg=Theme.BG2))); l.bind("<Button-1>", lambda *args: cmd()); return c

        ybtn(nav, "«", lambda: self.yil_degistir(-1)).pack(side=tk.LEFT); nbtn(nav, "‹", lambda: self.ay_degistir(-1)).pack(side=tk.LEFT, padx=(2,0))
        aylar = ["","Ocak","Şubat","Mart","Nisan","Mayıs","Haziran","Temmuz","Ağustos","Eylül","Ekim","Kasım","Aralık"]
        lbl_ay_yil = tk.Label(nav, text=f"{aylar[self.gosterilen_ay]}  {self.gosterilen_yil}", width=14, font=(F,13,"bold"), bg=Theme.BG1, fg=Theme.FW, cursor=Theme.CURSOR); lbl_ay_yil.pack(side=tk.LEFT, padx=10)
        lbl_ay_yil.bind("<Button-1>", lambda *args: self.tarihe_git_dialog()); lbl_ay_yil.bind("<Enter>", lambda e: lbl_ay_yil.config(fg=Theme.BLU)); lbl_ay_yil.bind("<Leave>", lambda e: lbl_ay_yil.config(fg=Theme.FW))
        nbtn(nav, "›", lambda: self.ay_degistir(1)).pack(side=tk.LEFT, padx=(0,2)); ybtn(nav, "»", lambda: self.yil_degistir(1)).pack(side=tk.LEFT)

        bl = tk.Label(nav, text="Bugün", bg=Theme.BG, fg=Theme.FG, font=(F,8), cursor=Theme.CURSOR, padx=8, pady=3)
        bl.bind("<Button-1>", lambda *args: (setattr(self, 'gosterilen_yil', date.today().year), setattr(self, 'gosterilen_ay', date.today().month), self.tarih_sec(bugun_str)))
        bl.bind("<Enter>", lambda e: (Components.animate_bg_color(bl, Theme.BG2, 150), bl.config(fg=Theme.FL))); bl.bind("<Leave>", lambda e: (Components.animate_bg_color(bl, Theme.BG, 150), bl.config(fg=Theme.FG))); bl.pack(side=tk.RIGHT, padx=4)

        for i, g in enumerate(["Pzt","Sal","Çar","Per","Cum","Cmt","Paz"]): tk.Label(self.takvim_ic, text=g, font=(F,8,"bold"), bg=Theme.BG1, fg=Theme.RED if i==6 else Theme.FG, width=4).grid(row=1, column=i, pady=(0,6))

        mat = calendar.monthcalendar(self.gosterilen_yil, self.gosterilen_ay)
        while len(mat)<6: mat.append([0]*7)

        for ri, hafta in enumerate(mat):
            for ci, gun in enumerate(hafta):
                if gun==0: outer = tk.Frame(self.takvim_ic, bg=Theme.BG1, padx=1, pady=1); tk.Label(outer, text=" \n ", width=4, height=2, bg=Theme.BG1, fg=Theme.BG1, font=(F,9,"bold"), relief="flat").pack(); outer.grid(row=ri+2, column=ci, padx=2, pady=2); continue
                ts = f"{self.gosterilen_yil}-{self.gosterilen_ay:02d}-{gun:02d}"
                is_temiz, is_bugun, is_secili, is_gelecek = ts in self.dm.veriler["temiz_tarihler"], ts == bugun_str, ts == self.secili_tarih, ts > bugun_str

                if is_temiz: bg, fg, txt = Theme.GRN, "#000", f"{gun}\n✓"
                elif is_bugun: bg, fg, txt = Theme.ORN, "#000", f"{gun}\n◉"
                elif is_gelecek: bg, fg, txt = Theme.BG1, Theme.FG, f"{gun}\n "
                else: bg, fg, txt = Theme.BG, Theme.FL, f"{gun}\n "

                if is_secili:
                    border = Theme.FW
                    if not (is_temiz or is_bugun): bg, fg = Theme.BG3, Theme.FW
                else: border = Theme.CYAN if is_bugun else bg

                outer = tk.Frame(self.takvim_ic, bg=border, padx=1, pady=1)
                lbl = tk.Label(outer, text=txt, width=4, height=2, bg=bg, fg=fg, font=(F,9,"bold"), cursor=Theme.CURSOR, relief="flat")
                lbl.bind("<Button-1>", lambda e, t=ts: self.tarih_sec(t))
                if not is_temiz and not is_bugun and not is_secili: lbl.bind("<Enter>", lambda e, w=lbl: w.config(bg=Theme.ACT)); lbl.bind("<Leave>", lambda e, w=lbl, b=bg: w.config(bg=b))
                lbl.pack(); outer.grid(row=ri+2, column=ci, padx=2, pady=2); self.takvim_gun_lbls[ts] = (outer, lbl)

    def ay_degistir(self, d):
        self.gosterilen_ay += d
        if self.gosterilen_ay>12: self.gosterilen_ay, self.gosterilen_yil = 1, self.gosterilen_yil+1
        elif self.gosterilen_ay<1: self.gosterilen_ay, self.gosterilen_yil = 12, self.gosterilen_yil-1
        self.takvim_ciz()
        
    def yil_degistir(self, d): self.gosterilen_yil += d; self.takvim_ciz()

    def tarih_sec(self, t):
        ContextMenu._cleanup(self)
        self.not_kaydet(auto=True); self.secili_tarih = t
        if t == str(date.today()): self.gosterilen_yil, self.gosterilen_ay = date.today().year, date.today().month
        self.takvim_ciz(); self.sag_panel_guncelle()

    def sag_panel_guncelle(self, guncelle_sol_liste=True):
        bugun_str = str(date.today()); is_bugun, is_gelecek, is_temiz = self.secili_tarih == bugun_str, self.secili_tarih > bugun_str, self.secili_tarih in self.dm.veriler["temiz_tarihler"]
        try: t_parts = self.secili_tarih.split('-'); g_tarih = f"{t_parts[2]}.{t_parts[1]}.{t_parts[0]}"
        except: g_tarih = self.secili_tarih

        if is_bugun and not self.borc_toplu_mod and self.borc_selected_idx is not None:
            self.btn_b_duzenle.set_state("normal")
            self.btn_b_duzenle.tt.text = ""
        else:
            self.btn_b_duzenle.set_state("disabled")
            if is_gelecek or not is_bugun: self.btn_b_duzenle.tt.text = "Geçmiş/gelecek tarihte düzenleme yapılamaz."
            elif self.borc_toplu_mod: self.btn_b_duzenle.tt.text = "Toplu işlem modunda düzenleme yapılamaz."
            else: self.btn_b_duzenle.tt.text = "Lütfen düzenlemek için listeden bir borç seçin."
            
        if is_bugun and not self.hedef_toplu_mod and getattr(self, 'hedef_selected_idx', None) is not None:
            self.btn_h_duzenle.set_state("normal")
            self.btn_h_duzenle.tt.text = ""
        else:
            self.btn_h_duzenle.set_state("disabled")
            if is_gelecek or not is_bugun: self.btn_h_duzenle.tt.text = "Geçmiş/gelecek tarihte düzenleme yapılamaz."
            elif self.hedef_toplu_mod: self.btn_h_duzenle.tt.text = "Toplu işlem modunda düzenleme yapılamaz."
            else: self.btn_h_duzenle.tt.text = "Lütfen düzenlemek için listeden bir hedef seçin."

        for btn in [self.btn_b_ekle, self.btn_b_ode, self.btn_b_sil, self.btn_b_gecmis, self.btn_b_toplu, self.btn_h_ekle, self.btn_h_tamam, self.btn_h_sil, self.btn_h_toplu]:
            btn.set_state("normal" if is_bugun else "disabled")
            if btn not in [self.btn_b_duzenle, self.btn_h_duzenle]:
                btn.tt.text = "Gelecek bir tarihte işlem yapılamaz." if is_gelecek else "Geçmiş bir tarihte işlem yapılamaz." if not is_bugun else ""

        for w in self.banner_c.winfo_children(): w.destroy()
        self.banner_c.configure(bg=Theme.BG); inner = tk.Frame(self.banner_c, bg=Theme.BG2); inner.pack(fill=tk.BOTH, expand=True)
        text_frame = tk.Frame(inner, bg=Theme.BG2); text_frame.pack(side=tk.LEFT, pady=10, padx=14)
        geri = tk.Label(inner, text="← Bugüne dön", bg=Theme.BG2, fg=Theme.FW, font=(F,9,"bold"), cursor=Theme.CURSOR, padx=12, pady=6)
        geri.bind("<Button-1>", lambda *args: self.tarih_sec(bugun_str)); geri.bind("<Enter>", lambda e: (Components.animate_bg_color(geri, Theme.BG3, 150))); geri.bind("<Leave>", lambda e: (Components.animate_bg_color(geri, Theme.BG2, 150)))

        if is_gelecek:
            tk.Label(text_frame, text=f"🔮 İLERİ TARİH SEÇİLİ  ·  {g_tarih}", bg=Theme.BG2, fg=Theme.BLU, font=(F,10,"bold")).pack(anchor="w")
            tk.Label(text_frame, text="Aşağıdaki veriler bugünkü güncel durumunuzu yansıtmaktadır.", bg=Theme.BG2, fg=Theme.FL, font=(F,8)).pack(anchor="w")
            geri.pack(side=tk.RIGHT, pady=6, padx=14)
        elif not is_bugun:
            tk.Label(text_frame, text=f"📅 GEÇMİŞ GÖRÜNÜM İNCELENİYOR  ·  {g_tarih}", bg=Theme.BG2, fg=Theme.ORN, font=(F,10,"bold")).pack(anchor="w")
            tk.Label(text_frame, text="Aşağıda o güne ait kaydedilmiş borç ve hedef durumunuzu görüyorsunuz.", bg=Theme.BG2, fg=Theme.FL, font=(F,8)).pack(anchor="w")
            geri.pack(side=tk.RIGHT, pady=6, padx=14)
        else:
            tk.Label(text_frame, text=f"✨ BUGÜNÜN ÖZETİ  ·  {g_tarih}", bg=Theme.BG2, fg=Theme.CYAN, font=(F,10,"bold")).pack(anchor="w")
            tk.Label(text_frame, text="Mevcut durumunuz ve aktif hedefleriniz aşağıdaki gibidir.", bg=Theme.BG2, fg=Theme.FL, font=(F,9)).pack(anchor="w")

        if guncelle_sol_liste:
            if is_bugun or is_gelecek: self.borc_listesi_guncelle(animate=False); self.hedef_listesi_guncelle(animate=False)
            else:
                gecmis = self.dm.veriler["gecmis_durumlar"].get(self.secili_tarih, {}); g_borc, g_hdef = gecmis.get("borclar",[]), gecmis.get("alinacaklar",[])
                self.borc_list_frame.clear(); toplam = sum(b["kalan"] for b in g_borc)
                self.lbl_borc_baslik.config(text=f"💳  BORÇ DURUMUNUZ  ·  {para(toplam)}" if g_borc else "💳  BORÇ DURUMUNUZ")
                
                for w in self.borc_progress_frame.winfo_children(): w.destroy()
                if g_borc:
                    renkler_p = [Theme.RED, Theme.BLU, Theme.ORN, Theme.PRP, Theme.GRN, Theme.ROSE, Theme.CYAN]
                    for i, b in enumerate(g_borc):
                        seg = tk.Frame(self.borc_progress_frame, bg=renkler_p[i % len(renkler_p)], height=4); seg.pack(side=tk.LEFT, fill=tk.Y, expand=False)
                        seg.config(width=max(2, int(((b["kalan"]/toplam) if toplam > 0 else 0) * 300)))
                
                if not g_borc:
                    row = tk.Frame(self.borc_list_frame.scrollable_window, bg=Theme.BG1); row.pack(fill=tk.X, pady=10)
                    tk.Label(row, text="       ✨ Harika! Bu tarihte hiç borcunuz yok.", bg=Theme.BG1, fg=Theme.GRN, font=(F,11)).pack(anchor="w")
                else:
                    for b in g_borc: 
                        row = tk.Frame(self.borc_list_frame.scrollable_window, bg=Theme.BG2, padx=12, pady=10); row.pack(fill=tk.X, pady=3)
                        Components.draw_bank_logo(row, b['isim'], 24, Theme.BG2, 14); tk.Label(row, text=b['isim'], font=(F,12,"bold"), bg=Theme.BG2, fg=Theme.FW).pack(side=tk.LEFT)
                        kisimlar = ([f"💳 {b['tur']}"] if b.get("tur") else []) + ([f"📅 Ayın {gun_eki(b['son_odeme_gunu'])}"] if b.get("son_odeme_gunu") else [])
                        
                        tk.Label(row, text=f"   [ {'  |  '.join(kisimlar)} ]" if kisimlar else "", font=(F,10), bg=Theme.BG2, fg=Theme.FL).pack(side=tk.LEFT)
                        tk.Label(row, text=para(b['kalan']), font=(F,13,"bold"), bg=Theme.BG2, fg=Theme.FW).pack(side=tk.RIGHT)
                
                self.hedef_list_frame.clear(); self.lbl_hedef_baslik.config(text=f"🎯  ALINACAK VE YAPILACAK HEDEFLERİNİZ  ·  {len(g_hdef)} hedef")
                if not g_hdef:
                    row = tk.Frame(self.hedef_list_frame.scrollable_window, bg=Theme.BG1); row.pack(fill=tk.X, pady=10)
                    tk.Label(row, text="       🎯 Geçmişte bir hedef eklenmemiş.", bg=Theme.BG1, fg=Theme.FG, font=(F,11)).pack(anchor="w")
                else:
                    for a in g_hdef:
                        row = tk.Frame(self.hedef_list_frame.scrollable_window, bg=Theme.BG2, padx=12, pady=10); row.pack(fill=tk.X, pady=3)
                        ikon = "💸" if a.get("kategori") in ["maddi", "alinacak"] else "📌"
                        tk.Label(row, text=ikon, font=(F,14), bg=Theme.BG2, fg=Theme.FW).pack(side=tk.LEFT, padx=(0,8))
                        tk.Label(row, text=a['isim'], font=(F,12,"bold"), bg=Theme.BG2, fg=Theme.FW).pack(side=tk.LEFT)
                        
                        eklenme_str = a.get('eklenme_tarihi', '').split(' ')[0] if a.get('eklenme_tarihi') else ''
                        if eklenme_str:
                            tk.Label(row, text=f"Eklendi: {tarih_formatla(eklenme_str)}", font=(F,9), bg=Theme.BG2, fg=Theme.FL).pack(side=tk.RIGHT, padx=(0,5))

        if is_gelecek:
            self.btn_hedef.config(text=f"☑️   {g_tarih} GÜNÜNÜN HEDEFİNİ İŞARETLE")
            self.hedef_btn_tt.text, self.hedef_btn_tt.enabled = "İleri bir tarih için işaretleme yapamazsınız.", True
        else:
            self.hedef_btn_tt.enabled = False
            self.btn_hedef.config(text=f"☑️  {g_tarih}  —  İŞARETLENDİ" if is_temiz else "☑️  BUGÜNÜN HEDEFİNİ İŞARETLE" if is_bugun else f"☑️   {g_tarih} GÜNÜNÜN HEDEFİNİ İŞARETLE")
        
        self.btn_hedef_update_colors()
        self.not_text.delete("1.0", tk.END); icerik = self.dm.veriler.get("gunluk_notlar",{}).get(self.secili_tarih,"")
        if icerik: self.not_text.insert("1.0", icerik)

    def _bind_all_children(self, widget, event, handler):
        widget.bind(event, handler)
        for child in widget.winfo_children(): self._bind_all_children(child, event, handler)

    def _bind_row_click(self, widget, handler):
        def on_click(event):
            handler()
            return "break"
        widget.bind("<Button-1>", on_click)
        for child in widget.winfo_children():
            self._bind_row_click(child, handler)

    def _bind_row_right_click(self, widget, handler):
        def on_right(event):
            handler(event.x_root, event.y_root)
            return "break"
        widget.bind("<Button-3>", on_right)
        widget.bind("<Button-2>", on_right)
        for child in widget.winfo_children():
            self._bind_row_right_click(child, handler)

    def update_borc_visuals(self, old_idx, new_idx):
        if not hasattr(self, 'borc_rows'): return
        if old_idx is not None and old_idx < len(self.borc_rows):
            row_data = self.borc_rows[old_idx]
            row, lbl_isim, lbl_kalan = row_data[0], row_data[1], row_data[2]
            if row.winfo_exists(): Components.animate_bg_color(row, Theme.BG2, duration=300)
            if lbl_isim.winfo_exists(): lbl_isim.config(fg=Theme.FW)
            if lbl_kalan.winfo_exists(): lbl_kalan.config(fg=Theme.FW)
        if new_idx is not None and new_idx < len(self.borc_rows):
            row_data = self.borc_rows[new_idx]
            row, lbl_isim, lbl_kalan = row_data[0], row_data[1], row_data[2]
            if row.winfo_exists(): Components.animate_bg_color(row, Theme.SEL_BG_HL, duration=300)
            if lbl_isim.winfo_exists(): lbl_isim.config(fg=Theme.SEL_FG_HL)
            if lbl_kalan.winfo_exists(): lbl_kalan.config(fg=Theme.SEL_FG_HL)

    def update_hedef_visuals(self, old_idx, new_idx):
        if not hasattr(self, 'hedef_rows'): return
        if old_idx is not None and old_idx < len(self.hedef_rows):
            row = self.hedef_rows[old_idx][0]
            if row.winfo_exists(): Components.animate_bg_color(row, Theme.BG2, duration=300)
        if new_idx is not None and new_idx < len(self.hedef_rows):
            row = self.hedef_rows[new_idx][0]
            if row.winfo_exists(): Components.animate_bg_color(row, Theme.SEL_BG_HL, duration=300)

    def __do_borc_row_click(self, idx):
        ContextMenu._cleanup(self)
        now = self.tk.call('clock', 'milliseconds')
        last = getattr(self, '_borc_last_click_time', 0)
        if now - last < 200: return
        self._borc_last_click_time = now
        
        if getattr(self, 'borc_toplu_mod', False):
            if idx in self.borc_secili: self.borc_secili.remove(idx)
            else: self.borc_secili.add(idx)
            self.borc_listesi_guncelle(animate=False)
        else: 
            if getattr(self, 'borc_selected_idx', None) == idx: return 
            old_idx = getattr(self, 'borc_selected_idx', None)
            self.borc_selected_idx = idx
            if getattr(self, 'hedef_selected_idx', None) is not None:
                old_h = self.hedef_selected_idx
                self.hedef_selected_idx = None
                self.update_hedef_visuals(old_h, None)
            self.update_borc_visuals(old_idx, idx)
        self.sag_panel_guncelle(guncelle_sol_liste=False)

    def _on_borc_row_click(self, idx):
        self.__do_borc_row_click(idx)

    def __do_hedef_row_click(self, idx):
        ContextMenu._cleanup(self)
        now = self.tk.call('clock', 'milliseconds')
        last = getattr(self, '_hedef_last_click_time', 0)
        if now - last < 200: return
        self._hedef_last_click_time = now
        
        if getattr(self, 'hedef_toplu_mod', False):
            if idx in self.hedef_secili: self.hedef_secili.remove(idx)
            else: self.hedef_secili.add(idx)
            self.hedef_listesi_guncelle(animate=False)
        else: 
            if getattr(self, 'hedef_selected_idx', None) == idx: return
            old_idx = getattr(self, 'hedef_selected_idx', None)
            self.hedef_selected_idx = idx
            if getattr(self, 'borc_selected_idx', None) is not None:
                old_b = self.borc_selected_idx
                self.borc_selected_idx = None 
                self.update_borc_visuals(old_b, None)
            self.update_hedef_visuals(old_idx, idx)
        self.sag_panel_guncelle(guncelle_sol_liste=False)

    def _on_hedef_row_click(self, idx):
        self.__do_hedef_row_click(idx)

    def _get_pct_color(self, pct):
        if pct <= 0: return Theme.FL
        elif pct >= 100: return Theme.GRN
        r1, g1, b1 = 255, 48, 96   
        r2, g2, b2 = 0, 229, 160   
        ratio = pct / 100.0
        r = int(r1 + (r2 - r1) * ratio); g = int(g1 + (g2 - g1) * ratio); b = int(b1 + (b2 - b1) * ratio)
        return f"#{r:02X}{g:02X}{b:02X}"

    def borc_listesi_guncelle(self, animate=False):
        self.borc_list_frame.clear()
        toplam = sum(b["kalan"] for b in self.dm.veriler["borclar"])
        self.lbl_borc_baslik.config(text=f"💳  BORÇ DURUMUNUZ  ·  {para(toplam)}" if self.dm.veriler["borclar"] else "💳  BORÇ DURUMUNUZ  ·  0 borç")
        
        for w in self.borc_progress_frame.winfo_children(): w.destroy()
        if self.dm.veriler["borclar"]:
            renkler_p = [Theme.RED, Theme.BLU, Theme.ORN, Theme.PRP, Theme.GRN, Theme.ROSE, Theme.CYAN]
            for i, b in enumerate(self.dm.veriler["borclar"]):
                seg = tk.Frame(self.borc_progress_frame, bg=renkler_p[i % len(renkler_p)], height=4, cursor=Theme.CURSOR); seg.pack(side=tk.LEFT, fill=tk.Y, expand=False)
                seg.config(width=max(2, int((b["kalan"]/toplam if toplam > 0 else 0) * 300))); seg.bind("<Button-1>", lambda *args, idx=i: self._on_borc_row_click(idx))

        if not self.dm.veriler["borclar"]:
            r = tk.Frame(self.borc_list_frame.scrollable_window, bg=Theme.BG1, pady=10); r.pack(fill=tk.X)
            tk.Label(r, text="       ✨ Harika! Şu anda hiç borcunuz yok.", bg=Theme.BG1, fg=Theme.GRN, font=(F,11)).pack(anchor="w")
        else:
            prev_sel = getattr(self, '_last_borc_selected_idx', None)
            self._last_borc_selected_idx = getattr(self, 'borc_selected_idx', None)
            
            self.borc_rows = []
            for idx, b in enumerate(self.dm.veriler["borclar"]):
                is_selected = not getattr(self, 'borc_toplu_mod', False) and (idx == self._last_borc_selected_idx)
                was_selected = animate and not getattr(self, 'borc_toplu_mod', False) and (idx == prev_sel)
                
                target_bg = Theme.SEL_BG_HL if is_selected else Theme.BG2
                start_bg = Theme.BG2 if (is_selected and animate) else (Theme.SEL_BG_HL if was_selected else target_bg)
                
                row = tk.Frame(self.borc_list_frame.scrollable_window, bg=start_bg, padx=12, pady=10, cursor=Theme.CURSOR, highlightthickness=0)
                row.pack(fill=tk.X, pady=3) 
                
                if start_bg != target_bg: Components.animate_bg_color(row, target_bg, duration=300)

                if getattr(self, 'borc_toplu_mod', False):
                    tk.Label(row, text="✅" if idx in self.borc_secili else "⬜", font=(F,14), bg=start_bg, fg=Theme.FW, highlightthickness=0, bd=0).pack(side=tk.LEFT, padx=(0,10))

                Components.draw_bank_logo(row, b['isim'], 24, start_bg, 14)
                lbl_isim = tk.Label(row, text=b['isim'], font=(F,12,"bold"), bg=start_bg, fg=Theme.SEL_FG_HL if is_selected else Theme.FW, highlightthickness=0, bd=0)
                lbl_isim.pack(side=tk.LEFT)

                kisimlar = ([f"💳 {b['tur']}"] if b.get("tur") else []) + ([f"📅 Ayın {gun_eki(b['son_odeme_gunu'])}"] if b.get("son_odeme_gunu") else [])
                
                detay_kapsayici = tk.Frame(row, bg=start_bg, highlightthickness=0); detay_kapsayici.pack(side=tk.LEFT)
                if kisimlar: tk.Label(detay_kapsayici, text=f"   [ {'  |  '.join(kisimlar)} ]", font=(F,10), bg=start_bg, fg=Theme.FW if is_selected else Theme.FL, highlightthickness=0, bd=0).pack(side=tk.LEFT)

                od, bas = b.get("odenen_toplam", 0), b["kalan"] + b.get("odenen_toplam", 0)
                pct, pct_col = int(od/bas*100) if bas > 0 else 0, self._get_pct_color(int(od/bas*100) if bas > 0 else 0)
                
                right_f = tk.Frame(row, bg=start_bg, highlightthickness=0); right_f.pack(side=tk.RIGHT)

                if b.get("notlar"):
                    not_lbl = tk.Label(right_f, text="ⓘ", font=(F,11,"bold"), bg=start_bg, fg=Theme.CYAN, highlightthickness=0, bd=0, cursor=Theme.CURSOR)
                    not_lbl.pack(side=tk.LEFT, padx=(0,10))
                    ToolTip(not_lbl, b['notlar'])

                lbl_kalan = tk.Label(right_f, text=f"{para(b['kalan'])}", font=(F,14,"bold"), bg=start_bg, fg=Theme.SEL_FG_HL if is_selected else Theme.FW, highlightthickness=0)
                lbl_kalan.pack(side=tk.LEFT, padx=(0, 8))

                self.borc_rows.append((row, lbl_isim, lbl_kalan))

                self._bind_row_click(row, lambda i=idx: self._on_borc_row_click(i))
                self._bind_row_right_click(row, lambda rx, ry, i=idx: self.after(10, lambda: self.borc_sag_tik(rx, ry, i)))
            
        self.ozet_guncelle()

    def hedef_listesi_guncelle(self, animate=False):
        self.hedef_list_frame.clear()
        self.lbl_hedef_baslik.config(text=f"🎯  ALINACAK VE YAPILACAK HEDEFLERİNİZ  ·  {len(self.dm.veriler['alinacaklar'])} hedef")
        
        if not self.dm.veriler["alinacaklar"]:
            r = tk.Frame(self.hedef_list_frame.scrollable_window, bg=Theme.BG1, pady=10); r.pack(fill=tk.X)
            tk.Label(r, text="       🎯 Henüz hedef eklemediniz.", bg=Theme.BG1, fg=Theme.FG, font=(F,11)).pack(anchor="w")
        else:
            prev_sel_h = getattr(self, '_last_hedef_selected_idx', None)
            self._last_hedef_selected_idx = getattr(self, 'hedef_selected_idx', None)
            
            self.hedef_rows = []
            for idx, a in enumerate(self.dm.veriler["alinacaklar"]):
                is_selected = not getattr(self, 'hedef_toplu_mod', False) and (idx == self._last_hedef_selected_idx)
                was_selected = animate and not getattr(self, 'hedef_toplu_mod', False) and (idx == prev_sel_h)
                
                target_bg = Theme.SEL_BG_HL if is_selected else Theme.BG2
                start_bg = Theme.BG2 if (is_selected and animate) else (Theme.SEL_BG_HL if was_selected else target_bg)
                
                row = tk.Frame(self.hedef_list_frame.scrollable_window, bg=start_bg, padx=12, pady=10, cursor=Theme.CURSOR, highlightthickness=0); row.pack(fill=tk.X, pady=3)
                
                if start_bg != target_bg: Components.animate_bg_color(row, target_bg, duration=300)

                if getattr(self, 'hedef_toplu_mod', False):
                    tk.Label(row, text="✅" if idx in self.hedef_secili else "⬜", font=(F,14), bg=start_bg, fg=Theme.FW, highlightthickness=0, bd=0).pack(side=tk.LEFT, padx=(0,10))

                ikon = "💸" if a.get("kategori") in ["maddi", "alinacak"] else "📌"
                tk.Label(row, text=ikon, font=(F,14), bg=start_bg, fg=Theme.FW, highlightthickness=0, bd=0).pack(side=tk.LEFT, padx=(0,8))
                
                lbl_isim = tk.Label(row, text=a['isim'], font=(F,12,"bold"), bg=start_bg, fg=Theme.FW, highlightthickness=0, bd=0)
                lbl_isim.pack(side=tk.LEFT)
                
                eklenme_str = a.get('eklenme_tarihi', '').split(' ')[0] if a.get('eklenme_tarihi') else ''
                if eklenme_str:
                    tk.Label(row, text=f"Eklendi: {tarih_formatla(eklenme_str)}", font=(F,9), bg=start_bg, fg=Theme.FL, highlightthickness=0, bd=0).pack(side=tk.RIGHT, padx=(0,5))

                lbl_kalan = None
                
                self.hedef_rows.append((row, lbl_isim, lbl_kalan))

                self._bind_row_click(row, lambda i=idx: self._on_hedef_row_click(i))
                self._bind_row_right_click(row, lambda rx, ry, i=idx: self.after(10, lambda: self.hedef_sag_tik(rx, ry, i)))
            
        self.ozet_guncelle()

    def hedef_toggle(self):
        if self.secili_tarih > str(date.today()): SoundManager.play_error(); return 
        t_str, is_added = f"{self.secili_tarih.split('-')[2]}.{self.secili_tarih.split('-')[1]}.{self.secili_tarih.split('-')[0]}", False
        
        if self.secili_tarih in self.dm.veriler["temiz_tarihler"]:
            self.dm.veriler["temiz_tarihler"].remove(self.secili_tarih)
        else:
            self.dm.veriler["temiz_tarihler"].append(self.secili_tarih)
            SoundManager.play_success(); is_added = True
            
        self.dm.snapshot(); self.streak_guncelle(); self.takvim_ciz()
        
        if is_added and self.secili_tarih in self.takvim_gun_lbls:
            outer, lbl = self.takvim_gun_lbls[self.secili_tarih]
            def pop_anim(step=0):
                if not lbl.winfo_exists(): return
                colors = ["#FFFFFF", Theme.GRN]
                if step < 4:
                    c = colors[step % 2]
                    lbl.config(bg=c); outer.config(bg=c)
                    lbl.after(60, lambda: pop_anim(step+1))
                else:
                    lbl.config(bg=Theme.GRN, fg="#000", font=(F, 9, "bold"))
                    outer.config(bg=Theme.GRN)
            pop_anim()
        self.sag_panel_guncelle()

    def not_kaydet(self, auto=False):
        t, eski_t = self.not_text.get("1.0", tk.END).strip(), self.dm.veriler.get("gunluk_notlar", {}).get(self.secili_tarih, "")
        if auto and t == eski_t: return
        if t: self.dm.veriler["gunluk_notlar"][self.secili_tarih] = t
        elif self.secili_tarih in self.dm.veriler["gunluk_notlar"]: del self.dm.veriler["gunluk_notlar"][self.secili_tarih]
        self.dm.save()
        if not auto: SoundManager.play_save()

    def sifirla(self):
        d = tk.Toplevel(self); d.title("Verileri Sıfırla"); Components.center_window(d, 400, 240); d.configure(bg=Theme.BG1); d.transient(self); d.grab_set(); d.attributes("-alpha", 0.0); Components.fade_in(d)
        tk.Frame(d, bg=Theme.RED, height=3).pack(fill=tk.X); content_frame = tk.Frame(d, bg=Theme.BG1); content_frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(content_frame, text="⚠️  TÜM VERİLERİ SİL", font=(F, 14, "bold"), bg=Theme.BG1, fg=Theme.RED).pack(pady=(30, 10))
        tk.Label(content_frame, text="Geçmiş kayıtlar, hedefler ve borçlar dahil olmak üzere\ntüm verileriniz kalıcı olarak silinecektir.\n\nEmin misiniz?", font=(F, 10), bg=Theme.BG1, fg=Theme.FL, justify=tk.CENTER).pack()
        
        btn_frame = tk.Frame(d, bg=Theme.BG1); btn_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(0, 25), padx=25)
        def onayla():
            self.not_text.delete("1.0", tk.END)
            self.dm.reset_all(); self.streak_guncelle(); self.tarih_sec(str(date.today())); self.sag_panel_guncelle(); SoundManager.play_delete(); Components.fade_out(d)
            
        Components.create_btn(btn_frame, "İPTAL ET", Theme.BG2, Theme.FW, lambda: Components.fade_out(d), fs=10, py=10).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        Components.create_btn(btn_frame, "EVET, SİL", Theme.RED, Theme.FW, onayla, fs=10, py=10, hbg="#C0002E").pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))

    def hizli_miktar_ayarla_dialog(self, mode="ekle"):
        d = tk.Toplevel(self); d.title("Hızlı Miktar Düzenle"); Components.center_window(d, 350, 480); d.configure(bg=Theme.BG1); d.transient(self); d.grab_set(); d.attributes("-alpha", 0.0); Components.fade_in(d)
        tk.Frame(d, bg=Theme.GRN, height=3).pack(fill=tk.X)
        
        h_ust = tk.Frame(d, bg=Theme.BG1)
        h_ust.pack(fill=tk.X, pady=(15, 5))
        tk.Label(h_ust, text="⚡ Hızlı Miktarlar", font=(F, 14, "bold"), bg=Theme.BG1, fg=Theme.FW).pack(side=tk.LEFT, padx=20)
        
        entries = []
        def reset_defaults():
            defs = [1000, 5000, 10000, 20000, 50000] if mode == "ekle" else [1000, 2500, 5000, 10000]
            for i, e in enumerate(entries):
                if i < len(defs):
                    e.delete(0, tk.END)
                    e.insert(0, str(defs[i]))
        
        btn_reset = tk.Label(h_ust, text="⟳ Sıfırla", font=(F, 9, "bold"), bg=Theme.BG1, fg=Theme.FL, cursor=Theme.CURSOR)
        btn_reset.pack(side=tk.RIGHT, padx=20)
        btn_reset.bind("<Button-1>", lambda *args: reset_defaults())
        btn_reset.bind("<Enter>", lambda *args: (Components.animate_bg_color(btn_reset, Theme.BG2, 150), btn_reset.config(fg=Theme.FW)))
        btn_reset.bind("<Leave>", lambda *args: (Components.animate_bg_color(btn_reset, Theme.BG1, 150), btn_reset.config(fg=Theme.FL)))

        tk.Label(d, text="Butonlarda görünecek miktarları aşağıdan\nbelirleyebilirsiniz.", font=(F, 9), bg=Theme.BG1, fg=Theme.FL, justify=tk.CENTER).pack(pady=(0, 15))
        
        c = tk.Frame(d, bg=Theme.BG1, padx=20); c.pack(fill=tk.BOTH, expand=True)
        key = "hizli_miktarlar" if mode == "ekle" else "odeme_hizli_miktarlar"
        mevcut = self.dm.veriler.get(key, [])
        limit = 5 if mode == "ekle" else 4
        
        for i in range(limit):
            row = tk.Frame(c, bg=Theme.BG1, pady=6); row.pack(fill=tk.X)
            tk.Label(row, text=f"Buton {i+1}:", bg=Theme.BG1, fg=Theme.FL, font=(F, 10, "bold"), width=8, anchor="w").pack(side=tk.LEFT)
            bg_f = tk.Frame(row, bg=Theme.LINE, padx=1, pady=1); bg_f.pack(side=tk.LEFT, fill=tk.X, expand=True)
            _, _, e = Components.build_safe_entry(bg_f, Theme.BG2, Theme.GRN, (F, 12, "bold"), justify="center")
            Components.bind_num_only(e)
            try: e.insert(0, str(mevcut[i]))
            except: e.insert(0, "1000")
            entries.append(e)
            
        def kaydet():
            yeni_liste = []
            for e in entries:
                val = sayi(e.get())
                yeni_liste.append(int(val) if val and val > 0 else 1000)
            self.dm.veriler[key] = sorted(yeni_liste)
            self.dm.save(); SoundManager.play_save(); 
            if hasattr(self, 'active_borc_modal_refresh'): self.active_borc_modal_refresh()
            Components.fade_out(d)
            
        btn_frame = tk.Frame(d, bg=Theme.BG1, padx=20, pady=20); btn_frame.pack(fill=tk.X, side=tk.BOTTOM)
        Components.create_btn(btn_frame, "İPTAL", Theme.BG2, Theme.FW, lambda: Components.fade_out(d), py=10, hbg=Theme.BG3).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        Components.create_btn(btn_frame, "KAYDET", Theme.GRN, "#000", kaydet, py=10, hbg="#00B070").pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5,0))

    def borc_islem_modal(self, b_idx=None):
        if self.secili_tarih != str(date.today()): SoundManager.play_error(); return
        is_edit = b_idx is not None
        if not is_edit and getattr(self, 'borc_toplu_mod', False) and self.borc_secili:
            is_edit, b_idx = True, list(self.borc_secili)[0]

        d = tk.Toplevel(self); d.title("Borç Düzenleme" if is_edit else "Yeni Borç")
        d.attributes("-alpha", 0.0); Components.fade_in(d); Components.center_window(d, 560, 760)
        d.configure(bg=Theme.BG1); d.transient(self); d.grab_set()
        
        d.columnconfigure(0, weight=1); d.rowconfigure(1, weight=1)

        top_f = tk.Frame(d, bg=Theme.BG1); top_f.grid(row=0, column=0, sticky="ew")
        tk.Frame(top_f, bg=Theme.BLU, height=3).pack(fill=tk.X)
        hdr = tk.Frame(top_f, bg=Theme.BG1, padx=22, pady=16); hdr.pack(fill=tk.X)
        tk.Label(hdr, text="💳 Borç Düzenleme" if is_edit else "💳 Yeni Borç Ekle", font=(F,16,"bold"), bg=Theme.BG1, fg=Theme.FW).pack(anchor="w")
        Components.create_sep(top_f, c=Theme.LINE, py=0)

        scroll_c = CustomScrollableFrame(d, bg_color=Theme.BG1)
        scroll_c.grid(row=1, column=0, sticky="nsew", padx=2, pady=5)
        inner = scroll_c.scrollable_window

        alt_frame = tk.Frame(d, bg=Theme.BG1, pady=20, padx=24)
        alt_frame.grid(row=2, column=0, sticky="ew")

        borc_data = {}
        if is_edit and b_idx is not None and b_idx < len(self.dm.veriler["borclar"]):
            borc_data = self.dm.veriler["borclar"][b_idx]
            
        tk.Label(inner, text="Banka / Kurum Seçimi", font=(F,10,"bold"), bg=Theme.BG1, fg=Theme.FL, anchor="w").pack(fill=tk.X, padx=24, pady=(15,6))
        grid_c = tk.Frame(inner, bg=Theme.BG1); grid_c.pack(fill=tk.X, padx=18)
        secili_banka = tk.StringVar(value=borc_data.get("isim", BANKALAR[0]["isim"]))
        
        banka_btn_refs = {}
        
        for i, bk in enumerate(BANKALAR):
            r, c = divmod(i, 4); outer = tk.Frame(grid_c, bg=Theme.LINE, padx=1, pady=1)
            outer.grid(row=r, column=c, padx=4, pady=4, sticky="nsew")
            grid_c.columnconfigure(c, weight=1, uniform="b_col")
            inner_f = tk.Frame(outer, bg=Theme.BG2, cursor=Theme.CURSOR); inner_f.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
            
            logo_img = None
            try: logo_img = get_cached_logo(bk, size=24)
            except: pass
            
            lbl_icon = tk.Label(inner_f, image=logo_img, bg=Theme.BG2) if logo_img else tk.Label(inner_f, text=bk.get("ikon", "💳"), font=(F, 14), bg=Theme.BG2, fg=Theme.FW)
            if logo_img: lbl_icon.image = logo_img 
            lbl_icon.pack(fill=tk.BOTH, expand=True, pady=(4,0))
            lbl_name = tk.Label(inner_f, text=bk["isim"], font=(F,7,"bold"), bg=Theme.BG2, fg=Theme.FW, wraplength=80); lbl_name.pack(fill=tk.X, side=tk.BOTTOM, pady=(0,4))
            
            start_a, stop_a = Components.apply_sliding_border(outer, Theme.CYAN, 2, speed=1.5)
            nm = bk["isim"]
            banka_btn_refs[nm] = (outer, inner_f, lbl_icon, lbl_name, start_a, stop_a)

        def banka_sec(isim):
            secili_banka.set(isim)
            for nm, (outer, inner_f, lbl_icon, lbl_name, start_a, stop_a) in banka_btn_refs.items():
                if nm == isim: 
                    outer.config(bg=Theme.BG1)
                    Components.animate_bg_color(inner_f, Theme.SEL_BG, duration=200)
                    lbl_icon.config(bg=Theme.SEL_BG)
                    lbl_name.config(bg=Theme.SEL_BG, fg=Theme.FW)
                    start_a() 
                else: 
                    stop_a() 
                    outer.config(bg=Theme.LINE)
                    Components.animate_bg_color(inner_f, Theme.BG2, duration=200)
                    lbl_icon.config(bg=Theme.BG2)
                    lbl_name.config(bg=Theme.BG2, fg=Theme.FL)

        for nm, (outer, inner_f, lbl_icon, lbl_name, start_a, stop_a) in banka_btn_refs.items():
            for w in [inner_f, lbl_icon, lbl_name]: 
                w.bind("<Button-1>", lambda e, n=nm: banka_sec(n))
                
        banka_sec(secili_banka.get())

        tk.Label(inner, text="Detaylar", font=(F,10,"bold"), bg=Theme.BG1, fg=Theme.FL, anchor="w").pack(fill=tk.X, padx=24, pady=(20,5))
        
        form_border = tk.Frame(inner, bg=Theme.LINE, padx=1, pady=1)
        form_border.pack(fill=tk.X, padx=24, pady=(0, 10))
        form_frame = tk.Frame(form_border, bg=Theme.BG2)
        form_frame.pack(fill=tk.BOTH, expand=True)

        row1 = tk.Frame(form_frame, bg=Theme.BG2, pady=8, padx=12); row1.pack(fill=tk.X)
        tk.Label(row1, text="🏷️", font=(F,12), bg=Theme.BG2, fg=Theme.BLU, width=3).pack(side=tk.LEFT)
        tk.Label(row1, text="Borç Türü:", font=(F,9), bg=Theme.BG2, fg=Theme.FL, width=15, anchor="w").pack(side=tk.LEFT)
        tur_var = tk.StringVar(value=borc_data.get("tur", "Kredi Kartı"))
        opt = CustomDropdown(row1, ["Kredi Kartı", "Ek Hesap (KMH)", "İhtiyaç Kredisi", "Diğer"], tur_var)
        opt.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Frame(form_frame, bg=Theme.LINE, height=1).pack(fill=tk.X)
        row2 = tk.Frame(form_frame, bg=Theme.BG2, pady=8, padx=12); row2.pack(fill=tk.X)
        tk.Label(row2, text="📅", font=(F,12), bg=Theme.BG2, fg=Theme.ORN, width=3).pack(side=tk.LEFT)
        tk.Label(row2, text="Son Ödeme Günü:", font=(F,9), bg=Theme.BG2, fg=Theme.FL, width=15, anchor="w").pack(side=tk.LEFT)
        
        s_bg = tk.Frame(row2, bg=Theme.BG1)
        s_bg.pack(side=tk.LEFT)
        _, _, sot_entry = Components.build_safe_entry(s_bg, Theme.BG1, Theme.FW, (F,10,"bold"), width=8, justify="center")
        Components.bind_num_only(sot_entry)
        if borc_data.get("son_odeme_gunu"): sot_entry.insert(0, str(borc_data["son_odeme_gunu"]))

        tk.Frame(form_frame, bg=Theme.LINE, height=1).pack(fill=tk.X)
        row3 = tk.Frame(form_frame, bg=Theme.BG2, pady=8, padx=12); row3.pack(fill=tk.X)
        
        tk.Label(row3, text="💰", font=(F,12), bg=Theme.BG2, fg=Theme.GRN, width=3).pack(side=tk.LEFT)
        tk.Label(row3, text="TOPLAM MİKTAR:", font=(F,9,"bold"), bg=Theme.BG2, fg=Theme.FW, width=15, anchor="w").pack(side=tk.LEFT)
        
        amt_out = tk.Frame(row3, bg=Theme.BG2)
        amt_out.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        amt_border, amt_inner, entry_miktar = Components.build_safe_entry(amt_out, Theme.BG1, Theme.GRN, (F,14,"bold"), justify="right")
        
        Components.bind_num_only(entry_miktar)
        
        entry_miktar.pack_forget()
        tk.Label(amt_inner, text="₺", font=(F,14,"bold"), bg=Theme.BG1, fg=Theme.GRN, padx=10).pack(side=tk.RIGHT)
        entry_miktar.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        if borc_data.get("kalan") is not None: entry_miktar.insert(0, str(int(borc_data["kalan"])))
        def on_amount_key(e=None):
            raw = "".join(filter(str.isdigit, entry_miktar.get()))
            if not raw: entry_miktar.delete(0, tk.END); return
            try:
                val = int(raw); formatted = f"{val:,}".replace(",", ".")
                pos, old_len = entry_miktar.index(tk.INSERT), len(entry_miktar.get())
                entry_miktar.delete(0, tk.END); entry_miktar.insert(0, formatted)
                new_len = len(formatted); new_pos = pos + (new_len - old_len); entry_miktar.icursor(max(0, new_pos))
            except: pass
        entry_miktar.bind("<KeyRelease>", on_amount_key)

        hm_kapsayici = tk.Frame(inner, bg=Theme.BG1)
        hm_kapsayici.pack(fill=tk.X, padx=24, pady=(0,10))
        h_ust = tk.Frame(hm_kapsayici, bg=Theme.BG1); h_ust.pack(fill=tk.X)
        tk.Label(h_ust, text="HIZLI MİKTAR", font=(F,8,"bold"), bg=Theme.BG1, fg=Theme.BLU, anchor="w").pack(side=tk.LEFT)
        ayarlar_btn = tk.Label(h_ust, text="⚙️ Düzenle", font=(F,8,"bold"), bg=Theme.BG1, fg=Theme.FL, cursor=Theme.CURSOR)
        ayarlar_btn.pack(side=tk.RIGHT)
        ayarlar_btn.bind("<Button-1>", lambda e: self.hizli_miktar_ayarla_dialog(mode="ekle"))
        ayarlar_btn.bind("<Enter>", lambda e: (Components.animate_bg_color(ayarlar_btn, Theme.BG2, 150), ayarlar_btn.config(fg=Theme.FW)))
        ayarlar_btn.bind("<Leave>", lambda e: (Components.animate_bg_color(ayarlar_btn, Theme.BG1, 150), ayarlar_btn.config(fg=Theme.FL)))
        
        hizli_btn_f = tk.Frame(hm_kapsayici, bg=Theme.BG1); hizli_btn_f.pack(fill=tk.X, pady=(5,0))
        
        def render_hizli_butonlar():
            def set_m(v): 
                curr = sayi(entry_miktar.get()) or 0
                def fmt(x): return f"{int(x):,}".replace(",", ".")
                Components.animate_entry_value(entry_miktar, curr, v, fmt, duration=200)
            mevcut_miktarlar = self.dm.veriler.get("hizli_miktarlar", [1000, 5000, 10000, 20000, 50000])
            Components.create_quick_amounts(hizli_btn_f, mevcut_miktarlar, Theme.GRN, Theme.GRN, set_m)
            
        render_hizli_butonlar()
        self.active_borc_modal_refresh = render_hizli_butonlar 

        tk.Label(inner, text="Notlar / Açıklama (İsteğe Bağlı)", font=(F,10,"bold"), bg=Theme.BG1, fg=Theme.FL, anchor="w").pack(fill=tk.X, padx=24, pady=(15,5))
        n_out = tk.Frame(inner, bg=Theme.BG1); n_out.pack(fill=tk.X, padx=24)
        
        n_border, n_inner, note_text = Components.build_safe_entry(n_out, Theme.BG2, Theme.FW, (F,12))
        
        note_text.pack_forget()
        note_text.pack(fill=tk.BOTH, expand=True, padx=6, pady=12)
        
        if borc_data.get("notlar"): note_text.insert("0", borc_data["notlar"])

        def kaydet_borc():
            m = sayi(entry_miktar.get())
            if not m or m<0: 
                SoundManager.play_error()
                return
            
            s_val = sot_entry.get().strip()
            sot = None
            if s_val:
                if not s_val.isdigit() or not (1 <= int(s_val) <= 31):
                    SoundManager.play_error()
                    return
                sot = int(s_val)
            
            isim, tur, not_icerik = secili_banka.get(), tur_var.get(), note_text.get().strip()
            target_indices = list(self.borc_secili) if getattr(self, 'borc_toplu_mod', False) else ([b_idx] if b_idx is not None else [])
            
            tarih_str = str(datetime.now())
            
            if target_indices:
                for idx in target_indices:
                    if idx < len(self.dm.veriler["borclar"]):
                        b = self.dm.veriler["borclar"][idx]; b["isim"] = isim; b["kalan"] = m; b["tur"] = tur; b["son_odeme_gunu"] = sot; b["notlar"] = not_icerik
                        b["son_guncelleme"] = tarih_str
            else:
                merged = False
                for existing in self.dm.veriler["borclar"]:
                    if existing["isim"] == isim and existing.get("tur") == tur:
                        existing["kalan"] += m
                        existing["odenen_toplam"] = existing.get("odenen_toplam", 0)
                        existing["son_guncelleme"] = tarih_str
                        if sot is not None: existing["son_odeme_gunu"] = sot
                        old_note = existing.get("notlar", "").strip()
                        if not_icerik:
                            if old_note:
                                existing["notlar"] = old_note + "\n---\n" + not_icerik
                            else:
                                existing["notlar"] = not_icerik
                        merged = True
                        break
                if not merged:
                    self.dm.veriler["borclar"].append({
                        "isim": isim, 
                        "kalan": m, 
                        "odenen_toplam": 0, 
                        "tur": tur, 
                        "son_odeme_gunu": sot, 
                        "notlar": not_icerik, 
                        "eklenme_tarihi": tarih_str, 
                        "son_guncelleme": tarih_str
                    })
            
            SoundManager.play_add(); self.dm.snapshot(); self.borc_listesi_guncelle(animate=False); self.sag_panel_guncelle(); Components.fade_out(d)

        Components.create_btn(alt_frame, "İPTAL ET", Theme.BG2, Theme.FW, lambda: Components.fade_out(d), fs=11, py=12, hbg=Theme.BG3).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        Components.create_btn(alt_frame, "✅ KAYDET", Theme.BLU, "white", kaydet_borc, fs=11, py=12, hbg="#2277CC").pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))
        d.update_idletasks()

    def borc_sag_tik(self, x, y, idx=None):
        ContextMenu._cleanup(self)
        if self.secili_tarih != str(date.today()): SoundManager.play_error(); return 
        if not self.dm.veriler["borclar"]: return
        try:
            if getattr(self, 'borc_toplu_mod', False) and self.borc_secili:
                options = [
                    ("🔄 Toplu Güncelle", Theme.FW, self.borc_islem_modal),
                    ("🗑 Toplu Sil", Theme.RED, self.borc_sil)
                ]
                ContextMenu.show(self, x, y, options)
            else:
                if idx is None: return
                self.borc_selected_idx = idx; self.hedef_selected_idx = None
                self.borc_listesi_guncelle(animate=False); self.hedef_listesi_guncelle(animate=False); self.sag_panel_guncelle()
                options = [
                    ("ℹ️ Düzenle / Detay", Theme.FW, lambda: self.borc_islem_modal(idx)),
                    ("💰 Öde", Theme.GRN, self.borc_ode),
                    ("🗑 Sil", Theme.RED, self.borc_sil)
                ]
                ContextMenu.show(self, x, y, options)
        except: pass

    def borc_ode(self):
        if self.secili_tarih != str(date.today()): SoundManager.play_error(); return
        if not self.dm.veriler["borclar"]: SoundManager.play_error(); return
        
        indices = list(self.borc_secili) if getattr(self, 'borc_toplu_mod', False) and self.borc_secili else [self.borc_selected_idx] if getattr(self, 'borc_selected_idx', None) is not None else []
        if not indices: SoundManager.play_error(); return

        is_single = len(indices) == 1
        d = tk.Toplevel(self); d.title("Ödeme Yap")
        modal_w = 640 if not is_single else 580
        modal_h = 630 if not is_single else 540
        d.resizable(False, False)
        d.attributes("-alpha", 0.0); Components.fade_in(d); Components.center_window(d, modal_w, modal_h)
        d.configure(bg=Theme.BG); d.transient(self); d.grab_set()
        
        d.columnconfigure(0, weight=1)
        d.rowconfigure(1, weight=1)

        top_f = tk.Frame(d, bg=Theme.BG1)
        top_f.grid(row=0, column=0, sticky="ew")
        tk.Frame(top_f, bg=Theme.GRN, height=3).pack(fill=tk.X)
        hdr = tk.Frame(top_f, bg=Theme.BG1, padx=24, pady=20)
        hdr.pack(fill=tk.X)
        
        baslik_text = "💰 Ödeme Yap" if is_single else "💰 Toplu Ödeme İşlemi"
        tk.Label(hdr, text=baslik_text, font=(F,18,"bold"), bg=Theme.BG1, fg=Theme.FW).pack(side=tk.LEFT)
        toplam_borc_secili = sum(self.dm.veriler["borclar"][i]["kalan"] for i in indices)
        tk.Label(hdr, text=f"Seçili Toplam: {para(toplam_borc_secili)}", font=(F,10,"bold"), bg=Theme.BG1, fg=Theme.FL).pack(side=tk.RIGHT)
        Components.create_sep(top_f, py=0)

        scroll_c = CustomScrollableFrame(d, bg_color=Theme.BG)
        scroll_c.grid(row=1, column=0, sticky="nsew", padx=2, pady=2)
        inner = scroll_c.scrollable_window

        btn_f = tk.Frame(d, bg=Theme.BG1, pady=10, padx=25)
        btn_f.grid(row=2, column=0, sticky="ew")

        entries_list = []

        for i, idx in enumerate(indices):
            if idx >= len(self.dm.veriler["borclar"]): continue
            borc = self.dm.veriler["borclar"][idx]
            max_v = borc["kalan"]
            sync_flag = {"is_updating": False} 
            
            wrap = tk.Frame(inner, bg=Theme.BG)
            wrap.pack(fill=tk.X, padx=24, pady=12)
            
            block = tk.Frame(wrap, bg=Theme.BG1, highlightthickness=0)
            block.pack(fill=tk.X)
            
            b_hdr = tk.Frame(block, bg=Theme.BG1, padx=16, pady=16)
            b_hdr.pack(fill=tk.X)
            Components.draw_bank_logo(b_hdr, borc['isim'], 24, Theme.BG1, 14)
            isim_kismi = tk.Frame(b_hdr, bg=Theme.BG1); isim_kismi.pack(side=tk.LEFT, padx=(4,0))
            tk.Label(isim_kismi, text=f"{borc['isim']}", font=(F,13,"bold"), bg=Theme.BG1, fg=Theme.FW).pack(anchor="w")
            if borc.get('tur'): tk.Label(isim_kismi, text=f"{borc['tur']}", font=(F,9), bg=Theme.BG1, fg=Theme.FL).pack(anchor="w")
            
            badge = tk.Frame(b_hdr, bg=Theme.RED2, padx=10, pady=6, highlightthickness=1, highlightbackground="#4A1020")
            badge.pack(side=tk.RIGHT)
            tk.Label(badge, text=f"Kalan Borç: {para(max_v)}", font=(F,10,"bold"), bg=Theme.RED2, fg=Theme.RED).pack()

            dt_f = tk.Frame(block, bg=Theme.BG1, padx=20)
            dt_f.pack(fill=tk.X, pady=(0,10))
            eklenme = tarih_formatla(borc.get("eklenme_tarihi", "Bilinmiyor"))
            guncelleme = tarih_formatla(borc.get("son_guncelleme", "Bilinmiyor"))
            tk.Label(dt_f, text=f"Eklenme: {eklenme}  |  Son Güncelleme: {guncelleme}", font=(F,8), bg=Theme.BG1, fg=Theme.FG).pack(anchor="w")
            
            input_area = tk.Frame(block, bg=Theme.BG2, padx=20, pady=20)
            input_area.pack(fill=tk.X)
            
            grid_f = tk.Frame(input_area, bg=Theme.BG2)
            grid_f.pack(fill=tk.X)
            grid_f.columnconfigure(0, weight=1)
            grid_f.columnconfigure(1, minsize=20) 
            grid_f.columnconfigure(2, weight=1)
            
            tk.Label(grid_f, text="Ödenecek Tutar (Net)", font=(F,10,"bold"), bg=Theme.BG2, fg=Theme.FW).grid(row=0, column=0, sticky="w", pady=(0,5))
            
            amt_out = tk.Frame(grid_f, bg=Theme.BG2)
            amt_out.grid(row=1, column=0, sticky="ew")
            amt_border, amt_inner, entry_amt = Components.build_safe_entry(amt_out, Theme.BG2, Theme.GRN, (F, 16, "bold"), justify="left")
            amt_border.config(bg=Theme.GRN)
            Components.apply_focus_glow(amt_border, entry_amt, Theme.GRN, Theme.GRN)
            tk.Label(amt_inner, text="₺", font=(F, 16, "bold"), bg=Theme.BG2, fg=Theme.GRN).pack(side=tk.LEFT, padx=(10,0), before=entry_amt)
            
            tk.Label(grid_f, text="Ödenecek Yüzde (%)", font=(F,9,"bold"), bg=Theme.BG2, fg=Theme.FL).grid(row=0, column=2, sticky="w", pady=(0,5))
            
            pct_out = tk.Frame(grid_f, bg=Theme.BG2)
            pct_out.grid(row=1, column=2, sticky="ew")
            pct_border, pct_inner, entry_pct = Components.build_safe_entry(pct_out, Theme.BG, Theme.CYAN, (F, 16, "bold"), justify="left")

            pct_border.config(bg=Theme.CYAN)
            Components.apply_focus_glow(pct_border, entry_pct, Theme.CYAN, Theme.CYAN)


            tk.Label(pct_inner, text="%", font=(F, 16, "bold"), bg=Theme.BG, fg=Theme.CYAN).pack(side=tk.LEFT, before=entry_pct)
            
            preset_f = tk.Frame(input_area, bg=Theme.BG2)
            preset_f.pack(fill=tk.X, pady=(15,0))
            
            dyn_lbl_f = tk.Frame(input_area, bg=Theme.BG2)
            kalan_dyn_lbl = tk.Label(dyn_lbl_f, text=f"Ödeme Sonrası Kalacak: {para(max_v)}", font=(F,10,"bold"), bg=Theme.BG2, fg=Theme.ORN)
            
            p_bg = tk.Frame(input_area, bg=Theme.BG1, height=6)
            p_fill = tk.Frame(p_bg, bg=Theme.GRN)
            p_fill.place(relx=0, rely=0, relwidth=0, relheight=1)

            def make_callbacks(mv, ent_a, ent_p, kl, pf, s_flag):
                def create_preset_btn(parent, text, val_pct):
                    def apply_p():
                        if s_flag["is_updating"]: return
                        s_flag["is_updating"] = True
                        amt_val = int((val_pct / 100.0) * mv)
                        
                        def fmt_p(x): return f"{x:.1f}".rstrip('0').rstrip('.')
                        def fmt_a(x): return f"{int(x):,}".replace(",", ".")
                        
                        curr_a = sayi(ent_a.get()) or 0
                        curr_p = float(ent_p.get().replace(',','.') or 0)
                        
                        Components.animate_entry_value(ent_p, curr_p, val_pct, fmt_p, duration=200)
                        Components.animate_entry_value(ent_a, curr_a, amt_val, fmt_a, duration=200)
                        
                        kl.config(text=f"Ödeme Sonrası Kalacak: {para(max(0, mv - amt_val))}")
                        Components.animate_progress_bar(pf, (amt_val/mv if mv>0 else 0), duration=250)
                        s_flag["is_updating"] = False
                        
                    b = tk.Label(parent, text=text, font=(F,10,"bold"), bg=Theme.BG3, fg=Theme.FW, cursor=Theme.CURSOR, padx=14, pady=6)
                    b.pack(side=tk.LEFT, padx=(0, 6))
                    b.bind("<Button-1>", lambda e: apply_p())
                    b.bind("<Enter>", lambda e, w=b: (Components.animate_bg_color(w, Theme.BLU, 150), w.config(fg=Theme.BG1)))
                    b.bind("<Leave>", lambda e, w=b: (Components.animate_bg_color(w, Theme.BG3, 150), w.config(fg=Theme.FW)))
                    return apply_p 

                def on_amt_key(e):
                    if s_flag["is_updating"]: return
                    s_flag["is_updating"] = True
                    
                    raw = "".join(filter(str.isdigit, ent_a.get()))
                    if not raw:
                        ent_a.delete(0, tk.END); ent_p.delete(0, tk.END)
                        kl.config(text=f"Ödeme Sonrası Kalacak: {para(mv)}")
                        Components.animate_progress_bar(pf, 0, 150)
                    else:
                        val = int(raw)
                        if val > mv: val = mv
                        
                        formatted = f"{val:,}".replace(",", ".")
                        pos = ent_a.index(tk.INSERT)
                        old_len = len(ent_a.get())
                        ent_a.delete(0, tk.END)
                        ent_a.insert(0, formatted)
                        new_len = len(formatted)
                        ent_a.icursor(max(0, pos + (new_len - old_len)))
                        
                        pct = (val / mv) * 100
                        def fmt_p(x): return f"{x:.1f}".rstrip('0').rstrip('.')
                        curr_p = float(ent_p.get().replace(',','.') or 0)
                        Components.animate_entry_value(ent_p, curr_p, pct, fmt_p, duration=150)
                        
                        kl.config(text=f"Ödeme Sonrası Kalacak: {para(mv - val)}")
                        Components.animate_progress_bar(pf, (val/mv if mv>0 else 0), 150)
                        
                    s_flag["is_updating"] = False

                def on_pct_key(e):
                    if s_flag["is_updating"]: return
                    s_flag["is_updating"] = True
                    
                    raw = ent_p.get().replace('%', '').replace(',', '.')
                    if raw == "" or raw == ".":
                        ent_a.delete(0, tk.END)
                        kl.config(text=f"Ödeme Sonrası Kalacak: {para(mv)}")
                        Components.animate_progress_bar(pf, 0, 150)
                    else:
                        try:
                            p = float(raw)
                            if p > 100: 
                                p = 100.0
                                ent_p.delete(0, tk.END)
                                ent_p.insert(0, "100")
                            
                            val = int((p / 100.0) * mv)
                            def fmt_a(x): return f"{int(x):,}".replace(",", ".")
                            curr_a = sayi(ent_a.get()) or 0
                            Components.animate_entry_value(ent_a, curr_a, val, fmt_a, duration=150)
                            
                            kl.config(text=f"Ödeme Sonrası Kalacak: {para(mv - val)}")
                            Components.animate_progress_bar(pf, (val/mv if mv>0 else 0), 150)
                        except ValueError: pass
                    s_flag["is_updating"] = False
                    
                return create_preset_btn, on_amt_key, on_pct_key
                
            c_preset, c_amt_key, c_pct_key = make_callbacks(max_v, entry_amt, entry_pct, kalan_dyn_lbl, p_fill, sync_flag)
            
            tk.Label(preset_f, text="⚡ Yüzdesel Ödeme", font=(F,9,"bold"), bg=Theme.BG2, fg=Theme.FL).pack(anchor="w", pady=(0,6))
            
            pct_btns_f = tk.Frame(preset_f, bg=Theme.BG2)
            pct_btns_f.pack(fill=tk.X)
            
            asg_p = 40 if max_v >= 50000 else 20
            for ptext, pval in [(f"⚡ Asgari (%{asg_p})", asg_p), ("1/2 Yarısı (%50)", 50), ("3/4 %75", 75), ("✅  TAMAMINI ÖDE", 100)]:
                pb = tk.Label(pct_btns_f, text=ptext, font=(F,10,"bold"), bg=Theme.BG3, fg=Theme.FW, cursor=Theme.CURSOR, pady=6)
                pb.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
                cmd_fn = c_preset(tk.Frame(), "x", pval)  
                pb.bind("<Button-1>", lambda e, fn=cmd_fn: fn())
                pb.bind("<Enter>", lambda e, w=pb: (Components.animate_bg_color(w, Theme.BLU, 150), w.config(fg=Theme.BG1)))
                pb.bind("<Leave>", lambda e, w=pb: (Components.animate_bg_color(w, Theme.BG3, 150), w.config(fg=Theme.FW)))
            tamami_cmd = c_preset(tk.Frame(), "x", 100)
            
            net_title_f = tk.Frame(input_area, bg=Theme.BG2)
            net_title_f.pack(fill=tk.X, pady=(12,5))
            tk.Label(net_title_f, text="💵 Net Miktar", font=(F,9,"bold"), bg=Theme.BG2, fg=Theme.FL).pack(side=tk.LEFT)
            
            net_btn_f = tk.Frame(input_area, bg=Theme.BG2)
            net_btn_f.pack(fill=tk.X, pady=(0, 0))
            
            def set_n(v, mv=max_v, ent_a=entry_amt, ent_p=entry_pct, kl=kalan_dyn_lbl, pf=p_fill, sf=sync_flag):
                if sf["is_updating"]: return
                sf["is_updating"] = True
                val = min(int(v), mv)
                pct = (val / mv) * 100 if mv > 0 else 0
                def fmt_p(x): return f"{x:.1f}".rstrip('0').rstrip('.')
                def fmt_a(x): return f"{int(x):,}".replace(",", ".")
                curr_a = sayi(ent_a.get()) or 0
                curr_p = float(ent_p.get().replace(',','.') or 0)
                Components.animate_entry_value(ent_p, curr_p, pct, fmt_p, duration=200)
                Components.animate_entry_value(ent_a, curr_a, val, fmt_a, duration=200)
                kl.config(text=f"Ödeme Sonrası Kalacak: {para(max(0, mv - val))}")
                Components.animate_progress_bar(pf, (val/mv if mv>0 else 0), duration=250)
                sf["is_updating"] = False
            
            hm = self.dm.veriler.get("odeme_hizli_miktarlar", [1000, 2500, 5000, 10000])
            Components.create_quick_amounts(net_btn_f, hm, Theme.CYAN, Theme.CYAN, set_n)
            
            dyn_lbl_f.pack(fill=tk.X, pady=(15,0))
            tk.Label(dyn_lbl_f, text="Ödeme Etki Analizi", font=(F,9,"bold"), bg=Theme.BG2, fg=Theme.FG).pack(side=tk.LEFT)
            kalan_dyn_lbl.pack(side=tk.RIGHT)
            p_bg.pack(fill=tk.X, pady=(6,0))
            
            self.active_borc_modal_refresh = lambda: None
            
            entry_amt.bind("<KeyRelease>", c_amt_key)
            entry_pct.bind("<KeyRelease>", c_pct_key)

            if is_single: 
                sync_flag["is_updating"] = False 
                tamami_cmd() 
                d.after(100, lambda e=entry_amt: e.focus_set())
            
            entries_list.append((idx, entry_amt))

        def onayla():
            guncellemeler, odenen_var = [], False
            for idx, en in entries_list:
                val = en.get().replace('.', '').replace(',', '')
                m = sayi(val)
                if m and m > 0:
                    borc = self.dm.veriler["borclar"][idx]
                    odenen = min(m, borc["kalan"])
                    isimm = f"{borc['isim']} ({borc.get('tur', '')})" if borc.get('tur') else borc['isim']
                    self.dm.veriler.setdefault("odeme_gecmisi", []).append({
                        "tarih": str(date.today()), 
                        "isim": isimm, 
                        "miktar": odenen
                    })
                    guncellemeler.append((idx, odenen))
                    odenen_var = True
            
            if not odenen_var: SoundManager.play_error(); return
            
            SoundManager.play_cash()
            for idx, m in sorted(guncellemeler, key=lambda x: x[0], reverse=True):
                b = self.dm.veriler["borclar"][idx]
                if m >= b["kalan"]: del self.dm.veriler["borclar"][idx]
                else: 
                    b["kalan"] -= m
                    b["odenen_toplam"] = b.get("odenen_toplam", 0) + m
                    b["son_guncelleme"] = str(datetime.now()) 
            
            if getattr(self, 'borc_toplu_mod', False): self._reset_toplu_mod(True)
            self.dm.snapshot(); self.borc_listesi_guncelle(animate=False); self.sag_panel_guncelle(); Components.fade_out(d)

        Components.create_btn(btn_f, "💰  ÖDEMEYİ ONAYLA", Theme.GRN, "#000", onayla, fs=12, py=14, hbg="#00B070").pack(fill=tk.X)
        if entries_list: entries_list[-1][1].bind("<Return>", lambda e: onayla())
        
        d.update_idletasks()

    def borc_sil(self):
        if self.secili_tarih != str(date.today()): SoundManager.play_error(); return
        if not self.dm.veriler["borclar"]: return

        indices = list(self.borc_secili) if getattr(self, 'borc_toplu_mod', False) and self.borc_secili else [self.borc_selected_idx] if getattr(self, 'borc_selected_idx', None) is not None else []
        if not indices: SoundManager.play_error(); return
        
        isimler = [self.dm.veriler["borclar"][i]["isim"] for i in indices]
        msg = f"Seçili {len(isimler)} adet borç kalıcı olarak silinsin mi?" if len(isimler) > 1 else f"'{isimler[0]}' silinsin mi?"
        
        if messagebox.askyesno("Borç Sil", msg, parent=self):
            for idx in sorted(indices, reverse=True): del self.dm.veriler["borclar"][idx]
            if getattr(self, 'borc_toplu_mod', False): self._reset_toplu_mod(True)
            self.borc_selected_idx = None 
            self.dm.snapshot(); self.borc_listesi_guncelle(animate=False); self.sag_panel_guncelle(); SoundManager.play_delete()

    def odenenler_goster(self):
        d = tk.Toplevel(self); d.title("Ödeme Geçmişi"); Components.center_window(d, 480, 520); d.configure(bg=Theme.BG1); d.transient(self); d.attributes("-alpha", 0.0); Components.fade_in(d)
        tk.Frame(d, bg=Theme.GRN, height=2).pack(fill=tk.X)
        tk.Label(d, text="💸 Ödeme Geçmişi", font=(F,14,"bold"), bg=Theme.BG1, fg=Theme.GRN, pady=16).pack()
        Components.create_sep(d)

        gecmis = self.dm.veriler.get("odeme_gecmisi", [])
        list_frame = tk.Frame(d, bg=Theme.BG2); list_frame.pack(fill=tk.BOTH, expand=True, padx=14, pady=14)
        scroll_frame = CustomScrollableFrame(list_frame, bg_color=Theme.BG2)
        scroll_frame.pack(fill=tk.BOTH, expand=True)

        if not gecmis:
            tk.Label(scroll_frame.scrollable_window, text="   Kayıt bulunamadı.", bg=Theme.BG2, fg=Theme.FL, font=(F,10)).pack(anchor="w", pady=10)
        else:
            gecmis.sort(key=lambda x: x["tarih"], reverse=True)
            toplam = sum(g["miktar"] for g in gecmis)
            tk.Label(scroll_frame.scrollable_window, text=f"   TOPLAM ÖDENDİ  ·  {para(toplam)}", bg=Theme.BG2, fg=Theme.GRN, font=(F,11,"bold")).pack(anchor="w", pady=(10, 5))
            
            for item in gecmis:
                row = tk.Frame(scroll_frame.scrollable_window, bg=Theme.BG2)
                row.pack(fill=tk.X, pady=3, anchor="w")
                tk.Label(row, text=f"   📅 {item['tarih']}   ·   ", bg=Theme.BG2, fg=Theme.FL, font=(F,10)).pack(side=tk.LEFT)
                saf_isim = item['isim'].split(' (')[0] if '(' in item['isim'] else item['isim']
                Components.draw_bank_logo(row, saf_isim, 18, Theme.BG2, 10)
                tk.Label(row, text=f" {item['isim']}   ·   {para(item['miktar'])}", bg=Theme.BG2, fg=Theme.FW, font=(F,10)).pack(side=tk.LEFT)

    def hedef_sag_tik(self, x, y, idx=None):
        ContextMenu._cleanup(self)
        if self.secili_tarih != str(date.today()): SoundManager.play_error(); return 
        if not self.dm.veriler["alinacaklar"]: return
        try:
            if getattr(self, 'hedef_toplu_mod', False) and self.hedef_secili:
                options = [("🗑 Toplu Sil", Theme.RED, self.hedef_sil)]
                ContextMenu.show(self, x, y, options)
            else:
                if idx is None: return
                self.hedef_selected_idx = idx; self.borc_selected_idx = None
                self.borc_listesi_guncelle(animate=False); self.hedef_listesi_guncelle(animate=False); self.sag_panel_guncelle()
                options = [
                    ("ℹ️ Düzenle", Theme.FW, lambda: self.hedef_islem_modal(idx)),
                    ("✅ Tamamla", Theme.GRN, self.hedef_tamamla),
                    ("🗑 Sil", Theme.RED, self.hedef_sil)
                ]
                ContextMenu.show(self, x, y, options)
        except: pass

    def hedef_islem_modal(self, h_idx=None):
        if self.secili_tarih != str(date.today()): SoundManager.play_error(); return
        is_edit = h_idx is not None
        if not is_edit and getattr(self, 'hedef_toplu_mod', False) and self.hedef_secili:
            is_edit, h_idx = True, list(self.hedef_secili)[0]

        d = tk.Toplevel(self); d.title("Hedef Düzenle" if is_edit else "Yeni Hedef")
        Components.center_window(d, 450, 340); d.configure(bg=Theme.BG1); d.transient(self); d.grab_set()
        d.attributes("-alpha", 0.0); Components.fade_in(d)
        
        tk.Frame(d, bg=Theme.BLU, height=3).pack(fill=tk.X); hdr = tk.Frame(d, bg=Theme.BG1, padx=22, pady=16); hdr.pack(fill=tk.X)
        tk.Label(hdr, text="🎯 Hedef Düzenle" if is_edit else "🎯 Yeni Hedef Ekle", font=(F,16,"bold"), bg=Theme.BG1, fg=Theme.BLU).pack(anchor="w"); Components.create_sep(d, c=Theme.LINE, py=0)

        hedef_data = {}
        if is_edit and h_idx is not None and h_idx < len(self.dm.veriler["alinacaklar"]):
            hedef_data = self.dm.veriler["alinacaklar"][h_idx]

        eski_kategori = hedef_data.get("kategori", "alinacak")
        if eski_kategori == "maddi": eski_kategori = "alinacak"
        if eski_kategori == "manevi": eski_kategori = "yapilacak"
        
        hedef_tipi = tk.StringVar(value=eski_kategori)
        
        tip_container = tk.Frame(d, bg=Theme.BG1); tip_container.pack(fill=tk.X, padx=24, pady=(20,10))
        btn_alinacak = tk.Label(tip_container, text="💸  Alınacak", font=(F,11,"bold"), bg=Theme.BG2, fg=Theme.FW, cursor=Theme.CURSOR, pady=10); btn_alinacak.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        btn_yapilacak = tk.Label(tip_container, text="📌  Yapılacak", font=(F,11,"bold"), bg=Theme.BG2, fg=Theme.FW, cursor=Theme.CURSOR, pady=10); btn_yapilacak.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5,0))

        def sec_alinacak(e=None):
            hedef_tipi.set("alinacak"); btn_alinacak.config(bg=Theme.BLU, fg="#000"); btn_yapilacak.config(bg=Theme.BG2, fg=Theme.FW)
        def sec_yapilacak(e=None):
            hedef_tipi.set("yapilacak"); btn_yapilacak.config(bg=Theme.BLU, fg="#000"); btn_alinacak.config(bg=Theme.BG2, fg=Theme.FW)
        
        btn_alinacak.bind("<Button-1>", sec_alinacak); btn_yapilacak.bind("<Button-1>", sec_yapilacak)
        
        if hedef_tipi.get() == "yapilacak": sec_yapilacak()
        else: sec_alinacak()

        tk.Label(d, text="Hedef Adı:", font=(F,10,"bold"), bg=Theme.BG1, fg=Theme.FL, anchor="w").pack(fill=tk.X, padx=24, pady=(15,4))
        
        n_out = tk.Frame(d, bg=Theme.BG1); n_out.pack(fill=tk.X, padx=24)
        
        n_inner = tk.Frame(n_out, bg=Theme.BG2)
        n_inner.pack(fill=tk.BOTH, expand=True)
        ne = tk.Entry(n_inner, bg=Theme.BG2, fg=Theme.FW, font=(F,14), bd=0, highlightthickness=0, insertbackground=Theme.FW)
        ne.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        
        if hedef_data.get("isim"): ne.insert(0, hedef_data["isim"])
        ne.focus()

        tk.Label(d, text="(Yeni bir dil, Yeni bir iş, Okul mezuniyeti, Herhangi bir pozitif alışkanlık.)", font=(F,9), bg=Theme.BG1, fg=Theme.FG).pack(fill=tk.X, padx=24, pady=(6,0))

        def onayla():
            isim = ne.get().strip(); 
            if not isim: return
            
            target_indices = list(self.hedef_secili) if getattr(self, 'hedef_toplu_mod', False) else ([h_idx] if h_idx is not None else [])
            tarih_str = str(datetime.now())
            
            if target_indices:
                for idx in target_indices:
                    if idx < len(self.dm.veriler["alinacaklar"]):
                        self.dm.veriler["alinacaklar"][idx]["isim"] = isim
                        self.dm.veriler["alinacaklar"][idx]["kategori"] = hedef_tipi.get()
                        if "miktar" in self.dm.veriler["alinacaklar"][idx]:
                            del self.dm.veriler["alinacaklar"][idx]["miktar"]
            else:
                self.dm.veriler["alinacaklar"].append({
                    "isim": isim, 
                    "kategori": hedef_tipi.get(),
                    "eklenme_tarihi": tarih_str
                })
                
            SoundManager.play_add(); self.dm.snapshot(); self.hedef_listesi_guncelle(animate=False); self.sag_panel_guncelle(); Components.fade_out(d)

        ne.bind("<Return>", lambda e: onayla())
        
        alt_frame = tk.Frame(d, bg=Theme.BG1); alt_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=15)
        btn_frame = tk.Frame(alt_frame, bg=Theme.BG1, padx=24); btn_frame.pack(fill=tk.X)
        Components.create_btn(btn_frame,"✅  KAYDET", Theme.BLU, "white", onayla, fs=12, py=14, hbg="#2277CC").pack(fill=tk.X)

    def hedef_tamamla(self, idx=None):
        if self.secili_tarih != str(date.today()): return
        if not self.dm.veriler["alinacaklar"]: return

        indices = list(self.hedef_secili) if getattr(self, 'hedef_toplu_mod', False) and self.hedef_secili else [idx] if idx is not None else [self.hedef_selected_idx] if getattr(self, 'hedef_selected_idx', None) is not None else []
        if not indices: return

        isimler = [self.dm.veriler["alinacaklar"][i]["isim"] for i in indices]
        msg = f"Seçili {len(isimler)} hedef tamamlandı olarak işaretlensin mi?" if len(isimler) > 1 else f"'{isimler[0]}' tamamlandı mı?"
        
        if messagebox.askyesno("Tamamlandı 🎉", msg, parent=self):
            for i in sorted(indices, reverse=True): del self.dm.veriler["alinacaklar"][i]
            if getattr(self, 'hedef_toplu_mod', False): self._reset_toplu_mod(False)
            self.hedef_selected_idx = None
            self.dm.snapshot(); self.hedef_listesi_guncelle(animate=False); self.sag_panel_guncelle(); SoundManager.play_success()

    def hedef_sil(self):
        if self.secili_tarih != str(date.today()): SoundManager.play_error(); return
        if not self.dm.veriler["alinacaklar"]: return

        indices = list(self.hedef_secili) if getattr(self, 'hedef_toplu_mod', False) and self.hedef_secili else [self.hedef_selected_idx] if getattr(self, 'hedef_selected_idx', None) is not None else []
        if not indices: return
        
        isimler = [self.dm.veriler["alinacaklar"][i]["isim"] for i in indices]
        msg = f"Seçili {len(isimler)} adet hedef silinsin mi?" if len(isimler) > 1 else f"'{isimler[0]}' adlı hedef silinsin mi?"
        
        if messagebox.askyesno("Hedef Sil", msg, parent=self):
            for idx in sorted(indices, reverse=True): del self.dm.veriler["alinacaklar"][idx]
            if getattr(self, 'hedef_toplu_mod', False): self._reset_toplu_mod(False)
            self.hedef_selected_idx = None
            self.dm.snapshot(); self.hedef_listesi_guncelle(animate=False); self.sag_panel_guncelle(); SoundManager.play_delete()

    def show_chart(self):
        if hasattr(self, 'chart_window') and self.chart_window.winfo_exists(): self.chart_window.lift(); self.chart_window.focus_force(); return
        if not self.dm.veriler["borclar"]: return
        
        d = tk.Toplevel(self); d.title("Dağılım"); Components.center_window(d, 540, 640); d.configure(bg=Theme.BG); d.transient(self); d.attributes("-alpha", 0.0)
        self.chart_window = d; Components.fade_in(d)
        
        tk.Label(d, text="📊  Borç Dağılımı", font=(F,16,"bold"), bg=Theme.BG, fg=Theme.FW, pady=18).pack()
        
        cs = 340; cv = tk.Canvas(d, width=cs, height=cs, bg=Theme.BG, highlightthickness=0); cv.pack()
        blist = [b for b in self.dm.veriler["borclar"] if b["kalan"]>0]; toplam = sum(b["kalan"] for b in blist)
        renkler = [Theme.RED, Theme.BLU, Theme.ORN, Theme.PRP, Theme.GRN, Theme.ROSE, Theme.CYAN, Theme.GLD]
        cx = cy = cs//2; R=150; r=62; arcs_data, a = [], -90
        
        for i, b in enumerate(blist):
            ext = min((b["kalan"]/toplam)*360, 359.99); col, pct = renkler[i % len(renkler)], (b["kalan"]/toplam)*100
            arc_id = cv.create_arc(cx-R, cy-R, cx+R, cy+R, start=a, extent=0, fill=col, outline=Theme.BG, width=3)
            arcs_data.append({"id":arc_id,"ext":ext,"isim":f"{b['isim']}\n[{b.get('tur', '')}]" if b.get('tur') else b['isim'],"kalan":b["kalan"],"pct":pct,"col":col}); a += ext

        cv.create_oval(cx-r, cy-r, cx+r, cy+r, fill=Theme.BG, outline=Theme.BG1, width=2, tags=("hole",))
        lbl_top = cv.create_text(cx, cy-14, text="TOPLAM", font=(F,9), fill=Theme.FG, tags=("text",))
        lbl_bot = cv.create_text(cx, cy+10, text=para(toplam), font=(F,12,"bold"), fill=Theme.FW, tags=("text",))
        animasyon_durumu = {"bitti": False, "clicked": None}

        def hex_dim(hex_col):
            hex_col = hex_col.lstrip('#')
            return '#' + ''.join([f"{int(max(0, int(hex_col[i:i+2], 16) * 0.4)):02x}" for i in (0, 2, 4)])

        def interpolate_color(c1, c2, factor):
            c1 = c1.lstrip('#'); c2 = c2.lstrip('#')
            if len(c1) != 6 or len(c2) != 6: return "#" + c2
            r1, g1, b1 = int(c1[0:2], 16), int(c1[2:4], 16), int(c1[4:6], 16)
            r2, g2, b2 = int(c2[0:2], 16), int(c2[2:4], 16), int(c2[4:6], 16)
            r = int(r1 + (r2 - r1) * factor); g = int(g1 + (g2 - g1) * factor); b = int(b1 + (b2 - b1) * factor)
            return f"#{max(0,min(255,r)):02x}{max(0,min(255,g)):02x}{max(0,min(255,b)):02x}"

        def animate_colors(target_colors, step=0):
            if not d.winfo_exists(): return
            factor = min(1.0, step / 15.0)
            for a_id, (start_col, end_col) in target_colors.items(): cv.itemconfig(a_id, fill=interpolate_color(start_col, end_col, factor))
            if step < 15: d.after(16, lambda: animate_colors(target_colors, step+1))

        def on_enter_slice(event, arc_info):
            if not animasyon_durumu["bitti"]: return
            if animasyon_durumu["clicked"] and animasyon_durumu["clicked"] != arc_info["id"]: return
            cv.itemconfig(arc_info["id"], outline=Theme.FW, width=4); cv.itemconfig(lbl_top, text=arc_info["isim"], fill=arc_info["col"], font=(F,9,"bold"))
            cv.itemconfig(lbl_bot, text=f"%{arc_info['pct']:.1f}\n{para(arc_info['kalan'])}", font=(F,10,"bold")); cv.tag_raise(arc_info["id"]); cv.tag_raise("hole"); cv.tag_raise("text")

        def on_leave_slice(event, arc_info):
            if not animasyon_durumu["bitti"]: return
            if animasyon_durumu["clicked"]: return
            cv.itemconfig(arc_info["id"], outline=Theme.BG, width=3); cv.itemconfig(lbl_top, text="TOPLAM", fill=Theme.FG, font=(F,9))
            cv.itemconfig(lbl_bot, text=para(toplam), font=(F,12,"bold"), fill=Theme.FW)

        list_rows = []
        def update_list_focus():
            clicked_id = animasyon_durumu["clicked"]
            for lr in list_rows:
                is_selected = clicked_id == lr["arc_id"]; any_selected = clicked_id is not None
                if is_selected: bg_col, fw_col = Theme.SEL_BG, Theme.FW
                elif any_selected: bg_col, fw_col = Theme.BG, Theme.FL
                else: bg_col, fw_col = Theme.BG, Theme.FW
                lr["row"].config(bg=bg_col)
                for child in lr["row"].winfo_children():
                    child.config(bg=bg_col)
                    if child in [lr["l_name"], lr["l_val"]]: child.config(fg=fw_col)

        def on_click_slice(event, arc_info):
            if not animasyon_durumu["bitti"]: return
            target_colors = {}
            if animasyon_durumu["clicked"] == arc_info["id"]:
                animasyon_durumu["clicked"] = None
                for a in arcs_data: target_colors[a["id"]] = (cv.itemcget(a["id"], "fill"), a["col"])
                on_leave_slice(event, arc_info)
            else:
                animasyon_durumu["clicked"] = arc_info["id"]
                for a in arcs_data:
                    curr = cv.itemcget(a["id"], "fill")
                    if a["id"] != arc_info["id"]: target_colors[a["id"]] = (curr, hex_dim(a["col"])); cv.itemconfig(a["id"], outline=Theme.BG, width=3)
                    else: target_colors[a["id"]] = (curr, a["col"])
                on_enter_slice(event, arc_info)
            animate_colors(target_colors, 0); update_list_focus()

        def on_enter_row(e, lr, a_info):
            if not animasyon_durumu["bitti"]: return
            if animasyon_durumu["clicked"] and animasyon_durumu["clicked"] != a_info["id"]: return
            lr["row"].config(bg=Theme.BG3)
            for child in lr["row"].winfo_children(): child.config(bg=Theme.BG3)
            on_enter_slice(None, a_info)

        def on_leave_row(e, lr, a_info):
            if not animasyon_durumu["bitti"]: return
            update_list_focus(); on_leave_slice(None, a_info)

        for arc in arcs_data: 
            cv.tag_bind(arc["id"], "<Enter>", lambda e, a=arc: on_enter_slice(e, a)); cv.tag_bind(arc["id"], "<Leave>", lambda e, a=arc: on_leave_slice(e, a))
            cv.tag_bind(arc["id"], "<Button-1>", lambda e, a=arc: on_click_slice(e, a))

        def animate_arcs(step=0):
            if not d.winfo_exists(): return
            if step <= 40:
                for arc in arcs_data: cv.itemconfig(arc["id"], extent=arc["ext"]*(1-(1-step/40)**3))
                d.after(14, lambda: animate_arcs(step+1))
            else:
                for arc in arcs_data: cv.itemconfig(arc["id"], extent=arc["ext"])
                animasyon_durumu["bitti"] = True; update_list_focus()
                
        d.after(200, animate_arcs)
        ac = tk.Frame(d, bg=Theme.BG); ac.pack(fill=tk.X, padx=28, pady=(8,22))
        for i, b in enumerate(blist):
            row = tk.Frame(ac, bg=Theme.BG, cursor=Theme.CURSOR); row.pack(fill=tk.X, pady=3)
            l_icon = tk.Label(row, text="■", bg=Theme.BG, fg=renkler[i % len(renkler)], font=(F,13)); l_icon.pack(side=tk.LEFT, padx=(0,8))
            Components.draw_bank_logo(row, b['isim'], 18, Theme.BG, 10)
            l_name = tk.Label(row, text=f"{b['isim']} [{b.get('tur', '')}]" if b.get('tur') else b['isim'], bg=Theme.BG, fg=Theme.FW, font=(F,9)); l_name.pack(side=tk.LEFT)
            l_val = tk.Label(row, text=f"%{(b['kalan']/toplam*100):.1f}  ·  {para(b['kalan'])}", bg=Theme.BG, fg=Theme.FW, font=(F,9,"bold")); l_val.pack(side=tk.RIGHT)
            tk.Frame(ac, bg=Theme.LINE, height=1).pack(fill=tk.X, pady=1)

            lr_dict = {"row": row, "l_icon": l_icon, "l_name": l_name, "l_val": l_val, "arc_id": arcs_data[i]["id"]}
            list_rows.append(lr_dict)
            self._bind_all_children(row, "<Enter>", lambda e, lr=lr_dict, a_info=arcs_data[i]: on_enter_row(e, lr, a_info))
            self._bind_all_children(row, "<Leave>", lambda e, lr=lr_dict, a_info=arcs_data[i]: on_leave_row(e, lr, a_info))
            self._bind_all_children(row, "<Button-1>", lambda e, a_info=arcs_data[i]: on_click_slice(None, a_info))

        update_list_focus()

if __name__ == "__main__":
    app = DashboardApp()