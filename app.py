"""
Electric Quote Builder  v2.0
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os, sys
from datetime import date
from data import DataManager
from quote_pdf import generate_pdf

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

YELLOW   = "#F5B800"
DARK_BG  = "#1A1A1A"
CARD_BG  = "#242424"
BORDER   = "#3A3A3A"
TEXT_MAIN= "#FFFFFF"
TEXT_DIM = "#888888"
GREEN    = "#2ECC71"
RED_CLR  = "#E74C3C"
BLUE     = "#4A90D9"
ORANGE   = "#E67E22"


def resource_path(p):
    base = sys._MEIPASS if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, p)

def make_tree(parent, style_name, columns, headings, widths, anchors=None):
    """Helper — build a styled ttk.Treeview inside parent."""
    s = ttk.Style()
    s.theme_use("default")
    s.configure(f"{style_name}.Treeview",
                background=CARD_BG, foreground=TEXT_MAIN,
                fieldbackground=CARD_BG, rowheight=28,
                font=("Segoe UI", 11), borderwidth=0, relief="flat")
    s.configure(f"{style_name}.Treeview.Heading",
                background=DARK_BG, foreground=YELLOW,
                font=("Segoe UI", 10, "bold"), relief="flat")
    s.map(f"{style_name}.Treeview",
          background=[("selected", "#2A4A7A")],
          fieldbackground=[("!focus", CARD_BG), ("focus", CARD_BG)])

    tree = ttk.Treeview(parent, style=f"{style_name}.Treeview",
                        columns=columns, show="headings")
    for col, heading, width in zip(columns, headings, widths):
        anchor = "w"
        if anchors and col in anchors:
            anchor = anchors[col]
        tree.heading(col, text=heading)
        tree.column(col, width=width, anchor=anchor)

    sb = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    tree.pack(side="left", fill="both", expand=True, padx=(8,0), pady=8)
    sb.pack(side="right", fill="y", pady=8)
    return tree

def section_header(parent, text):
    f = ctk.CTkFrame(parent, fg_color="transparent")
    f.pack(fill="x", padx=16, pady=(14, 2))
    ctk.CTkLabel(f, text=text.upper(), font=("Segoe UI", 10, "bold"),
                 text_color=YELLOW).pack(side="left")
    ctk.CTkFrame(f, height=1, fg_color=BORDER).pack(side="left", fill="x",
                                                     expand=True, padx=(8,0))


# ══════════════════════════════════════════════════════════════════════════════
class MaterialPickerDialog(ctk.CTkToplevel):
    def __init__(self, parent, materials):
        super().__init__(parent)
        self.title("Add Material")
        self.geometry("560x500")
        self.resizable(False, False)
        self.grab_set()
        self.result   = None
        self.materials = materials
        self._build()

    def _build(self):
        self.configure(fg_color=CARD_BG)
        sf = ctk.CTkFrame(self, fg_color="transparent")
        sf.pack(fill="x", padx=16, pady=(16,8))
        ctk.CTkLabel(sf, text="🔍  Search materials", text_color=TEXT_DIM,
                     font=("Segoe UI", 12)).pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._filter)
        ctk.CTkEntry(sf, textvariable=self.search_var, width=280,
                     placeholder_text="e.g. romex, outlet…",
                     fg_color=DARK_BG, border_color=BORDER).pack(side="right")

        tf = ctk.CTkFrame(self, fg_color=DARK_BG, corner_radius=8)
        tf.pack(fill="both", expand=True, padx=16, pady=4)
        self.tree = make_tree(tf, "Pick",
                              ("id","name","price"),
                              ("ID","Material","Unit Price"),
                              (60,320,100),
                              anchors={"id":"center","price":"e"})
        self._populate(self.materials)
        self.tree.bind("<Double-1>", lambda e: self._select())

        bot = ctk.CTkFrame(self, fg_color="transparent")
        bot.pack(fill="x", padx=16, pady=12)
        ctk.CTkLabel(bot, text="Qty:", font=("Segoe UI", 13, "bold")).pack(side="left")
        self.qty_var = tk.StringVar(value="1")
        ctk.CTkEntry(bot, textvariable=self.qty_var, width=70,
                     fg_color=DARK_BG, border_color=BORDER).pack(side="left", padx=(6,16))
        ctk.CTkButton(bot, text="Cancel", width=90, fg_color=BORDER,
                      hover_color="#555", command=self.destroy).pack(side="right", padx=(8,0))
        ctk.CTkButton(bot, text="Add to Quote", width=130,
                      fg_color=YELLOW, text_color="#000", hover_color="#D4A000",
                      font=("Segoe UI", 12, "bold"), command=self._select).pack(side="right")

    def _populate(self, items):
        self.tree.delete(*self.tree.get_children())
        for m in items:
            self.tree.insert("", "end", values=(m["id"], m["name"], f"${m['price']:.2f}"))

    def _filter(self, *_):
        q = self.search_var.get().lower()
        self._populate([m for m in self.materials
                        if q in m["name"].lower() or q in str(m["id"])])

    def _select(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select a material", "Click a material first.", parent=self)
            return
        vals = self.tree.item(sel[0], "values")
        try:
            qty = float(self.qty_var.get())
            assert qty > 0
        except Exception:
            messagebox.showwarning("Invalid qty", "Enter a positive number.", parent=self)
            return
        price = float(vals[2].replace("$",""))
        self.result = {"id": vals[0], "name": vals[1], "qty": qty,
                       "unit_price": price, "line_total": qty * price}
        self.destroy()


# ══════════════════════════════════════════════════════════════════════════════
class QuoteBuilderFrame(ctk.CTkFrame):
    def __init__(self, parent, dm, on_save_callback):
        super().__init__(parent, fg_color="transparent")
        self.dm         = dm
        self.on_save    = on_save_callback
        self.line_items = []
        self.estimate_id= self._next_estimate_id()
        self._build_ui()
        self._recalculate()

    def _next_estimate_id(self):
        ests = self.dm.load_estimates()
        if not ests: return "EST-1001"
        last = ests[-1].get("estimate_id", "EST-1000")
        try:    num = int(last.split("-")[1]) + 1
        except: num = 1001
        return f"EST-{num}"

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)
        left = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12)
        left.grid(row=0, column=0, sticky="nsew", padx=(0,8))
        left.grid_rowconfigure(2, weight=1)
        left.grid_columnconfigure(0, weight=1)
        self._build_left(left)
        right = ctk.CTkScrollableFrame(self, fg_color=CARD_BG, corner_radius=12)
        right.grid(row=0, column=1, sticky="nsew", padx=(8,0))
        right.grid_columnconfigure(0, weight=1)
        self._build_right(right)

    def _build_left(self, p):
        hdr = ctk.CTkFrame(p, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=16, pady=(16,8))
        ctk.CTkLabel(hdr, text="Materials", font=("Segoe UI", 16, "bold")).pack(side="left")
        ctk.CTkButton(hdr, text="+ Add Material", width=130,
                      fg_color=YELLOW, text_color="#000", hover_color="#D4A000",
                      font=("Segoe UI", 12, "bold"),
                      command=self._open_picker).pack(side="right")

        cols = ctk.CTkFrame(p, fg_color=DARK_BG, corner_radius=6)
        cols.grid(row=1, column=0, sticky="ew", padx=16, pady=(0,4))
        for text, w in [("Material",280),("Qty",50),("Unit $",80),("Total",90),("",36)]:
            ctk.CTkLabel(cols, text=text, font=("Segoe UI",10,"bold"),
                         text_color=YELLOW, width=w, anchor="w").pack(side="left", padx=4, pady=4)

        self.items_frame = ctk.CTkScrollableFrame(p, fg_color="transparent")
        self.items_frame.grid(row=2, column=0, sticky="nsew", padx=16, pady=4)
        self.items_frame.grid_columnconfigure(0, weight=1)
        self._show_empty()

        sub = ctk.CTkFrame(p, fg_color=DARK_BG, corner_radius=8)
        sub.grid(row=3, column=0, sticky="ew", padx=16, pady=(4,16))
        ctk.CTkLabel(sub, text="Materials Subtotal", font=("Segoe UI",12),
                     text_color=TEXT_DIM).pack(side="left", padx=12, pady=8)
        self.mat_subtotal_label = ctk.CTkLabel(sub, text="$0.00",
                                               font=("Segoe UI",14,"bold"))
        self.mat_subtotal_label.pack(side="right", padx=12, pady=8)

    def _show_empty(self):
        ctk.CTkLabel(self.items_frame,
                     text="No materials yet — click '+ Add Material' to start.",
                     text_color=TEXT_DIM, font=("Segoe UI",12)).pack(pady=40)

    def _build_right(self, p):
        pad = {"padx":16,"pady":(8,4)}

        section_header(p, "Estimate Info")
        ig = ctk.CTkFrame(p, fg_color="transparent")
        ig.pack(fill="x", **pad)
        ctk.CTkLabel(ig, text=f"ID: {self.estimate_id}",
                     font=("Segoe UI",12), text_color=TEXT_DIM).pack(anchor="w")
        ctk.CTkLabel(ig, text="Date", font=("Segoe UI",11),
                     text_color=TEXT_DIM).pack(anchor="w", pady=(8,0))
        self.date_entry = ctk.CTkEntry(ig, fg_color=DARK_BG, border_color=BORDER)
        self.date_entry.insert(0, str(date.today()))
        self.date_entry.pack(fill="x")

        section_header(p, "Customer Info")
        cust = ctk.CTkFrame(p, fg_color="transparent")
        cust.pack(fill="x", **pad)
        self.client_id_var = tk.StringVar()
        client_names = self.dm.get_client_names()
        ctk.CTkLabel(cust, text="Client (existing)", font=("Segoe UI",11),
                     text_color=TEXT_DIM).pack(anchor="w")
        self.client_combo = ctk.CTkComboBox(cust, values=["(new client)"] + client_names,
                                            variable=self.client_id_var,
                                            fg_color=DARK_BG, border_color=BORDER,
                                            command=self._autofill_client)
        self.client_combo.set("(new client)")
        self.client_combo.pack(fill="x", pady=(0,6))

        self.cust_fields = {}
        for label, key in [("Name","name"),("Address","address"),
                            ("Phone","phone"),("Email","email")]:
            ctk.CTkLabel(cust, text=label, font=("Segoe UI",11),
                         text_color=TEXT_DIM).pack(anchor="w", pady=(4,0))
            e = ctk.CTkEntry(cust, fg_color=DARK_BG, border_color=BORDER)
            e.pack(fill="x")
            self.cust_fields[key] = e

        ctk.CTkLabel(cust, text="Service Address (if different)", font=("Segoe UI",11),
                     text_color=TEXT_DIM).pack(anchor="w", pady=(8,0))
        self.service_addr = ctk.CTkEntry(cust, fg_color=DARK_BG, border_color=BORDER)
        self.service_addr.pack(fill="x")

        section_header(p, "Job Variables")
        job = ctk.CTkFrame(p, fg_color="transparent")
        job.pack(fill="x", **pad)
        self.job_vars = {}
        for label, key, default in [
            ("Hourly Rate ($)","hourly_rate","120"),
            ("Hours Estimated","hours",""),
            ("Miles from Shop","miles",""),
            ("MPG","mpg","13"),
            ("Gas Price ($/gal)","gas_price","4.50"),
        ]:
            ctk.CTkLabel(job, text=label, font=("Segoe UI",11),
                         text_color=TEXT_DIM).pack(anchor="w", pady=(4,0))
            v = tk.StringVar(value=default)
            v.trace_add("write", lambda *a: self._recalculate())
            e = ctk.CTkEntry(job, textvariable=v, fg_color=DARK_BG, border_color=BORDER)
            e.pack(fill="x")
            self.job_vars[key] = v

        ctk.CTkLabel(job, text="Markup / Contingency %", font=("Segoe UI",11),
                     text_color=TEXT_DIM).pack(anchor="w", pady=(8,0))
        self.markup_var = tk.StringVar(value="10")
        self.markup_var.trace_add("write", lambda *a: self._recalculate())
        ctk.CTkEntry(job, textvariable=self.markup_var,
                     fg_color=DARK_BG, border_color=BORDER).pack(fill="x")

        section_header(p, "Cost Breakdown")
        bd = ctk.CTkFrame(p, fg_color=DARK_BG, corner_radius=8)
        bd.pack(fill="x", padx=16, pady=(4,8))
        self.breakdown_labels = {}
        for key, label, color in [
            ("materials","Materials",TEXT_DIM),
            ("labor","Labor",TEXT_DIM),
            ("drive","Drive",TEXT_DIM),
            ("pre_markup","Pre-Markup",TEXT_DIM),
            ("markup_amt","Markup",TEXT_DIM),
            ("total","TOTAL ESTIMATE",YELLOW),
        ]:
            row = ctk.CTkFrame(bd, fg_color="transparent")
            row.pack(fill="x", padx=8, pady=2)
            bold = "bold" if key == "total" else "normal"
            sz   = 13 if key == "total" else 11
            ctk.CTkLabel(row, text=label, font=("Segoe UI",sz,bold),
                         text_color=color, anchor="w").pack(side="left")
            lbl = ctk.CTkLabel(row, text="$0.00",
                               font=("Segoe UI",sz,"bold"), text_color=color)
            lbl.pack(side="right")
            self.breakdown_labels[key] = lbl

        section_header(p, "Description & Notes")
        notes = ctk.CTkFrame(p, fg_color="transparent")
        notes.pack(fill="x", **pad)
        ctk.CTkLabel(notes, text="Description of Work", font=("Segoe UI",11),
                     text_color=TEXT_DIM).pack(anchor="w")
        self.desc_text = ctk.CTkTextbox(notes, height=70, fg_color=DARK_BG, border_color=BORDER)
        self.desc_text.pack(fill="x", pady=(0,6))
        ctk.CTkLabel(notes, text="Notes / Terms", font=("Segoe UI",11),
                     text_color=TEXT_DIM).pack(anchor="w")
        self.notes_text = ctk.CTkTextbox(notes, height=70, fg_color=DARK_BG, border_color=BORDER)
        self.notes_text.pack(fill="x")

        btns = ctk.CTkFrame(p, fg_color="transparent")
        btns.pack(fill="x", padx=16, pady=(12,20))
        ctk.CTkButton(btns, text="💾 Save Estimate", width=160,
                      fg_color=GREEN, hover_color="#27AE60", text_color="#000",
                      font=("Segoe UI",13,"bold"), command=self._save).pack(side="left", padx=(0,8))
        ctk.CTkButton(btns, text="📄 Export PDF", width=140,
                      fg_color=BLUE, hover_color="#357ABD",
                      font=("Segoe UI",13,"bold"), command=self._export_pdf).pack(side="left")
        ctk.CTkButton(btns, text="🗑 Clear", width=80,
                      fg_color=BORDER, hover_color="#555",
                      command=self._clear).pack(side="right")

    def _open_picker(self):
        dlg = MaterialPickerDialog(self, self.dm.materials)
        self.wait_window(dlg)
        if dlg.result:
            self.line_items.append(dlg.result)
            self._refresh_items()
            self._recalculate()

    def _refresh_items(self):
        for w in self.items_frame.winfo_children():
            w.destroy()
        if not self.line_items:
            self._show_empty()
            return
        for i, item in enumerate(self.line_items):
            row = ctk.CTkFrame(self.items_frame,
                               fg_color=DARK_BG if i%2==0 else CARD_BG, corner_radius=4)
            row.pack(fill="x", pady=1)
            ctk.CTkLabel(row, text=item["name"], font=("Segoe UI",11),
                         width=280, anchor="w").pack(side="left", padx=(8,4), pady=5)
            ctk.CTkLabel(row, text=f"×{item['qty']:.0f}", font=("Segoe UI",11),
                         text_color=TEXT_DIM, width=40, anchor="center").pack(side="left", padx=4)
            ctk.CTkLabel(row, text=f"${item['unit_price']:.2f}", font=("Segoe UI",11),
                         text_color=TEXT_DIM, width=75, anchor="e").pack(side="left", padx=4)
            ctk.CTkLabel(row, text=f"${item['line_total']:.2f}", font=("Segoe UI",11,"bold"),
                         width=90, anchor="e").pack(side="left", padx=4)
            idx = i
            ctk.CTkButton(row, text="✕", width=28, height=24,
                          fg_color="transparent", hover_color=RED_CLR, text_color=TEXT_DIM,
                          font=("Segoe UI",11),
                          command=lambda x=idx: self._remove_item(x)).pack(side="right", padx=4)

    def _remove_item(self, idx):
        self.line_items.pop(idx)
        self._refresh_items()
        self._recalculate()

    def _recalculate(self):
        mats = sum(i["line_total"] for i in self.line_items)
        self.mat_subtotal_label.configure(text=f"${mats:,.2f}")
        def _f(key, default=0.0):
            try:    return float(self.job_vars[key].get())
            except: return default
        rate  = _f("hourly_rate", 120)
        hours = _f("hours")
        miles = _f("miles")
        mpg   = _f("mpg", 13) or 13
        gas   = _f("gas_price", 4.5)
        labor = rate * hours
        drive = miles * 2 * (gas / mpg)
        try:    markup_pct = float(self.markup_var.get()) / 100
        except: markup_pct = 0.0
        pre   = mats + labor + drive
        mkup  = pre * markup_pct
        total = pre + mkup
        self.breakdown_labels["materials"].configure(text=f"${mats:,.2f}")
        self.breakdown_labels["labor"].configure(text=f"${labor:,.2f}")
        self.breakdown_labels["drive"].configure(text=f"${drive:,.2f}")
        self.breakdown_labels["pre_markup"].configure(text=f"${pre:,.2f}")
        self.breakdown_labels["markup_amt"].configure(text=f"${mkup:,.2f}")
        self.breakdown_labels["total"].configure(text=f"${total:,.2f}")
        self._current_total = total

    def _autofill_client(self, choice):
        if choice == "(new client)":
            for e in self.cust_fields.values(): e.delete(0,"end")
            return
        client = self.dm.get_client(choice)
        if client:
            for field in ("name","address","phone","email"):
                self.cust_fields[field].delete(0,"end")
                self.cust_fields[field].insert(0, client.get(field,""))

    def _gather_data(self):
        self._recalculate()
        return {
            "estimate_id": self.estimate_id,
            "date":        self.date_entry.get(),
            "client_id":   self.client_combo.get(),
            "customer":    {k: v.get() for k, v in self.cust_fields.items()},
            "service_address": self.service_addr.get(),
            "line_items":  self.line_items,
            "job_vars":    {k: v.get() for k, v in self.job_vars.items()},
            "markup_pct":  self.markup_var.get(),
            "description": self.desc_text.get("1.0","end").strip(),
            "notes":       self.notes_text.get("1.0","end").strip(),
            "total":       self._current_total,
            "breakdown": {
                "materials":  sum(i["line_total"] for i in self.line_items),
                "labor":      float(self.job_vars["hourly_rate"].get() or 0) *
                              float(self.job_vars["hours"].get() or 0),
                "drive":      self.breakdown_labels["drive"].cget("text"),
                "markup_amt": self.breakdown_labels["markup_amt"].cget("text"),
            }
        }

    def _save(self):
        data = self._gather_data()
        if not data["customer"]["name"] and data["client_id"] == "(new client)":
            messagebox.showwarning("Missing info", "Please enter a customer name.")
            return
        self.dm.save_estimate(data)
        if data["client_id"] == "(new client)" and data["customer"]["name"]:
            self.dm.save_client(data["customer"])
        messagebox.showinfo("Saved", f"Estimate {self.estimate_id} saved!")
        self.on_save()

    def _export_pdf(self):
        data = self._gather_data()
        path = filedialog.asksaveasfilename(defaultextension=".pdf",
                                            filetypes=[("PDF","*.pdf")],
                                            initialfile=f"{self.estimate_id}.pdf")
        if path:
            generate_pdf(data, path)
            messagebox.showinfo("PDF Exported", f"Saved to:\n{path}")

    def _clear(self):
        if messagebox.askyesno("Clear?", "Clear all materials and reset the form?"):
            self.line_items.clear()
            self._refresh_items()
            for e in self.cust_fields.values(): e.delete(0,"end")
            self.desc_text.delete("1.0","end")
            self.notes_text.delete("1.0","end")
            self._recalculate()


# ══════════════════════════════════════════════════════════════════════════════
class EstimatesLogFrame(ctk.CTkFrame):
    def __init__(self, parent, dm):
        super().__init__(parent, fg_color="transparent")
        self.dm = dm
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        hdr = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=10)
        hdr.grid(row=0, column=0, sticky="ew", pady=(0,8))
        ctk.CTkLabel(hdr, text="Saved Estimates",
                     font=("Segoe UI",16,"bold")).pack(side="left", padx=16, pady=12)
        ctk.CTkButton(hdr, text="↻ Refresh", width=100, fg_color=BORDER,
                      hover_color="#555", command=self._load).pack(side="right", padx=16)

        tree_card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=10)
        tree_card.grid(row=1, column=0, sticky="nsew")
        self.tree = make_tree(tree_card, "Log",
                              ("id","date","customer","total"),
                              ("Estimate ID","Date","Customer","Total"),
                              (130,120,300,130),
                              anchors={"id":"center","date":"center","total":"e"})

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=2, column=0, sticky="ew", pady=(8,0))
        ctk.CTkButton(actions, text="📄 Export PDF", width=140,
                      fg_color=BLUE, hover_color="#357ABD",
                      command=self._export_selected).pack(side="left", padx=(0,8))
        ctk.CTkButton(actions, text="🗑 Delete", width=100,
                      fg_color=RED_CLR, hover_color="#C0392B",
                      command=self._delete_selected).pack(side="left")
        self._load()

    def _load(self):
        self.tree.delete(*self.tree.get_children())
        for est in self.dm.load_estimates():
            name = est.get("customer",{}).get("name","") or est.get("client_id","")
            self.tree.insert("", "end", iid=est["estimate_id"], values=(
                est["estimate_id"], est.get("date",""), name,
                f"${est.get('total',0):,.2f}"
            ))

    def _get_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("No selection","Select an estimate first.")
            return None
        return self.dm.get_estimate(sel[0])

    def _export_selected(self):
        est = self._get_selected()
        if not est: return
        path = filedialog.asksaveasfilename(defaultextension=".pdf",
                                            filetypes=[("PDF","*.pdf")],
                                            initialfile=f"{est['estimate_id']}.pdf")
        if path:
            generate_pdf(est, path)
            messagebox.showinfo("PDF Exported", f"Saved to:\n{path}")

    def _delete_selected(self):
        sel = self.tree.selection()
        if not sel: return
        if messagebox.askyesno("Delete?", f"Delete estimate {sel[0]}?"):
            self.dm.delete_estimate(sel[0])
            self._load()


# ══════════════════════════════════════════════════════════════════════════════
class ClientLogFrame(ctk.CTkFrame):
    """Browse, add, edit, and delete clients."""

    def __init__(self, parent, dm):
        super().__init__(parent, fg_color="transparent")
        self.dm = dm
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        hdr = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=10)
        hdr.grid(row=0, column=0, sticky="ew", pady=(0,8))
        ctk.CTkLabel(hdr, text="Client Log",
                     font=("Segoe UI",16,"bold")).pack(side="left", padx=16, pady=12)
        ctk.CTkButton(hdr, text="+ New Client", width=120,
                      fg_color=YELLOW, text_color="#000", hover_color="#D4A000",
                      font=("Segoe UI",12,"bold"),
                      command=self._new_client).pack(side="right", padx=8)
        ctk.CTkButton(hdr, text="↻ Refresh", width=100, fg_color=BORDER,
                      hover_color="#555", command=self._load).pack(side="right")

        tree_card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=10)
        tree_card.grid(row=1, column=0, sticky="nsew")
        self.tree = make_tree(tree_card, "Clients",
                              ("id","name","phone","email","address"),
                              ("Client ID","Name","Phone","Email","Address"),
                              (90,180,120,200,260),
                              anchors={"id":"center"})
        self.tree.bind("<Double-1>", self._edit_client)

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=2, column=0, sticky="ew", pady=(8,0))
        ctk.CTkLabel(actions, text="Double-click a row to edit.",
                     text_color=TEXT_DIM, font=("Segoe UI",11)).pack(side="left")
        ctk.CTkButton(actions, text="🗑 Delete", width=100,
                      fg_color=RED_CLR, hover_color="#C0392B",
                      command=self._delete_client).pack(side="right")
        self._load()

    def _load(self):
        self.tree.delete(*self.tree.get_children())
        for c in self.dm.load_clients():
            self.tree.insert("", "end", iid=c["id"], values=(
                c["id"], c.get("name",""), c.get("phone",""),
                c.get("email",""), c.get("address","")
            ))

    def _open_form(self, client=None):
        """Open add/edit dialog. If client is None, creates new."""
        dlg = ctk.CTkToplevel(self)
        dlg.title("Edit Client" if client else "New Client")
        dlg.geometry("460x380")
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.configure(fg_color=CARD_BG)

        fields = {}
        for label, key in [("Name","name"),("Phone","phone"),
                            ("Email","email"),("Address","address")]:
            ctk.CTkLabel(dlg, text=label, font=("Segoe UI",11),
                         text_color=TEXT_DIM).pack(anchor="w", padx=20, pady=(10,0))
            e = ctk.CTkEntry(dlg, fg_color=DARK_BG, border_color=BORDER)
            if client: e.insert(0, client.get(key,""))
            e.pack(fill="x", padx=20)
            fields[key] = e

        def _save():
            info = {k: v.get() for k, v in fields.items()}
            if client: info["id"] = client["id"]
            if not info.get("name"):
                messagebox.showwarning("Missing", "Name is required.", parent=dlg)
                return
            self.dm.save_client(info)
            self._load()
            dlg.destroy()

        bot = ctk.CTkFrame(dlg, fg_color="transparent")
        bot.pack(fill="x", padx=20, pady=16)
        ctk.CTkButton(bot, text="Cancel", width=90, fg_color=BORDER,
                      hover_color="#555", command=dlg.destroy).pack(side="right", padx=(8,0))
        ctk.CTkButton(bot, text="Save Client", width=120,
                      fg_color=GREEN, hover_color="#27AE60", text_color="#000",
                      font=("Segoe UI",12,"bold"), command=_save).pack(side="right")

    def _new_client(self):
        self._open_form()

    def _edit_client(self, event):
        sel = self.tree.selection()
        if not sel: return
        client = self.dm.get_client(sel[0])
        if client: self._open_form(client)

    def _delete_client(self):
        sel = self.tree.selection()
        if not sel: return
        vals = self.tree.item(sel[0], "values")
        if messagebox.askyesno("Delete?", f"Delete client '{vals[1]}' (ID {vals[0]})?"):
            self.dm.delete_client(sel[0])
            self._load()


# ══════════════════════════════════════════════════════════════════════════════
class JobLogFrame(ctk.CTkFrame):
    """Track jobs from start to completion with actual cost."""

    STATUS_COLORS = {
        "In Progress": ORANGE,
        "Completed":   GREEN,
    }

    def __init__(self, parent, dm):
        super().__init__(parent, fg_color="transparent")
        self.dm = dm
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        hdr = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=10)
        hdr.grid(row=0, column=0, sticky="ew", pady=(0,8))
        ctk.CTkLabel(hdr, text="Job Log",
                     font=("Segoe UI",16,"bold")).pack(side="left", padx=16, pady=12)
        ctk.CTkButton(hdr, text="+ Start New Job", width=140,
                      fg_color=YELLOW, text_color="#000", hover_color="#D4A000",
                      font=("Segoe UI",12,"bold"),
                      command=self._new_job).pack(side="right", padx=8)
        ctk.CTkButton(hdr, text="↻ Refresh", width=100, fg_color=BORDER,
                      hover_color="#555", command=self._load).pack(side="right")

        tree_card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=10)
        tree_card.grid(row=1, column=0, sticky="nsew")
        self.tree = make_tree(tree_card, "Jobs",
                              ("job_id","est_id","client","start","end","estimate","actual","status"),
                              ("Job ID","Est. ID","Client","Start Date","End Date",
                               "Estimate","Actual Cost","Status"),
                              (100,100,180,100,100,110,110,110),
                              anchors={"job_id":"center","est_id":"center",
                                       "start":"center","end":"center",
                                       "estimate":"e","actual":"e","status":"center"})
        self.tree.bind("<Double-1>", self._edit_job)

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=2, column=0, sticky="ew", pady=(8,0))
        ctk.CTkLabel(actions, text="Double-click a job to update it.",
                     text_color=TEXT_DIM, font=("Segoe UI",11)).pack(side="left")
        ctk.CTkButton(actions, text="✏ Complete Job", width=130,
                      fg_color=GREEN, hover_color="#27AE60", text_color="#000",
                      command=self._complete_selected).pack(side="left", padx=(12,0))
        ctk.CTkButton(actions, text="🗑 Delete", width=100,
                      fg_color=RED_CLR, hover_color="#C0392B",
                      command=self._delete_job).pack(side="right")
        self._load()

    def _load(self):
        self.tree.delete(*self.tree.get_children())
        for j in self.dm.load_jobs():
            actual = f"${float(j.get('actual_cost') or 0):,.2f}" if j.get('actual_cost') else "—"
            end    = j.get("end_date","") or "—"
            self.tree.insert("", "end", iid=j["job_id"], values=(
                j["job_id"],
                j.get("estimate_id",""),
                j.get("client_name",""),
                j.get("start_date",""),
                end,
                f"${float(j.get('estimate_total') or 0):,.2f}",
                actual,
                j.get("status","In Progress"),
            ))

    def _open_form(self, job=None):
        """New job form or edit form."""
        is_new = job is None
        dlg = ctk.CTkToplevel(self)
        dlg.title("Start New Job" if is_new else f"Edit Job {job['job_id']}")
        dlg.geometry("500x560")
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.configure(fg_color=CARD_BG)

        scroll = ctk.CTkScrollableFrame(dlg, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=4, pady=4)

        def lbl(text):
            ctk.CTkLabel(scroll, text=text, font=("Segoe UI",11),
                         text_color=TEXT_DIM).pack(anchor="w", padx=16, pady=(10,0))

        def entry(default=""):
            e = ctk.CTkEntry(scroll, fg_color=DARK_BG, border_color=BORDER)
            if default: e.insert(0, default)
            e.pack(fill="x", padx=16)
            return e

        # Job ID (display only for existing)
        if not is_new:
            lbl("Job ID")
            ctk.CTkLabel(scroll, text=job["job_id"],
                         font=("Segoe UI",12,"bold"), text_color=YELLOW).pack(anchor="w", padx=16)

        lbl("Linked Estimate ID")
        estimates = [e["estimate_id"] for e in self.dm.load_estimates()]
        est_var = tk.StringVar(value=job.get("estimate_id","") if job else "")
        est_combo = ctk.CTkComboBox(scroll, values=["(none)"] + estimates,
                                    variable=est_var,
                                    fg_color=DARK_BG, border_color=BORDER,
                                    command=lambda c: _autofill_from_estimate(c))
        est_combo.set(job.get("estimate_id","(none)") if job else "(none)")
        est_combo.pack(fill="x", padx=16)

        lbl("Client ID")
        client_names = self.dm.get_client_names()
        client_var = tk.StringVar()
        client_combo = ctk.CTkComboBox(scroll, values=["(none)"] + client_names,
                                       variable=client_var,
                                       fg_color=DARK_BG, border_color=BORDER)
        if job:
            client_combo.set(job.get("client_id","(none)"))
        else:
            client_combo.set("(none)")
        client_combo.pack(fill="x", padx=16)

        lbl("Start Date")
        start_e = entry(job.get("start_date", str(date.today())) if job else str(date.today()))

        lbl("End Date (fill when complete)")
        end_e = entry(job.get("end_date","") if job else "")

        lbl("Estimate Total ($)")
        est_total_e = entry(str(job.get("estimate_total","")) if job else "")

        lbl("Actual Cost ($)  — fill at completion")
        actual_e = entry(str(job.get("actual_cost","")) if job else "")

        lbl("Notes")
        notes_box = ctk.CTkTextbox(scroll, height=80, fg_color=DARK_BG, border_color=BORDER)
        if job: notes_box.insert("1.0", job.get("notes",""))
        notes_box.pack(fill="x", padx=16)

        def _autofill_from_estimate(choice):
            if choice == "(none)": return
            est = self.dm.get_estimate(choice)
            if not est: return
            # Fill estimate total
            est_total_e.delete(0,"end")
            est_total_e.insert(0, str(round(est.get("total",0), 2)))
            # Fill client
            cid = est.get("client_id","")
            client = self.dm.get_client(cid)
            if client:
                for val in client_names:
                    if val.startswith(client["id"]):
                        client_combo.set(val)
                        break

        def _save():
            client_choice = client_combo.get()
            client = self.dm.get_client(client_choice) if client_choice != "(none)" else None
            client_name = client["name"] if client else ""
            client_id   = client["id"]   if client else ""

            status = "In Progress"
            if end_e.get().strip() and actual_e.get().strip():
                status = "Completed"
            elif end_e.get().strip():
                status = "Completed"

            j = {
                "job_id":         job["job_id"] if job else self.dm.next_job_id(),
                "estimate_id":    est_combo.get() if est_combo.get() != "(none)" else "",
                "client_id":      client_id,
                "client_name":    client_name,
                "start_date":     start_e.get(),
                "end_date":       end_e.get(),
                "estimate_total": est_total_e.get(),
                "actual_cost":    actual_e.get(),
                "notes":          notes_box.get("1.0","end").strip(),
                "status":         status,
            }
            self.dm.save_job(j)
            self._load()
            dlg.destroy()

        bot = ctk.CTkFrame(dlg, fg_color="transparent")
        bot.pack(fill="x", padx=16, pady=12)
        ctk.CTkButton(bot, text="Cancel", width=90, fg_color=BORDER,
                      hover_color="#555", command=dlg.destroy).pack(side="right", padx=(8,0))
        label = "Save Job" if job else "Start Job"
        ctk.CTkButton(bot, text=label, width=120,
                      fg_color=GREEN, hover_color="#27AE60", text_color="#000",
                      font=("Segoe UI",12,"bold"), command=_save).pack(side="right")

    def _new_job(self):
        self._open_form()

    def _edit_job(self, event):
        sel = self.tree.selection()
        if not sel: return
        job = self.dm.get_job(sel[0])
        if job: self._open_form(job)

    def _complete_selected(self):
        """Quick-complete: opens edit form focused on end date + actual cost."""
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("No selection","Select a job first.")
            return
        job = self.dm.get_job(sel[0])
        if job: self._open_form(job)

    def _delete_job(self):
        sel = self.tree.selection()
        if not sel: return
        if messagebox.askyesno("Delete?", f"Delete job {sel[0]}?"):
            self.dm.delete_job(sel[0])
            self._load()


# ══════════════════════════════════════════════════════════════════════════════
class MaterialsManagerFrame(ctk.CTkFrame):
    def __init__(self, parent, dm):
        super().__init__(parent, fg_color="transparent")
        self.dm = dm
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        hdr = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=10)
        hdr.grid(row=0, column=0, sticky="ew", pady=(0,8))
        ctk.CTkLabel(hdr, text="Materials Price List",
                     font=("Segoe UI",16,"bold")).pack(side="left", padx=16, pady=12)
        ctk.CTkButton(hdr, text="+ Add Item", width=110,
                      fg_color=YELLOW, text_color="#000", hover_color="#D4A000",
                      command=self._add_item).pack(side="right", padx=16)

        tree_card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=10)
        tree_card.grid(row=1, column=0, sticky="nsew")
        self.tree = make_tree(tree_card, "Mat",
                              ("id","name","price"),
                              ("ID","Material","Unit Price"),
                              (80,440,120),
                              anchors={"id":"center","price":"e"})
        self.tree.bind("<Double-1>", self._edit_item)

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=2, column=0, sticky="ew", pady=(8,0))
        ctk.CTkLabel(actions, text="Double-click a row to edit price.",
                     text_color=TEXT_DIM, font=("Segoe UI",11)).pack(side="left")
        ctk.CTkButton(actions, text="🗑 Delete", width=100,
                      fg_color=RED_CLR, hover_color="#C0392B",
                      command=self._delete_item).pack(side="right")
        self._load()

    def _load(self):
        self.tree.delete(*self.tree.get_children())
        for m in self.dm.materials:
            self.tree.insert("", "end", iid=str(m["id"]),
                             values=(m["id"], m["name"], f"${m['price']:.2f}"))

    def _add_item(self):
        dlg = ctk.CTkInputDialog(
            text="Enter: ID, Name, Price\n(comma-separated)\ne.g. 1040, LED fixture, 22.50",
            title="Add Material")
        val = dlg.get_input()
        if val:
            try:
                parts = [p.strip() for p in val.split(",")]
                mid, name, price = int(parts[0]), parts[1], float(parts[2])
                self.dm.add_material({"id": mid, "name": name, "price": price})
                self._load()
            except Exception:
                messagebox.showerror("Error","Format: ID, Name, Price\nExample: 1040, LED, 22.50")

    def _edit_item(self, event):
        sel = self.tree.selection()
        if not sel: return
        vals = self.tree.item(sel[0], "values")
        dlg = ctk.CTkInputDialog(text=f"New price for '{vals[1]}':", title="Edit Price")
        val = dlg.get_input()
        if val:
            try:
                self.dm.update_material_price(int(vals[0]), float(val))
                self._load()
            except Exception:
                messagebox.showerror("Error","Enter a valid number.")

    def _delete_item(self):
        sel = self.tree.selection()
        if not sel: return
        if messagebox.askyesno("Delete?", f"Remove material {sel[0]}?"):
            self.dm.delete_material(int(sel[0]))
            self._load()


# ══════════════════════════════════════════════════════════════════════════════
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Electric Quote Builder")
        self.geometry("1340x840")
        self.minsize(960, 640)
        self.configure(fg_color=DARK_BG)

        data_path = resource_path("data")
        os.makedirs(data_path, exist_ok=True)
        self.dm = DataManager(data_path)

        self._build_sidebar()
        self._build_content()
        self._show("quote")

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=215, fg_color=CARD_BG, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        brand = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand.pack(fill="x", padx=16, pady=(24,8))
        ctk.CTkLabel(brand, text="⚡", font=("Segoe UI",32)).pack()
        ctk.CTkLabel(brand, text="Electric",
                     font=("Segoe UI",14,"bold"), justify="center").pack()
        ctk.CTkLabel(brand, text="Quote Builder",
                     font=("Segoe UI",11), text_color=YELLOW).pack()

        ctk.CTkFrame(self.sidebar, height=1, fg_color=BORDER).pack(fill="x", padx=16, pady=16)

        self.nav_buttons = {}
        nav_items = [
            ("quote",     "📋  New Quote",   self._show_quote),
            ("estimates", "📁  Estimates",   self._show_estimates),
            ("clients",   "👤  Client Log",  self._show_clients),
            ("jobs",      "🔨  Job Log",     self._show_jobs),
            ("materials", "🔧  Materials",   self._show_materials),
        ]
        for key, label, cmd in nav_items:
            btn = ctk.CTkButton(self.sidebar, text=label, anchor="w",
                                fg_color="transparent", hover_color=BORDER,
                                font=("Segoe UI",13), height=40, command=cmd)
            btn.pack(fill="x", padx=8, pady=2)
            self.nav_buttons[key] = btn

        ctk.CTkLabel(self.sidebar, text="v2.0", font=("Segoe UI",10),
                     text_color=TEXT_DIM).pack(side="bottom", pady=12)

    def _build_content(self):
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.pack(side="left", fill="both", expand=True, padx=16, pady=16)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)
        self.current_frame = None

    def _show(self, key):
        if self.current_frame:
            self.current_frame.destroy()
        for k, btn in self.nav_buttons.items():
            btn.configure(fg_color=YELLOW if k==key else "transparent",
                          text_color="#000" if k==key else TEXT_MAIN)
        frames = {
            "quote":     lambda: QuoteBuilderFrame(self.content, self.dm, self._show_estimates),
            "estimates": lambda: EstimatesLogFrame(self.content, self.dm),
            "clients":   lambda: ClientLogFrame(self.content, self.dm),
            "jobs":      lambda: JobLogFrame(self.content, self.dm),
            "materials": lambda: MaterialsManagerFrame(self.content, self.dm),
        }
        frame = frames[key]()
        frame.grid(row=0, column=0, sticky="nsew")
        self.current_frame = frame

    def _show_quote(self):     self._show("quote")
    def _show_estimates(self): self._show("estimates")
    def _show_clients(self):   self._show("clients")
    def _show_jobs(self):      self._show("jobs")
    def _show_materials(self): self._show("materials")


if __name__ == "__main__":
    app = App()
    app.mainloop()
