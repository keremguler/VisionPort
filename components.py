import tkinter as tk
import platform
from config import Theme, F, banka_bul, get_cached_logo
from core import SoundManager

# ============================================================
# UI BİLEŞENLERİ & HELPERLAR
# ============================================================
class ToolTip:
    def __init__(self, widget, text=""):
        self.widget = widget; self.text = text; self.tip = None; self.enabled = True
        self.widget.bind("<Enter>", self.show, add="+"); self.widget.bind("<Leave>", self.hide, add="+"); self.widget.bind("<Button-1>", self.hide, add="+")

    def show(self, event=None):
        if not self.enabled or not self.text: return
        if self.tip: return
        sw, sh = self.widget.winfo_screenwidth(), self.widget.winfo_screenheight()
        wx, wy = self.widget.winfo_rootx(), self.widget.winfo_rooty()
        ww, wh = self.widget.winfo_width(), self.widget.winfo_height()
        x, y = wx + (ww // 2) - 60, wy - 40 
        if y < 0: y = wy + wh + 12
        if x < 10: x = 10
        if x > sw - 200: x = sw - 200
        self.tip = tk.Toplevel(self.widget); self.tip.wm_overrideredirect(True); self.tip.wm_geometry(f"+{int(x)}+{int(y)}"); self.tip.attributes("-topmost", True); self.tip.attributes("-alpha", 1.0)
        outer = tk.Frame(self.tip, bg=Theme.LINE, padx=1, pady=1); outer.pack()
        tk.Label(outer, text=self.text, bg="#131325", fg="#F0F0FF", font=(F, 9), padx=12, pady=6, justify=tk.LEFT).pack()

    def hide(self, event=None):
        if self.tip: self.tip.destroy(); self.tip = None

class ContextMenu:
    _active_menu = None
    _bind_id = None
    
    @staticmethod
    def _cleanup(root=None):
        if ContextMenu._active_menu:
            try: ContextMenu._active_menu.destroy()
            except: pass
            ContextMenu._active_menu = None
        if root and ContextMenu._bind_id:
            try: 
                if hasattr(root, 'winfo_toplevel'):
                    tl = root.winfo_toplevel()
                    tl.unbind("<Button-1>", ContextMenu._bind_id)
                else:
                    root.unbind("<Button-1>", ContextMenu._bind_id)
            except: pass
            ContextMenu._bind_id = None
    
    @staticmethod
    def show(parent, x, y, options):
        root = parent.winfo_toplevel()
        ContextMenu._cleanup(root)
        
        menu = tk.Toplevel(parent)
        ContextMenu._active_menu = menu
        menu.wm_overrideredirect(True)
        menu.geometry(f"+{x}+{y}")
        menu.configure(bg=Theme.LINE)
        menu.attributes("-topmost", True)
        menu.attributes("-alpha", 0.0)
        Components.fade_in(menu, step=0.15, delay=10)
        
        inner = tk.Frame(menu, bg=Theme.BG2)
        inner.pack(padx=1, pady=1, fill=tk.BOTH, expand=True)
        
        def close_menu(e=None):
            if hasattr(menu, '_closing') and menu._closing: return
            menu._closing = True
            ContextMenu._active_menu = None
            if ContextMenu._bind_id:
                try: root.unbind("<Button-1>", ContextMenu._bind_id)
                except: pass
                ContextMenu._bind_id = None
            try: root.unbind("<Escape>")
            except: pass
            Components.fade_out(menu, step=0.2, delay=10)
        
        def on_root_click(e):
            try:
                mx, my = menu.winfo_rootx(), menu.winfo_rooty()
                mw, mh = menu.winfo_width(), menu.winfo_height()
                if not (mx <= e.x_root <= mx + mw and my <= e.y_root <= my + mh):
                    close_menu()
            except: close_menu()
        
        def bind_later():
            ContextMenu._bind_id = root.bind("<Button-1>", on_root_click, add="+")
        root.after(150, bind_later)
        root.bind("<Escape>", close_menu)
        
        for text, color, cmd in options:
            btn = tk.Label(inner, text=text, bg=Theme.BG2, fg=color, font=(F, 10, "bold"), anchor="w", padx=15, pady=10, cursor=Theme.CURSOR)
            btn.pack(fill=tk.X)
            
            def make_cmd(c=cmd):
                def wrapper(e):
                    close_menu()
                    parent.after(150, c)
                return wrapper
                
            btn.bind("<Button-1>", make_cmd())
            btn.bind("<Enter>", lambda e, w=btn: Components.animate_bg_color(w, Theme.SEL_BG, 150))
            btn.bind("<Leave>", lambda e, w=btn: Components.animate_bg_color(w, Theme.BG2, 150))
            
        menu.focus_set()

class CustomDropdown(tk.Frame):
    def __init__(self, parent, options, var, **kwargs):
        super().__init__(parent, bg=Theme.BG1, cursor=Theme.CURSOR, **kwargs)
        self.options = options
        self.var = var
        self.lbl = tk.Label(self, textvariable=self.var, bg=Theme.BG1, fg=Theme.FW, font=(F,10,"bold"), anchor="w")
        self.lbl.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=6)
        tk.Label(self, text="▼", bg=Theme.BG1, fg=Theme.FL, font=(F,8)).pack(side=tk.RIGHT, padx=8)
        self.bind("<Button-1>", self.toggle)
        self.lbl.bind("<Button-1>", self.toggle)
        self.menu_win = None

    def toggle(self, e=None):
        if self.menu_win:
            self.close_menu()
        else:
            tl = self.winfo_toplevel()
            self.menu_win = tk.Frame(tl, bg=Theme.BG2, highlightthickness=1, highlightbackground=Theme.LINE, highlightcolor=Theme.LINE)
            x = self.winfo_rootx() - tl.winfo_rootx()
            y = self.winfo_rooty() - tl.winfo_rooty() + self.winfo_height()
            self.menu_win.place(x=x, y=y, width=self.winfo_width())
            
            for opt in self.options:
                l = tk.Label(self.menu_win, text=opt, bg=Theme.BG2, fg=Theme.FW, font=(F,10,"bold"), anchor="w", pady=8, padx=12, cursor=Theme.CURSOR)
                l.pack(fill=tk.X)
                l.bind("<Enter>", lambda e, w=l: (Components.animate_bg_color(w, Theme.BLU, 150), w.config(fg=Theme.BG1)))
                l.bind("<Leave>", lambda e, w=l: (Components.animate_bg_color(w, Theme.BG2, 150), w.config(fg=Theme.FW)))
                l.bind("<Button-1>", lambda e, o=opt: self.select(o))

    def select(self, opt):
        self.var.set(opt)
        self.close_menu()

    def close_menu(self):
        if self.menu_win:
            self.menu_win.destroy()
            self.menu_win = None

class Components:
    @staticmethod
    def center_window(win, w, h):
        sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
        x, y = (sw - w) // 2, (sh - h) // 2
        win.geometry(f"{w}x{h}+{x}+{y}")

    @staticmethod
    def fade_in(win, step=0.08, delay=10):
        win.attributes("-alpha", 0.0)
        def fade(a=0.0):
            a += step
            if a < 1.0: win.attributes("-alpha", a); win.after(delay, lambda: fade(a))
            else: win.attributes("-alpha", 1.0)
        fade()

    @staticmethod
    def fade_out(win, step=0.08, delay=10, on_complete=None):
        def fade(a=1.0):
            try:
                if not win.winfo_exists(): return
            except: return
            a -= step
            if a > 0.0: win.attributes("-alpha", a); win.after(delay, lambda: fade(a))
            else:
                try: win.attributes("-alpha", 0.0)
                except: pass
                if on_complete: on_complete()
                else: 
                    try: win.destroy()
                    except: pass
        fade()

    @staticmethod
    def animate_bg_color(widget, end_color, duration=200):
        if not widget.winfo_exists(): return
        start_color = widget.cget("bg")
        if start_color == end_color: return
        
        if hasattr(widget, '_bg_anim_id') and widget._bg_anim_id:
            widget.after_cancel(widget._bg_anim_id)
            widget._bg_anim_id = None
            
        def hex_to_rgb(hx):
            hx = hx.lstrip('#')
            return tuple(int(hx[i:i+2], 16) for i in (0, 2, 4))
        
        def rgb_to_hex(rgb): return '#%02x%02x%02x' % rgb

        c1 = hex_to_rgb(start_color); c2 = hex_to_rgb(end_color)
        steps = 10; delay = duration // steps

        def step(i=1):
            if not widget.winfo_exists(): return
            f = i / steps
            curr = tuple(int(c1[j] + (c2[j] - c1[j]) * f) for j in range(3))
            hex_val = rgb_to_hex(curr)
            
            def update_w(w, col):
                try: 
                    if not isinstance(w, (tk.Entry, tk.Text, tk.Canvas)): w.config(bg=col)
                    for child in w.winfo_children(): update_w(child, col)
                except: pass
                
            update_w(widget, hex_val)
            if i < steps: 
                widget._bg_anim_id = widget.after(delay, lambda: step(i + 1))
            else:
                widget._bg_anim_id = None
        step()

    @staticmethod
    def animate_entry_value(entry, start_val, end_val, format_func, duration=250):
        steps = 15
        delay = duration // steps
        def step(i):
            if not entry.winfo_exists(): return
            val = start_val + (end_val - start_val) * (i / float(steps))
            entry.delete(0, tk.END)
            entry.insert(0, format_func(val))
            if i < steps: entry.after(delay, lambda: step(i + 1))
            else:
                entry.delete(0, tk.END)
                entry.insert(0, format_func(end_val))
        step(1)

    @staticmethod
    def animate_progress_bar(widget, target_relwidth, duration=250):
        if not widget.winfo_exists(): return
        current_relwidth = float(widget.place_info().get('relwidth', 0))
        steps = 15
        delay = duration // steps
        def step(i):
            if not widget.winfo_exists(): return
            new_w = current_relwidth + (target_relwidth - current_relwidth) * (i / float(steps))
            widget.place(relwidth=new_w)
            if i < steps: widget.after(delay, lambda: step(i + 1))
            else: widget.place(relwidth=target_relwidth)
        step(1)

    @staticmethod
    def apply_focus_glow(wrapper_frame, entry_widget, glow_color=Theme.BLU, idle_color=Theme.LINE):
        def on_focus_in(e):
            Components.animate_bg_color(wrapper_frame, glow_color, 150)
            entry_widget.config(fg=glow_color)
        def on_focus_out(e):
            Components.animate_bg_color(wrapper_frame, idle_color, 150)
            entry_widget.config(fg=Theme.FW)
            
        entry_widget.bind("<FocusIn>", on_focus_in, add="+")
        entry_widget.bind("<FocusOut>", on_focus_out, add="+")

    @staticmethod
    def apply_sliding_border(parent_frame, border_color=Theme.BLU, thickness=2, speed=1.5, delay=20):
        canvas = tk.Canvas(parent_frame, bg=parent_frame.cget("bg"), highlightthickness=0, bd=0)
        canvas.place(x=0, y=0, relwidth=1, relheight=1)
        
        for child in parent_frame.winfo_children():
            if child != canvas: child.lift()
                
        def hex_to_rgb(hx):
            hx = hx.lstrip('#')
            return tuple(int(hx[i:i+2], 16) for i in (0, 2, 4))
        def rgb_to_hex(rgb): return '#%02x%02x%02x' % rgb
            
        bg_rgb = hex_to_rgb(parent_frame.cget("bg"))
        fg_rgb = hex_to_rgb(border_color)
        
        def animate(offset=0, fade_step=0):
            if not canvas.winfo_exists(): return
            if not getattr(canvas, 'animating', False):
                canvas.place_forget()
                return
            
            canvas.delete("flow")
            w, h = canvas.winfo_width(), canvas.winfo_height()
            if w <= 1 or h <= 1: 
                canvas.after(delay, lambda: animate(offset, fade_step))
                return

            if fade_step < 20: fade_step += 1
            f_ratio = fade_step / 20.0
            curr_border_rgb = tuple(int(bg_rgb[j] + (fg_rgb[j] - bg_rgb[j]) * f_ratio) for j in range(3))
            curr_color = rgb_to_hex(curr_border_rgb)

            canvas.create_rectangle(thickness//2, thickness//2, w-(thickness//2), h-(thickness//2), outline=Theme.LINE, width=thickness, tags="flow")

            perimeter = 2 * (w + h)
            length = perimeter * 0.4 
            
            def get_point(dist):
                dist = dist % perimeter
                if dist < w: return dist, 0
                elif dist < w + h: return w, dist - w
                elif dist < 2*w + h: return w - (dist - (w + h)), h
                else: return 0, h - (dist - (2*w + h))

            pts = []
            for i in range(15): 
                p_dist = (offset + (i * length / 15)) % perimeter
                pts.append(get_point(p_dist))
            
            for i in range(len(pts)-1):
                alpha = (i+1) / len(pts)
                canvas.create_line(pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1], fill=curr_color, width=thickness + (alpha*1.5), tags="flow")

            canvas.after(delay, lambda: animate((offset + speed) % perimeter, fade_step))

        def start_anim():
            canvas.animating = True
            canvas.place(x=0, y=0, relwidth=1, relheight=1)
            for child in parent_frame.winfo_children():
                if child != canvas: child.lift()
            animate(0, 0)

        def stop_anim():
            canvas.animating = False
            canvas.place_forget()
            
        return start_anim, stop_anim

    @staticmethod
    def build_safe_entry(parent_frame, bg_color, fg_color, font, width=None, justify="left"):
        border = tk.Frame(parent_frame, bg=Theme.LINE, highlightthickness=0, bd=0)
        border.pack(fill=tk.BOTH, expand=True)
        inner = tk.Frame(border, bg=bg_color, highlightthickness=0, bd=0)
        inner.pack(padx=1, pady=1, fill=tk.BOTH, expand=True)
        
        kw = {"width": width} if width else {}
        entry = tk.Entry(inner, bg=bg_color, fg=fg_color, font=font, justify=justify, 
                         bd=0, highlightthickness=0, highlightcolor=bg_color, highlightbackground=bg_color, 
                         insertbackground=Theme.FW, selectbackground=Theme.SEL_BG, selectforeground=Theme.FW, **kw)
        entry.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        
        return border, inner, entry

    @staticmethod
    def create_btn(parent, text, bg, fg, cmd, fs=9, px=14, py=7, hbg=None, hfg=None):
        c = tk.Frame(parent, bg=bg, padx=1, pady=1)
        l = tk.Label(c, text=text, bg=bg, fg=fg, font=(F, fs, "bold"), cursor=Theme.CURSOR, padx=px, pady=py)
        l.pack(fill=tk.BOTH, expand=True)
        c._bg, c._fg, c._hbg, c._hfg, c._cmd = bg, fg, hbg or Theme.BG3, hfg or fg, cmd
        c.state = "normal"; c.l = l; c.tt = ToolTip(c.l, "")

        def on_enter(*args):
            if c.state == "normal": 
                Components.animate_bg_color(c, c._hbg, duration=150)
                l.config(fg=c._hfg)
            elif c.state == "disabled" and c.tt.enabled: c.tt.show(*args)
                
        def on_leave(*args):
            if c.state == "normal": 
                Components.animate_bg_color(c, c._bg, duration=150)
                l.config(fg=c._fg)
            elif c.state == "disabled": c.tt.hide(*args)
                
        def on_click(*args):
            if c.state == "normal": c._cmd()
            else: SoundManager.play_error() 

        l.bind("<Enter>", on_enter); l.bind("<Leave>", on_leave); l.bind("<Button-1>", on_click)
        
        def set_state(state):
            c.state = state
            if state == "disabled":
                c.l.config(bg=Theme.BG1, fg="#606080", cursor="arrow"); c.config(bg=Theme.BG1); c.tt.enabled = True
            else:
                c.l.config(bg=c._bg, fg=c._fg, cursor=Theme.CURSOR); c.config(bg=c._bg); c.tt.enabled = False
                
        c.set_state = set_state
        return c

    @staticmethod
    def create_card(parent, accent=None, **kw): 
        return tk.Frame(parent, bg=Theme.BG1, highlightbackground=Theme.LINE, highlightcolor=Theme.LINE, highlightthickness=1, bd=0, **kw)

    @staticmethod
    def create_sep(parent, c=Theme.LINE, h=1, py=4): 
        tk.Frame(parent, bg=c, height=h).pack(fill=tk.X, pady=py)

    @staticmethod
    def bind_num_only(widget):
        vcmd = (widget.register(lambda P: all(c.isdigit() or c in ".,%" for c in P)), '%P')
        widget.config(validate="key", validatecommand=vcmd)

    @staticmethod
    def create_quick_amounts(parent, values, fg_col, hover_bg, set_cmd, is_pct=False, borc_kalan=0):
        for w in parent.winfo_children(): w.destroy()
        for v in values:
            if is_pct: t, amt = f"%{v}", borc_kalan * v / 100
            else: t, amt = (f"{v:,}".replace(",", "."), v)
            lbl = tk.Label(parent, text=t, bg=Theme.BG2, fg=fg_col, font=(F,11,"bold"), cursor=Theme.CURSOR, pady=8)
            lbl.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
            lbl.bind("<Button-1>", lambda e, a=amt: set_cmd(a))
            lbl.bind("<Enter>", lambda e, w=lbl: (Components.animate_bg_color(w, hover_bg, 150), w.config(fg=Theme.BG1)))
            lbl.bind("<Leave>", lambda e, w=lbl: (Components.animate_bg_color(w, Theme.BG2, 150), w.config(fg=fg_col)))

    @staticmethod
    def draw_bank_logo(parent, bank_name, size, bg_color, font_size=15):
        bk = banka_bul(bank_name); img = get_cached_logo(bk, size=size)
        if img: l = tk.Label(parent, image=img, bg=bg_color); l.image = img; l.pack(side=tk.LEFT, padx=(0,8))
        else: tk.Label(parent, text=bk.get("ikon", "💳"), font=(F, font_size), bg=bg_color, fg=Theme.FW).pack(side=tk.LEFT, padx=(0,8))
        return bk

class DarkScrollbar(tk.Canvas):
    def __init__(self, parent, command=None, **kw):
        self.bar_color, self.bar_hover, self.trough_color = kw.pop('bar_color', '#5A5A7A'), kw.pop('bar_hover', '#7A7A9A'), kw.pop('trough_color', Theme.BG1)
        super().__init__(parent, width=10, bg=self.trough_color, highlightthickness=0, bd=0, relief='flat', **kw)
        self.command, self._dragging, self._start_y, self._start_top, self._top, self._bot, self._hovering = command, False, 0, 0, 0.0, 1.0, False
        self.bind('<Configure>', self._draw); self.bind('<ButtonPress-1>', self._on_press); self.bind('<ButtonRelease-1>', self._on_release)
        self.bind('<B1-Motion>', self._on_drag); self.bind('<Enter>', self._on_enter); self.bind('<Leave>', self._on_leave)

    def set(self, top, bot): self._top, self._bot = float(top), float(bot); self._draw()

    def _draw(self, event=None):
        self.delete('all')
        h, w = self.winfo_height(), self.winfo_width()
        if h <= 1 or (self._top <= 0.0 and self._bot >= 1.0): return
        y1, y2 = int(self._top * h), int(self._bot * h)
        bar_h = max(y2 - y1, 20)
        if y1 + bar_h > h: y1 = h - bar_h
        col = self.bar_hover if self._hovering else self.bar_color
        self.create_rectangle(2, y1+2, w-2, y1+bar_h-2, fill=col, outline='', width=0, tags="bar")

    def _on_press(self, event): self._dragging, self._start_y, self._start_top = True, event.y, self._top
    def _on_release(self, event): self._dragging = False
    def _on_drag(self, event):
        if not self._dragging or not self.command: return
        h = self.winfo_height()
        if h <= 1: return
        dy = (event.y - self._start_y) / h
        self.command('moveto', str(max(0.0, min(self._start_top + dy, 1.0 - (self._bot - self._top)))))
        
    def _on_enter(self, event): self._hovering = True; self._draw()
    def _on_leave(self, event): self._hovering = False; self._draw()

class CustomScrollableFrame(tk.Frame):
    def __init__(self, container, bg_color=Theme.BG1, *args, **kwargs):
        super().__init__(container, bg=bg_color, *args, **kwargs)
        self.canvas = tk.Canvas(self, bg=bg_color, highlightthickness=0)
        self.scrollbar = DarkScrollbar(self, command=self.canvas.yview, trough_color=bg_color)
        self.scrollable_window = tk.Frame(self.canvas, bg=bg_color)

        self.scrollable_window.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.scrollable_window, anchor="nw")
        
        def _on_canvas_configure(event):
            if getattr(self.canvas, '_last_width', None) != event.width:
                self.canvas.itemconfig(self.canvas_frame, width=event.width)
                self.canvas._last_width = event.width
                
        self.canvas.bind("<Configure>", _on_canvas_configure)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        def _on_mousewheel(event):
            if platform.system() == 'Windows': self.canvas.yview_scroll(int(-1*(event.delta/120))*2, "units")
            elif platform.system() == 'Darwin': self.canvas.yview_scroll(int(-1*event.delta), "units")
            else: self.canvas.yview_scroll(-2 if event.num == 4 else 2, "units")
                
        self.canvas.bind("<MouseWheel>", _on_mousewheel)
        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", _on_mousewheel))
        self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))

    def clear(self):
        for w in self.scrollable_window.winfo_children(): w.destroy()

class GridPatternCanvas(tk.Canvas):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=Theme.BG, highlightthickness=0, bd=0, **kw)
        self.bind('<Configure>', self._draw_grid)

    def _draw_grid(self, event=None):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        self.create_oval(-200, -200, 400, 400, fill="#0A0A1A", outline="", tags="bg_glow")
        self.create_oval(w//2-300, h-100, w//2+300, h+300, fill="#0A151A", outline="", tags="bg_glow")
        
        for x in range(0, w, 30): self.create_line(x, 0, x, h, fill="#0B0B14", tags="grid")
        for y in range(0, h, 30): self.create_line(0, y, w, y, fill="#0B0B14", tags="grid")

class ToastManager:
    @classmethod
    def show(cls, parent, msg, col=Theme.GRN):
        pass