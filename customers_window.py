import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import os
import csv
import threading
import datetime
from tkcalendar import DateEntry
import pandas as pd

# مكتبات الـ PDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle

# مكتبات اللغة العربية
import arabic_reshaper
from bidi.algorithm import get_display

# استدعاء دالة الاتصال الموحدة من db_config
from db_config import get_connection, get_db_path

class CustomersWindow(ctk.CTkToplevel):
    def __init__(self):
        super().__init__()
        self.title("إدارة العملاء وحساباتهم")
        self.geometry("1200x750")
        self.grab_set()
        self.focus()
       
        self.selected_customer_id = None
        self.selected_customer_phone = None

        # --- العنوان ---
        ctk.CTkLabel(self, text="إدارة العملاء وكشف الحسابات", font=("Arial", 26, "bold"), text_color="#2c3e50").pack(pady=10)

        # --- الحاوية الرئيسية ---
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=10)

        self.setup_right_panel()
        self.setup_left_panel()
        self.load_customers()

    def setup_right_panel(self):
        """اللوحة اليمنى: إضافة/تعديل/حذف وعرض العملاء"""
        self.right_panel = ctk.CTkFrame(self.main_container, width=400)
        self.right_panel.pack(side="right", fill="y", padx=10)

        ctk.CTkLabel(self.right_panel, text="بيانات العميل", font=("Arial", 18, "bold"), text_color="#3498db").pack(pady=15)
      
        self.entry_name = ctk.CTkEntry(self.right_panel, placeholder_text="اسم العميل", justify="right")
        self.entry_name.pack(pady=5, padx=20, fill="x")

        self.entry_phone = ctk.CTkEntry(self.right_panel, placeholder_text="رقم الهاتف (الأساسي للربط)", justify="right")
        self.entry_phone.pack(pady=5, padx=20, fill="x")

        self.entry_balance = ctk.CTkEntry(self.right_panel, placeholder_text="الرصيد الافتتاحي", justify="right")
        self.entry_balance.pack(pady=5, padx=20, fill="x")
        self.entry_balance.insert(0, "0.0")

        buttons_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        buttons_frame.pack(pady=10, padx=20, fill="x")

        ctk.CTkButton(buttons_frame, text="إضافة عميل ➕", fg_color="#2ecc71", command=self.add_customer).pack(pady=2, fill="x")
        ctk.CTkButton(buttons_frame, text="تعديل ✏️", fg_color="#f39c12", command=self.edit_customer).pack(pady=2, fill="x")
        ctk.CTkButton(buttons_frame, text="حذف ❌", fg_color="#e74c3c", command=self.delete_customer).pack(pady=2, fill="x")
        ctk.CTkButton(buttons_frame, text="تفريغ 🔄", fg_color="#7f8c8d", command=self.clear_fields).pack(pady=2, fill="x")

        # البحث والجدول
        self.entry_search = ctk.CTkEntry(self.right_panel, placeholder_text="بحث بالاسم أو الهاتف...", justify="right")
        self.entry_search.pack(pady=10, padx=20, fill="x")
        self.entry_search.bind("<KeyRelease>", self.search_customers)
        
        self.tree_customers = ttk.Treeview(self.right_panel, columns=("id", "name", "phone", "balance"), show="headings", height=10)
        self.tree_customers.heading("id", text="الرقم")
        self.tree_customers.heading("name", text="الاسم")
        self.tree_customers.heading("phone", text="رقم الهاتف")
        self.tree_customers.heading("balance", text="الرصيد")
        
        self.tree_customers.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree_customers.bind("<ButtonRelease-1>", self.on_customer_select)

    def setup_left_panel(self):
        """اللوحة اليسرى: الحسابات والفواتير"""
        self.left_panel = ctk.CTkFrame(self.main_container)
        self.left_panel.pack(side="left", fill="both", expand=True, padx=10)

        # عرض الرصيد
        info_frame = ctk.CTkFrame(self.left_panel, fg_color="#34495e", corner_radius=10)
        info_frame.pack(pady=10, padx=20, fill="x")
        self.lbl_selected_customer = ctk.CTkLabel(info_frame, text="يرجى اختيار عميل", font=("Arial", 16, "bold"), text_color="white")
        self.lbl_selected_customer.pack(pady=5)
        self.lbl_current_balance = ctk.CTkLabel(info_frame, text="الرصيد: 0.0", font=("Arial", 18, "bold"), text_color="#f1c40f")
        self.lbl_current_balance.pack(pady=5)

        # التسديد
        pay_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        pay_frame.pack(pady=10, padx=20, fill="x")
        self.entry_payment = ctk.CTkEntry(pay_frame, placeholder_text="مبلغ التسديد")
        self.entry_payment.pack(side="right", fill="x", expand=True, padx=10)
        ctk.CTkButton(pay_frame, text="تسديد دفعة 💸", fg_color="#27ae60", command=self.pay_debt).pack(side="left")
        
        self.btn_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        self.btn_frame.pack(pady=5, padx=20, fill="x")
        ctk.CTkButton(self.btn_frame, text="تصدير Excel", command=self.export_excel).pack(side="left", padx=5)
        ctk.CTkButton(self.btn_frame, text="تصدير PDF", command=self.export_to_pdf).pack(side="left", padx=5)
        
        # إطار الفلاتر (التاريخ)
        self.filter_frame = ctk.CTkFrame(self.left_panel)
        self.filter_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(self.filter_frame, text="من:").pack(side="right", padx=5)
        self.date_from = DateEntry(self.filter_frame, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.date_from.pack(side="right", padx=5)

        ctk.CTkLabel(self.filter_frame, text="إلى:").pack(side="right", padx=5)
        self.date_to = DateEntry(self.filter_frame, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.date_to.pack(side="right", padx=5)

        ctk.CTkButton(self.filter_frame, text="فلترة 🔍", command=self.apply_filter).pack(side="left", padx=10)
        
        # إعداد جدول كشف الحساب (الفواتير)
        columns = ("date", "total", "type", "paid", "rem")
        self.tree_invoices = ttk.Treeview(self.left_panel, columns=columns, show="headings")
        
        self.tree_invoices.heading("date", text="التاريخ")
        self.tree_invoices.heading("total", text="الإجمالي")
        self.tree_invoices.heading("type", text="نوع الدفع")
        self.tree_invoices.heading("paid", text="المدفوع")
        self.tree_invoices.heading("rem", text="المتبقي")

        for col in columns:
            self.tree_invoices.column(col, anchor="center", width=100)

        self.tree_invoices.pack(fill="both", expand=True, padx=20, pady=10)

    # --- المنطق (Logic) ---

    def load_customers(self, search=""):
        for i in self.tree_customers.get_children(): 
            self.tree_customers.delete(i)
        conn = get_connection()
        cursor = conn.cursor()
        query = "SELECT id, name, phone, balance FROM Customers WHERE name LIKE ? OR phone LIKE ?"
        cursor.execute(query, (f"%{search}%", f"%{search}%"))
        for row in cursor.fetchall(): 
            self.tree_customers.insert("", "end", values=row)
        conn.close()

    def on_customer_select(self, event):
        """عرض بيانات العميل وفواتيره عند النقر في الجدول"""
        selected_item = self.tree_customers.focus()
        if not selected_item: return
        
        values = self.tree_customers.item(selected_item, 'values')
        if values:
            self.selected_customer_id = values[0]
            
            # تعبئة الحقول في اليمين
            self.entry_name.delete(0, 'end'); self.entry_name.insert(0, values[1])
            self.entry_phone.delete(0, 'end'); self.entry_phone.insert(0, values[2])
            self.entry_balance.delete(0, 'end'); self.entry_balance.insert(0, values[3])
            
            # تحديث تسميات الـ Labels
            self.lbl_selected_customer.configure(text=f"العميل: {values[1]}")
            self.lbl_current_balance.configure(text=f"الرصيد: {values[3]}")
            
            # جلب فواتير العميل
            self.load_customer_invoices(self.selected_customer_id)

    def load_customer_invoices(self, customer_id):
        for item in self.tree_invoices.get_children():
            self.tree_invoices.delete(item)
            
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT date_time, total_amount, payment_type, paid_amount, remaining_amount
                FROM Invoices
                WHERE customer_id = ?
                ORDER BY date_time DESC
            """
            cursor.execute(query, (customer_id,))
            
            for row in cursor.fetchall():
                p_type = row[2] if row[2] else "غير محدد"
                self.tree_invoices.insert("", "end", values=(
                    row[0],                  # التاريخ
                    f"{row[1]:.2f}",         # الإجمالي
                    p_type,                  # نوع الدفع
                    f"{row[3]:.2f}",         # المدفوع
                    f"{row[4]:.2f}"          # المتبقي
                ))
            conn.close()
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ أثناء جلب فواتير العميل: {e}")

    def pay_debt(self):
        if not self.selected_customer_id: return
        try:
            amount = float(self.entry_payment.get())
            conn = get_connection()
            cursor = conn.cursor()
            
            # 1. تحديث رصيد العميل
            cursor.execute("UPDATE Customers SET balance = balance - ? WHERE id = ?", (amount, self.selected_customer_id))
            
            # 2. تسجيل العملية في جدول الحركات المالية
            cursor.execute("INSERT INTO Credit_Transactions (customer_id, amount, type, date_time) VALUES (?, ?, 'payment', ?)", 
                           (self.selected_customer_id, amount, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            
            conn.commit()
            conn.close()
            messagebox.showinfo("نجاح", "تم تسجيل عملية التسديد")
            self.load_customers()
            self.entry_payment.delete(0, 'end')
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ: {e}")

    def add_customer(self):
        """إضافة عميل جديد لقاعدة البيانات"""
        name = self.entry_name.get().strip()
        phone = self.entry_phone.get().strip()
        balance_str = self.entry_balance.get().strip()

        if not name:
            messagebox.showwarning("تنبيه", "اسم العميل مطلوب!")
            return

        try:
            balance = float(balance_str) if balance_str else 0.0
            
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Customers (name, phone, balance) VALUES (?, ?, ?)", (name, phone, balance))
            conn.commit()
            conn.close()
            
            messagebox.showinfo("نجاح", "تمت إضافة العميل بنجاح!")
            self.clear_fields()
            self.load_customers()
        except ValueError:
            messagebox.showerror("خطأ", "قيمة الرصيد يجب أن تكون رقماً!")
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ أثناء الإضافة: {e}")

    def edit_customer(self):
        """تعديل بيانات العميل المحدد"""
        if not self.selected_customer_id:
            messagebox.showwarning("تنبيه", "الرجاء اختيار عميل من الجدول أولاً.")
            return

        name = self.entry_name.get().strip()
        phone = self.entry_phone.get().strip()
        balance_str = self.entry_balance.get().strip()

        if not name:
            messagebox.showwarning("تنبيه", "اسم العميل مطلوب!")
            return

        try:
            balance = float(balance_str) if balance_str else 0.0
            
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE Customers SET name=?, phone=?, balance=? WHERE id=?", 
                           (name, phone, balance, self.selected_customer_id))
            conn.commit()
            conn.close()
            
            messagebox.showinfo("نجاح", "تم تحديث بيانات العميل!")
            self.clear_fields()
            self.load_customers()
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ أثناء التعديل: {e}")

    def delete_customer(self):
        """حذف العميل المحدد"""
        if not self.selected_customer_id:
            messagebox.showwarning("تنبيه", "الرجاء اختيار عميل لحذفه.")
            return
            
        confirm = messagebox.askyesno("تأكيد الحذف", "هل أنت متأكد من حذف هذا العميل؟ \nملاحظة: سيتم حذف بياناته بالكامل.")
        if confirm:
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM Customers WHERE id=?", (self.selected_customer_id,))
                conn.commit()
                conn.close()
                
                messagebox.showinfo("نجاح", "تم حذف العميل.")
                self.clear_fields()
                self.load_customers()
            except Exception as e:
                messagebox.showerror("خطأ", f"حدث خطأ أثناء الحذف: {e}")

    def clear_fields(self):
        """تفريغ الحقول وإعادة تهيئة المتغيرات"""
        self.entry_name.delete(0, 'end')
        self.entry_phone.delete(0, 'end')
        self.entry_balance.delete(0, 'end')
        self.entry_balance.insert(0, "0.0")
        self.selected_customer_id = None
        self.lbl_selected_customer.configure(text="يرجى اختيار عميل")
        self.lbl_current_balance.configure(text="الرصيد: 0.0")

    def search_customers(self, event=None):
        self.load_customers(self.entry_search.get())

    def export_excel(self):
        """تصدير تقرير تفصيلي واحترافي للعميل إلى ملف CSV يفتح عبر Excel"""
        if not self.selected_customer_id:
            messagebox.showwarning("تنبيه", "الرجاء اختيار عميل من القائمة أولاً لطباعة تقريره.")
            return

        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name, phone, balance FROM Customers WHERE id = ?", (self.selected_customer_id,))
            cust_data = cursor.fetchone()
            conn.close()
            
            customer_name = cust_data[0] if cust_data else "غير معروف"
            customer_phone = cust_data[1] if cust_data else "غير مسجل"
            customer_debt = cust_data[2] if cust_data else 0.0

            total_invoices = 0.0
            invoices_data = []
            for item in self.tree_invoices.get_children():
                val = self.tree_invoices.item(item, 'values')
                total_invoices += float(val[1])
                invoices_data.append(val)

            file_name = f"كشف_حساب_العميل_{customer_name}.csv".replace(" ", "_") 
            
            with open(file_name, mode='w', newline='', encoding='utf-8-sig') as file:
                writer = csv.writer(file)
                writer.writerow(["", "", "كشف حساب عميل"])
                writer.writerow(["=" * 50])
                writer.writerow(["اسم العميل:", customer_name])
                writer.writerow(["رقم الهاتف:", customer_phone])
                writer.writerow(["إجمالي المديونية الحالية (الرصيد الكلي):", f"{customer_debt:.2f}"])
                writer.writerow(["إجمالي قيمة الفواتير (المعروضة أدناه):", f"{total_invoices:.2f}"])
                writer.writerow(["=" * 50])
                writer.writerow([]) 
                
                writer.writerow(["سجل الفواتير"])
                writer.writerow(["المتبقي", "المدفوع", "نوع الدفع", "الإجمالي", "التاريخ"])
                
                for row in invoices_data:
                    writer.writerow([row[4], row[3], row[2], row[1], row[0]])
            
            messagebox.showinfo("نجاح", f"تم إنشاء التقرير بنجاح!\nسيتم فتحه الآن.")
            os.startfile(file_name) 
            
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل تصدير التقرير: {e}")

    def fix_arabic(self, text):
        """تعديل النصوص العربية لتظهر بشكل صحيح في الـ PDF"""
        if not text: return ""
        reshaped_text = arabic_reshaper.reshape(str(text))
        return get_display(reshaped_text)

    def export_to_pdf(self):
        """تشغيل عملية التصدير في خلفية البرنامج"""
        if not self.selected_customer_id:
            messagebox.showwarning("تنبيه", "الرجاء اختيار عميل أولاً.")
            return
        threading.Thread(target=self._run_pdf_export_process, daemon=True).start()

    def _run_pdf_export_process(self):
        try:
            file_name = f"كشف_حساب_العميل_{self.selected_customer_id}.pdf"
            doc = SimpleDocTemplate(file_name, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
            
            font_path = "arial.ttf" 
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('Arabic', font_path))
            else:
                self.after(0, lambda: messagebox.showerror("خطأ", "ملف الخط arial.ttf غير موجود!"))
                return
            
            elements = []
            
            # عنوان التقرير
            title = Paragraph(self.fix_arabic("تقرير كشف حساب العميل"), ParagraphStyle('Title', fontName='Arabic', fontSize=20, alignment=1))
            elements.append(title)
            elements.append(Spacer(1, 20))

            # حساب الإجماليات
            total_invoices = 0.0
            for item in self.tree_invoices.get_children():
                val = self.tree_invoices.item(item, 'values')
                try: total_invoices += float(val[1])
                except: pass

            customer_name = self.lbl_selected_customer.cget("text").replace("العميل: ", "").replace("يرجى اختيار عميل", "")
            current_balance = self.lbl_current_balance.cget("text").replace("الرصيد: ", "")
            
            # ديباجة التقرير
            summary_data = [
                [self.fix_arabic("اسم العميل"), self.fix_arabic(customer_name)],
                [self.fix_arabic("إجمالي المديونية (الرصيد)"), self.fix_arabic(current_balance)],
                [self.fix_arabic("إجمالي قيمة الفواتير المعروضة"), f"{total_invoices:.2f}"]
            ]
            
            summary_table = Table(summary_data, colWidths=[180, 200])
            summary_table.setStyle(TableStyle([
                ('FONTNAME', (0,0), (-1,-1), 'Arabic'),
                ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
                ('GRID', (0,0), (-1,-1), 1, colors.black),
                ('BACKGROUND', (0,0), (0,-1), colors.lightgrey)
            ]))
            elements.append(summary_table)
            elements.append(Spacer(1, 30))
            
            # عناوين جدول الفواتير
            table_data = [[
                self.fix_arabic("المتبقي"), 
                self.fix_arabic("المدفوع"), 
                self.fix_arabic("نوع الدفع"), 
                self.fix_arabic("الإجمالي"), 
                self.fix_arabic("التاريخ")
            ]]
            
            # تعبئة الجدول
            for item in self.tree_invoices.get_children():
                row = self.tree_invoices.item(item, 'values')
                table_data.append([
                    str(row[4]), 
                    str(row[3]), 
                    self.fix_arabic(str(row[2])), 
                    str(row[1]), 
                    str(row[0])
                ])
            
            # رسم الجدول وتنسيقه
            table = Table(table_data, colWidths=[80, 80, 90, 90, 140])
            
            table_style = TableStyle([
                ('FONTNAME', (0,0), (-1,-1), 'Arabic'),
                ('BACKGROUND', (0,0), (-1,0), colors.darkblue),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ])
            
            for i in range(1, len(table_data)):
                if i % 2 == 0:
                    table_style.add('BACKGROUND', (0, i), (-1, i), colors.lavender)
            
            table.setStyle(table_style)
            elements.append(table)
            
            doc.build(elements)
            self.after(0, lambda: messagebox.showinfo("نجاح", "تم إنشاء التقرير الاحترافي (PDF) بنجاح!"))
            self.after(0, lambda: os.startfile(file_name))
            
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("خطأ", f"فشل إنشاء التقرير: {str(e)}"))
    
    def apply_filter(self):
        """تطبيق الفلترة بين تاريخين وجلب البيانات مجدداً من القاعدة"""
        if not self.selected_customer_id:
            messagebox.showwarning("تنبيه", "الرجاء اختيار عميل أولاً لتطبيق الفلتر.")
            return
            
        date_f = self.date_from.get_date().strftime('%Y-%m-%d')
        date_t = self.date_to.get_date().strftime('%Y-%m-%d')
        
        for item in self.tree_invoices.get_children():
            self.tree_invoices.delete(item)
            
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT date_time, total_amount, payment_type, paid_amount, remaining_amount
                FROM Invoices
                WHERE customer_id = ? AND date(date_time) BETWEEN ? AND ?
                ORDER BY date_time DESC
            """
            cursor.execute(query, (self.selected_customer_id, date_f, date_t))
            
            for row in cursor.fetchall():
                p_type = row[2] if row[2] else "غير محدد"
                self.tree_invoices.insert("", "end", values=(
                    row[0],                  # التاريخ
                    f"{row[1]:.2f}",         # الإجمالي
                    p_type,                  # نوع الدفع
                    f"{row[3]:.2f}",         # المدفوع
                    f"{row[4]:.2f}"          # المتبقي
                ))
            conn.close()
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل تطبيق الفلتر: {e}")