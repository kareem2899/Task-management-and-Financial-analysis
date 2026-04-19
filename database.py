import sqlite3, os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "taskflow.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_db():
    conn = get_connection(); c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        color TEXT DEFAULT '#6C63FF',
        status TEXT DEFAULT 'Active',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER DEFAULT NULL,
        title TEXT NOT NULL,
        description TEXT,
        category TEXT DEFAULT 'General',
        status TEXT DEFAULT 'Pending',
        priority TEXT DEFAULT 'Medium',
        start_date TEXT,
        end_date TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE SET NULL
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL,
        amount REAL NOT NULL,
        category TEXT,
        source TEXT,
        expense_location TEXT,
        date TEXT NOT NULL,
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    # Migration: add project_id column if upgrading from old DB
    try:
        c.execute("ALTER TABLE tasks ADD COLUMN project_id INTEGER DEFAULT NULL")
    except Exception:
        pass
    conn.commit(); conn.close()

# ── PROJECTS ─────────────────────────────────────────────────────────────────
def add_project(name, description, color, status):
    conn = get_connection(); c = conn.cursor()
    c.execute("INSERT INTO projects (name,description,color,status) VALUES (?,?,?,?)",
              (name, description, color, status))
    conn.commit(); rid = c.lastrowid; conn.close(); return rid

def update_project(pid, name, description, color, status):
    conn = get_connection(); c = conn.cursor()
    c.execute("UPDATE projects SET name=?,description=?,color=?,status=? WHERE id=?",
              (name, description, color, status, pid))
    conn.commit(); conn.close()

def delete_project(pid):
    conn = get_connection(); c = conn.cursor()
    c.execute("DELETE FROM projects WHERE id=?", (pid,)); conn.commit(); conn.close()

def get_projects():
    conn = get_connection(); c = conn.cursor()
    c.execute("SELECT * FROM projects ORDER BY created_at DESC")
    rows = [dict(r) for r in c.fetchall()]; conn.close(); return rows

def get_project_task_counts():
    conn = get_connection(); c = conn.cursor()
    c.execute("""SELECT project_id,
                        COUNT(*) as total,
                        SUM(CASE WHEN status='Completed' THEN 1 ELSE 0 END) as done
                 FROM tasks WHERE project_id IS NOT NULL GROUP BY project_id""")
    res = {r["project_id"]: {"total": r["total"], "done": r["done"]} for r in c.fetchall()}
    conn.close(); return res

# ── TASKS ─────────────────────────────────────────────────────────────────────
def add_task(title, description, category, status, priority, start_date, end_date, project_id=None):
    conn = get_connection(); c = conn.cursor()
    c.execute("""INSERT INTO tasks (title,description,category,status,priority,start_date,end_date,project_id)
                 VALUES (?,?,?,?,?,?,?,?)""",
              (title, description, category, status, priority, start_date, end_date, project_id))
    conn.commit(); rid = c.lastrowid; conn.close(); return rid

def update_task(task_id, title, description, category, status, priority, start_date, end_date, project_id=None):
    conn = get_connection(); c = conn.cursor()
    c.execute("""UPDATE tasks SET title=?,description=?,category=?,status=?,priority=?,
                 start_date=?,end_date=?,project_id=? WHERE id=?""",
              (title, description, category, status, priority, start_date, end_date, project_id, task_id))
    conn.commit(); conn.close()

def delete_task(task_id):
    conn = get_connection(); c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE id=?", (task_id,)); conn.commit(); conn.close()

def get_tasks(filters=None):
    conn = get_connection(); c = conn.cursor()
    query = """SELECT t.*, p.name as project_name, p.color as project_color
               FROM tasks t LEFT JOIN projects p ON t.project_id=p.id WHERE 1=1"""
    params = []
    if filters:
        if filters.get("category") and filters["category"] != "All":
            query += " AND t.category=?"; params.append(filters["category"])
        if filters.get("status") and filters["status"] != "All":
            query += " AND t.status=?"; params.append(filters["status"])
        if filters.get("priority") and filters["priority"] != "All":
            query += " AND t.priority=?"; params.append(filters["priority"])
        if filters.get("project_id"):
            query += " AND t.project_id=?"; params.append(filters["project_id"])
    query += " ORDER BY t.created_at DESC"
    c.execute(query, params)
    rows = [dict(r) for r in c.fetchall()]; conn.close(); return rows

def get_task_stats():
    conn = get_connection(); c = conn.cursor()
    c.execute("SELECT status, COUNT(*) as count FROM tasks GROUP BY status")
    sc = {r["status"]: r["count"] for r in c.fetchall()}
    c.execute("SELECT category, COUNT(*) as count FROM tasks GROUP BY category")
    cc = {r["category"]: r["count"] for r in c.fetchall()}
    c.execute("SELECT DATE(created_at) as day, COUNT(*) as count FROM tasks GROUP BY day ORDER BY day")
    daily = [(r["day"], r["count"]) for r in c.fetchall()]
    conn.close(); return sc, cc, daily

# ── TRANSACTIONS ──────────────────────────────────────────────────────────────
def add_transaction(type_, amount, category, source, expense_location, date_, notes):
    conn = get_connection(); c = conn.cursor()
    c.execute("""INSERT INTO transactions (type,amount,category,source,expense_location,date,notes)
                 VALUES (?,?,?,?,?,?,?)""",
              (type_, amount, category, source, expense_location, date_, notes))
    conn.commit(); rid = c.lastrowid; conn.close(); return rid

def delete_transaction(trans_id):
    conn = get_connection(); c = conn.cursor()
    c.execute("DELETE FROM transactions WHERE id=?", (trans_id,)); conn.commit(); conn.close()

def get_transactions(filters=None):
    conn = get_connection(); c = conn.cursor()
    query = "SELECT * FROM transactions WHERE 1=1"; params = []
    if filters:
        if filters.get("type") and filters["type"] != "All":
            query += " AND type=?"; params.append(filters["type"])
        if filters.get("category") and filters["category"] != "All":
            query += " AND category=?"; params.append(filters["category"])
        if filters.get("month"):
            query += " AND strftime('%Y-%m', date)=?"; params.append(filters["month"])
    query += " ORDER BY date DESC"
    c.execute(query, params)
    rows = [dict(r) for r in c.fetchall()]; conn.close(); return rows

def get_finance_stats(month=None):
    conn = get_connection(); c = conn.cursor()
    mf = "AND strftime('%Y-%m', date)=?" if month else ""
    mp = [month] if month else []

    c.execute(f"SELECT SUM(amount) FROM transactions WHERE type='income' {mf}", mp)
    total_income = c.fetchone()[0] or 0
    c.execute(f"SELECT SUM(amount) FROM transactions WHERE type='expense' {mf}", mp)
    total_expense = c.fetchone()[0] or 0

    c.execute(f"""SELECT date,
                    SUM(CASE WHEN type='income'  THEN amount ELSE 0 END) as income,
                    SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) as expense
                 FROM transactions {('WHERE ' + mf[4:]) if month else ''}
                 GROUP BY date ORDER BY date""", mp)
    daily = [(r["date"], r["income"], r["expense"]) for r in c.fetchall()]

    c.execute("""SELECT strftime('%Y-%m', date) as month,
                        SUM(CASE WHEN type='income'  THEN amount ELSE 0 END) as income,
                        SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) as expense
                 FROM transactions GROUP BY month ORDER BY month""")
    monthly = [(r["month"], r["income"], r["expense"]) for r in c.fetchall()]

    c.execute(f"SELECT category, SUM(amount) as total FROM transactions WHERE type='expense' {mf} GROUP BY category ORDER BY total DESC", mp)
    expense_by_cat = {r["category"]: r["total"] for r in c.fetchall()}

    c.execute(f"SELECT source, SUM(amount) as total FROM transactions WHERE type='income' {mf} AND source!='' GROUP BY source ORDER BY total DESC", mp)
    income_by_src = {r["source"]: r["total"] for r in c.fetchall()}

    c.execute(f"SELECT expense_location, SUM(amount) as total FROM transactions WHERE type='expense' {mf} AND expense_location!='' GROUP BY expense_location ORDER BY total DESC", mp)
    expense_by_loc = {r["expense_location"]: r["total"] for r in c.fetchall()}

    conn.close()
    return total_income, total_expense, daily, monthly, expense_by_cat, income_by_src, expense_by_loc
