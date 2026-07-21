import customtkinter as ctk
from tkinter import messagebox, ttk
import sqlite3
import os

# استدعاء دالة الاتصال الموحدة من db_config
from db_config import get_db_path, get_connection

class CustomersWindow(ctk.CTkToplevel):
    def __init__(self):
        super().__init__()
        self.title("إدارة العملاء والديون")
        self.geometry("600x500")
        self.grab_set()

        # قسم الإضافة
        self.frame_add = ctk.CTkFrame(self)
        self.frame_add.pack(pady=10, padx=10, fill="x")
        
        self.entry_name = ctk.CTkEntry(self.frame_add, placeholder_text="اسم العميل")
        self.entry_name.pack(side="left", padx=5, expand=True, fill="x")
        
        self.entry_phone = ctk.CTkEntry(self.frame_add, placeholder_text="رقم الهاتف")
        self.entry_phone.pack(side="left", padx=5, expand=True, fill="x")
        
        ctk.CTkButton(self.frame_add, text="إضافة", command=self.add_customer).pack(side="left", padx=5)

        # جدول عرض العملاء
        self.tree = ttk.Treeview(self, columns=("ID", "Name", "Phone", "Balance"), show="headings")
        self.tree.heading("ID", text="م")
        self.tree.heading("Name", text="الاسم")
        self.tree.heading("Phone", text="الهاتف")
        self.tree.heading("Balance", text="الرصيد")
        self.tree.column("ID", width=50)
        self.tree.pack(pady=10, padx=10, fill="both", expand=True)
        
        self.load_customers()

    def add_customer(self):
        name = self.entry_name.get()
        phone = self.entry_phone.get()
        if not name:
            messagebox.showwarning("خطأ", "يجب كتابة اسم العميل")
            return
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Customers (name, phone) VALUES (?, ?)", (name, phone))
        conn.commit()
        conn.close()
        self.entry_name.delete(0, 'end')
        self.entry_phone.delete(0, 'end')
        self.load_customers()

    def load_customers(self):
        for i in self.tree.get_children(): 
            self.tree.delete(i)
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Customers")
        for row in cursor.fetchall():
            self.tree.insert("", "end", values=row)
        conn.close()