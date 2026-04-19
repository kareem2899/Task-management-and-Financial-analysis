"""
Monthly Progress Tab
- Shows a grid of day-boxes for a selected date range (default: current month)
- Each day box shows: date, tasks due that day, completion %, green progress bar
- Summary bar at top: total income / expense for the month
"""
import customtkinter as ctk
import tkinter as tk
from datetime import date, timedelta
import calendar
import database as db
from date_picker import DatePicker

COLORS = {
    "bg":       "#0F1117",
    "card":     "#1A1D27",
    "card2":    "#22263A",
    "accent":   "#6C63FF",
    "success":  "#43E97B",
    "danger":   "#FF4B4B",
    "warning":  "#F7971E",
    "text":     "#E8E9F3",
    "subtext":  "#8B8FA8",
    "border":   "#2E3250",
    "today":    "#2D2F4A",
    "bar_bg":   "#1A2A1A",
    "bar_fg":   "#43E97B",
}


def _daterange(start: date, end: date):
    """Yield each date from start to end inclusive."""
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def _tasks_for_day(tasks: list, day: date):
    """Return tasks whose end_date == day (tasks due that day)."""
    ds = day.strftime("%Y-%m-%d")
    return [t for t in tasks if t.get("end_date") == ds]


def _tasks_in_range(tasks: list, start: date, end: date):
    """Return tasks active (start_date..end_date overlaps range)."""
    result = []
    for t in tasks:
        sd = t.get("start_date")
        ed = t.get("end_date")
        try:
            ts = date.fromisoformat(sd) if sd else None
            te = date.fromisoformat(ed) if ed else None
        except Exception:
            continue
        # task overlaps range if it starts before end AND ends after start
        if ts and te:
            if ts <= end and te >= start:
                result.append(t)
        elif te and te >= start and te <= end:
            result.append(t)
        elif ts and ts >= start and ts <= end:
            result.append(t)
    return result


class ProgressTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        today = date.today()
        # Default: first → last of current month
        self._start = date(today.year, today.month, 1)
        last_day = calendar.monthrange(today.year, today.month)[1]
        self._end = date(today.year, today.month, last_day)
        self._build()
        self._refresh()

    # ── Layout ────────────────────────────────────────────────────────────────
    def _build(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=22, pady=(18, 8))
        ctk.CTkLabel(hdr, text="MONTHLY PROGRESS",
                     font=("Georgia", 20, "bold"), text_color=COLORS["text"]).pack(side="left")

        # Date range selector
        ctrl = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=12)
        ctrl.pack(fill="x", padx=22, pady=(0, 10))
        ci = ctk.CTkFrame(ctrl, fg_color="transparent")
        ci.pack(fill="x", padx=14, pady=10)

        ctk.CTkLabel(ci, text="From", font=("Georgia", 11),
                     text_color=COLORS["subtext"]).pack(side="left")
        self._from_dp = DatePicker(ci, initial_date=self._start,
                                   on_change=self._on_from, width=130, bg=COLORS["card"])
        self._from_dp.pack(side="left", padx=(6, 16))

        ctk.CTkLabel(ci, text="To", font=("Georgia", 11),
                     text_color=COLORS["subtext"]).pack(side="left")
        self._to_dp = DatePicker(ci, initial_date=self._end,
                                 on_change=self._on_to, width=130, bg=COLORS["card"])
        self._to_dp.pack(side="left", padx=(6, 16))

        ctk.CTkButton(ci, text="This Month", width=100, height=32,
                      fg_color=COLORS["accent"], hover_color="#5a52d5",
                      command=self._set_this_month).pack(side="left", padx=(0, 6))
        ctk.CTkButton(ci, text="↺ Refresh", width=90, height=32,
                      fg_color=COLORS["card2"], hover_color=COLORS["border"],
                      text_color=COLORS["subtext"],
                      command=self._refresh).pack(side="left")

        # Summary strip (income / expense / balance)
        self._summary_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._summary_frame.pack(fill="x", padx=22, pady=(0, 10))

        # Scrollable day grid
        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.pack(fill="both", expand=True, padx=22, pady=(0, 12))

    # ── Controls ──────────────────────────────────────────────────────────────
    def _on_from(self, d: date):
        self._start = d
        if self._start > self._end:
            self._end = self._start
            self._to_dp.set_date(self._end)
        self._refresh()

    def _on_to(self, d: date):
        self._end = d
        if self._end < self._start:
            self._start = self._end
            self._from_dp.set_date(self._start)
        self._refresh()

    def _set_this_month(self):
        today = date.today()
        self._start = date(today.year, today.month, 1)
        last_day = calendar.monthrange(today.year, today.month)[1]
        self._end = date(today.year, today.month, last_day)
        self._from_dp.set_date(self._start)
        self._to_dp.set_date(self._end)
        self._refresh()

    # ── Refresh ───────────────────────────────────────────────────────────────
    def _refresh(self):
        self._draw_summary()
        self._draw_grid()

    def _draw_summary(self):
        for w in self._summary_frame.winfo_children():
            w.destroy()

        # Pull transactions in range
        start_s = self._start.strftime("%Y-%m-%d")
        end_s = self._end.strftime("%Y-%m-%d")
        txns = db.get_transactions()
        inc = sum(t["amount"] for t in txns
                  if t["type"] == "income" and start_s <= t["date"] <= end_s)
        exp = sum(t["amount"] for t in txns
                  if t["type"] == "expense" and start_s <= t["date"] <= end_s)
        bal = inc - exp
        bal_c = COLORS["success"] if bal >= 0 else COLORS["danger"]

        # Count tasks in range
        all_tasks = db.get_tasks()
        range_tasks = _tasks_in_range(all_tasks, self._start, self._end)
        done = sum(1 for t in range_tasks if t["status"] == "Completed")
        total = len(range_tasks)
        pct = int(done / total * 100) if total else 0

        cards_data = [
            ("Total Income",    f"EGP {inc:,.0f}",   COLORS["success"]),
            ("Total Expenses",  f"EGP {exp:,.0f}",   COLORS["danger"]),
            ("Balance",         f"EGP {bal:,.0f}",   bal_c),
            ("Tasks Progress",  f"{done}/{total}  ({pct}%)", COLORS["accent"]),
        ]
        for label, val, color in cards_data:
            card = ctk.CTkFrame(self._summary_frame,
                                fg_color=COLORS["card"], corner_radius=12)
            card.pack(side="left", fill="x", expand=True, padx=4)
            ctk.CTkLabel(card, text=label, font=("Georgia", 10),
                         text_color=COLORS["subtext"]).pack(pady=(10, 2))
            ctk.CTkLabel(card, text=val, font=("Georgia", 14, "bold"),
                         text_color=color).pack(pady=(0, 10))

    def _draw_grid(self):
        for w in self._scroll.winfo_children():
            w.destroy()

        all_tasks = db.get_tasks()
        today = date.today()
        days = list(_daterange(self._start, self._end))

        if not days:
            ctk.CTkLabel(self._scroll, text="Select a valid date range.",
                         font=("Georgia", 13), text_color=COLORS["subtext"]).pack(pady=40)
            return

        # Grid: 7 columns (one per weekday)
        grid = tk.Frame(self._scroll, bg=COLORS["bg"])
        grid.pack(fill="both", expand=True)
        for col in range(7):
            grid.columnconfigure(col, weight=1)

        # Weekday headers
        for i, name in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
            fg = "#FF8FA3" if i >= 5 else COLORS["subtext"]
            tk.Label(grid, text=name, bg=COLORS["bg"], fg=fg,
                     font=("Georgia", 9, "bold")).grid(
                row=0, column=i, pady=(0, 4), padx=2)

        # Work out which grid-column each day falls in (Mon=0)
        # First pad empty cells before the first day
        first_weekday = days[0].weekday()   # 0=Mon
        row = 1
        col = first_weekday

        for day in days:
            tasks_due = _tasks_for_day(all_tasks, day)
            done_due = sum(1 for t in tasks_due if t["status"] == "Completed")
            total_due = len(tasks_due)
            pct = done_due / total_due if total_due > 0 else 0

            is_today = (day == today)
            is_past = (day < today)
            is_wkd = day.weekday() >= 5

            self._day_box(grid, day, tasks_due, done_due, total_due,
                          pct, is_today, is_past, is_wkd, row, col)

            col += 1
            if col == 7:
                col = 0
                row += 1

    def _day_box(self, parent, day: date, tasks: list, done: int, total: int,
                 pct: float, is_today: bool, is_past: bool, is_wkd: bool,
                 row: int, col: int):

        # Box colours
        if is_today:
            box_bg = COLORS["today"]
            border_c = COLORS["accent"]
        elif is_wkd:
            box_bg = "#15171F"
            border_c = COLORS["border"]
        else:
            box_bg = COLORS["card"]
            border_c = COLORS["border"]

        # Outer frame with border effect
        outer = tk.Frame(parent, bg=border_c, padx=1, pady=1)
        outer.grid(row=row, column=col, padx=3, pady=3, sticky="nsew")
        parent.rowconfigure(row, weight=1)

        inner = tk.Frame(outer, bg=box_bg)
        inner.pack(fill="both", expand=True)

        # Day number
        day_num_color = COLORS["accent"] if is_today else (
            COLORS["subtext"] if is_wkd else COLORS["text"])
        tk.Label(inner, text=str(day.day),
                 bg=box_bg, fg=day_num_color,
                 font=("Georgia", 13, "bold")).pack(anchor="w", padx=8, pady=(6, 2))

        # Weekday label tiny
        wday_name = day.strftime("%a")
        tk.Label(inner, text=wday_name, bg=box_bg, fg=COLORS["subtext"],
                 font=("Georgia", 8)).pack(anchor="w", padx=8)

        if total > 0:
            # Task count text
            tk.Label(inner,
                     text=f"{done}/{total} task{'s' if total>1 else ''}",
                     bg=box_bg, fg=COLORS["subtext"],
                     font=("Georgia", 9)).pack(anchor="w", padx=8, pady=(4, 2))

            # Progress bar
            bar_frame = tk.Frame(inner, bg=COLORS["bar_bg"], height=8)
            bar_frame.pack(fill="x", padx=8, pady=(0, 4))
            bar_frame.pack_propagate(False)

            if pct > 0:
                # Color: green if done, orange if partial, red if nothing done and past
                if pct >= 1.0:
                    bar_color = COLORS["success"]
                elif pct >= 0.5:
                    bar_color = "#90EE60"
                elif is_past:
                    bar_color = COLORS["warning"]
                else:
                    bar_color = COLORS["success"]

                fill = tk.Frame(bar_frame, bg=bar_color, height=8)
                fill.place(relwidth=min(pct, 1.0), relheight=1.0)

            # Percentage label
            pct_color = COLORS["success"] if pct >= 1.0 else COLORS["warning"] if (
                is_past and pct < 1.0 and total > 0) else COLORS["subtext"]
            tk.Label(inner, text=f"{int(pct*100)}%",
                     bg=box_bg, fg=pct_color,
                     font=("Georgia", 9, "bold")).pack(anchor="e", padx=8, pady=(0, 2))

        else:
            # No tasks — show empty state
            empty_color = "#2E3250" if is_past else COLORS["border"]
            tk.Label(inner, text="no tasks", bg=box_bg, fg=empty_color,
                     font=("Georgia", 8, "italic")).pack(pady=8)

        # Bottom padding
        tk.Frame(inner, bg=box_bg, height=4).pack()
