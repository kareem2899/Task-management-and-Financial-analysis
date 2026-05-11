"""
DatePicker for macOS tkinter.
Uses .place() overlay on the root window — no Toplevel, no overrideredirect.
v9 fixes:
  - Nav buttons (‹ ›) use tk.Label + bindings — bypasses macOS Aqua theme
  - Day cells use tk.Label + bindings — background color now fully respected
  - Calendar icon button uses tk.Label + binding for same reason
  - highlightthickness=0 on all internal frames to kill light borders
"""
import tkinter as tk
from datetime import date, datetime
import calendar

C = {
    "bg":      "#0F1117",   # main app background
    "card":    "#22263A",   # inner grid surface
    "card2":   "#1A1D27",   # entry/popup background
    "accent":  "#6C63FF",   # purple — header, selected day, icon button bg
    "hover":   "#5a52d5",   # purple hover
    "success": "#43E97B",   # green — today highlight
    "text":    "#E8E9F3",   # primary text
    "sub":     "#8B8FA8",   # muted labels (weekday headers)
    "border":  "#2E3250",   # dark navy border
    "weekend": "#6C63FF",   # purple for Sa/Su
    "shadow":  "#090B10",
}

_CAL_W      = 300
_HEADER_H   = 36
_DOW_H      = 24
_ROW_H      = 30
_BOTTOM_PAD = 6


def _cal_height(year: int, month: int) -> int:
    weeks = len(calendar.monthcalendar(year, month))
    return _HEADER_H + _DOW_H + weeks * _ROW_H + _BOTTOM_PAD


def _make_label_btn(parent, text, bg, fg, font, width=None, height=None,
                    hover_bg=None, hover_fg="white", command=None, **grid_kw):
    """
    A tk.Label styled and wired to behave like a button.
    Using Label instead of Button bypasses the macOS Aqua theme that
    ignores bg/fg on tk.Button widgets.
    """
    kw = dict(text=text, bg=bg, fg=fg, font=font,
              cursor="hand2", relief="flat",
              highlightthickness=0)
    if width  is not None: kw["width"]  = width
    if height is not None: kw["height"] = height

    lbl = tk.Label(parent, **kw)

    _hbg = hover_bg or C["hover"]

    def on_enter(e):  lbl.config(bg=_hbg,  fg=hover_fg)
    def on_leave(e):  lbl.config(bg=bg,    fg=fg)
    def on_click(e):
        if command:
            command()

    lbl.bind("<Enter>",    on_enter)
    lbl.bind("<Leave>",    on_leave)
    lbl.bind("<Button-1>", on_click)
    return lbl


class DatePicker(tk.Frame):
    """
    Embeddable date-picker.
        dp = DatePicker(parent, on_change=callback)
        dp.pack(...)
        d  = dp.get_date()           # → datetime.date
        dp.set_date("2026-05-01")    # string or date object
    """

    _active: "DatePicker | None" = None

    def __init__(self, parent, initial_date=None, on_change=None, width=130, **kw):
        kw.setdefault("bg", C["card2"])
        super().__init__(parent, **kw)
        self._sel = initial_date if isinstance(initial_date, date) else date.today()
        self._on_change  = on_change
        self._width      = width
        self._cal_year   = self._sel.year
        self._cal_month  = self._sel.month
        self._overlay    = None
        self._build_entry()

    # ── entry + calendar button ───────────────────────────────────────────────
    def _build_entry(self):
        self._var = tk.StringVar(value=self._sel.strftime("%Y-%m-%d"))

        self._entry = tk.Entry(
            self, textvariable=self._var, state="readonly",
            width=11, relief="flat",
            readonlybackground=C["card2"], fg=C["text"],
            font=("Georgia", 11), cursor="arrow",
            highlightthickness=1,
            highlightbackground=C["border"],
            highlightcolor=C["accent"],
        )
        self._entry.pack(side="left", ipady=4)
        self._entry.bind("<Button-1>", lambda e: self._toggle())

        # Calendar icon — Label so macOS respects the purple bg
        icon = tk.Label(
            self, text="📅",
            bg=C["accent"], fg="white",
            font=("Arial", 13), cursor="hand2",
            highlightthickness=0, relief="flat",
            padx=6, pady=4,
        )
        icon.pack(side="left", padx=(0, 0))
        icon.bind("<Enter>",    lambda e: icon.config(bg=C["hover"]))
        icon.bind("<Leave>",    lambda e: icon.config(bg=C["accent"]))
        icon.bind("<Button-1>", lambda e: self._toggle())

    # ── open / close ──────────────────────────────────────────────────────────
    def _toggle(self):
        if self._overlay and self._overlay.winfo_exists():
            self._close()
        else:
            if DatePicker._active and DatePicker._active is not self:
                DatePicker._active._close()
            self._open()

    def _open(self):
        self._cal_year  = self._sel.year
        self._cal_month = self._sel.month

        root = self.winfo_toplevel()
        self.update_idletasks()

        rx = self.winfo_rootx() - root.winfo_rootx()
        ry = self.winfo_rooty() - root.winfo_rooty() + self.winfo_height() + 3

        rw = root.winfo_width()
        if rx + _CAL_W > rw:
            rx = max(0, rw - _CAL_W - 4)

        cal_h = _cal_height(self._cal_year, self._cal_month)

        ov = tk.Frame(root, bg=C["card2"], bd=0,
                      highlightthickness=1, highlightbackground=C["border"])
        ov.place(x=rx, y=ry, width=_CAL_W, height=cal_h)
        ov.lift()

        self._overlay    = ov
        DatePicker._active = self
        self._render()

        root.bind("<Button-1>", self._on_root_click, add="+")

    def _close(self):
        if self._overlay and self._overlay.winfo_exists():
            self._overlay.destroy()
        self._overlay = None
        if DatePicker._active is self:
            DatePicker._active = None
        try:
            self.winfo_toplevel().unbind("<Button-1>")
        except Exception:
            pass

    def _on_root_click(self, event):
        if not (self._overlay and self._overlay.winfo_exists()):
            self._close()
            return
        ox = self._overlay.winfo_rootx()
        oy = self._overlay.winfo_rooty()
        ow = self._overlay.winfo_width()
        oh = self._overlay.winfo_height()
        if not (ox <= event.x_root <= ox + ow and oy <= event.y_root <= oy + oh):
            self._close()

    # ── render calendar ───────────────────────────────────────────────────────
    def _render(self):
        ov = self._overlay
        for w in ov.winfo_children():
            w.destroy()

        cal_h = _cal_height(self._cal_year, self._cal_month)
        ov.place_configure(height=cal_h)

        # ── header ────────────────────────────────────────────────────────────
        hdr = tk.Frame(ov, bg=C["accent"], height=_HEADER_H,
                       highlightthickness=0)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        # Prev nav — Label so macOS keeps the purple bg
        prev_btn = _make_label_btn(
            hdr, text="‹",
            bg=C["accent"], fg="white",
            font=("Georgia", 16, "bold"),
            hover_bg=C["hover"],
            command=self._prev,
        )
        prev_btn.pack(side="left", padx=10, pady=4)

        tk.Label(
            hdr,
            text=f"{calendar.month_name[self._cal_month]} {self._cal_year}",
            bg=C["accent"], fg="white",
            font=("Georgia", 12, "bold"),
            highlightthickness=0,
        ).pack(side="left", expand=True)

        # Next nav — same treatment
        next_btn = _make_label_btn(
            hdr, text="›",
            bg=C["accent"], fg="white",
            font=("Georgia", 16, "bold"),
            hover_bg=C["hover"],
            command=self._next,
        )
        next_btn.pack(side="right", padx=10, pady=4)

        # ── weekday labels ────────────────────────────────────────────────────
        dow = tk.Frame(ov, bg=C["card"], height=_DOW_H,
                       highlightthickness=0)
        dow.pack(fill="x", padx=4, pady=(4, 0))
        dow.pack_propagate(False)
        for i, d in enumerate(["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]):
            tk.Label(
                dow, text=d, bg=C["card"],
                fg=C["weekend"] if i >= 5 else C["sub"],
                font=("Georgia", 8, "bold"),
                width=4,
                highlightthickness=0,
            ).grid(row=0, column=i, padx=1, pady=2)

        # ── day grid ──────────────────────────────────────────────────────────
        gf = tk.Frame(ov, bg=C["card"], highlightthickness=0)
        gf.pack(fill="both", expand=True, padx=4, pady=(0, _BOTTOM_PAD))

        today = date.today()
        for r, week in enumerate(calendar.monthcalendar(self._cal_year, self._cal_month)):
            for c, day in enumerate(week):
                if day == 0:
                    tk.Label(
                        gf, text="", bg=C["card"],
                        width=4, height=1,
                        highlightthickness=0,
                    ).grid(row=r, column=c, padx=1, pady=2)
                    continue

                is_sel = (day == self._sel.day and
                          self._cal_month == self._sel.month and
                          self._cal_year  == self._sel.year)
                is_tod = (day == today.day and
                          self._cal_month == today.month and
                          self._cal_year  == today.year)
                is_wkd = c >= 5

                if is_sel:
                    bg, fg = C["accent"], "white"
                elif is_tod:
                    bg, fg = C["card2"],  C["success"]
                elif is_wkd:
                    bg, fg = C["card"],   C["weekend"]
                else:
                    bg, fg = C["card"],   C["text"]

                # Use Label + bindings so macOS respects bg/fg
                cell = _make_label_btn(
                    gf, text=str(day),
                    bg=bg, fg=fg,
                    font=("Georgia", 10),
                    width=4, height=1,
                    hover_bg=C["accent"],
                    hover_fg="white",
                    command=lambda d=day: self._pick(d),
                )
                cell.grid(row=r, column=c, padx=1, pady=2)

    # ── navigation ────────────────────────────────────────────────────────────
    def _prev(self):
        if self._cal_month == 1:
            self._cal_month, self._cal_year = 12, self._cal_year - 1
        else:
            self._cal_month -= 1
        self._render()

    def _next(self):
        if self._cal_month == 12:
            self._cal_month, self._cal_year = 1, self._cal_year + 1
        else:
            self._cal_month += 1
        self._render()

    # ── pick a day ────────────────────────────────────────────────────────────
    def _pick(self, day):
        self._sel = date(self._cal_year, self._cal_month, day)
        self._var.set(self._sel.strftime("%Y-%m-%d"))
        self._close()
        if self._on_change:
            self._on_change(self._sel)

    # ── public API ────────────────────────────────────────────────────────────
    def get_date(self) -> date:
        return self._sel

    def set_date(self, d):
        if isinstance(d, str):
            try:
                d = datetime.strptime(d, "%Y-%m-%d").date()
            except Exception:
                return
        if not isinstance(d, date):
            return
        self._sel = d
        self._var.set(d.strftime("%Y-%m-%d"))
