import customtkinter as ctk
from tkinter import messagebox
import tkinter as tk
from datetime import date
from date_picker import DatePicker
import database as db

INCOME_SOURCES    = ["Salary","Freelance","Business","Investment","Rental","Gift","Bonus","Other"]
EXPENSE_CATEGORIES= ["Food & Dining","Transport","Housing","Health","Shopping","Education","Entertainment","Utilities","Travel","Savings","Other"]
EXPENSE_LOCATIONS = ["Supermarket","Restaurant","Pharmacy","Hospital","Online Store","Mall","Gas Station","Bank","School","Gym","Cafe","Other"]

COLORS = {
    "bg":"#0F1117","card":"#1A1D27","card2":"#22263A",
    "accent":"#6C63FF","success":"#43E97B","danger":"#FF4B4B",
    "warning":"#F7971E","text":"#E8E9F3","subtext":"#8B8FA8","border":"#2E3250",
}


class TransactionDialog(ctk.CTkToplevel):
    def __init__(self, parent, trans_type="income", on_save=None):
        super().__init__(parent)
        self.trans_type=trans_type; self.on_save=on_save
        self.title("Add Income" if trans_type=="income" else "Add Expense")
        self.geometry("520x520"); self.configure(fg_color=COLORS["bg"])
        self.resizable(False,False); self.grab_set()
        self._build()

    def _build(self):
        is_inc=self.trans_type=="income"
        accent=COLORS["success"] if is_inc else COLORS["danger"]
        ctk.CTkLabel(self,text="💰  ADD INCOME" if is_inc else "💸  ADD EXPENSE",
                     font=("Georgia",14,"bold"),text_color=accent).pack(pady=(24,6),padx=28,anchor="w")

        card=ctk.CTkFrame(self,fg_color=COLORS["card"],corner_radius=14); card.pack(fill="x",padx=24,pady=6)
        f=ctk.CTkFrame(card,fg_color="transparent"); f.pack(fill="x",padx=18,pady=14)

        def lbl(t): ctk.CTkLabel(f,text=t,font=("Georgia",11),text_color=COLORS["subtext"],anchor="w").pack(fill="x")
        def inp(**kw): return ctk.CTkEntry(f,fg_color=COLORS["card2"],border_color=COLORS["border"],border_width=1,text_color=COLORS["text"],height=36,**kw)

        lbl("Amount (EGP) *"); self.amount_e=inp(); self.amount_e.pack(fill="x",pady=(2,12))

        lbl("Category *")
        cats=INCOME_SOURCES if is_inc else EXPENSE_CATEGORIES
        self.cat_var=ctk.StringVar(value=cats[0])
        self.cat_menu=ctk.CTkOptionMenu(f,variable=self.cat_var,values=cats,fg_color=COLORS["card2"],
                                        button_color=COLORS["border"],dropdown_fg_color=COLORS["card"],
                                        command=self._on_cat); self.cat_menu.pack(fill="x",pady=(2,4))
        self.custom_cat=inp(placeholder_text="Specify category…")

        if is_inc:
            lbl("Source *")
            self.src_var=ctk.StringVar(value=INCOME_SOURCES[0])
            self.src_menu=ctk.CTkOptionMenu(f,variable=self.src_var,values=INCOME_SOURCES,fg_color=COLORS["card2"],
                                            button_color=COLORS["border"],dropdown_fg_color=COLORS["card"],
                                            command=self._on_src); self.src_menu.pack(fill="x",pady=(2,4))
            self.custom_src=inp(placeholder_text="Specify source…")
            self.loc_var=None
        else:
            self.src_var=None
            lbl("Where (Location) *")
            self.loc_var=ctk.StringVar(value=EXPENSE_LOCATIONS[0])
            self.loc_menu=ctk.CTkOptionMenu(f,variable=self.loc_var,values=EXPENSE_LOCATIONS,fg_color=COLORS["card2"],
                                            button_color=COLORS["border"],dropdown_fg_color=COLORS["card"],
                                            command=self._on_loc); self.loc_menu.pack(fill="x",pady=(2,4))
            self.custom_loc=inp(placeholder_text="Specify location…")
            self.custom_src=None

        lbl("Date *")
        self.date_dp=DatePicker(f,width=180); self.date_dp.pack(fill="x",pady=(2,12))

        lbl("Notes")
        self.notes_e=inp(placeholder_text="Optional…"); self.notes_e.pack(fill="x",pady=(2,4))

        btns=ctk.CTkFrame(self,fg_color="transparent"); btns.pack(fill="x",padx=24,pady=14)
        ctk.CTkButton(btns,text="Cancel",fg_color=COLORS["card2"],hover_color=COLORS["border"],text_color=COLORS["subtext"],command=self.destroy).pack(side="left",expand=True,padx=(0,6))
        ctk.CTkButton(btns,text="✓  Save",fg_color=accent,command=self._save).pack(side="left",expand=True)

    def _on_cat(self,v):
        if v=="Other": self.custom_cat.pack(fill="x",pady=(0,8))
        else: self.custom_cat.pack_forget()
    def _on_src(self,v):
        if v=="Other": self.custom_src.pack(fill="x",pady=(0,8))
        else: self.custom_src.pack_forget()
    def _on_loc(self,v):
        if v=="Other": self.custom_loc.pack(fill="x",pady=(0,8))
        else: self.custom_loc.pack_forget()

    def _save(self):
        try:
            amount=float(self.amount_e.get().strip())
            if amount<=0: raise ValueError
        except: messagebox.showerror("Error","Enter a valid positive amount.",parent=self); return

        cat=self.cat_var.get()
        if cat=="Other": cat=self.custom_cat.get().strip() or "Other"

        src,loc="",""
        if self.trans_type=="income":
            src=self.src_var.get()
            if src=="Other": src=self.custom_src.get().strip() or "Other"
        else:
            loc=self.loc_var.get()
            if loc=="Other": loc=self.custom_loc.get().strip() or "Other"

        date_str=self.date_dp.get_date().strftime("%Y-%m-%d")
        notes=self.notes_e.get().strip()
        db.add_transaction(self.trans_type,amount,cat,src,loc,date_str,notes)
        if self.on_save: self.on_save()
        self.destroy()


class FinanceTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.filter_month=None; self.active_cat="All"
        self._build(); self.load_transactions()

    def _build(self):
        top=ctk.CTkFrame(self,fg_color="transparent"); top.pack(fill="x",padx=22,pady=(18,8))
        ctk.CTkLabel(top,text="FINANCE TRACKER",font=("Georgia",20,"bold"),text_color=COLORS["text"]).pack(side="left")
        br=ctk.CTkFrame(top,fg_color="transparent"); br.pack(side="right")
        ctk.CTkButton(br,text="＋  Income",fg_color=COLORS["success"],hover_color="#2dc960",width=110,height=36,command=self.add_income).pack(side="left",padx=(0,6))
        ctk.CTkButton(br,text="－  Expense",fg_color=COLORS["danger"],hover_color="#cc3333",width=110,height=36,command=self.add_expense).pack(side="left")

        self.summary_frame=ctk.CTkFrame(self,fg_color="transparent"); self.summary_frame.pack(fill="x",padx=22,pady=(0,8))

        fbar=ctk.CTkFrame(self,fg_color=COLORS["card"],corner_radius=12); fbar.pack(fill="x",padx=22,pady=(0,8))
        fi=ctk.CTkFrame(fbar,fg_color="transparent"); fi.pack(fill="x",padx=14,pady=10)
        ctk.CTkLabel(fi,text="Filter:",font=("Georgia",11,"bold"),text_color=COLORS["subtext"]).pack(side="left",padx=(0,10))

        ctk.CTkLabel(fi,text="Type",font=("Georgia",10),text_color=COLORS["subtext"]).pack(side="left")
        self.type_f=ctk.CTkOptionMenu(fi,values=["All","income","expense"],width=100,fg_color=COLORS["card2"],button_color=COLORS["border"],dropdown_fg_color=COLORS["card"],command=lambda _:self.load_transactions()); self.type_f.pack(side="left",padx=(4,10))

        ctk.CTkLabel(fi,text="Month",font=("Georgia",10),text_color=COLORS["subtext"]).pack(side="left")
        months=self._get_months()
        self.month_f=ctk.CTkOptionMenu(fi,values=["All"]+months,width=130,fg_color=COLORS["card2"],button_color=COLORS["border"],dropdown_fg_color=COLORS["card"],command=self._on_month); self.month_f.pack(side="left",padx=(4,10))

        ctk.CTkLabel(fi,text="From",font=("Georgia",10),text_color=COLORS["subtext"]).pack(side="left")
        self.from_dp=DatePicker(fi,on_change=lambda _:self.load_transactions(),width=130); self.from_dp.pack(side="left",padx=(4,8))

        ctk.CTkLabel(fi,text="To",font=("Georgia",10),text_color=COLORS["subtext"]).pack(side="left")
        self.to_dp=DatePicker(fi,on_change=lambda _:self.load_transactions(),width=130); self.to_dp.pack(side="left",padx=(4,10))

        ctk.CTkButton(fi,text="↺ Reset",width=80,height=30,fg_color=COLORS["card2"],hover_color=COLORS["border"],text_color=COLORS["subtext"],command=self.reset_filters).pack(side="left")

        cframe=ctk.CTkFrame(self,fg_color="transparent"); cframe.pack(fill="x",padx=22,pady=(0,8))
        ctk.CTkLabel(cframe,text="Category:",font=("Georgia",10),text_color=COLORS["subtext"]).pack(side="left",padx=(0,6))
        self.cat_btns={}
        all_cats=["All"]+EXPENSE_CATEGORIES[:8]
        for cat in all_cats:
            btn=ctk.CTkButton(cframe,text=cat,width=100,height=26,font=("Georgia",9),
                              fg_color=COLORS["accent"] if cat=="All" else COLORS["card2"],
                              hover_color=COLORS["accent"],corner_radius=20,
                              command=lambda c=cat:self.toggle_cat(c))
            btn.pack(side="left",padx=2); self.cat_btns[cat]=btn

        self.scroll=ctk.CTkScrollableFrame(self,fg_color="transparent")
        self.scroll.pack(fill="both",expand=True,padx=22,pady=(0,12))

    def _get_months(self):
        y=date.today().year; return [f"{y}-{m:02d}" for m in range(1,13)]

    def _on_month(self,v): self.filter_month=None if v=="All" else v; self.load_transactions()

    def toggle_cat(self,cat):
        self.active_cat=cat
        for c,b in self.cat_btns.items(): b.configure(fg_color=COLORS["accent"] if c==cat else COLORS["card2"])
        self.load_transactions()

    def reset_filters(self):
        self.type_f.set("All"); self.month_f.set("All"); self.filter_month=None
        self.from_dp.set_date(date.today()); self.to_dp.set_date(date.today())
        self.active_cat="All"
        for c,b in self.cat_btns.items(): b.configure(fg_color=COLORS["accent"] if c=="All" else COLORS["card2"])
        self.load_transactions()

    def get_filters(self):
        f={}
        if self.type_f.get()!="All": f["type"]=self.type_f.get()
        if self.active_cat!="All": f["category"]=self.active_cat
        if self.filter_month: f["month"]=self.filter_month
        return f

    def load_transactions(self):
        for w in self.summary_frame.winfo_children(): w.destroy()
        income,expense,_,_,_,_,_=db.get_finance_stats(self.filter_month)
        balance=income-expense; bal_c=COLORS["success"] if balance>=0 else COLORS["danger"]
        for label,val,color in [("Total Income",income,COLORS["success"]),("Total Expenses",expense,COLORS["danger"]),("Balance",balance,bal_c)]:
            card=ctk.CTkFrame(self.summary_frame,fg_color=COLORS["card"],corner_radius=12); card.pack(side="left",fill="x",expand=True,padx=4)
            ctk.CTkLabel(card,text=label,font=("Georgia",10),text_color=COLORS["subtext"]).pack(pady=(10,2))
            ctk.CTkLabel(card,text=f"EGP {val:,.2f}",font=("Georgia",15,"bold"),text_color=color).pack(pady=(0,10))

        for w in self.scroll.winfo_children(): w.destroy()
        txns=db.get_transactions(self.get_filters())
        if not txns:
            ctk.CTkLabel(self.scroll,text="No transactions found. Add income or expense! ✦",font=("Georgia",14),text_color=COLORS["subtext"]).pack(pady=50); return
        for t in txns: self._txn_card(t)

    def _txn_card(self,t):
        is_inc=t["type"]=="income"; color=COLORS["success"] if is_inc else COLORS["danger"]
        card=ctk.CTkFrame(self.scroll,fg_color=COLORS["card"],corner_radius=12); card.pack(fill="x",pady=4)
        row=ctk.CTkFrame(card,fg_color="transparent"); row.pack(fill="x",padx=16,pady=10)
        ctk.CTkLabel(row,text="💰" if is_inc else "💸",font=("Arial",22)).pack(side="left",padx=(0,12))
        info=ctk.CTkFrame(row,fg_color="transparent"); info.pack(side="left",fill="both",expand=True)
        tr=ctk.CTkFrame(info,fg_color="transparent"); tr.pack(fill="x")
        ctk.CTkLabel(tr,text=t["category"] or t["type"].capitalize(),font=("Georgia",12,"bold"),text_color=COLORS["text"]).pack(side="left")
        ctk.CTkLabel(tr,text=t["date"],font=("Georgia",10),text_color=COLORS["subtext"]).pack(side="right")
        sub=[]
        if t["source"]: sub.append(f"Source: {t['source']}")
        if t["expense_location"]: sub.append(f"At: {t['expense_location']}")
        if t["notes"]: sub.append(t["notes"])
        if sub: ctk.CTkLabel(info,text=" · ".join(sub),font=("Georgia",10),text_color=COLORS["subtext"],anchor="w").pack(fill="x")
        ctk.CTkLabel(row,text=f"{'+'if is_inc else'-'} EGP {t['amount']:,.2f}",font=("Georgia",14,"bold"),text_color=color).pack(side="right",padx=(8,8))
        ctk.CTkButton(row,text="✕",width=28,height=28,fg_color=COLORS["card2"],hover_color=COLORS["danger"],command=lambda t=t:self.confirm_delete(t)).pack(side="right")

    def add_income(self): TransactionDialog(self,"income",on_save=self.load_transactions)
    def add_expense(self): TransactionDialog(self,"expense",on_save=self.load_transactions)
    def confirm_delete(self,t):
        if messagebox.askyesno("Delete",f"Delete this {t['type']} of EGP {t['amount']:,.2f}?"): db.delete_transaction(t["id"]); self.load_transactions()
