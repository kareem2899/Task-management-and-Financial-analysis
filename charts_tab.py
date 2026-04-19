import customtkinter as ctk
import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import date
from date_picker import DatePicker
import database as db

COLORS = {
    "bg":"#0F1117","card":"#1A1D27","card2":"#22263A",
    "accent":"#6C63FF","success":"#43E97B","danger":"#FF4B4B",
    "warning":"#F7971E","text":"#E8E9F3","subtext":"#8B8FA8","border":"#2E3250",
}
MPL_BG="#1A1D27"; MPL_FACE="#22263A"
PAL=["#6C63FF","#43E97B","#FF6584","#F7971E","#38BDF8","#E879F9","#FB923C","#A3E635","#FF4B4B","#14B8A6"]


def sax(ax, title=""):
    ax.set_facecolor(MPL_FACE)
    ax.tick_params(colors="#8B8FA8", labelsize=8)
    for sp in ax.spines.values(): sp.set_edgecolor("#2E3250")
    ax.title.set_color("#E8E9F3"); ax.title.set_fontsize(11)
    ax.xaxis.label.set_color("#8B8FA8"); ax.yaxis.label.set_color("#8B8FA8")
    if title: ax.set_title(title, pad=8)


CHART_TABS = [
    ("📋 Tasks Overview",      "tasks"),
    ("📈 Tasks Trend",         "tasks_line"),
    ("💰 Finance Daily",       "finance_daily"),
    ("📆 Finance Monthly",     "finance_monthly"),
    ("🍩 Expense Categories",  "categories"),
    ("🔍 Finance Analysis",    "finance_analysis"),
]


class ChartsTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.current_chart = "tasks"
        self.canvas_widget = None
        self._build()
        self.refresh_all()

    def _build(self):
        # Header
        top = ctk.CTkFrame(self, fg_color="transparent"); top.pack(fill="x", padx=22, pady=(18,8))
        ctk.CTkLabel(top, text="ANALYTICS & CHARTS", font=("Georgia",20,"bold"),
                     text_color=COLORS["text"]).pack(side="left")
        ctk.CTkButton(top, text="↺ Refresh", fg_color=COLORS["card2"], hover_color=COLORS["border"],
                      text_color=COLORS["subtext"], width=100, command=self.refresh_all).pack(side="right")

        # Tab buttons row 1
        tr1 = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=12); tr1.pack(fill="x", padx=22, pady=(0,4))
        inner1 = ctk.CTkFrame(tr1, fg_color="transparent"); inner1.pack(padx=10, pady=8, side="left")
        self.tab_btns = {}
        for label, key in CHART_TABS:
            btn = ctk.CTkButton(inner1, text=label, width=152, height=30, font=("Georgia",10),
                                fg_color=COLORS["accent"] if key=="tasks" else COLORS["card2"],
                                hover_color=COLORS["accent"], corner_radius=8,
                                command=lambda k=key: self.switch_chart(k))
            btn.pack(side="left", padx=3)
            self.tab_btns[key] = btn

        # Filter bar
        fbar = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=12); fbar.pack(fill="x", padx=22, pady=(0,8))
        fi = ctk.CTkFrame(fbar, fg_color="transparent"); fi.pack(fill="x", padx=14, pady=8)
        ctk.CTkLabel(fi, text="Month:", font=("Georgia",10), text_color=COLORS["subtext"]).pack(side="left", padx=(0,6))
        self.month_var = ctk.StringVar(value="All")
        ctk.CTkOptionMenu(fi, variable=self.month_var, values=["All"]+self._months(),
                          width=130, fg_color=COLORS["card2"], button_color=COLORS["border"],
                          dropdown_fg_color=COLORS["card"],
                          command=lambda _: self.refresh_all()).pack(side="left", padx=4)
        ctk.CTkLabel(fi, text="From", font=("Georgia",10), text_color=COLORS["subtext"]).pack(side="left", padx=(14,4))
        self.from_dp = DatePicker(fi, on_change=lambda _: self.refresh_all(), width=130); self.from_dp.pack(side="left", padx=(0,8))
        ctk.CTkLabel(fi, text="To", font=("Georgia",10), text_color=COLORS["subtext"]).pack(side="left", padx=(0,4))
        self.to_dp = DatePicker(fi, on_change=lambda _: self.refresh_all(), width=130); self.to_dp.pack(side="left")

        # Chart canvas
        self.chart_frame = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=14)
        self.chart_frame.pack(fill="both", expand=True, padx=22, pady=(0,12))

    def _months(self):
        y = date.today().year; return [f"{y}-{m:02d}" for m in range(1,13)]

    def switch_chart(self, key):
        self.current_chart = key
        for k, b in self.tab_btns.items():
            b.configure(fg_color=COLORS["accent"] if k==key else COLORS["card2"])
        self.refresh_all()

    def refresh_all(self):
        month = self.month_var.get() if self.month_var.get() != "All" else None
        # Destroy canvas widget
        if self.canvas_widget:
            self.canvas_widget.get_tk_widget().destroy()
            self.canvas_widget = None
        # Also clear any native tk widgets left by _finance_analysis
        for w in self.chart_frame.winfo_children():
            w.destroy()
        dispatch = {
            "tasks":            lambda: self._tasks_chart(),
            "tasks_line":       lambda: self._tasks_line(),
            "finance_daily":    lambda: self._finance_daily(month),
            "finance_monthly":  lambda: self._finance_monthly(),
            "categories":       lambda: self._categories_pie(month),
            "finance_analysis": lambda: self._finance_analysis(month),
        }
        dispatch.get(self.current_chart, lambda: None)()

    def _embed(self, fig):
        c = FigureCanvasTkAgg(fig, master=self.chart_frame)
        c.draw(); c.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)
        self.canvas_widget = c

    def _no_data(self, fig, msg="No data yet!"):
        ax = fig.add_subplot(111); ax.set_facecolor(MPL_FACE)
        ax.text(0.5, 0.5, msg, ha="center", va="center", color="#8B8FA8", fontsize=14, transform=ax.transAxes)
        ax.axis("off")

    # ── 1. Tasks Overview ─────────────────────────────────────────────────────
    def _tasks_chart(self):
        sc, cc, daily = db.get_task_stats()
        fig = Figure(figsize=(13,5), facecolor=MPL_BG, tight_layout=True)
        if not sc and not cc: self._no_data(fig,"No tasks yet!"); self._embed(fig); return
        ax1 = fig.add_subplot(131)
        if sc:
            cols={"Pending":"#6C63FF","In Progress":"#F7971E","Completed":"#43E97B","Cancelled":"#8B8FA8"}
            ax1.pie(list(sc.values()), labels=list(sc.keys()),
                    colors=[cols.get(k,"#6C63FF") for k in sc],
                    autopct='%1.0f%%', pctdistance=0.8, startangle=90,
                    textprops={"color":"#E8E9F3","fontsize":8})
        sax(ax1,"Tasks by Status")
        ax2 = fig.add_subplot(132)
        if cc:
            bars = ax2.barh(list(cc.keys()), list(cc.values()), color=PAL[:len(cc)], edgecolor="none", height=0.6)
            ax2.bar_label(bars, fmt="%d", color="#E8E9F3", fontsize=8, padding=4)
        sax(ax2,"Tasks by Category")
        ax3 = fig.add_subplot(133)
        if daily:
            days, counts = zip(*daily)
            ax3.plot(days, counts, color="#6C63FF", linewidth=2, marker="o", markersize=5, markerfacecolor="#43E97B")
            ax3.fill_between(days, counts, alpha=0.2, color="#6C63FF")
            ax3.tick_params(axis='x', rotation=45)
        sax(ax3,"Tasks Created Daily")
        self._embed(fig)

    # ── 2. Tasks Line Trend ───────────────────────────────────────────────────
    def _tasks_line(self):
        sc, cc, daily = db.get_task_stats()
        fig = Figure(figsize=(13,5), facecolor=MPL_BG, tight_layout=True)
        if not daily: self._no_data(fig,"No task history yet!"); self._embed(fig); return

        ax1 = fig.add_subplot(121)
        days, counts = zip(*daily)
        # Cumulative
        cumulative = []
        running = 0
        for c in counts: running += c; cumulative.append(running)
        ax1.plot(days, counts, color="#6C63FF", linewidth=2.5, marker="o", markersize=5,
                 markerfacecolor="#43E97B", label="New tasks/day")
        ax1.fill_between(days, counts, alpha=0.15, color="#6C63FF")
        ax1.tick_params(axis='x', rotation=45)
        ax1.legend(facecolor=MPL_FACE, labelcolor="#E8E9F3", fontsize=9)
        sax(ax1,"Daily New Tasks")

        ax2 = fig.add_subplot(122)
        ax2.plot(days, cumulative, color="#43E97B", linewidth=2.5, marker="s", markersize=5,
                 markerfacecolor="#F7971E", label="Cumulative tasks")
        ax2.fill_between(days, cumulative, alpha=0.15, color="#43E97B")
        ax2.tick_params(axis='x', rotation=45)
        ax2.legend(facecolor=MPL_FACE, labelcolor="#E8E9F3", fontsize=9)
        sax(ax2,"Cumulative Tasks Over Time")
        self._embed(fig)

    # ── 3. Finance Daily ──────────────────────────────────────────────────────
    def _finance_daily(self, month=None):
        _, _, daily, _, _, _, _ = db.get_finance_stats(month)
        fig = Figure(figsize=(13,5), facecolor=MPL_BG, tight_layout=True)
        if not daily: self._no_data(fig,"No transactions yet!"); self._embed(fig); return
        ax = fig.add_subplot(111)
        days, incomes, expenses = zip(*daily)
        x = range(len(days)); w = 0.35
        ax.bar([i-w/2 for i in x], incomes, width=w, color="#43E97B", label="Income", edgecolor="none")
        ax.bar([i+w/2 for i in x], expenses, width=w, color="#FF4B4B", label="Expense", edgecolor="none")
        ax.set_xticks(list(x)); ax.set_xticklabels(list(days), rotation=45, ha="right")
        ax.legend(facecolor=MPL_FACE, labelcolor="#E8E9F3", fontsize=9)
        sax(ax,"Daily Income vs Expenses")
        self._embed(fig)

    # ── 4. Finance Monthly ────────────────────────────────────────────────────
    def _finance_monthly(self):
        _, _, _, monthly, _, _, _ = db.get_finance_stats()
        fig = Figure(figsize=(13,5), facecolor=MPL_BG, tight_layout=True)
        if not monthly: self._no_data(fig,"No monthly data!"); self._embed(fig); return
        ax = fig.add_subplot(111)
        months, incomes, expenses = zip(*monthly)
        bal = [i-e for i,e in zip(incomes,expenses)]
        x = range(len(months))
        ax.plot(list(x), list(incomes), color="#43E97B", linewidth=2.5, marker="o", markersize=6, label="Income")
        ax.plot(list(x), list(expenses), color="#FF4B4B", linewidth=2.5, marker="s", markersize=6, label="Expenses")
        ax.plot(list(x), bal, color="#6C63FF", linewidth=2, linestyle="--", marker="^", markersize=5, label="Balance")
        ax.fill_between(list(x), list(incomes), list(expenses), alpha=0.1, color="#43E97B")
        ax.set_xticks(list(x)); ax.set_xticklabels(list(months), rotation=45, ha="right")
        ax.legend(facecolor=MPL_FACE, labelcolor="#E8E9F3", fontsize=9)
        sax(ax,"Monthly Income vs Expenses Trend")
        self._embed(fig)

    # ── 5. Expense Categories Pie ─────────────────────────────────────────────
    def _categories_pie(self, month=None):
        _, _, _, _, by_cat, _, _ = db.get_finance_stats(month)
        fig = Figure(figsize=(13,5), facecolor=MPL_BG, tight_layout=True)
        if not by_cat: self._no_data(fig,"No expense data!"); self._embed(fig); return
        labels = list(by_cat.keys()); sizes = list(by_cat.values()); cols = PAL[:len(labels)]
        ax1 = fig.add_subplot(121)
        ax1.pie(sizes, labels=labels, colors=cols, autopct='%1.1f%%', pctdistance=0.8,
                startangle=90, textprops={"color":"#E8E9F3","fontsize":8})
        sax(ax1,"Expenses by Category")
        ax2 = fig.add_subplot(122)
        bars = ax2.barh(labels, sizes, color=cols, edgecolor="none", height=0.6)
        ax2.bar_label(bars, fmt="EGP %.0f", color="#E8E9F3", fontsize=8, padding=4)
        sax(ax2,"Expense Amounts by Category")
        self._embed(fig)

    # ── 6. Finance Analysis ────────────────────────────────────────────────────
    def _finance_analysis(self, month=None):
        """
        Layout (all native tkinter widgets + one matplotlib figure):
          ┌─────────────────────────────────────────────────────┐
          │  Title: "Financial Analysis"                        │
          ├───────────────┬───────────────┬─────────────────────┤
          │  KPI: Income  │ KPI: Expenses │   KPI: Balance      │
          ├───────────────┴───────────────┴─────────────────────┤
          │  [matplotlib] left: bar chart   right: pie chart    │
          └─────────────────────────────────────────────────────┘
        """
        total_inc, total_exp, _, _, by_cat, by_src, by_loc = db.get_finance_stats(month)
        balance = total_inc - total_exp
        bal_color = "#43E97B" if balance >= 0 else "#FF4B4B"

        # ── Destroy previous canvas if any ────────────────────────────────
        if self.canvas_widget:
            self.canvas_widget.get_tk_widget().destroy()
            self.canvas_widget = None

        # ── Clear chart_frame and rebuild as a custom layout ──────────────
        for w in self.chart_frame.winfo_children():
            w.destroy()

        # ── Title ─────────────────────────────────────────────────────────
        tk.Label(
            self.chart_frame,
            text="Financial Analysis",
            bg=COLORS["card"], fg=COLORS["text"],
            font=("Georgia", 16, "bold"),
        ).pack(pady=(14, 10))

        # ── KPI cards row ─────────────────────────────────────────────────
        kpi_row = tk.Frame(self.chart_frame, bg=COLORS["card"])
        kpi_row.pack(fill="x", padx=16, pady=(0, 12))
        kpi_row.columnconfigure(0, weight=1)
        kpi_row.columnconfigure(1, weight=1)
        kpi_row.columnconfigure(2, weight=1)

        kpi_specs = [
            # (bg_color, icon, label, value, trend_label, trend_lo, trend_hi)
            ("#1B3A2A", "💰", "Income",
             f"EGP {total_inc:,.0f}", "↑  Income",
             f"EGP {total_inc*0.6:,.0f}", f"EGP {total_inc:,.0f}",
             "#43E97B"),
            ("#3A1B1B", "💸", "Expenses",
             f"EGP {total_exp:,.0f}", "⬆  Expenses",
             f"EGP {total_exp*0.5:,.0f}", f"EGP {total_exp:,.0f}",
             "#FF4B4B"),
            ("#1B2340", "💼", "Balance",
             f"EGP {balance:,.0f}", "↑  Balance",
             f"EGP {total_inc:,.0f}", f"EGP {balance:,.0f}",
             bal_color),
        ]

        for col, (bg, icon, label, value, trend_lbl, lo, hi, accent) in enumerate(kpi_specs):
            card = tk.Frame(kpi_row, bg=bg, padx=18, pady=14)
            card.grid(row=0, column=col, padx=6, pady=0, sticky="nsew")

            # Icon + label on same row
            top_row = tk.Frame(card, bg=bg)
            top_row.pack(fill="x")
            tk.Label(top_row, text=icon, bg=bg, font=("Arial", 22)).pack(side="left", padx=(0, 10))
            tk.Label(top_row, text=label, bg=bg, fg=COLORS["subtext"],
                     font=("Georgia", 12)).pack(side="left", anchor="s", pady=(8, 0))

            # Big number
            tk.Label(card, text=value, bg=bg, fg=accent,
                     font=("Georgia", 20, "bold")).pack(anchor="w", pady=(6, 10))

            # Divider
            tk.Frame(card, bg=accent, height=1).pack(fill="x", pady=(0, 8))

            # Trend row
            trend_row = tk.Frame(card, bg=bg)
            trend_row.pack(fill="x")
            tk.Label(trend_row, text=trend_lbl, bg=bg, fg=accent,
                     font=("Georgia", 10, "bold")).pack(side="left")
            tk.Label(trend_row, text=lo, bg=bg, fg=COLORS["subtext"],
                     font=("Georgia", 10)).pack(side="left", padx=(12, 0))
            tk.Label(trend_row, text=hi, bg=bg, fg=accent,
                     font=("Georgia", 10, "bold")).pack(side="right")

        # ── Matplotlib: 2 charts side by side ─────────────────────────────
        fig = Figure(figsize=(13, 4.8), facecolor=COLORS["card"], tight_layout=True)

        # Left: combined bar chart — income by source on top, expenses by location below
        ax_left = fig.add_subplot(121)
        plotted = False

        if by_src:
            srcs  = list(by_src.keys())[:6]
            svals = [by_src[s] for s in srcs]
            max_s = max(svals)
            scols = ["#FFD700" if v == max_s else "#43E97B" for v in svals]
            bars1 = ax_left.barh(
                [f"↑ {s}" for s in srcs], svals,
                color=scols, edgecolor="none", height=0.55,
            )
            ax_left.bar_label(bars1, fmt="EGP %.0f",
                              color="#E8E9F3", fontsize=8, padding=4)
            plotted = True

        if by_loc:
            locs  = list(by_loc.keys())[:6]
            lvals = [by_loc[l] for l in locs]
            max_l = max(lvals)
            lcols = ["#FF4B4B" if v == max_l else "#F7971E" for v in lvals]
            bars2 = ax_left.barh(
                [f"↓ {l}" for l in locs], lvals,
                color=lcols, edgecolor="none", height=0.55,
            )
            ax_left.bar_label(bars2, fmt="EGP %.0f",
                              color="#E8E9F3", fontsize=8, padding=4)
            plotted = True

        if not plotted:
            ax_left.text(0.5, 0.5, "No data yet",
                         ha="center", va="center", color="#8B8FA8",
                         transform=ax_left.transAxes, fontsize=12)

        top_src_label = (f"Income by Source  ★ Top: {list(by_src.keys())[0]}"
                         if by_src else "Income & Expense Breakdown")
        top_loc_label = (f"   |   Expenses  ★ Highest: {list(by_loc.keys())[0]}"
                         if by_loc else "")
        sax(ax_left, top_src_label + top_loc_label)

        # Right: expense category pie
        ax_right = fig.add_subplot(122)
        if by_cat:
            c4     = list(by_cat.keys())[:6]
            v4     = [by_cat[c] for c in c4]
            max_c  = max(v4)
            idx_mx = v4.index(max_c)
            explode = [0.08 if i == idx_mx else 0 for i in range(len(c4))]
            wedges, texts, autos = ax_right.pie(
                v4, labels=c4, colors=PAL[:len(c4)],
                autopct='%1.0f%%', pctdistance=0.80,
                startangle=90, explode=explode,
                textprops={"color": "#E8E9F3", "fontsize": 8},
            )
            # Amount legend below pie
            legend_txt = "   ".join(
                f"EGP {v:,.0f}  •  {c}" for c, v in zip(c4, v4)
            )
            ax_right.set_xlabel(legend_txt, color=COLORS["subtext"],
                                fontsize=7, labelpad=10)
            sax(ax_right,
                f"Expense Categories  ★ Biggest: {c4[idx_mx]}")
        else:
            ax_right.text(0.5, 0.5, "No expense data",
                          ha="center", va="center", color="#8B8FA8",
                          transform=ax_right.transAxes, fontsize=12)
            sax(ax_right, "Expense Categories")

        # Embed into chart_frame (not using self._embed so we don't destroy the KPI cards)
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.canvas_widget = canvas