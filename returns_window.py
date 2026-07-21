import customtkinter as ctk
from tkinter import messagebox
import sqlite3
import datetime
import os

# استدعاء دالة الاتصال الموحدة ودالة المسار من db_config
from db_config import get_db_path, get_connection

class ReturnsWindow(ctk.CTkToplevel):
    def __init__(self):
        super().__init__()
        self.title("إدارة المرتجعات")
        self.geometry("500x400")
        self.grab_set() # التركيز على هذه النافذة
        self.attributes("-topmost", True)
        self.after(200, lambda: self.attributes("-topmost", False))

        # --- واجهة المستخدم ---
        ctk.CTkLabel(self, text="إرجاع صنف إلى المخزون", font=("Arial", 20, "bold"), text_color="#e74c3c").pack(pady=20)

        ctk.CTkLabel(self, text="باركود الصنف:", font=("Arial", 14)).pack(anchor="e", padx=30)
        self.barcode_entry = ctk.CTkEntry(self, placeholder_text="امسح الباركود هنا...", font=("Arial", 14))
        self.barcode_entry.pack(pady=5, padx=30, fill="x")

        ctk.CTkLabel(self, text="الكمية المرتجعة:", font=("Arial", 14)).pack(anchor="e", padx=30, pady=(10,0))
        self.qty_entry = ctk.CTkEntry(self, placeholder_text="1", font=("Arial", 14))
        self.qty_entry.pack(pady=5, padx=30, fill="x")
        self.qty_entry.insert(0, "1")

        # زر التنفيذ
        ctk.CTkButton(self, text="تنفيذ الإرجاع ورد المبلغ 🔄", font=("Arial", 16, "bold"), 
                      fg_color="#e74c3c", hover_color="#c0392b", height=50, 
                      command=self.process_return).pack(pady=30, padx=30, fill="x")

    def process_return(self):
        barcode = self.barcode_entry.get().strip()
        try:
            qty = int(self.qty_entry.get().strip())
            if qty <= 0: raise ValueError
        except:
            messagebox.showerror("خطأ", "الرجاء إدخال كمية صحيحة (رقم أكبر من الصفر)!")
            return

        if not barcode:
            messagebox.showwarning("تنبيه", "الرجاء إدخال باركود الصنف!")
            return

        try:
            # الاتصال بقاعدة البيانات عبر الدالة الموحدة
            conn = get_connection()
            cursor = conn.cursor()

            # 1. جلب بيانات الصنف للتحقق من وجوده ومعرفة سعره
            cursor.execute("SELECT name, sell_price FROM Products WHERE barcode = ?", (barcode,))
            product = cursor.fetchone()
            
            if not product:
                messagebox.showerror("خطأ", "هذا الصنف غير مسجل في قاعدة البيانات!")
                conn.close()
                return

            name, price = product
            refund_amount = price * qty # حساب المبلغ الذي سيتم رده للعميل

            # 2. إنشاء جدول المرتجعات إذا لم يكن موجوداً
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Sales_Returns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    barcode TEXT,
                    quantity INTEGER,
                    refund_amount REAL,
                    date_time TEXT
                )
            """)

            # 3. تحديث المخزون (إضافة الكمية المرتجعة للمخزن)
            cursor.execute("UPDATE Products SET stock_quantity = stock_quantity + ? WHERE barcode = ?", (qty, barcode))
            
            # 4. تسجيل عملية المرتجع في سجل المرتجعات
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("INSERT INTO Sales_Returns (barcode, quantity, refund_amount, date_time) VALUES (?, ?, ?, ?)", 
                           (barcode, qty, refund_amount, current_time))

            conn.commit()
            conn.close()

            messagebox.showinfo("نجاح العملية", f"تم إرجاع عدد ({qty}) من الصنف:\n'{name}'\n\nالمبلغ المسترد للعميل: {refund_amount:.2f} ر.ي")
            
            # تفريغ الحقول بعد النجاح
            self.barcode_entry.delete(0, 'end')
            self.qty_entry.delete(0, 'end')
            self.qty_entry.insert(0, "1")
            self.barcode_entry.focus()

        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ أثناء محاولة الإرجاع: {e}")