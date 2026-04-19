import customtkinter as ctk
import tkinter as tk
import database as db

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

COLORS = {
    "bg": "#0F1117", "card": "#1A1D27", "card2": "#22263A",
    "accent": "#6C63FF", "success": "#43E97B", "danger": "#FF4B4B",
    "warning": "#F7971E", "text": "#E8E9F3", "subtext": "#8B8FA8",
    "border": "#2E3250", "sidebar": "#13151F",
}


class TaskFlowApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        db.initialize_db()
        self.title("TaskFlow — Task & Finance Manager")
        self.geometry("1320x840")
        self.minsize(1024, 680)
        self.configure(fg_color=COLORS["bg"])
        self._current_tab = "tasks"
        self.pages = {}
        self._build()
        # Build all pages immediately so switching is instant
        self._preload_all()
        self._switch_tab("tasks")

    def _build(self):
        # ── Sidebar ───────────────────────────────────────
        self.sidebar = tk.Frame(self, bg=COLORS["sidebar"], width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Brand
        tk.Label(self.sidebar, text="✦", bg=COLORS["sidebar"], fg=COLORS["accent"],
                 font=("Georgia", 30)).pack(pady=(32, 4))
        tk.Label(self.sidebar, text="TaskFlow", bg=COLORS["sidebar"], fg=COLORS["text"],
                 font=("Georgia", 20, "bold")).pack()
        tk.Label(self.sidebar, text="by Karim Mamdouh", bg=COLORS["sidebar"], fg=COLORS["subtext"],
                 font=("Georgia", 9)).pack(pady=(2, 16))

        tk.Frame(self.sidebar, bg=COLORS["border"], height=1).pack(fill="x", padx=20, pady=8)

        # Nav
        self.nav_btns = {}
        for icon, label, key in [("📋", "Tasks", "tasks"), ("🗂", "Projects", "projects"), ("💰", "Finance", "finance"), ("📊", "Analytics", "charts"), ("📅", "Progress", "progress"), ("🤖", "AI Assistant", "ai")]:
            self._nav_item(icon, label, key)

        # Footer
        tk.Frame(self.sidebar, bg=COLORS["border"], height=1).pack(fill="x", padx=20, pady=8, side="bottom")
        tk.Label(self.sidebar, text="SQLite  •  v1.0.0", bg=COLORS["sidebar"],
                 fg=COLORS["subtext"], font=("Georgia", 9)).pack(side="bottom", pady=4)

        # ── Content ────────────────────────────────────────
        self.content = tk.Frame(self, bg=COLORS["bg"])
        self.content.pack(side="left", fill="both", expand=True)

    def _nav_item(self, icon, label, key):
        frame = tk.Frame(self.sidebar, bg=COLORS["sidebar"], cursor="hand2")
        frame.pack(fill="x", padx=8, pady=2)
        icon_l = tk.Label(frame, text=icon, bg=COLORS["sidebar"], fg=COLORS["subtext"],
                          font=("Arial", 17), padx=12, pady=10)
        icon_l.pack(side="left")
        text_l = tk.Label(frame, text=label, bg=COLORS["sidebar"], fg=COLORS["subtext"],
                          font=("Georgia", 12), anchor="w", pady=10)
        text_l.pack(side="left", fill="x", expand=True)

        def click(e=None, k=key): self._switch_tab(k)
        def enter(e, f=frame, il=icon_l, tl=text_l):
            if getattr(self, "_current_tab", None) != key:
                f.configure(bg=COLORS["card2"]); il.configure(bg=COLORS["card2"]); tl.configure(bg=COLORS["card2"])
        def leave(e, f=frame, il=icon_l, tl=text_l):
            if getattr(self, "_current_tab", None) != key:
                f.configure(bg=COLORS["sidebar"]); il.configure(bg=COLORS["sidebar"]); tl.configure(bg=COLORS["sidebar"])

        for w in (frame, icon_l, text_l):
            w.bind("<Button-1>", click)
            w.bind("<Enter>", enter)
            w.bind("<Leave>", leave)

        self.nav_btns[key] = (frame, icon_l, text_l)

    def _preload_all(self):
        """Build every page once at startup — switching becomes instant (just .lift/.lower)."""
        for key in ["tasks", "projects", "finance", "charts", "progress", "ai"]:
            page = self._build_page(key)
            self.pages[key] = page
            page.place(relx=0, rely=0, relwidth=1, relheight=1)
            page.lower()

    def _build_page(self, key):
        if key == "tasks":
            from tasks_tab import TasksTab
            return TasksTab(self.content)
        elif key == "projects":
            from projects_tab import ProjectsTab
            return ProjectsTab(self.content)
        elif key == "finance":
            from finance_tab import FinanceTab
            return FinanceTab(self.content)
        elif key == "charts":
            from charts_tab import ChartsTab
            return ChartsTab(self.content)
        elif key == "progress":
            from progress_tab import ProgressTab
            return ProgressTab(self.content)
        elif key == "ai":
            from ai_chat_tab import AIChatTab
            return AIChatTab(self.content)

    def refresh_projects(self):
        """Called by AI tab after it creates a project — reload the projects page."""
        p = self.pages.get("projects")
        if p and hasattr(p, "refresh"):
            p.refresh()

    def _switch_tab(self, key):
        self._current_tab = key
        for k, (frame, icon_l, text_l) in self.nav_btns.items():
            if k == key:
                frame.configure(bg=COLORS["card2"])
                icon_l.configure(bg=COLORS["card2"], fg=COLORS["accent"])
                text_l.configure(bg=COLORS["card2"], fg=COLORS["text"])
            else:
                frame.configure(bg=COLORS["sidebar"])
                icon_l.configure(bg=COLORS["sidebar"], fg=COLORS["subtext"])
                text_l.configure(bg=COLORS["sidebar"], fg=COLORS["subtext"])
        # Instant: just raise / lower — no rebuild, no pack/forget
        for k, page in self.pages.items():
            page.lift() if k == key else page.lower()


if __name__ == "__main__":
    app = TaskFlowApp()
    app.mainloop()
