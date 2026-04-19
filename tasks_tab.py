import customtkinter as ctk
from tkinter import messagebox
import tkinter as tk
from datetime import date
from date_picker import DatePicker
import database as db

TASK_CATEGORIES = ["General","Work","Personal","Health","Finance","Shopping","Learning","Other"]
PRIORITIES = ["Low","Medium","High","Critical"]
STATUSES   = ["Pending","In Progress","Completed","Cancelled"]

COLORS = {
    "bg":"#0F1117","card":"#1A1D27","card2":"#22263A",
    "accent":"#6C63FF","success":"#43E97B","warning":"#F7971E",
    "danger":"#FF4B4B","text":"#E8E9F3","subtext":"#8B8FA8","border":"#2E3250",
}
PRIORITY_COLORS = {"Low":"#43E97B","Medium":"#6C63FF","High":"#F7971E","Critical":"#FF4B4B"}
STATUS_COLORS   = {"Pending":"#6C63FF","In Progress":"#F7971E","Completed":"#43E97B","Cancelled":"#8B8FA8"}


class TaskDialog(ctk.CTkToplevel):
    def __init__(self, parent, task=None, on_save=None, default_project_id=None):
        super().__init__(parent)
        self.task = task; self.on_save = on_save
        self.default_project_id = default_project_id
        self.title("Edit Task" if task else "New Task")
        self.geometry("580x720"); self.configure(fg_color=COLORS["bg"])
        self.resizable(False, False); self.grab_set()
        self._projects = db.get_projects()
        self._build()
        if task: self._populate(task)

    def _build(self):
        ctk.CTkLabel(self, text="✦  TASK DETAILS", font=("Georgia",13,"bold"),
                     text_color=COLORS["accent"]).pack(pady=(24,6), padx=28, anchor="w")
        card = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=14)
        card.pack(fill="x", padx=24, pady=6)
        f = ctk.CTkFrame(card, fg_color="transparent"); f.pack(fill="x", padx=18, pady=16)

        def lbl(t):
            ctk.CTkLabel(f, text=t, font=("Georgia",11), text_color=COLORS["subtext"], anchor="w").pack(fill="x")
        def inp(**kw):
            return ctk.CTkEntry(f, fg_color=COLORS["card2"], border_color=COLORS["border"],
                                border_width=1, text_color=COLORS["text"], height=36, **kw)

        lbl("Title *"); self.title_e = inp(); self.title_e.pack(fill="x", pady=(2,12))

        lbl("Description")
        self.desc_e = ctk.CTkTextbox(f, height=60, fg_color=COLORS["card2"],
                                      border_color=COLORS["border"], border_width=1, text_color=COLORS["text"])
        self.desc_e.pack(fill="x", pady=(2,12))

        # Project
        lbl("Project (optional)")
        proj_names = ["None"] + [p["name"] for p in self._projects]
        self.proj_var = ctk.StringVar(value="None")
        # Pre-select if default_project_id set
        if self.default_project_id:
            for p in self._projects:
                if p["id"] == self.default_project_id:
                    self.proj_var.set(p["name"]); break
        ctk.CTkOptionMenu(f, variable=self.proj_var, values=proj_names,
                          fg_color=COLORS["card2"], button_color=COLORS["accent"],
                          dropdown_fg_color=COLORS["card"]).pack(fill="x", pady=(2,12))

        r1=ctk.CTkFrame(f,fg_color="transparent"); r1.pack(fill="x")
        c1=ctk.CTkFrame(r1,fg_color="transparent"); c1.pack(side="left",fill="x",expand=True,padx=(0,6))
        c2=ctk.CTkFrame(r1,fg_color="transparent"); c2.pack(side="left",fill="x",expand=True)
        ctk.CTkLabel(c1,text="Category",font=("Georgia",11),text_color=COLORS["subtext"]).pack(fill="x")
        self.cat_var=ctk.StringVar(value="General")
        ctk.CTkOptionMenu(c1,variable=self.cat_var,values=TASK_CATEGORIES,fg_color=COLORS["card2"],
                          button_color=COLORS["accent"],dropdown_fg_color=COLORS["card"]).pack(fill="x",pady=(2,12))
        ctk.CTkLabel(c2,text="Priority",font=("Georgia",11),text_color=COLORS["subtext"]).pack(fill="x")
        self.pri_var=ctk.StringVar(value="Medium")
        ctk.CTkOptionMenu(c2,variable=self.pri_var,values=PRIORITIES,fg_color=COLORS["card2"],
                          button_color=COLORS["accent"],dropdown_fg_color=COLORS["card"]).pack(fill="x",pady=(2,12))

        lbl("Status"); self.status_var=ctk.StringVar(value="Pending")
        ctk.CTkOptionMenu(f,variable=self.status_var,values=STATUSES,fg_color=COLORS["card2"],
                          button_color=COLORS["accent"],dropdown_fg_color=COLORS["card"]).pack(fill="x",pady=(2,12))

        r2=ctk.CTkFrame(f,fg_color="transparent"); r2.pack(fill="x")
        c3=ctk.CTkFrame(r2,fg_color="transparent"); c3.pack(side="left",fill="x",expand=True,padx=(0,6))
        c4=ctk.CTkFrame(r2,fg_color="transparent"); c4.pack(side="left",fill="x",expand=True)
        ctk.CTkLabel(c3,text="Start Date",font=("Georgia",11),text_color=COLORS["subtext"]).pack(fill="x")
        self.start_dp=DatePicker(c3,width=160); self.start_dp.pack(fill="x",pady=(2,12))
        ctk.CTkLabel(c4,text="End Date",font=("Georgia",11),text_color=COLORS["subtext"]).pack(fill="x")
        self.end_dp=DatePicker(c4,width=160); self.end_dp.pack(fill="x",pady=(2,12))

        btns=ctk.CTkFrame(self,fg_color="transparent"); btns.pack(fill="x",padx=24,pady=16)
        ctk.CTkButton(btns,text="Cancel",fg_color=COLORS["card2"],hover_color=COLORS["border"],
                      text_color=COLORS["subtext"],command=self.destroy).pack(side="left",expand=True,padx=(0,6))
        ctk.CTkButton(btns,text="✓  Save Task",fg_color=COLORS["accent"],hover_color="#5a52d5",
                      command=self._save).pack(side="left",expand=True)

    def _populate(self, t):
        self.title_e.insert(0, t["title"])
        if t["description"]: self.desc_e.insert("1.0", t["description"])
        self.cat_var.set(t["category"] or "General")
        self.pri_var.set(t["priority"] or "Medium")
        self.status_var.set(t["status"] or "Pending")
        if t.get("project_id"):
            for p in self._projects:
                if p["id"] == t["project_id"]: self.proj_var.set(p["name"]); break
        if t["start_date"]:
            try: self.start_dp.set_date(t["start_date"])
            except: pass
        if t["end_date"]:
            try: self.end_dp.set_date(t["end_date"])
            except: pass

    def _save(self):
        title = self.title_e.get().strip()
        if not title: messagebox.showerror("Error","Title is required.",parent=self); return
        desc   = self.desc_e.get("1.0","end").strip()
        start  = self.start_dp.get_date().strftime("%Y-%m-%d")
        end    = self.end_dp.get_date().strftime("%Y-%m-%d")
        pname  = self.proj_var.get()
        pid    = None
        for p in self._projects:
            if p["name"] == pname: pid = p["id"]; break
        if self.task:
            db.update_task(self.task["id"],title,desc,self.cat_var.get(),
                           self.status_var.get(),self.pri_var.get(),start,end,pid)
        else:
            db.add_task(title,desc,self.cat_var.get(),
                        self.status_var.get(),self.pri_var.get(),start,end,pid)
        if self.on_save: self.on_save()
        self.destroy()


class TasksTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.active_cat = "All"
        self._build(); self.load_tasks()

    def _build(self):
        top=ctk.CTkFrame(self,fg_color="transparent"); top.pack(fill="x",padx=22,pady=(18,8))
        ctk.CTkLabel(top,text="TASK MANAGER",font=("Georgia",20,"bold"),text_color=COLORS["text"]).pack(side="left")
        ctk.CTkButton(top,text="＋  New Task",fg_color=COLORS["accent"],hover_color="#5a52d5",
                      width=130,height=36,command=self.open_add).pack(side="right")

        fbar=ctk.CTkFrame(self,fg_color=COLORS["card"],corner_radius=12); fbar.pack(fill="x",padx=22,pady=(0,8))
        fi=ctk.CTkFrame(fbar,fg_color="transparent"); fi.pack(fill="x",padx=14,pady=10)
        ctk.CTkLabel(fi,text="Filter:",font=("Georgia",11,"bold"),text_color=COLORS["subtext"]).pack(side="left",padx=(0,10))
        ctk.CTkLabel(fi,text="Status",font=("Georgia",10),text_color=COLORS["subtext"]).pack(side="left")
        self.status_f=ctk.CTkOptionMenu(fi,values=["All"]+STATUSES,width=120,fg_color=COLORS["card2"],
                                        button_color=COLORS["border"],dropdown_fg_color=COLORS["card"],
                                        command=lambda _:self.load_tasks()); self.status_f.pack(side="left",padx=(4,10))
        ctk.CTkLabel(fi,text="Priority",font=("Georgia",10),text_color=COLORS["subtext"]).pack(side="left")
        self.pri_f=ctk.CTkOptionMenu(fi,values=["All"]+PRIORITIES,width=110,fg_color=COLORS["card2"],
                                     button_color=COLORS["border"],dropdown_fg_color=COLORS["card"],
                                     command=lambda _:self.load_tasks()); self.pri_f.pack(side="left",padx=(4,10))
        ctk.CTkLabel(fi,text="From",font=("Georgia",10),text_color=COLORS["subtext"]).pack(side="left")
        self.from_dp=DatePicker(fi,on_change=lambda _:self.load_tasks(),width=130); self.from_dp.pack(side="left",padx=(4,8))
        ctk.CTkLabel(fi,text="To",font=("Georgia",10),text_color=COLORS["subtext"]).pack(side="left")
        self.to_dp=DatePicker(fi,on_change=lambda _:self.load_tasks(),width=130); self.to_dp.pack(side="left",padx=(4,10))
        ctk.CTkButton(fi,text="↺ Reset",width=80,height=30,fg_color=COLORS["card2"],hover_color=COLORS["border"],
                      text_color=COLORS["subtext"],command=self.reset_filters).pack(side="left")

        chips=ctk.CTkFrame(self,fg_color="transparent"); chips.pack(fill="x",padx=22,pady=(0,8))
        ctk.CTkLabel(chips,text="Category:",font=("Georgia",10),text_color=COLORS["subtext"]).pack(side="left",padx=(0,6))
        self.cat_btns={}
        for cat in ["All"]+TASK_CATEGORIES:
            btn=ctk.CTkButton(chips,text=cat,width=80,height=26,font=("Georgia",10),
                              fg_color=COLORS["accent"] if cat=="All" else COLORS["card2"],
                              hover_color=COLORS["accent"],corner_radius=20,
                              command=lambda c=cat:self.toggle_cat(c))
            btn.pack(side="left",padx=2); self.cat_btns[cat]=btn

        self.scroll=ctk.CTkScrollableFrame(self,fg_color="transparent")
        self.scroll.pack(fill="both",expand=True,padx=22,pady=(0,12))

    def toggle_cat(self,cat):
        self.active_cat=cat
        for c,b in self.cat_btns.items(): b.configure(fg_color=COLORS["accent"] if c==cat else COLORS["card2"])
        self.load_tasks()

    def reset_filters(self):
        self.status_f.set("All"); self.pri_f.set("All")
        self.from_dp.set_date(date.today()); self.to_dp.set_date(date.today())
        self.active_cat="All"
        for c,b in self.cat_btns.items(): b.configure(fg_color=COLORS["accent"] if c=="All" else COLORS["card2"])
        self.load_tasks()

    def get_filters(self):
        f={}
        if self.status_f.get()!="All": f["status"]=self.status_f.get()
        if self.pri_f.get()!="All": f["priority"]=self.pri_f.get()
        if self.active_cat!="All": f["category"]=self.active_cat
        return f

    def load_tasks(self):
        for w in self.scroll.winfo_children(): w.destroy()
        tasks=db.get_tasks(self.get_filters())
        if not tasks:
            ctk.CTkLabel(self.scroll,text="No tasks found. Add your first task! ✦",
                         font=("Georgia",14),text_color=COLORS["subtext"]).pack(pady=50); return
        for t in tasks: self._task_card(t)

    def _task_card(self,t):
        card=ctk.CTkFrame(self.scroll,fg_color=COLORS["card"],corner_radius=12); card.pack(fill="x",pady=5)
        row=ctk.CTkFrame(card,fg_color="transparent"); row.pack(fill="x",padx=14,pady=12)
        bar_c=PRIORITY_COLORS.get(t["priority"],COLORS["accent"])
        tk.Frame(row,bg=bar_c,width=4).pack(side="left",fill="y",padx=(0,12))
        ct=ctk.CTkFrame(row,fg_color="transparent"); ct.pack(side="left",fill="both",expand=True)
        tr=ctk.CTkFrame(ct,fg_color="transparent"); tr.pack(fill="x")
        ctk.CTkLabel(tr,text=t["title"],font=("Georgia",13,"bold"),text_color=COLORS["text"],anchor="w").pack(side="left")
        st_c=STATUS_COLORS.get(t["status"],COLORS["subtext"])
        ctk.CTkLabel(tr,text=f"● {t['status']}",font=("Georgia",10),text_color=st_c).pack(side="right")
        meta=ctk.CTkFrame(ct,fg_color="transparent"); meta.pack(fill="x",pady=(3,0))
        tk.Label(meta,text=t["category"],bg=COLORS["card2"],fg=COLORS["subtext"],font=("Georgia",9),padx=7,pady=2).pack(side="left",padx=(0,4))
        tk.Label(meta,text=t["priority"],bg=COLORS["card2"],fg=bar_c,font=("Georgia",9),padx=7,pady=2).pack(side="left",padx=(0,4))
        # Project badge
        if t.get("project_name"):
            pc = t.get("project_color") or COLORS["accent"]
            tk.Label(meta,text=f"⬡ {t['project_name']}",bg=COLORS["card2"],fg=pc,
                     font=("Georgia",9),padx=7,pady=2).pack(side="left",padx=(0,4))
        if t["start_date"] or t["end_date"]:
            ctk.CTkLabel(meta,text=f"  📅 {t['start_date'] or '?'} → {t['end_date'] or '?'}",
                         font=("Georgia",10),text_color=COLORS["subtext"]).pack(side="left",padx=6)
        if t["description"]:
            prev=t["description"][:90]+("…" if len(t["description"])>90 else "")
            ctk.CTkLabel(ct,text=prev,font=("Georgia",10),text_color=COLORS["subtext"],anchor="w").pack(fill="x",pady=(4,0))
        ac=ctk.CTkFrame(row,fg_color="transparent"); ac.pack(side="right",padx=(8,0))
        ctk.CTkButton(ac,text="✎",width=32,height=32,fg_color=COLORS["card2"],hover_color=COLORS["accent"],
                      command=lambda t=t:self.open_edit(t)).pack(pady=2)
        ctk.CTkButton(ac,text="✕",width=32,height=32,fg_color=COLORS["card2"],hover_color=COLORS["danger"],
                      command=lambda t=t:self.confirm_delete(t)).pack(pady=2)

    def open_add(self): TaskDialog(self,on_save=self.load_tasks)
    def open_edit(self,t): TaskDialog(self,task=t,on_save=self.load_tasks)
    def confirm_delete(self,t):
        if messagebox.askyesno("Delete Task",f"Delete '{t['title']}'?"): db.delete_task(t["id"]); self.load_tasks()
