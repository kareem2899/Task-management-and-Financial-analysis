<div align="center">

```
╔════════════════════════════════════════╗
║          ✦  T A S K F L O W           ║
║   Task · Finance · AI — All-in-One    ║
╚════════════════════════════════════════╝
```

**A fully offline, AI-powered personal productivity desktop app**  
Built with Python · CustomTkinter · SQLite · Matplotlib · Ollama

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![CustomTkinter](https://img.shields.io/badge/CustomTkinter-5.2.2-6C63FF?style=flat-square)](https://github.com/TomSchimansky/CustomTkinter)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=flat-square&logo=sqlite&logoColor=white)](https://sqlite.org)
[![Matplotlib](https://img.shields.io/badge/Matplotlib-3.9-11557C?style=flat-square)](https://matplotlib.org)
[![Ollama](https://img.shields.io/badge/Ollama-Local_AI-000000?style=flat-square)](https://ollama.com)
[![macOS](https://img.shields.io/badge/macOS-Supported-000000?style=flat-square&logo=apple)](https://apple.com)
[![License](https://img.shields.io/badge/License-MIT-43E97B?style=flat-square)](LICENSE)

*Built by **Karim Mamdouh***

</div>

---

## Overview

**TaskFlow** is a feature-rich personal productivity desktop application that combines task management, project planning, financial tracking, and an AI assistant — all running completely offline on your machine. No cloud. No subscriptions. No data leaving your computer.

Everything is stored in a local SQLite database (`taskflow.db`) that is created automatically on first run. The AI assistant is powered by [Ollama](https://ollama.com), a free local model runner, so your private financial and task data is never sent to any external server.

---

## ✨ Feature Overview

| Module | Capabilities |
|--------|-------------|
| 📋 **Tasks** | Add, edit, delete tasks · Priority, status, category, dates · Multi-filter · Project assignment |
| 🗂 **Projects** | Create color-coded projects · Progress bars · Add tasks directly from cards · Full task dialog |
| 💰 **Finance** | Track income & expenses · Source / location tagging · Category filters · Monthly selector |
| 📊 **Analytics** | 6 chart views · Task trends · Finance daily/monthly · Expense breakdown · Finance analysis KPIs |
| 📅 **Progress** | Monthly calendar grid · Day-by-day task completion % · Income/expense summary · Date range picker |
| 🤖 **AI Assistant** | Q&A about your data · Create projects with full task plans · Editable plan preview · 100% local via Ollama |

---

## 📸 Screenshots

> check images folder

---

## 🗂 Project Structure

```
taskflow/
│
├── main.py               ← App entry point · sidebar · tab preloading
├── database.py           ← All SQLite CRUD · single data access layer
├── date_picker.py        ← Custom dark-themed calendar widget (macOS safe)
│
├── tasks_tab.py          ← Task Manager screen
├── projects_tab.py       ← Projects screen + task dialogs
├── finance_tab.py        ← Finance Tracker screen
├── charts_tab.py         ← Analytics & 6 chart types
├── progress_tab.py       ← Monthly progress calendar grid
├── ai_chat_tab.py        ← AI Assistant (Ollama) with plan cards
│
├── taskflow.db           ← SQLite database (auto-created on first run)
├── requirements.txt      ← Python dependencies
├── README.md             ← This file
├── SETUP_GUIDE.md        ← Full macOS setup walkthrough
└── AI_SETUP.md           ← Ollama / AI model setup guide
```

---

## 🗄 Database Schema

TaskFlow uses a single SQLite file with three tables.

### Entity Relationship Diagram

```
┌─────────────────────────────────┐         ┌──────────────────────────────────────────┐
│           projects              │         │                  tasks                   │
├──────────────────┬──────────────┤         ├──────────────────┬───────────────────────┤
│ id               │ INTEGER PK   │◄────────│ project_id       │ INTEGER FK (nullable) │
│ name             │ TEXT NOT NULL│  0..*   │ id               │ INTEGER PK            │
│ description      │ TEXT         │         │ title            │ TEXT NOT NULL         │
│ color            │ TEXT         │         │ description      │ TEXT                  │
│ status           │ TEXT         │         │ category         │ TEXT                  │
│ created_at       │ TEXT         │         │ status           │ TEXT                  │
└─────────────────────────────────┘         │ priority         │ TEXT                  │
                                            │ start_date       │ TEXT (YYYY-MM-DD)     │
                                            │ end_date         │ TEXT (YYYY-MM-DD)     │
                                            │ created_at       │ TEXT                  │
                                            └──────────────────────────────────────────┘

┌──────────────────────────────────────────────┐
│                 transactions                 │
├──────────────────┬───────────────────────────┤
│ id               │ INTEGER PK                │
│ type             │ TEXT ('income'|'expense') │
│ amount           │ REAL                      │
│ category         │ TEXT                      │
│ source           │ TEXT (income source name) │
│ expense_location │ TEXT (where money spent)  │
│ date             │ TEXT (YYYY-MM-DD)         │
│ notes            │ TEXT                      │
│ created_at       │ TEXT                      │
└──────────────────────────────────────────────┘

  Note: transactions has NO foreign key to tasks or projects.
  It is a fully independent financial ledger.
```

### Table Descriptions

#### `projects`

| Column | Type | Description |
|--------|------|-------------|
| `id` | `INTEGER PK` | Auto-incremented primary key |
| `name` | `TEXT NOT NULL` | Project display name |
| `description` | `TEXT` | Optional project description |
| `color` | `TEXT` | Hex color string (e.g. `#6C63FF`) used for UI theming |
| `status` | `TEXT` | One of: `Active`, `On Hold`, `Completed`, `Archived` |
| `created_at` | `TEXT` | ISO timestamp, auto-set by SQLite |

#### `tasks`

| Column | Type | Description |
|--------|------|-------------|
| `id` | `INTEGER PK` | Auto-incremented primary key |
| `project_id` | `INTEGER FK` | Optional reference to `projects.id`. `NULL` = standalone task. On project delete → set to `NULL` (task is kept) |
| `title` | `TEXT NOT NULL` | Task title |
| `description` | `TEXT` | Detailed description |
| `category` | `TEXT` | One of: `General`, `Work`, `Personal`, `Health`, `Finance`, `Shopping`, `Learning`, `Other` |
| `status` | `TEXT` | One of: `Pending`, `In Progress`, `Completed`, `Cancelled` |
| `priority` | `TEXT` | One of: `Low`, `Medium`, `High`, `Critical` |
| `start_date` | `TEXT` | `YYYY-MM-DD` format |
| `end_date` | `TEXT` | `YYYY-MM-DD` format — used to detect overdue tasks |
| `created_at` | `TEXT` | ISO timestamp, auto-set by SQLite |

#### `transactions`

| Column | Type | Description |
|--------|------|-------------|
| `id` | `INTEGER PK` | Auto-incremented primary key |
| `type` | `TEXT NOT NULL` | Either `income` or `expense` |
| `amount` | `REAL` | Monetary amount in EGP |
| `category` | `TEXT` | e.g. `Food & Dining`, `Transport`, `Salary`, `Freelance` |
| `source` | `TEXT` | Income source name (e.g. `Salary`, `Investment`) — populated for income records |
| `expense_location` | `TEXT` | Where money was spent (e.g. `Supermarket`, `Hospital`) — populated for expense records |
| `date` | `TEXT NOT NULL` | `YYYY-MM-DD` format |
| `notes` | `TEXT` | Optional free-text note |
| `created_at` | `TEXT` | ISO timestamp, auto-set by SQLite |

### Key Business Rules

- A task with `end_date < today` and `status NOT IN ('Completed', 'Cancelled')` is considered **overdue**
- Deleting a project sets `project_id = NULL` on its tasks — tasks are never cascade-deleted
- All date values are stored as plain text strings in `YYYY-MM-DD` ISO format
- The `transactions` table has zero foreign keys — it is a completely standalone financial ledger

---

## 🏗 System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         main.py  (App shell)                           │
│  • Sidebar navigation          • Page preloading (.lift/.lower)        │
│  • 6 tabs built once at startup — instant switching, no rebuild        │
└──────────┬──────────────────────────────────────────────────────────────┘
           │ creates & manages
           ▼
┌──────────────────────────────────── UI LAYER ────────────────────────────────────────┐
│                                                                                      │
│  tasks_tab.py    projects_tab.py    finance_tab.py    charts_tab.py                 │
│  📋 Tasks        🗂 Projects        💰 Finance         📊 Analytics                  │
│                                                                                      │
│  progress_tab.py                   ai_chat_tab.py                                   │
│  📅 Monthly Grid                   🤖 AI Assistant                                   │
│                                                                                      │
└──────────────────────────────┬───────────────────────────────────────────────────────┘
                               │ all tabs import directly
                               ▼
┌──────────────────────────── DATA LAYER ──────────────────────────────────────────────┐
│                           database.py                                                │
│                                                                                      │
│  get_tasks()       add_task()       update_task()      delete_task()                │
│  get_projects()    add_project()    update_project()   delete_project()             │
│  get_transactions() add_transaction() delete_transaction()                          │
│  get_finance_stats()   get_task_stats()   get_project_task_counts()                │
│                                                                                      │
└──────────────────────────────┬───────────────────────────────────────────────────────┘
                               │ reads/writes
                               ▼
                    ┌──────────────────────┐
                    │     taskflow.db      │
                    │  (SQLite file)       │
                    │  projects            │
                    │  tasks               │
                    │  transactions        │
                    └──────────────────────┘

┌──────────────────────────── EXTERNAL SERVICES ───────────────────────────────────────┐
│                                                                                      │
│  ai_chat_tab.py ──► _classify_intent()  ──► Ollama HTTP API (localhost:11434)       │
│                ──► _call_qa()                  Model: llama3.2 (or mistral/llama3)  │
│                ──► _call_action()              Runs 100% offline — no internet       │
│                                                                                      │
│  charts_tab.py ──► matplotlib FigureCanvasTkAgg ──► rendered inside chart_frame    │
│  date_picker.py ──► tk.Frame .place() overlay ──► root window (no Toplevel)        │
│                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### AI Assistant Architecture

The AI tab uses a **three-call pipeline** to avoid the truncation problems that occur when forcing small local models to produce structured JSON for both Q&A and action responses:

```
User message
     │
     ▼
[Call 1]  _classify_intent()   ~1 second
          Prompt: "Is this ACTION or QUESTION?"
          Returns: "ACTION" | "QUESTION"
     │
     ├─── QUESTION ──► [Call 2a]  _call_qa()
     │                            Plain-text system prompt
     │                            Full detailed answer (no JSON)
     │                            Supports: overdue tasks, finance summaries,
     │                            task details, project status, anything
     │
     └─── ACTION ───► [Call 2b]  _call_action()
                                  JSON-only system prompt
                                  Returns plan: {action, message, plan{}}
                                  Triggers editable PlanCard in chat
                                       │
                                       ▼
                                  User edits fields inline
                                  (title, dates, priority, description…)
                                       │
                                  [Confirm] ──► database.py writes
                                  [Cancel]  ──► nothing saved
```

---

## 📦 Installation

### Prerequisites

- macOS (tested on macOS 13+)
- Python 3.11 or later
- Homebrew

### Step 1 — Install Python and Tcl/Tk

```bash
# Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python with Tk support
brew install python@3.11 tcl-tk python-tk@3.11
```

### Step 2 — Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/taskflow.git
cd taskflow
```

### Step 3 — Create a virtual environment

```bash
# Intel Mac
/usr/local/opt/python@3.11/bin/python3.11 -m venv venv

# Apple Silicon (M1/M2/M3)
/opt/homebrew/opt/python@3.11/bin/python3.11 -m venv venv

source venv/bin/activate
```

### Step 4 — Install dependencies

```bash
pip install -r requirements.txt
```

**Dependencies:**

| Package | Version | Purpose |
|---------|---------|---------|
| `customtkinter` | 5.2.2 | Modern styled UI widgets |
| `matplotlib` | 3.9.0 | Charts and graphs |
| `Pillow` | 10.3.0 | Image support (required by customtkinter) |
| `sqlite3` | built-in | Database — no install needed |
| `tkinter` | built-in | GUI framework — no install needed |

### Step 5 — Run the app

```bash
python3 main.py
```

The SQLite database (`taskflow.db`) is created automatically on first launch.

---

## 🤖 AI Assistant Setup (Free, Offline)

The AI assistant uses **Ollama** — a free tool that runs AI language models entirely on your Mac. No API key, no internet connection, no cost.

### Install Ollama

```bash
# Option A: Download the macOS app from https://ollama.com
# Option B: Install via terminal
curl -fsSL https://ollama.com/install.sh | sh
```

### Download the AI model (one-time, ~2 GB)

```bash
ollama pull llama3.2
```

### Start Ollama

```bash
ollama serve
```

Or open the Ollama app from your Applications folder — it runs in the menu bar.

### Available models

| Model | Size | Speed | Quality |
|-------|------|-------|---------|
| `llama3.2` | ~2 GB | ⚡ Fast | ✅ Good (default) |
| `mistral` | ~4 GB | Medium | ✅ Good |
| `llama3` | ~5 GB | Slower | ⭐ Best |
| `phi3` | ~2 GB | ⚡ Fast | ✅ Good |

To change the model, edit line 43 in `ai_chat_tab.py`:
```python
OLLAMA_MODEL = "llama3.2"  # ← change this
```

### What the AI can do

- Answer questions about your tasks, projects, and finances
- Detect and list overdue tasks with days late
- Summarize your financial situation
- Show task details for any project
- **Plan entire projects** — generates tasks with titles, descriptions, priorities, and deadlines
- **Add individual tasks** to existing projects
- Always shows an editable preview before saving anything

---

## 🎯 Feature Deep-Dive

### 📋 Task Manager

- Create tasks with: title, description, category (8 options), priority (Low/Medium/High/Critical), status (Pending/In Progress/Completed/Cancelled), start date, end date, and optional project assignment
- Edit or delete any task with instant inline forms
- **Multi-filter bar**: filter simultaneously by status, priority, category chips, and date range
- Color-coded priority bar on each task card (green/purple/orange/red)
- Project badge shown on each task card
- All filters persist during the session

### 🗂 Project Manager

- Color-coded project cards in a 3-column grid
- Each card shows: name, status badge, description preview, task progress bar (done/total), percentage
- **Quick actions per card**:
  - `Open Tasks` — full dialog listing all project tasks with edit/delete per task
  - `＋` — add a task directly to the project without opening the full dialog
  - `✎` — edit project details
  - `✕` — delete project (tasks are unlinked, not deleted)
- Global `↺ Refresh` button
- When AI creates a project, the Projects page auto-refreshes

### 💰 Finance Tracker

- **Income** entries: amount, category, source (Salary/Freelance/Business/etc), date, notes
- **Expense** entries: amount, category, location (Supermarket/Restaurant/etc), date, notes
- Both support "Other" option with free-text entry
- Filter by: type, month picker, date range, category chips
- Live summary bar: Total Income / Total Expenses / Balance
- All amounts in EGP

### 📊 Analytics

Six chart views, all responding to month and date filters:

| Chart | What it shows |
|-------|--------------|
| Tasks Overview | Status pie + category bar + daily creation line |
| Tasks Trend | Daily new tasks line + cumulative total line |
| Finance Daily | Income vs expense grouped bar chart by day |
| Finance Monthly | Income / expense / balance trend lines over months |
| Expense Categories | Pie + horizontal bar by category |
| Finance Analysis | KPI cards (Income/Expenses/Balance) + income sources bar + expense location bar + expense category pie |

### 📅 Monthly Progress

- Calendar grid layout (7 columns, Mon–Sun)
- Each day shows: day number, tasks due that day, completion count, **green progress bar**, percentage
- Color logic: green = 100% done, light green = >50%, orange = past deadline with incomplete tasks
- Summary bar: Total Income, Total Expenses, Balance, Tasks Progress for the selected range
- Date range picker with "This Month" quick reset button
- Default: first day to last day of current month

### 🤖 AI Assistant

- **Q&A mode**: ask anything about your data in natural language
- **Action mode**: say "Plan a project" or "Add a task to X" — AI creates a full editable plan
- Editable plan cards with per-task fields: title, description, priority, category, start date, end date
- Add or remove tasks from the plan before confirming
- Nothing is saved until you click "Confirm & Save"
- Conversation history (last 10 turns)
- Suggested prompt chips for quick start
- Clear chat button

---

## 🔧 Technical Notes

### Date Picker

The custom `DatePicker` widget (`date_picker.py`) uses `.place()` overlay on the root window instead of `Toplevel` with `overrideredirect`. This is necessary on macOS because `overrideredirect(True)` strips the window's event mask, making button clicks inside the popup unresponsive. The overlay approach places a `tk.Frame` directly in the root coordinate space where all events work normally.

### Tab Switching Performance

All 6 tabs are built once at startup and kept in memory using `.place(relwidth=1, relheight=1)`. Switching tabs calls `.lift()` on the target tab and `.lower()` on all others — this is instant (no widget rebuild, no pack/forget). First startup takes ~2–3 seconds to build all tabs; subsequent switches are imperceptible.

### AI Two-Prompt Architecture

Forcing a small local LLM (llama3.2, 3B parameters) to encode long answers as JSON string values causes consistent truncation and invalid JSON errors. The solution is intent classification: a ~1-second call classifies the message as `ACTION` or `QUESTION`, then routes to either a plain-text Q&A prompt (no JSON constraints, full detailed answers) or a JSON-only action prompt (compact schema for project/task creation). This gives both reliable Q&A and reliable structured output.

---

## 📁 Data Privacy

- **No internet connection required** for any feature (AI runs via Ollama locally)
- **No telemetry, analytics, or tracking** of any kind
- All data is stored in `taskflow.db` — a plain SQLite file on your local disk
- You can open, inspect, backup, or delete this file at any time with any SQLite tool
- The AI model (llama3.2) runs entirely on your CPU/GPU via Ollama — your financial data never leaves your machine

---

## 🛠 Troubleshooting

### App won't start — `No module named '_tkinter'`

```bash
brew install python-tk@3.11
# Then recreate your venv with Homebrew's Python:
rm -rf venv
/usr/local/opt/python@3.11/bin/python3.11 -m venv venv   # Intel
/opt/homebrew/opt/python@3.11/bin/python3.11 -m venv venv # Apple Silicon
source venv/bin/activate
pip install -r requirements.txt
```

### AI says "Cannot reach Ollama"

```bash
# Make sure Ollama is running
ollama serve
# In another terminal, verify
curl http://localhost:11434/api/tags
```

### Calendar dates are cut off

Ensure you have the latest `date_picker.py` — the overlay height is now computed dynamically per month (5-week vs 6-week months) and day buttons use `width=4` to fit two-digit numbers.

### Projects page doesn't show new project after AI creates one

The AI tab calls `refresh_projects()` on the main app automatically. If it doesn't update, click the `↺ Refresh` button on the Projects page.

---

## 🗺 Roadmap

- [ ] Export tasks to CSV / PDF
- [ ] Recurring tasks (daily / weekly / monthly)
- [ ] Budget limits per expense category with alerts
- [ ] Dark/light theme toggle
- [ ] Windows support
- [ ] Data backup / restore dialog
- [ ] Multi-currency support
- [ ] Calendar view for tasks (monthly calendar with drag-and-drop)
- [ ] Email / notification reminders for overdue tasks
- [ ] Sync between devices via self-hosted server

---

## 🤝 Contributing

Contributions are welcome! Please open an issue first to discuss what you'd like to change.

```bash
# Fork the repo, then:
git checkout -b feature/your-feature-name
git commit -m "Add: description of your change"
git push origin feature/your-feature-name
# Open a Pull Request
```

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

Built with ❤️ by **Karim Mamdouh**

*TaskFlow — because your tasks and finances deserve better than a spreadsheet.*

</div>
