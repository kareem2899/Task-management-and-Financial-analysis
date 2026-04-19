# ✦ TaskFlow — Setup & Run Guide (macOS)
# ==========================================

## WHAT YOU NEED TO INSTALL

### Step 1 — Install Python 3.11+ (if not already installed)
Open Terminal and run:

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python via Homebrew
brew install python@3.11
```

Verify:
```bash
python3 --version
```

---

### Step 2 — Install Tcl/Tk (required for tkinter/tkcalendar)

```bash
brew install tcl-tk
```

---

### Step 3 — Navigate to the project folder

```bash
cd /path/to/taskflow
# Example: cd ~/Desktop/taskflow
```

---

### Step 4 — Create a virtual environment (recommended)

```bash
python3 -m venv venv
source venv/bin/activate
```

---

### Step 5 — Install all required libraries

```bash
pip install customtkinter==5.2.2 tkcalendar==1.6.1 matplotlib==3.9.0 Pillow==10.3.0
```

Or use requirements.txt:
```bash
pip install -r requirements.txt
```

---

### Step 6 — Run the app

```bash
python3 main.py
```

---

## FULL LIBRARY LIST

| Library         | Version  | Purpose                                  |
|-----------------|----------|------------------------------------------|
| customtkinter   | 5.2.2    | Modern beautiful UI widgets              |
| tkcalendar      | 1.6.1    | Date picker calendar widget              |
| matplotlib      | 3.9.0    | Charts (bar, line, pie graphs)           |
| Pillow          | 10.3.0   | Image handling (required by customtkinter)|
| sqlite3         | built-in | Database — NO install needed             |
| tkinter         | built-in | GUI base — NO install needed             |

---

## PROJECT FILE STRUCTURE

```
taskflow/
├── main.py           ← Run this file to start the app
├── database.py       ← SQLite database logic
├── tasks_tab.py      ← Task Manager screen
├── finance_tab.py    ← Finance Tracker screen
├── charts_tab.py     ← Analytics & Charts screen
├── requirements.txt  ← Library list
└── taskflow.db       ← Auto-created on first run
```

---

## FEATURES

### 📋 Tasks Tab
- Add, Edit, Delete tasks
- Set Start & End dates using calendar picker
- Assign Category, Priority (Low/Medium/High/Critical), Status
- Multi-filter: by Status, Priority, Category chips, Date range
- Color-coded priority bars and status indicators

### 💰 Finance Tab
- Add Income with: Amount, Source (Salary/Freelance/etc or custom), Category, Date, Notes
- Add Expense with: Amount, Category, Location (where you spent), Date, Notes
- Dropdown lists with "Other" option to type custom values
- Filter by: Type, Month selector, Date range, Category chips
- Live summary: Total Income, Total Expenses, Balance

### 📊 Analytics Tab
- Tasks chart: Status pie + Category bar + Daily creation line
- Finance Daily: Income vs Expense bar chart per day
- Finance Monthly: Trend line chart (income/expenses/balance)
- Category Donut: Expense breakdown by category
- All charts respond to Month & Date filters

---

## TROUBLESHOOTING (macOS)

**App doesn't open / tkinter error:**
```bash
brew install python-tk@3.11
```

**"No module named customtkinter":**
Make sure your venv is active:
```bash
source venv/bin/activate
pip install customtkinter
```

**Window appears but looks blank:**
Try running with:
```bash
PYTHONPATH=. python3 main.py
```
