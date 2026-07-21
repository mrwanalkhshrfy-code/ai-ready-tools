import customtkinter as ctk
from tkinter import ttk, messagebox
import sqlite3
import os
import datetime
from tkcalendar import DateEntry
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import arabic_reshaper
from bidi.algorithm import get_display

# استدعاء الدوال الموحدة من db_config
from db_config import get_db_path, get_connection

# تسجيل خط Arial لدعم اللغة العربية
try:
    pdfmetrics.registerFont(TTFont('Arial', 'C:\\Windows\\Fonts\\arial.ttf'))
except:
    pass

def fix_arabic(text):
    reshaped_text = arabic_reshaper.reshape(text)
    return get_display(reshaped_text)

class ReportsWindow(ctk.CTkToplevel):
    def __init__(self):
        super().__init__()
        self.title("لوحة تقارير المبيعات")
        self.geometry("1100x700")

        self.label = ctk.CTkLabel(self, text="سجل المبيعات والتقارير", font=("Arial", 28, "bold"))
        self.label.pack(pady=10)

        # حاوية الفلترة
        self.filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.filter_frame.pack(fill="x", padx=20, pady=5)

        today = datetime.date.today()

        ctk.CTkLabel(self.filter_frame, text="من:").pack(side="right", padx=5)
        self.entry_from = DateEntry(self.filter_frame, width=12, background='darkblue', 
                                    foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd',
                                    max_date=today)
        # عند تغيير التاريخ في "من"، نحدث الحد الأدنى لـ "إلى"
        self.entry_from.bind("<<DateEntrySelected>>", self.update_min_date)
        self.entry_from.pack(side="right", padx=5)

        ctk.CTkLabel(self.filter_frame, text="إلى:").pack(side="right", padx=5)
        self.entry_to = DateEntry(self.filter_frame, width=12, background='darkblue', 
                                  foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd',
                                  max_date=today)
        self.entry_to.pack(side="right", padx=5)

        ctk.CTkButton(self.filter_frame, text="عرض", width=80, command=self.filter_data).pack(side="right", padx=10)
        ctk.CTkButton(self.filter_frame, text="تحديث الكل", width=80, fg_color="#7f8c8d", command=self.load_data).pack(side="right", padx=5)
        ctk.CTkButton(self.filter_frame, text="تصدير PDF", width=100, fg_color="#2ecc71", command=self.export_to_pdf).pack(side="left", padx=10)

        self.setup_table()
        self.load_data()

    def update_min_date(self, event=None):
        """تحديث الحد الأدنى لتاريخ 'إلى' بناءً على اختيار 'من'"""
        selected_date = self.entry_from.get_date()
        self.entry_to.config(mindate=selected_date)

    def setup_table(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", font=("Arial", 12), rowheight=35)
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"))
        
        columns = ("id", "date", "total", "cashier", "phone")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        
        headers = {"id": "رقم الفاتورة", "date": "التاريخ", "total": "الإجمالي", "cashier": "الكاشير", "phone": "هاتف العميل"}
        for col, text in headers.items():
            self.tree.heading(col, text=text, command=lambda c=col: self.sort_treeview(c, False))
            self.tree.column(col, anchor="center", width=120)

        self.tree.pack(fill="both", expand=True, padx=20, pady=10)

    def sort_treeview(self, col, reverse):
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        try:
            l.sort(key=lambda t: float(t[0]), reverse=reverse)
        except:
            l.sort(key=lambda t: t[0], reverse=reverse)
        for index, (val, k) in enumerate(l):
            self.tree.move(k, '', index)
        self.tree.heading(col, command=lambda: self.sort_treeview(col, not reverse))

    def load_data(self, query=None, params=()):
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not query:
            query = "SELECT id, date_time, total_amount, cashier_name, customer_phone FROM Invoices ORDER BY id DESC"
        
        try:
            # استخدام دالة الاتصال الموحدة
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            for row in rows:
                self.tree.insert("", "end", values=(row[0], row[1], row[2], row[3], row[4]))
        except Exception as e:
            messagebox.showerror("خطأ", f"تعذر تحميل البيانات: {e}")

    def filter_data(self):
        start = self.entry_from.get_date().strftime('%Y-%m-%d')
        end = self.entry_to.get_date().strftime('%Y-%m-%d')
            
        query = "SELECT id, date_time, total_amount, cashier_name, customer_phone FROM Invoices WHERE date(date_time) BETWEEN ? AND ? ORDER BY date_time DESC"
        self.load_data(query, (start, end))

    def export_to_pdf(self):
        file_name = "Sales_Report.pdf"
        doc = SimpleDocTemplate(file_name, pagesize=A4)
        elements = []
        
        styles = getSampleStyleSheet()
        style_title = ParagraphStyle('Title', fontName='Arial', fontSize=18, alignment=1)
        style_normal = ParagraphStyle('Normal', fontName='Arial', fontSize=12)

        elements.append(Paragraph(fix_arabic("تقرير مبيعات سوبر ماركت"), style_title))
        elements.append(Spacer(1, 20))
        
        data = [[fix_arabic("الإجمالي"), fix_arabic("هاتف العميل"), fix_arabic("الكاشير"), fix_arabic("التاريخ"), fix_arabic("رقم الفاتورة")]]
        
        total_revenue = 0
        rows = [self.tree.item(item)['values'] for item in self.tree.get_children()]
        
        for row in rows:
            data.append([str(row[2]), str(row[4]), fix_arabic(str(row[3])), str(row[1]), str(row[0])])
            total_revenue += float(row[2])
            
        table = Table(data, colWidths=[60, 80, 80, 120, 60])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Arial'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 20))
        elements.append(Paragraph(fix_arabic(f"إجمالي المبيعات للفترة المختارة: {total_revenue:.2f} ر.ي"), style_normal))
        
        doc.build(elements)
        messagebox.showinfo("تم", "تم تصدير التقرير!")