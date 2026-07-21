import customtkinter as ctk
from tkinter import ttk, messagebox
import sqlite3
import os
import csv
import threading 
import datetime
from tkcalendar import DateEntry

# مكتبات الـ PDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# مكتبات اللغة العربية للـ PDF
import arabic_reshaper
from bidi.algorithm import get_display

import db_config
from db_config import get_db_path, get_connection

class SuppliersWindow(ctk.CTkToplevel):
    def __init__(self):
        super().__init__()
          
        self.title("إدارة الموردين وحساباتهم")
        self.geometry("1200x750")
        self.grab_set()
        self.focus()
       
        self.selected_supplier_id = None

        # --- العنوان ---
        self.lbl_title = ctk.CTkLabel(self, text="إدارة الموردين وكشف الحسابات", font=("Arial", 26, "bold"), text_color="#2c3e50")
        self.lbl_title.pack(pady=10)

        # --- الحاوية الرئيسية ---
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=10)

        # تجهيز الواجهات (اليمين واليسار)
        self.setup_right_panel()
        self.setup_left_panel()
       
        # تحميل البيانات الأولية عند فتح النافذة
        self.load_suppliers()
       
    def setup_right_panel(self):
        """اللوحة اليمنى: إضافة وتعديل وعرض الموردين"""
        self.right_panel = ctk.CTkFrame(self.main_container, width=400)
        self.right_panel.pack(side="right", fill="y", padx=10)

        ctk.CTkLabel(self.right_panel, text="بيانات المورد", font=("Arial", 18, "bold"), text_color="#3498db").pack(pady=15)
      
        # الحقول
        self.entry_name = ctk.CTkEntry(self.right_panel, placeholder_text="اسم المورد", justify="right", font=("Arial", 14))
        self.entry_name.pack(pady=10, padx=20, fill="x")

        self.entry_phone = ctk.CTkEntry(self.right_panel, placeholder_text="رقم الهاتف", justify="right", font=("Arial", 14))
        self.entry_phone.pack(pady=10, padx=20, fill="x")

        self.entry_balance = ctk.CTkEntry(self.right_panel, placeholder_text="الرصيد الافتتاحي (ديون سابقة)", justify="right", font=("Arial", 14))
        self.entry_balance.pack(pady=10, padx=20, fill="x")
        self.entry_balance.insert(0, "0.0") # قيمة افتراضية

        # أزرار التحكم
        buttons_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        buttons_frame.pack(pady=15, padx=20, fill="x")

        self.btn_add = ctk.CTkButton(buttons_frame, text="إضافة مورد ➕", fg_color="#2ecc71", hover_color="#27ae60", command=self.add_supplier)
        self.btn_add.pack(pady=5, fill="x")

        self.btn_edit = ctk.CTkButton(buttons_frame, text="تعديل البيانات ✏️", fg_color="#f39c12", hover_color="#d35400", command=self.edit_supplier)
        self.btn_edit.pack(pady=5, fill="x")

        self.btn_delete = ctk.CTkButton(buttons_frame, text="حذف المورد ❌", fg_color="#e74c3c", hover_color="#c0392b", command=self.delete_supplier)
        self.btn_delete.pack(pady=5, fill="x")

        self.btn_clear = ctk.CTkButton(buttons_frame, text="تفريغ الحقول 🔄", fg_color="#7f8c8d", hover_color="#95a5a6", command=self.clear_fields)
        self.btn_clear.pack(pady=5, fill="x")

        # جدول الموردين
        ctk.CTkLabel(self.right_panel, text="قائمة الموردين (اضغط لاختيار مورد)", font=("Arial", 14, "bold")).pack(pady=(10, 0))
        
        # --- شريط البحث ---
        self.entry_search = ctk.CTkEntry(self.right_panel, placeholder_text="بحث بالاسم، الرقم، أو الهاتف...", justify="right", font=("Arial", 14))
        self.entry_search.pack(pady=(5, 10), padx=20, fill="x")
        self.entry_search.bind("<KeyRelease>", self.search_suppliers)
        
        self.tree_suppliers = ttk.Treeview(self.right_panel, columns=("id", "name", "phone", "balance"), show="headings", height=10)
        self.tree_suppliers.heading("id", text="الرقم")
        self.tree_suppliers.heading("name", text="الاسم")
        self.tree_suppliers.heading("phone", text="الهاتف")
        self.tree_suppliers.heading("balance", text="الرصيد")

        self.tree_suppliers.column("id", width=40, anchor="center")
        self.tree_suppliers.column("name", width=120, anchor="center")
        self.tree_suppliers.column("phone", width=100, anchor="center")
        self.tree_suppliers.column("balance", width=80, anchor="center")

        self.tree_suppliers.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree_suppliers.bind("<ButtonRelease-1>", self.on_supplier_select)


    def setup_left_panel(self):
        """اللوحة اليسرى: كشف الحساب وتسديد الديون والفلاتر والجدول"""
        self.left_panel = ctk.CTkFrame(self.main_container)
        self.left_panel.pack(side="left", fill="both", expand=True, padx=10)

        # 1. معلومات المورد المحدد
        info_frame = ctk.CTkFrame(self.left_panel, fg_color="#34495e", corner_radius=10)
        info_frame.pack(pady=15, padx=20, fill="x")

        self.lbl_selected_supplier = ctk.CTkLabel(info_frame, text="يرجى اختيار مورد من القائمة", font=("Arial", 18, "bold"), text_color="white")
        self.lbl_selected_supplier.pack(pady=10)

        self.lbl_current_balance = ctk.CTkLabel(info_frame, text="إجمالي الديون: 0.0", font=("Arial", 20, "bold"), text_color="#f1c40f")
        self.lbl_current_balance.pack(pady=(0, 10))

        # 2. قسم التسديد
        payment_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        payment_frame.pack(pady=10, padx=20, fill="x")

        self.entry_payment = ctk.CTkEntry(payment_frame, placeholder_text="المبلغ المراد تسديده", justify="center", font=("Arial", 16))
        self.entry_payment.pack(side="right", fill="x", expand=True, padx=10)

        self.btn_pay = ctk.CTkButton(payment_frame, text="تسديد دفعة 💸", fg_color="#27ae60", hover_color="#2ecc71", font=("Arial", 16, "bold"), command=self.pay_debt)
        self.btn_pay.pack(side="left", padx=10)

        # 3. قسم الأزرار (Excel و PDF)
        btn_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        btn_frame.pack(pady=5, padx=20, fill="x")

        self.btn_export_csv = ctk.CTkButton(btn_frame, text="تصدير Excel 📊", fg_color="#27ae60", command=self.print_supplier_report)
        self.btn_export_csv.pack(side="right", padx=5, expand=True, fill="x")

        self.btn_export_pdf = ctk.CTkButton(btn_frame, text="طباعة PDF 🖨️", fg_color="#c0392b", command=self.export_to_pdf)
        self.btn_export_pdf.pack(side="left", padx=5, expand=True, fill="x")

        # 4. إطار الفلاتر (التاريخ)
        self.filter_frame = ctk.CTkFrame(self.left_panel)
        self.filter_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(self.filter_frame, text="من:").pack(side="right", padx=5)
        self.date_from = DateEntry(self.filter_frame, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.date_from.pack(side="right", padx=5)

        ctk.CTkLabel(self.filter_frame, text="إلى:").pack(side="right", padx=5)
        self.date_to = DateEntry(self.filter_frame, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd', mindate=datetime.date.today())
        self.date_to.pack(side="right", padx=5)

        ctk.CTkButton(self.filter_frame, text="فلترة 🔍", command=self.apply_filter).pack(side="left", padx=10)

        # 5. جدول كشف الحساب (الفواتير)
        ctk.CTkLabel(self.left_panel, text="سجل فواتير المشتريات للمورد", font=("Arial", 16, "bold"), text_color="#3498db").pack(pady=(10, 5))

        columns = ("inv_id", "date", "amount", "type")
        self.tree_invoices = ttk.Treeview(self.left_panel, columns=columns, show="headings")
        
        self.tree_invoices.heading("inv_id", text="رقم الفاتورة", command=lambda c="inv_id": self.sort_column(c, False))
        self.tree_invoices.heading("date", text="التاريخ", command=lambda c="date": self.sort_column(c, False))
        self.tree_invoices.heading("amount", text="الإجمالي", command=lambda c="amount": self.sort_column(c, False))
        self.tree_invoices.heading("type", text="نوع الدفع", command=lambda c="type": self.sort_column(c, False))

        for col in columns:
            self.tree_invoices.column(col, anchor="center", width=100)

        self.tree_invoices.pack(fill="both", expand=True, padx=20, pady=10)


    # ================== دوال قواعد البيانات والمنطق ================== #

    def search_suppliers(self, event=None):
        search_term = self.entry_search.get().strip()
        self.load_suppliers(search_term)

    def load_suppliers(self, search_term=""):
        for item in self.tree_suppliers.get_children():
            self.tree_suppliers.delete(item)
        
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            if search_term:
                query = """
                    SELECT id, name, phone, balance 
                    FROM Suppliers 
                    WHERE id LIKE ? OR name LIKE ? OR phone LIKE ?
                    ORDER BY id DESC
                """
                cursor.execute(query, (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
            else:
                cursor.execute("SELECT id, name, phone, balance FROM Suppliers ORDER BY id DESC")
                
            for row in cursor.fetchall():
                self.tree_suppliers.insert("", "end", values=row)
            conn.close()
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل تحميل الموردين: {e}")

    def on_supplier_select(self, event):
        selected_item = self.tree_suppliers.focus()
        if not selected_item:
            return

        values = self.tree_suppliers.item(selected_item, 'values')
        if values:
            self.entry_name.delete(0, 'end')
            self.entry_phone.delete(0, 'end')
            self.entry_balance.delete(0, 'end')
            
            self.selected_supplier_id = values[0]
            
            self.entry_name.insert(0, values[1])
            self.entry_phone.insert(0, values[2] if values[2] != 'None' else "")
            self.entry_balance.insert(0, values[3])

            self.lbl_selected_supplier.configure(text=f"المورد: {values[1]}")
            self.lbl_current_balance.configure(text=f"إجمالي الديون: {values[3]}")
            
            self.load_supplier_invoices(self.selected_supplier_id)

    def load_supplier_invoices(self, supplier_id):
        for item in self.tree_invoices.get_children():
            self.tree_invoices.delete(item)
            
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, date_time, total_amount, payment_type 
                FROM Purchase_Invoices 
                WHERE supplier_id = ? 
                ORDER BY date_time DESC
            """, (supplier_id,))
            
            for row in cursor.fetchall():
                p_type = row[3] if row[3] else "غير محدد"
                self.tree_invoices.insert("", "end", values=(row[0], row[1], f"{row[2]:.2f}", p_type))
            conn.close()
        except Exception as e:
            pass

    def add_supplier(self):
        name = self.entry_name.get().strip()
        phone = self.entry_phone.get().strip()
        balance_str = self.entry_balance.get().strip()

        if not name:
            messagebox.showwarning("تنبيه", "اسم المورد مطلوب!")
            return

        try:
            balance = float(balance_str) if balance_str else 0.0
            
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Suppliers (name, phone, balance) VALUES (?, ?, ?)", (name, phone, balance))
            conn.commit()
            conn.close()
            
            messagebox.showinfo("نجاح", "تمت إضافة المورد بنجاح!")
            self.clear_fields()
            self.load_suppliers()
        except ValueError:
            messagebox.showerror("خطأ", "قيمة الرصيد يجب أن تكون رقماً!")
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ: {e}")

    def edit_supplier(self):
        if not self.selected_supplier_id:
            messagebox.showwarning("تنبيه", "الرجاء اختيار مورد من الجدول لتعديله.")
            return

        name = self.entry_name.get().strip()
        phone = self.entry_phone.get().strip()
        balance_str = self.entry_balance.get().strip()

        if not name:
            messagebox.showwarning("تنبيه", "اسم المورد مطلوب!")
            return

        try:
            balance = float(balance_str) if balance_str else 0.0
            
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE Suppliers SET name=?, phone=?, balance=? WHERE id=?", (name, phone, balance, self.selected_supplier_id))
            conn.commit()
            conn.close()
            
            messagebox.showinfo("نجاح", "تم التعديل بنجاح!")
            self.clear_fields()
            self.load_suppliers()
            
            self.lbl_selected_supplier.configure(text="يرجى اختيار مورد من القائمة")
            self.lbl_current_balance.configure(text="إجمالي الديون: 0.0")
            for item in self.tree_invoices.get_children(): self.tree_invoices.delete(item)
            
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ أثناء التعديل: {e}")

    def delete_supplier(self):
        if not self.selected_supplier_id:
            messagebox.showwarning("تنبيه", "الرجاء اختيار مورد من الجدول لحذفه.")
            return
            
        confirm = messagebox.askyesno("تأكيد", "هل أنت متأكد من حذف هذا المورد؟\nتنبيه: ستبقى فواتيره مسجلة برقم تعريفه.")
        if confirm:
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM Suppliers WHERE id=?", (self.selected_supplier_id,))
                conn.commit()
                conn.close()
                
                messagebox.showinfo("نجاح", "تم حذف المورد بنجاح.")
                self.clear_fields()
                self.load_suppliers()
                
                self.lbl_selected_supplier.configure(text="يرجى اختيار مورد من القائمة")
                self.lbl_current_balance.configure(text="إجمالي الديون: 0.0")
                for item in self.tree_invoices.get_children(): self.tree_invoices.delete(item)
                self.selected_supplier_id = None
                
            except Exception as e:
                messagebox.showerror("خطأ", f"حدث خطأ أثناء الحذف: {e}")

    def pay_debt(self):
        if not self.selected_supplier_id:
            messagebox.showwarning("تنبيه", "الرجاء اختيار مورد أولاً لتسديد الدفعة.")
            return

        payment_str = self.entry_payment.get().strip()
        if not payment_str:
            messagebox.showwarning("تنبيه", "الرجاء إدخال المبلغ المراد تسديده.")
            return

        try:
            payment_amount = float(payment_str)
            if payment_amount <= 0:
                messagebox.showerror("خطأ", "يجب أن يكون مبلغ السداد أكبر من صفر.")
                return

            confirm = messagebox.askyesno("تأكيد السداد", f"هل أنت متأكد من تسديد مبلغ {payment_amount} للمورد؟")
            if not confirm:
                return

            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("UPDATE Suppliers SET balance = balance - ? WHERE id = ?", (payment_amount, self.selected_supplier_id))
            conn.commit()
            
            cursor.execute("SELECT balance FROM Suppliers WHERE id = ?", (self.selected_supplier_id,))
            new_balance = cursor.fetchone()[0]
            conn.close()

            messagebox.showinfo("نجاح", f"تم تسديد الدفعة بنجاح!\nالرصيد المتبقي: {new_balance:.2f}")
            
            self.entry_payment.delete(0, 'end')
            self.lbl_current_balance.configure(text=f"إجمالي الديون: {new_balance:.2f}")
            self.load_suppliers() 
            
        except ValueError:
            messagebox.showerror("خطأ", "الرجاء إدخال رقم صحيح للمبلغ.")
        except Exception as e:
            messagebox.showerror("خطأ", f"فشلت عملية السداد: {e}")

    def clear_fields(self):
        self.entry_name.delete(0, 'end')
        self.entry_phone.delete(0, 'end')
        self.entry_balance.delete(0, 'end')
        self.entry_balance.insert(0, "0.0")
        self.selected_supplier_id = None

    def apply_filter(self):
        """تطبيق الفلترة بين تاريخين وجلب البيانات مجدداً من القاعدة"""
        if not self.selected_supplier_id:
            messagebox.showwarning("تنبيه", "الرجاء اختيار مورد أولاً لتطبيق الفلتر.")
            return
            
        date_f = self.date_from.get_date().strftime('%Y-%m-%d')
        date_t = self.date_to.get_date().strftime('%Y-%m-%d')
        
        for item in self.tree_invoices.get_children():
            self.tree_invoices.delete(item)
            
        try:
            conn = get_connection()
            cursor = conn.cursor()
            query = """
                SELECT id, date_time, total_amount, payment_type 
                FROM Purchase_Invoices 
                WHERE supplier_id = ? AND date(date_time) BETWEEN ? AND ?
                ORDER BY date_time DESC
            """
            cursor.execute(query, (self.selected_supplier_id, date_f, date_t))
            
            for row in cursor.fetchall():
                p_type = row[3] if row[3] else "غير محدد"
                self.tree_invoices.insert('', 'end', values=(row[0], row[1], f"{row[2]:.2f}", p_type))
            conn.close()
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل تطبيق الفلتر: {e}")

    def sort_column(self, col, reverse):
        """دالة للترتيب التصاعدي والتنازلي عند النقر على رأس العمود"""
        l = [(self.tree_invoices.set(k, col), k) for k in self.tree_invoices.get_children('')]
        
        try:
            l.sort(key=lambda t: float(t[0]), reverse=reverse)
        except ValueError:
            l.sort(reverse=reverse)
            
        for index, (val, k) in enumerate(l):
            self.tree_invoices.move(k, '', index)
            
        self.tree_invoices.heading(col, command=lambda _c=col: self.sort_column(_c, not reverse))

    # ================== دوال الطباعة والتصدير ================== #

    def print_supplier_report(self):
        if not self.selected_supplier_id:
            messagebox.showwarning("تنبيه", "الرجاء اختيار مورد من القائمة أولاً لطباعة تقريره.")
            return

        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name, balance FROM Suppliers WHERE id = ?", (self.selected_supplier_id,))
            sup_data = cursor.fetchone()
            conn.close()
            
            supplier_name = sup_data[0] if sup_data else "غير معروف"
            supplier_debt = sup_data[1] if sup_data else 0.0

            total_purchases = 0.0
            invoices_data = []
            for item in self.tree_invoices.get_children():
                val = self.tree_invoices.item(item, 'values')
                total_purchases += float(val[2])
                invoices_data.append(val)

            file_name = f"كشف_حساب_{supplier_name}.csv".replace(" ", "_") 
            
            with open(file_name, mode='w', newline='', encoding='utf-8-sig') as file:
                writer = csv.writer(file)
                writer.writerow(["", "", "كشف حساب مورد"])
                writer.writerow(["=" * 40])
                writer.writerow(["اسم المورد:", supplier_name])
                writer.writerow(["إجمالي الديون الحالية:", f"{supplier_debt:.2f}"])
                writer.writerow(["إجمالي قيمة المشتريات (للفواتير المعروضة):", f"{total_purchases:.2f}"])
                writer.writerow(["=" * 40])
                writer.writerow([]) 
                
                writer.writerow(["سجل الفواتير للمورد"])
                writer.writerow(["نوع الدفع", "الإجمالي", "التاريخ", "رقم الفاتورة"])
                
                for row in invoices_data:
                    writer.writerow([row[3], row[2], row[1], row[0]])
            
            messagebox.showinfo("نجاح", f"تم إنشاء التقرير بنجاح!\nسيتم فتحه الآن.")
            os.startfile(file_name) 
            
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل توليد التقرير: {e}")

    def fix_arabic(self, text):
        if not text: return ""
        reshaped_text = arabic_reshaper.reshape(str(text))
        return get_display(reshaped_text)
    
    def export_to_pdf(self):
        if not self.selected_supplier_id:
            messagebox.showwarning("تنبيه", "الرجاء اختيار مورد أولاً.")
            return
        threading.Thread(target=self._run_pdf_export_process, daemon=True).start()

    def _run_pdf_export_process(self):
        try:
            file_name = f"كشف_حساب_{self.selected_supplier_id}.pdf"
            doc = SimpleDocTemplate(file_name, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
            
            font_path = "arial.ttf" 
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('Arabic', font_path))
            else:
                self.after(0, lambda: messagebox.showerror("خطأ", "ملف الخط arial.ttf غير موجود!"))
                return
            
            elements = []
            
            title = Paragraph(self.fix_arabic("تقرير كشف حساب المورد"), ParagraphStyle('Title', fontName='Arabic', fontSize=20, alignment=1))
            elements.append(title)
            elements.append(Spacer(1, 20))

            total_purchases = 0.0
            for item in self.tree_invoices.get_children():
                val = self.tree_invoices.item(item, 'values')
                try: total_purchases += float(val[2])
                except: pass

            supplier_name = self.lbl_selected_supplier.cget("text").replace("المورد: ", "").replace("يرجى اختيار مورد من القائمة", "")
            
            summary_data = [
                [self.fix_arabic("اسم المورد"), self.fix_arabic(supplier_name)],
                [self.fix_arabic("إجمالي الديون الحالية"), self.fix_arabic(self.lbl_current_balance.cget("text").replace("إجمالي الديون: ", ""))],
                [self.fix_arabic("إجمالي المشتريات"), f"{total_purchases:.2f}"]
            ]
            
            summary_table = Table(summary_data, colWidths=[150, 200])
            summary_table.setStyle(TableStyle([
                ('FONTNAME', (0,0), (-1,-1), 'Arabic'),
                ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
                ('GRID', (0,0), (-1,-1), 1, colors.black),
            ]))
            elements.append(summary_table)
            elements.append(Spacer(1, 30))
            
            table_data = [[self.fix_arabic("نوع الدفع"), self.fix_arabic("الإجمالي"), self.fix_arabic("التاريخ"), self.fix_arabic("رقم الفاتورة")]]
            
            for item in self.tree_invoices.get_children():
                row = self.tree_invoices.item(item, 'values')
                table_data.append([self.fix_arabic(str(row[3])), str(row[2]), str(row[1]), str(row[0])])
            
            table = Table(table_data, colWidths=[100, 100, 120, 80])
            
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
            self.after(0, lambda: messagebox.showinfo("نجاح", "تم إنشاء التقرير الاحترافي بنجاح!"))
            self.after(0, lambda: os.startfile(file_name))
            
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("خطأ", f"فشل إنشاء التقرير: {str(e)}"))