"""
AI Chat Tab — Ollama-powered assistant with full action support.

Flow for actions:
  1. User asks to create/add something
  2. AI generates a plan (JSON)
  3. We render an EDITABLE preview card in the chat
  4. User edits fields inline, then clicks Confirm or Cancel
  5. On confirm → execute DB writes

Q&A questions (no action) → just show the AI reply as a bubble.
"""

import customtkinter as ctk
import tkinter as tk
import threading
import json
import re
import urllib.request
import urllib.error
from datetime import date, timedelta
import database as db

# ─── colours ──────────────────────────────────────────────────────────────────
C = {
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
    "user_bg":  "#2D2F4A",
    "ai_bg":    "#1A1F35",
    "edit_bg":  "#22263A",
    "confirm":  "#1A2F1A",
}

OLLAMA_URL   = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2"

SUGGESTED = [
    "What is my financial balance?",
    "Show me pending high-priority tasks",
    "Plan a House Renovation project",
    "Add a task to my Work project",
    "What are my top expenses this month?",
    "Which tasks are overdue?",
]

# ─── Two separate prompts — one for Q&A, one for actions ─────────────────────

# Intent classifier remains the same
CLASSIFY_PROMPT = """\
You are a classifier. The user message is either:
- ACTION: user wants to create a project, plan a project, add tasks, or modify data
- QUESTION: user wants information, analysis, or details about their data

Reply with exactly one word: ACTION or QUESTION

User: {msg}
Answer:"""

# Q&A prompt remains mostly the same (only small improvement)
QA_PROMPT = """\
You are a smart personal assistant inside TaskFlow, a task and finance management app.
Answer questions clearly, in detail, using bullet points and structure where helpful.
Use the user's real data below. Format currency as EGP.

IMPORTANT RULES:
- Today is {today}. A task is OVERDUE if its end_date < today AND status is not Completed or Cancelled.
- The OVERDUE TASKS section below is pre-calculated — trust it completely.
- When listing tasks, always show: title, status, priority, end_date, and project.
- When showing finances, be specific with numbers.
- Be conversational and helpful.

USER DATA:
{context}
"""

# ==================== MAIN IMPROVEMENT: ACTION_PROMPT ====================
ACTION_PROMPT = """\
You are an action executor inside TaskFlow. Respond with ONLY a valid JSON object — no extra text.

Schema:
{
  "action": "create_project" or "add_task",
  "message": "Brief friendly summary of what you planned",
  "plan": {
    "project_name": "Clean project name",
    "project_description": "Short description",
    "tasks": [ ... ]     // only used for create_project
  }
}

For add_task, use this simpler plan instead:
{
  "project_name": "existing project name or empty string",
  "title": "...",
  "description": "...",
  "priority": "Low|Medium|High|Critical",
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD",
  "category": "..."
}

CRITICAL PLANNING RULES:

1. PROJECT NAME HANDLING:
   - Always create a new project if the user is asking to "plan", "create", or "build" something.
   - Extract a clean, professional project name. Examples:
     - "work and javascript" → "Work & JavaScript"
     - "creating web app project" → "Web Application Development"
     - "house renovation" → "House Renovation"
   - Never refuse to create a project. If the name doesn't exist, create it.

2. NUMBER OF TASKS:
   - If the user specifies a number (e.g. "5 tasks", "with 8 tasks", "plan with 6 steps"), generate EXACTLY that number of tasks.
   - If no number is mentioned, generate 5–7 high-quality, realistic tasks.
   - Minimum 3 tasks, maximum 10.

3. TASK QUALITY (especially important for learning/coding projects):
   - Make tasks logical, sequential, and complete enough to finish the project.
   - For JavaScript / Web App projects, include: setup, learning, building features, testing, deployment.
   - Give each task a clear, actionable title and useful 1-2 sentence description.
   - Use realistic deadlines starting from today.
   - Priorities: Mix of Medium and High. Use "Critical" only for setup/foundation tasks.

4. General Rules:
   - Today is {today}. Use YYYY-MM-DD format for all dates.
   - Spread tasks over 2–8 weeks depending on project size.
   - Categories: Use "Learning" for study-related, "Work" for professional, etc.
   - Always include at least one task for planning/setup and one for review/testing.

USER DATA (existing projects and tasks):
{context}
"""



def _classify_intent(user_msg: str) -> str:
    """Returns 'ACTION' or 'QUESTION'. Fast single-word call."""
    prompt = CLASSIFY_PROMPT.replace("{msg}", user_msg)
    payload = json.dumps({
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.0, "num_predict": 5},
    }).encode()
    req = urllib.request.Request(
        OLLAMA_URL, data=payload,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            word = json.loads(r.read())["response"].strip().upper()
            return "ACTION" if "ACTION" in word else "QUESTION"
    except Exception:
        return "QUESTION"


def _call_qa(user_msg: str, context: str, history: list) -> str:
    """Plain-text Q&A call — returns a string answer."""
    today = date.today().isoformat()
    system = QA_PROMPT.replace("{today}", today).replace("{context}", context)

    conv = ""
    for m in history[-10:]:
        role = "User" if m["role"] == "user" else "Assistant"
        conv += f"{role}: {m['content']}\n"
    conv += f"User: {user_msg}\nAssistant:"

    payload = json.dumps({
        "model": OLLAMA_MODEL,
        "prompt": f"{system}\n\n{conv}",
        "stream": False,
        "options": {"temperature": 0.3, "num_predict": 2048},
    }).encode()

    req = urllib.request.Request(
        OLLAMA_URL, data=payload,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())["response"].strip()
    except urllib.error.URLError as e:
        raise ConnectionError(
            f"⚠️ Cannot reach Ollama.\nRun: ollama serve\nThen: ollama pull {OLLAMA_MODEL}\n\nError: {e}"
        )


def _call_action(user_msg: str, context: str, history: list) -> dict:
    """JSON action call — returns parsed dict with action + plan."""
    today = date.today().isoformat()
    system = ACTION_PROMPT.replace("{today}", today).replace("{context}", context)

    conv = ""
    for m in history[-6:]:
        role = "User" if m["role"] == "user" else "Assistant"
        conv += f"{role}: {m['content']}\n"
    conv += f"User: {user_msg}\nAssistant:"

    payload = json.dumps({
        "model": OLLAMA_MODEL,
        "prompt": f"{system}\n\n{conv}",
        "stream": False,
        "options": {"temperature": 0.2, "num_predict": 2048},
    }).encode()

    req = urllib.request.Request(
        OLLAMA_URL, data=payload,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            raw = json.loads(r.read())["response"].strip()
    except urllib.error.URLError as e:
        raise ConnectionError(
            f"⚠️ Cannot reach Ollama.\nRun: ollama serve\nThen: ollama pull {OLLAMA_MODEL}\n\nError: {e}"
        )

    # Parse JSON tolerantly
    clean = re.sub(r"```(?:json)?|```", "", raw).strip()
    m = re.search(r"\{.*\}", clean, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except Exception:
            pass
    # Fallback: treat as Q&A reply
    return {"action": "none", "message": raw, "plan": {}}


def _build_context() -> str:
    today_date = date.today()
    today = today_date.isoformat()
    lines = [f"Today: {today}"]

    tasks = db.get_tasks()
    lines.append(f"\n=== TASKS ({len(tasks)}) ===")
    for t in tasks:
        proj = f" [Project: {t.get('project_name')}]" if t.get("project_name") else ""
        end_str = t.get("end_date", "") or ""
        # Flag overdue directly in the task line
        overdue_flag = ""
        if end_str and t["status"] not in ("Completed", "Cancelled"):
            try:
                if date.fromisoformat(end_str) < today_date:
                    days_late = (today_date - date.fromisoformat(end_str)).days
                    overdue_flag = f" ⚠️OVERDUE({days_late}d late)"
            except Exception:
                pass
        lines.append(
            f"- ID:{t['id']} [{t['status']}]{overdue_flag} | {t['title']} | {t['priority']} | start_date:{t.get('start_date','?')} | end_date:{end_str or '?'}{proj}"
        )
    if not tasks:
        lines.append("  (none)")

    # Dedicated overdue section so the AI never misses it
    overdue = []
    for t in tasks:
        end_str = t.get("end_date", "") or ""
        if end_str and t["status"] not in ("Completed", "Cancelled"):
            try:
                if date.fromisoformat(end_str) < today_date:
                    overdue.append(t)
            except Exception:
                pass
    lines.append(f"\n=== OVERDUE TASKS ({len(overdue)}) ===")
    if overdue:
        for t in overdue:
            proj = f" [Project: {t.get('project_name')}]" if t.get("project_name") else ""
            days_late = (today_date - date.fromisoformat(t["end_date"])).days
            lines.append(
                f"- ID:{t['id']} [{t['status']}] {t['title']} | due: {t['end_date']} | {days_late} day(s) overdue{proj}"
            )
    else:
        lines.append("  (none — all active tasks have future or no end dates)")

    projects = db.get_projects()
    counts   = db.get_project_task_counts()
    lines.append(f"\n=== PROJECTS ({len(projects)}) ===")
    for p in projects:
        c = counts.get(p["id"], {"total":0,"done":0})
        pct = int(c["done"]/c["total"]*100) if c["total"] else 0
        lines.append(f"- ID:{p['id']} [{p['status']}] {p['name']} | {c['done']}/{c['total']} tasks ({pct}%)")
    if not projects: lines.append("  (none)")

    try:
        inc, exp, _, _, by_cat, by_src, _ = db.get_finance_stats()
        lines.append(f"\n=== FINANCE ===")
        lines.append(f"Income: EGP {inc:,.0f}  Expense: EGP {exp:,.0f}  Balance: EGP {inc-exp:,.0f}")
        txns = db.get_transactions()
        lines.append(f"Transactions: {len(txns)}")
        for t in txns[:20]:
            lines.append(f"- [{t['type'].upper()}] EGP {t['amount']:,.0f} | {t['date']} | {t.get('category','—')}")
        if by_cat:
            top = sorted(by_cat.items(), key=lambda x:x[1], reverse=True)[:5]
            lines.append("Top expenses: " + ", ".join(f"{k} EGP {v:,.0f}" for k,v in top))
        if by_src:
            top = sorted(by_src.items(), key=lambda x:x[1], reverse=True)[:5]
            lines.append("Top income: " + ", ".join(f"{k} EGP {v:,.0f}" for k,v in top))
    except Exception:
        pass

    return "\n".join(lines)



# ─────────────────────────────────────────────────────────────────────────────
def _entry(parent, value="", width=None, **kw):
    """Styled inline entry widget."""
    kw.setdefault("fg_color", C["edit_bg"])
    kw.setdefault("border_color", C["border"])
    kw.setdefault("border_width", 1)
    kw.setdefault("text_color", C["text"])
    kw.setdefault("height", 30)
    kw.setdefault("font", ("Georgia", 11))
    e = ctk.CTkEntry(parent, **kw)
    if width: e.configure(width=width)
    if value: e.insert(0, str(value))
    return e


def _label(parent, text, color=None, font=None, **kw):
    color = color or C["subtext"]
    font  = font  or ("Georgia", 10)
    return ctk.CTkLabel(parent, text=text, text_color=color, font=font, **kw)


# ═════════════════════════════════════════════════════════════════════════════
class PlanCard(ctk.CTkFrame):
    """
    An inline editable card shown in the chat before the user confirms.
    Supports two modes:
      - create_project : shows project fields + editable task list
      - add_task       : shows a single task form
    """
    def __init__(self, parent, plan_data: dict, action: str, on_confirm, on_cancel):
        super().__init__(parent, fg_color=C["confirm"], corner_radius=14,
                         border_width=1, border_color=C["success"])
        self._plan    = plan_data
        self._action  = action
        self._on_confirm = on_confirm
        self._on_cancel  = on_cancel
        self._task_rows  = []   # list of dicts with entry widgets
        self._build()

    def _build(self):
        # Title bar
        hdr = ctk.CTkFrame(self, fg_color="#1F301F", corner_radius=0)
        hdr.pack(fill="x", padx=0, pady=(0,0))
        _label(hdr, "✦  PLAN PREVIEW — Review & Edit Before Confirming",
               color=C["success"], font=("Georgia", 11, "bold")).pack(side="left", padx=12, pady=8)

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="x", padx=14, pady=10)

        if self._action == "create_project":
            self._build_project_form(body)
        elif self._action == "add_task":
            self._build_task_form(body)

        # Confirm / Cancel buttons
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=14, pady=(4, 12))

        ctk.CTkButton(btn_row, text="✓  Confirm & Save",
                      fg_color=C["success"], hover_color="#30b050",
                      text_color="#0A1A0A", font=("Georgia", 12, "bold"),
                      height=38, command=self._confirm).pack(side="left", expand=True, fill="x", padx=(0,6))

        ctk.CTkButton(btn_row, text="✕  Cancel",
                      fg_color=C["card2"], hover_color=C["danger"],
                      text_color=C["subtext"], height=38,
                      command=self._cancel).pack(side="left", expand=True, fill="x")

    # ── Project form ──────────────────────────────────────────────────────────
    def _build_project_form(self, body):
        _label(body, "PROJECT NAME", color=C["success"], font=("Georgia", 9, "bold")).pack(anchor="w")
        self._proj_name = _entry(body, self._plan.get("project_name",""))
        self._proj_name.pack(fill="x", pady=(2,8))

        _label(body, "DESCRIPTION", color=C["success"], font=("Georgia", 9, "bold")).pack(anchor="w")
        self._proj_desc = ctk.CTkTextbox(body, height=50, fg_color=C["edit_bg"],
                                          border_color=C["border"], border_width=1,
                                          text_color=C["text"], font=("Georgia", 11))
        self._proj_desc.pack(fill="x", pady=(2,12))
        desc = self._plan.get("project_description","")
        if desc: self._proj_desc.insert("1.0", desc)

        # Tasks
        tasks = self._plan.get("tasks", [])
        _label(body, f"TASKS  ({len(tasks)})", color=C["success"], font=("Georgia", 9, "bold")).pack(anchor="w", pady=(0,4))

        self._tasks_frame = ctk.CTkScrollableFrame(body, fg_color="transparent", height=min(320, len(tasks)*90+20))
        self._tasks_frame.pack(fill="x")

        self._task_rows = []
        for i, t in enumerate(tasks):
            self._add_task_row(i, t)

        ctk.CTkButton(body, text="＋ Add Another Task", height=28,
                      fg_color=C["card2"], hover_color=C["accent"],
                      text_color=C["subtext"], font=("Georgia", 10),
                      command=self._add_blank_task_row).pack(anchor="w", pady=(6,0))

    def _add_task_row(self, idx: int, t: dict):
        row_frame = ctk.CTkFrame(self._tasks_frame, fg_color=C["card2"], corner_radius=8)
        row_frame.pack(fill="x", pady=3)

        top = ctk.CTkFrame(row_frame, fg_color="transparent")
        top.pack(fill="x", padx=8, pady=(6,2))

        # Index badge
        _label(top, f"#{idx+1}", color=C["accent"], font=("Georgia", 10, "bold")).pack(side="left", padx=(0,8))

        # Title
        title_e = _entry(top, t.get("title",""), font=("Georgia", 11, "bold"))
        title_e.pack(side="left", fill="x", expand=True, padx=(0,6))

        # Delete button
        del_btn = ctk.CTkButton(top, text="✕", width=26, height=26,
                                fg_color=C["card"], hover_color=C["danger"],
                                font=("Georgia",10),
                                command=lambda f=row_frame, i=idx: self._delete_task_row(f))
        del_btn.pack(side="right")

        mid = ctk.CTkFrame(row_frame, fg_color="transparent")
        mid.pack(fill="x", padx=8, pady=2)

        # Priority
        _label(mid, "Priority:", color=C["subtext"]).pack(side="left", padx=(0,4))
        pri_var = ctk.StringVar(value=t.get("priority","Medium"))
        pri_menu = ctk.CTkOptionMenu(mid, variable=pri_var,
                                     values=["Low","Medium","High","Critical"],
                                     width=110, height=26, font=("Georgia",10),
                                     fg_color=C["card"], button_color=C["accent"],
                                     dropdown_fg_color=C["card"])
        pri_menu.pack(side="left", padx=(0,10))

        # Category
        _label(mid, "Category:", color=C["subtext"]).pack(side="left", padx=(0,4))
        cat_var = ctk.StringVar(value=t.get("category","General"))
        cat_menu = ctk.CTkOptionMenu(mid, variable=cat_var,
                                     values=["General","Work","Personal","Health","Finance","Shopping","Learning","Other"],
                                     width=120, height=26, font=("Georgia",10),
                                     fg_color=C["card"], button_color=C["accent"],
                                     dropdown_fg_color=C["card"])
        cat_menu.pack(side="left", padx=(0,10))

        # Start / End dates
        _label(mid, "Start:", color=C["subtext"]).pack(side="left", padx=(0,4))
        start_e = _entry(mid, t.get("start_date", date.today().isoformat()), width=100)
        start_e.pack(side="left", padx=(0,8))

        _label(mid, "End:", color=C["subtext"]).pack(side="left", padx=(0,4))
        end_e = _entry(mid, t.get("end_date",""), width=100)
        end_e.pack(side="left")

        # Description
        bot = ctk.CTkFrame(row_frame, fg_color="transparent")
        bot.pack(fill="x", padx=8, pady=(2,6))
        _label(bot, "Description:", color=C["subtext"]).pack(anchor="w")
        desc_box = ctk.CTkTextbox(bot, height=44, fg_color=C["bg"],
                                   border_color=C["border"], border_width=1,
                                   text_color=C["text"], font=("Georgia",10))
        desc_box.pack(fill="x")
        if t.get("description"): desc_box.insert("1.0", t["description"])

        row_data = {
            "frame": row_frame,
            "title_e": title_e,
            "pri_var": pri_var,
            "cat_var": cat_var,
            "start_e": start_e,
            "end_e": end_e,
            "desc_box": desc_box,
        }
        self._task_rows.append(row_data)

    def _add_blank_task_row(self):
        idx = len(self._task_rows)
        tomorrow = (date.today() + timedelta(days=7)).isoformat()
        self._add_task_row(idx, {"title":"New Task","priority":"Medium",
                                  "category":"General","start_date":date.today().isoformat(),
                                  "end_date":tomorrow,"description":""})

    def _delete_task_row(self, frame):
        frame.destroy()
        self._task_rows = [r for r in self._task_rows if r["frame"].winfo_exists()]

    # ── Single task form ──────────────────────────────────────────────────────
    def _build_task_form(self, body):
        _label(body, "TASK TITLE", color=C["success"], font=("Georgia", 9, "bold")).pack(anchor="w")
        self._task_title = _entry(body, self._plan.get("title",""))
        self._task_title.pack(fill="x", pady=(2,8))

        _label(body, "DESCRIPTION", color=C["success"], font=("Georgia", 9, "bold")).pack(anchor="w")
        self._task_desc = ctk.CTkTextbox(body, height=60, fg_color=C["edit_bg"],
                                          border_color=C["border"], border_width=1,
                                          text_color=C["text"], font=("Georgia", 11))
        self._task_desc.pack(fill="x", pady=(2,8))
        if self._plan.get("description"):
            self._task_desc.insert("1.0", self._plan["description"])

        row = ctk.CTkFrame(body, fg_color="transparent"); row.pack(fill="x", pady=(0,8))

        _label(row, "Priority:", color=C["subtext"]).pack(side="left", padx=(0,4))
        self._task_pri = ctk.StringVar(value=self._plan.get("priority","Medium"))
        ctk.CTkOptionMenu(row, variable=self._task_pri,
                          values=["Low","Medium","High","Critical"],
                          width=120, height=28, fg_color=C["card2"],
                          button_color=C["accent"], dropdown_fg_color=C["card"]).pack(side="left",padx=(0,10))

        _label(row, "Category:", color=C["subtext"]).pack(side="left", padx=(0,4))
        self._task_cat = ctk.StringVar(value=self._plan.get("category","General"))
        ctk.CTkOptionMenu(row, variable=self._task_cat,
                          values=["General","Work","Personal","Health","Finance","Shopping","Learning","Other"],
                          width=130, height=28, fg_color=C["card2"],
                          button_color=C["accent"], dropdown_fg_color=C["card"]).pack(side="left")

        row2 = ctk.CTkFrame(body, fg_color="transparent"); row2.pack(fill="x", pady=(0,8))
        _label(row2, "Start Date:", color=C["subtext"]).pack(side="left", padx=(0,4))
        self._task_start = _entry(row2, self._plan.get("start_date", date.today().isoformat()), width=120)
        self._task_start.pack(side="left", padx=(0,10))
        _label(row2, "End Date:", color=C["subtext"]).pack(side="left", padx=(0,4))
        self._task_end = _entry(row2, self._plan.get("end_date",""), width=120)
        self._task_end.pack(side="left", padx=(0,10))

        _label(body, "Project:", color=C["subtext"]).pack(anchor="w")
        projects = db.get_projects()
        proj_names = ["None"] + [p["name"] for p in projects]
        self._task_proj = ctk.StringVar(value=self._plan.get("project_name","None") or "None")
        ctk.CTkOptionMenu(body, variable=self._task_proj, values=proj_names,
                          fg_color=C["card2"], button_color=C["accent"],
                          dropdown_fg_color=C["card"]).pack(fill="x", pady=(2,0))

    # ── Read edited values ────────────────────────────────────────────────────
    def _read_project(self) -> dict:
        name = self._proj_name.get().strip()
        desc = self._proj_desc.get("1.0","end").strip()
        tasks = []
        for r in self._task_rows:
            if not r["frame"].winfo_exists(): continue
            t_title = r["title_e"].get().strip()
            if not t_title: continue
            tasks.append({
                "title":       t_title,
                "description": r["desc_box"].get("1.0","end").strip(),
                "priority":    r["pri_var"].get(),
                "category":    r["cat_var"].get(),
                "start_date":  r["start_e"].get().strip(),
                "end_date":    r["end_e"].get().strip(),
            })
        return {"project_name": name, "project_description": desc, "tasks": tasks}

    def _read_task(self) -> dict:
        return {
            "title":        self._task_title.get().strip(),
            "description":  self._task_desc.get("1.0","end").strip(),
            "priority":     self._task_pri.get(),
            "category":     self._task_cat.get(),
            "start_date":   self._task_start.get().strip(),
            "end_date":     self._task_end.get().strip(),
            "project_name": self._task_proj.get(),
        }

    def _confirm(self):
        if self._action == "create_project":
            data = self._read_project()
        else:
            data = self._read_task()
        self.configure(border_color=C["accent"])
        self._on_confirm(self._action, data)

    def _cancel(self):
        self.configure(border_color=C["danger"])
        self._on_cancel()


# ═════════════════════════════════════════════════════════════════════════════
class AIChatTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._history   = []
        self._busy      = False
        self._build()

    # ── Layout ────────────────────────────────────────────────────────────────
    def _build(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=22, pady=(18,4))
        ctk.CTkLabel(hdr, text="AI ASSISTANT", font=("Georgia",20,"bold"),
                     text_color=C["text"]).pack(side="left")
        ctk.CTkButton(hdr, text="↺  Clear", width=90, height=34,
                      fg_color=C["card2"], hover_color=C["border"],
                      text_color=C["subtext"], command=self._clear).pack(side="right")

        # Model badge
        ctk.CTkLabel(self, text=f"⬤  Ollama — {OLLAMA_MODEL}  (runs locally, free)",
                     font=("Georgia",10), text_color=C["subtext"]).pack(anchor="w", padx=24, pady=(0,6))

        # Suggested chips
        sug = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=10)
        sug.pack(fill="x", padx=22, pady=(0,8))
        si  = ctk.CTkFrame(sug, fg_color="transparent"); si.pack(fill="x", padx=10, pady=8)
        ctk.CTkLabel(si, text="Try:", font=("Georgia",10), text_color=C["subtext"]).pack(side="left",padx=(0,6))
        for q in SUGGESTED:
            ctk.CTkButton(si, text=q, height=26, font=("Georgia",9),
                          fg_color=C["card2"], hover_color=C["accent"],
                          text_color=C["subtext"], corner_radius=14,
                          command=lambda q=q: self._send(q)).pack(side="left", padx=3)

        # Chat scroll area
        self.chat_outer = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=14)
        self.chat_outer.pack(fill="both", expand=True, padx=22, pady=(0,8))
        self.chat_scroll = ctk.CTkScrollableFrame(self.chat_outer, fg_color="transparent")
        self.chat_scroll.pack(fill="both", expand=True, padx=6, pady=6)

        self._ai_bubble(
            "👋 Hi Karim!\n\n"
            "I can answer questions about your data AND take actions:\n"
            "• Ask about finances, tasks, or projects\n"
            "• Say \"Plan a Kitchen Renovation project\" — I'll build a full task plan\n"
            "• Say \"Add a task to my Work project\" — I'll prepare it for you\n\n"
            "I'll always show you a preview you can edit before saving anything.",
            is_welcome=True
        )

        # Input row
        inp = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=12)
        inp.pack(fill="x", padx=22, pady=(0,14))
        ii  = ctk.CTkFrame(inp, fg_color="transparent"); ii.pack(fill="x", padx=12, pady=10)

        self.input_box = ctk.CTkEntry(ii,
            placeholder_text="Ask anything or say 'Plan a project called …'",
            fg_color=C["card2"], border_color=C["border"], border_width=1,
            text_color=C["text"], font=("Georgia",12), height=42)
        self.input_box.pack(side="left", fill="x", expand=True, padx=(0,10))
        self.input_box.bind("<Return>", lambda e: self._on_send())

        self.send_btn = ctk.CTkButton(ii, text="Send  ➤", width=110, height=42,
                                      fg_color=C["accent"], hover_color="#5a52d5",
                                      font=("Georgia",12,"bold"), command=self._on_send)
        self.send_btn.pack(side="left")

    # ── Bubble helpers ────────────────────────────────────────────────────────
    def _user_bubble(self, text: str):
        outer = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
        outer.pack(fill="x", pady=(6,2), padx=8)
        bub = ctk.CTkFrame(outer, fg_color=C["user_bg"], corner_radius=12)
        bub.pack(side="right", anchor="e")
        ctk.CTkLabel(bub, text=text, font=("Georgia",12), text_color=C["text"],
                     wraplength=500, justify="left").pack(padx=14, pady=10)

    def _ai_bubble(self, text: str, is_welcome=False):
        outer = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
        outer.pack(fill="x", pady=(2,6), padx=8)
        row = ctk.CTkFrame(outer, fg_color="transparent"); row.pack(side="left", anchor="w")
        ctk.CTkLabel(row, text="✦", fg_color=C["accent"], text_color="white",
                     font=("Georgia",13,"bold"), width=30, height=30,
                     corner_radius=15).pack(side="left", anchor="n", padx=(0,8), pady=4)
        bub = ctk.CTkFrame(row, fg_color=C["ai_bg"], corner_radius=12); bub.pack(side="left")
        ctk.CTkLabel(bub, text=text, font=("Georgia",12), text_color=C["text"],
                     wraplength=580, justify="left").pack(padx=14, pady=10)

    def _plan_card(self, plan_data: dict, action: str):
        """Render an editable plan card in the chat."""
        outer = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
        outer.pack(fill="x", pady=(4,8), padx=8)

        card = PlanCard(
            outer, plan_data, action,
            on_confirm=lambda a, d: self._on_confirm(outer, a, d),
            on_cancel=lambda: self._on_cancel(outer),
        )
        card.pack(fill="x")

    def _thinking_bubble(self):
        outer = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
        outer.pack(fill="x", pady=(2,6), padx=8)
        row = ctk.CTkFrame(outer, fg_color="transparent"); row.pack(side="left", anchor="w")
        ctk.CTkLabel(row, text="✦", fg_color=C["accent"], text_color="white",
                     font=("Georgia",13,"bold"), width=30, height=30,
                     corner_radius=15).pack(side="left", padx=(0,8), pady=4)
        bub = ctk.CTkFrame(row, fg_color=C["ai_bg"], corner_radius=12); bub.pack(side="left")
        self._dots_var = ctk.StringVar(value="Thinking .")
        ctk.CTkLabel(bub, textvariable=self._dots_var, font=("Georgia",12),
                     text_color=C["subtext"]).pack(padx=14, pady=10)
        self._animate_dots(0)
        return outer

    def _animate_dots(self, n):
        if self._busy:
            self._dots_var.set("Thinking " + "." * (n % 3 + 1))
            self.after(450, lambda: self._animate_dots(n+1))

    def _scroll_bottom(self):
        self.after(120, lambda: self.chat_scroll._parent_canvas.yview_moveto(1.0))

    # ── Send ──────────────────────────────────────────────────────────────────
    def _on_send(self):
        text = self.input_box.get().strip()
        if text and not self._busy:
            self.input_box.delete(0, "end")
            self._send(text)

    def _send(self, text: str):
        self._user_bubble(text)
        self._history.append({"role":"user","content":text})
        self._scroll_bottom()

        self._busy = True
        self.send_btn.configure(state="disabled", text="…")
        thinking = self._thinking_bubble()
        self._scroll_bottom()

        context = _build_context()

        def worker():
            try:
                # Step 1: classify intent (fast, ~1s)
                intent = _classify_intent(text)

                if intent == "ACTION":
                    # Step 2a: action path — returns JSON with plan
                    result = _call_action(text, context, self._history[:-1])
                    self.after(0, lambda r=result: self._on_action_response(thinking, r))
                else:
                    # Step 2b: Q&A path — returns plain text
                    reply = _call_qa(text, context, self._history[:-1])
                    self.after(0, lambda r=reply: self._on_qa_response(thinking, r))

            except ConnectionError as e:
                msg = str(e)
                self.after(0, lambda m=msg: self._on_qa_response(thinking, m))
            except Exception as e:
                msg = f"⚠️ Unexpected error: {e}"
                self.after(0, lambda m=msg: self._on_qa_response(thinking, m))

        threading.Thread(target=worker, daemon=True).start()

    # ── Handle Q&A response (plain text) ──────────────────────────────────────
    def _on_qa_response(self, thinking_widget, reply: str):
        thinking_widget.destroy()
        self._busy = False
        self.send_btn.configure(state="normal", text="Send  ➤")
        self._ai_bubble(reply)
        self._history.append({"role":"assistant","content":reply})
        self._scroll_bottom()

    # ── Handle action response (JSON with plan) ────────────────────────────────
    def _on_action_response(self, thinking_widget, parsed: dict):
        thinking_widget.destroy()
        self._busy = False
        self.send_btn.configure(state="normal", text="Send  ➤")

        action  = parsed.get("action", "none")
        message = parsed.get("message", "")
        plan    = parsed.get("plan", {})

        if message:
            self._ai_bubble(message)
            self._history.append({"role":"assistant","content":message})

        if action in ("create_project","add_task") and plan:
            self._ai_bubble("📋 Here's my plan — edit any field then confirm:")
            self._plan_card(plan, action)
        elif not plan:
            # Action classified but no plan returned — treat as Q&A fallback
            pass

        self._scroll_bottom()

    # ── Confirm / Cancel ──────────────────────────────────────────────────────
    def _on_confirm(self, card_outer, action: str, data: dict):
        try:
            if action == "create_project":
                self._execute_create_project(data)
            elif action == "add_task":
                self._execute_add_task(data)
        except Exception as e:
            self._ai_bubble(f"❌ Error while saving: {e}")
        self._scroll_bottom()

    def _on_cancel(self, card_outer):
        self._ai_bubble("Okay, cancelled. Let me know if you'd like to try again or change anything.")
        self._scroll_bottom()

    # ── DB execution ──────────────────────────────────────────────────────────
    def _notify_app(self):
        """Tell the main app to refresh the projects page after AI creates data."""
        try:
            root = self.winfo_toplevel()
            if hasattr(root, "refresh_projects"):
                root.refresh_projects()
        except Exception:
            pass

    def _execute_create_project(self, data: dict):
        name = data.get("project_name","").strip()
        if not name:
            self._ai_bubble("❌ Project name is empty — nothing was saved.")
            return

        pid = db.add_project(
            name=name,
            description=data.get("project_description",""),
            color="#6C63FF",
            status="Active",
        )

        tasks = data.get("tasks",[])
        saved = 0
        for t in tasks:
            title = t.get("title","").strip()
            if not title: continue
            sd = t.get("start_date") or date.today().isoformat()
            ed = t.get("end_date")   or (date.today()+timedelta(days=14)).isoformat()
            db.add_task(
                title=title,
                description=t.get("description",""),
                category=t.get("category","General"),
                status="Pending",
                priority=t.get("priority","Medium"),
                start_date=sd,
                end_date=ed,
                project_id=pid,
            )
            saved += 1

        self._ai_bubble(
            f"✅ Project \"{name}\" created with {saved} task{'s' if saved!=1 else ''}.\n"
            "You can view it in the Projects tab."
        )
        self._history.append({"role":"assistant","content":f"Created project {name} with {saved} tasks."})
        self._notify_app()

    def _execute_add_task(self, data: dict):
        title = data.get("title","").strip()
        if not title:
            self._ai_bubble("❌ Task title is empty — nothing was saved.")
            return

        # Resolve project
        pid = None
        proj_name = data.get("project_name","")
        if proj_name and proj_name != "None":
            for p in db.get_projects():
                if p["name"].lower() == proj_name.lower():
                    pid = p["id"]; break
            if pid is None:
                self._ai_bubble(f"⚠️ Project \"{proj_name}\" not found. Task saved without a project.")

        sd = data.get("start_date") or date.today().isoformat()
        ed = data.get("end_date")   or (date.today()+timedelta(days=7)).isoformat()

        db.add_task(
            title=title,
            description=data.get("description",""),
            category=data.get("category","General"),
            status="Pending",
            priority=data.get("priority","Medium"),
            start_date=sd,
            end_date=ed,
            project_id=pid,
        )
        proj_str = f" in \"{proj_name}\"" if pid else ""
        self._ai_bubble(f"✅ Task \"{title}\" added{proj_str}.\nCheck the Tasks tab to see it.")
        self._history.append({"role":"assistant","content":f"Added task: {title}"})
        self._notify_app()

    # ── Clear ─────────────────────────────────────────────────────────────────
    def _clear(self):
        self._history = []
        for w in self.chat_scroll.winfo_children(): w.destroy()
        self._ai_bubble("Chat cleared! Ready for new questions or actions.", is_welcome=True)