import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import database as db

PROJECT_COLORS   = ["#6C63FF","#43E97B","#FF6584","#F7971E","#38BDF8","#E879F9","#FB923C","#A3E635","#FF4B4B","#14B8A6"]
PROJECT_STATUSES = ["Active","On Hold","Completed","Archived"]

COLORS = {
    "bg":     "#0F1117",
    "card":   "#1A1D27",
    "card2":  "#22263A",
    "accent": "#6C63FF",
    "success":"#43E97B",
    "danger": "#FF4B4B",
    "warning":"#F7971E",
    "text":   "#E8E9F3",
    "subtext":"#8B8FA8",
    "border": "#2E3250",
}


# ══════════════════════════════════════════════════════════════════════════════
class ProjectDialog(ctk.CTkToplevel):
    def __init__(self, parent, project=None, on_save=None):
        super().__init__(parent)
        self.project        = project
        self.on_save        = on_save
        self.selected_color = project["color"] if project else PROJECT_COLORS[0]

        self.title("Edit Project" if project else "New Project")
        self.geometry("500x560")
        self.configure(fg_color=COLORS["bg"])
        self.resizable(False, False)
        self.grab_set()
        self._build()
        if project:
            self._populate(project)

    def _build(self):
        ctk.CTkLabel(self,
                     text="✦  NEW PROJECT" if not self.project else "✦  EDIT PROJECT",
                     font=("Georgia", 14, "bold"),
                     text_color=COLORS["accent"]).pack(pady=(24, 8), padx=28, anchor="w")

        card = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=14)
        card.pack(fill="x", padx=24, pady=(0, 8))
        f = ctk.CTkFrame(card, fg_color="transparent")
        f.pack(fill="x", padx=18, pady=18)

        def lbl(txt):
            ctk.CTkLabel(f, text=txt, font=("Georgia", 11),
                         text_color=COLORS["subtext"], anchor="w").pack(fill="x")

        lbl("Project Name *")
        self.name_e = ctk.CTkEntry(f, fg_color=COLORS["card2"],
                                    border_color=COLORS["border"], border_width=1,
                                    text_color=COLORS["text"], height=38)
        self.name_e.pack(fill="x", pady=(2, 12))

        lbl("Description")
        self.desc_e = ctk.CTkTextbox(f, height=64, fg_color=COLORS["card2"],
                                      border_color=COLORS["border"], border_width=1,
                                      text_color=COLORS["text"])
        self.desc_e.pack(fill="x", pady=(2, 12))

        lbl("Status")
        self.status_var = ctk.StringVar(value="Active")
        ctk.CTkOptionMenu(f, variable=self.status_var, values=PROJECT_STATUSES,
                          fg_color=COLORS["card2"], button_color=COLORS["accent"],
                          dropdown_fg_color=COLORS["card"]).pack(fill="x", pady=(2, 14))

        lbl("Project Color")
        cf = tk.Frame(f, bg=COLORS["card"])
        cf.pack(fill="x", pady=(4, 4))
        self._color_indicators = {}
        for col in PROJECT_COLORS:
            size = 28
            cv = tk.Canvas(cf, width=size, height=size, bg=COLORS["card"],
                           highlightthickness=0, cursor="hand2")
            cv.pack(side="left", padx=3)
            cv.create_rectangle(2, 2, size-2, size-2, fill=col, outline="", width=0)
            cv.bind("<Button-1>", lambda e, c=col: self._pick_color(c))
            self._color_indicators[col] = cv
        self._pick_color(self.selected_color)

        # Buttons always outside the card so they're never hidden
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=24, pady=(8, 20))
        ctk.CTkButton(btn_frame, text="Cancel",
                      fg_color=COLORS["card2"], hover_color=COLORS["border"],
                      text_color=COLORS["subtext"], height=44,
                      command=self.destroy).pack(side="left", expand=True, fill="x", padx=(0, 8))
        label = "✓  Save Changes" if self.project else "✦  Create Project"
        ctk.CTkButton(btn_frame, text=label,
                      fg_color=COLORS["accent"], hover_color="#5a52d5",
                      text_color="white", height=44, font=("Georgia", 13, "bold"),
                      command=self._save).pack(side="left", expand=True, fill="x")

    def _pick_color(self, col):
        self.selected_color = col
        for c, cv in self._color_indicators.items():
            cv.configure(highlightthickness=2 if c == col else 0,
                         highlightbackground="white")

    def _populate(self, p):
        self.name_e.insert(0, p["name"])
        if p.get("description"):
            self.desc_e.insert("1.0", p["description"])
        self.status_var.set(p.get("status") or "Active")
        self._pick_color(p.get("color") or PROJECT_COLORS[0])

    def _save(self):
        name = self.name_e.get().strip()
        if not name:
            messagebox.showerror("Error", "Project name is required.", parent=self)
            return
        desc   = self.desc_e.get("1.0", "end").strip()
        status = self.status_var.get()
        color  = self.selected_color
        if self.project:
            db.update_project(self.project["id"], name, desc, color, status)
        else:
            db.add_project(name, desc, color, status)
        if self.on_save:
            self.on_save()
        self.destroy()


# ══════════════════════════════════════════════════════════════════════════════
class ProjectTasksDialog(ctk.CTkToplevel):
    """Full-screen popup: lists tasks for a project + inline add/edit/delete."""

    def __init__(self, parent, project, on_change=None):
        super().__init__(parent)
        self.project   = project
        self.on_change = on_change
        self.title(f"Tasks — {project['name']}")
        self.geometry("740x640")
        self.configure(fg_color=COLORS["bg"])
        self.grab_set()
        self._build()
        self._load()

    def _build(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=(16, 8))

        # Colour dot
        dot = tk.Canvas(top, width=16, height=16, bg=COLORS["bg"], highlightthickness=0)
        dot.create_oval(0, 0, 16, 16, fill=self.project["color"], outline="")
        dot.pack(side="left", padx=(0, 10))

        ctk.CTkLabel(top, text=self.project["name"],
                     font=("Georgia", 16, "bold"), text_color=COLORS["text"]).pack(side="left")

        # Refresh + Add buttons
        btn_row = ctk.CTkFrame(top, fg_color="transparent")
        btn_row.pack(side="right")
        ctk.CTkButton(btn_row, text="↺ Refresh", width=90, height=32,
                      fg_color=COLORS["card2"], hover_color=COLORS["border"],
                      text_color=COLORS["subtext"], command=self._load).pack(side="left", padx=(0, 6))
        ctk.CTkButton(btn_row, text="＋  Add Task", width=120, height=32,
                      fg_color=COLORS["accent"], hover_color="#5a52d5",
                      command=self._add_task).pack(side="left")

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=20, pady=(0, 16))

    def _load(self):
        for w in self.scroll.winfo_children():
            w.destroy()
        tasks = db.get_tasks({"project_id": self.project["id"]})
        if not tasks:
            ctk.CTkLabel(self.scroll, text="No tasks yet — click ＋ Add Task!",
                         font=("Georgia", 13), text_color=COLORS["subtext"]).pack(pady=40)
            return

        pc = {"Pending":"#6C63FF","In Progress":"#F7971E",
              "Completed":"#43E97B","Cancelled":"#8B8FA8"}
        for t in tasks:
            card = ctk.CTkFrame(self.scroll, fg_color=COLORS["card"], corner_radius=10)
            card.pack(fill="x", pady=4)
            row  = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=10)
            tk.Frame(row, bg=self.project["color"], width=4).pack(side="left", fill="y", padx=(0,10))
            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(side="left", fill="both", expand=True)
            tr = ctk.CTkFrame(info, fg_color="transparent"); tr.pack(fill="x")
            ctk.CTkLabel(tr, text=t["title"], font=("Georgia", 12, "bold"),
                         text_color=COLORS["text"]).pack(side="left")
            ctk.CTkLabel(tr, text=f"● {t['status']}", font=("Georgia", 10),
                         text_color=pc.get(t["status"], COLORS["subtext"])).pack(side="right")
            meta = f"{t['priority']}  •  {t.get('start_date','?')} → {t.get('end_date','?')}"
            ctk.CTkLabel(info, text=meta, font=("Georgia", 10),
                         text_color=COLORS["subtext"]).pack(anchor="w")
            if t.get("description"):
                ctk.CTkLabel(info, text=t["description"][:80],
                             font=("Georgia", 10), text_color=COLORS["subtext"],
                             anchor="w").pack(fill="x", pady=(2, 0))
            act = ctk.CTkFrame(row, fg_color="transparent"); act.pack(side="right")
            ctk.CTkButton(act, text="✎", width=30, height=30,
                          fg_color=COLORS["card2"], hover_color=COLORS["accent"],
                          command=lambda t=t: self._edit_task(t)).pack(pady=(0,4))
            ctk.CTkButton(act, text="✕", width=30, height=30,
                          fg_color=COLORS["card2"], hover_color=COLORS["danger"],
                          command=lambda t=t: self._del_task(t)).pack()

    def _add_task(self):
        from tasks_tab import TaskDialog
        TaskDialog(self, on_save=self._on_task_saved, default_project_id=self.project["id"])

    def _edit_task(self, t):
        from tasks_tab import TaskDialog
        TaskDialog(self, task=t, on_save=self._on_task_saved)

    def _on_task_saved(self):
        self._load()
        if self.on_change:
            self.on_change()

    def _del_task(self, t):
        if messagebox.askyesno("Delete", f"Delete '{t['title']}'?"):
            db.delete_task(t["id"])
            self._on_task_saved()


# ══════════════════════════════════════════════════════════════════════════════
class ProjectsTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._build()
        self._load()

    # Public method so AI tab can trigger a refresh
    def refresh(self):
        self._load()

    def _build(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=22, pady=(18, 8))

        ctk.CTkLabel(top, text="PROJECTS",
                     font=("Georgia", 20, "bold"), text_color=COLORS["text"]).pack(side="left")

        btn_row = ctk.CTkFrame(top, fg_color="transparent")
        btn_row.pack(side="right")

        # ← Refresh button
        ctk.CTkButton(btn_row, text="↺  Refresh",
                      fg_color=COLORS["card2"], hover_color=COLORS["border"],
                      text_color=COLORS["subtext"], width=110, height=38,
                      command=self._load).pack(side="left", padx=(0, 8))

        ctk.CTkButton(btn_row, text="✦  New Project",
                      fg_color=COLORS["accent"], hover_color="#5a52d5",
                      width=148, height=38, font=("Georgia", 12, "bold"),
                      command=self._new).pack(side="left")

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=22, pady=(0, 12))

    def _load(self):
        for w in self.scroll.winfo_children():
            w.destroy()

        projects = db.get_projects()
        counts   = db.get_project_task_counts()

        if not projects:
            ctk.CTkLabel(self.scroll,
                         text="No projects yet.\nClick  ✦ New Project  to get started!",
                         font=("Georgia", 14), text_color=COLORS["subtext"],
                         justify="center").pack(pady=80)
            return

        grid = ctk.CTkFrame(self.scroll, fg_color="transparent")
        grid.pack(fill="both", expand=True)
        for col in range(3):
            grid.grid_columnconfigure(col, weight=1)

        for i, p in enumerate(projects):
            self._project_card(grid, p,
                               counts.get(p["id"], {"total":0,"done":0}),
                               row=i//3, col=i%3)

    def _project_card(self, parent, p, cnt, row, col):
        card = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=14)
        card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

        tk.Frame(card, bg=p["color"], height=6).pack(fill="x")

        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=14, pady=12)

        # Name + status
        nr = ctk.CTkFrame(body, fg_color="transparent"); nr.pack(fill="x")
        ctk.CTkLabel(nr, text=p["name"], font=("Georgia", 14, "bold"),
                     text_color=COLORS["text"]).pack(side="left")
        st_c = {"Active":COLORS["success"],"On Hold":COLORS["warning"],
                "Completed":COLORS["accent"],"Archived":COLORS["subtext"]}
        ctk.CTkLabel(nr, text=p["status"], font=("Georgia", 9),
                     text_color=st_c.get(p["status"], COLORS["subtext"])).pack(side="right")

        # Description
        if p.get("description"):
            ctk.CTkLabel(body,
                         text=p["description"][:72]+("…" if len(p["description"])>72 else ""),
                         font=("Georgia", 10), text_color=COLORS["subtext"],
                         anchor="w", wraplength=210, justify="left").pack(fill="x", pady=(4,8))
        else:
            ctk.CTkFrame(body, fg_color="transparent", height=8).pack()

        # Progress bar
        total = cnt["total"]; done = cnt["done"]
        pct   = done / total if total else 0
        pb_bg = tk.Frame(body, bg=COLORS["card2"], height=6)
        pb_bg.pack(fill="x", pady=(0, 2))
        if pct > 0:
            tk.Frame(pb_bg, bg=p["color"], height=6).place(relwidth=pct, relheight=1)
        ctk.CTkLabel(body, text=f"{done}/{total} tasks  ({int(pct*100)}%)",
                     font=("Georgia", 9), text_color=COLORS["subtext"]).pack(anchor="w")

        # ── Action buttons ──────────────────────────────────────────────────
        btns = ctk.CTkFrame(body, fg_color="transparent")
        btns.pack(fill="x", pady=(10, 0))

        # Open Tasks (full dialog)
        ctk.CTkButton(btns, text="Open Tasks",
                      fg_color=p["color"], hover_color=p["color"],
                      height=32, font=("Georgia", 10),
                      command=lambda p=p: ProjectTasksDialog(self, p, on_change=self._load),
                      ).pack(side="left", expand=True, fill="x", padx=(0, 3))

        # ＋ Add Task — directly open TaskDialog pre-set to this project
        ctk.CTkButton(btns, text="＋", width=32, height=32,
                      fg_color=COLORS["success"], hover_color="#2dc960",
                      font=("Georgia", 14),
                      command=lambda p=p: self._add_task_to(p),
                      ).pack(side="left", padx=(0, 3))

        ctk.CTkButton(btns, text="✎", width=32, height=32,
                      fg_color=COLORS["card2"], hover_color=COLORS["accent"],
                      command=lambda p=p: ProjectDialog(self, p, on_save=self._load),
                      ).pack(side="left", padx=(0, 3))

        ctk.CTkButton(btns, text="✕", width=32, height=32,
                      fg_color=COLORS["card2"], hover_color=COLORS["danger"],
                      command=lambda p=p: self._del(p),
                      ).pack(side="left")

    def _add_task_to(self, project):
        """Open the TaskDialog directly from the project card."""
        from tasks_tab import TaskDialog
        TaskDialog(self, on_save=self._load, default_project_id=project["id"])

    def _new(self):
        ProjectDialog(self, on_save=self._load)

    def _del(self, p):
        if messagebox.askyesno("Delete Project",
                               f"Delete '{p['name']}'?\nTasks will be unlinked."):
            db.delete_project(p["id"])
            self._load()
