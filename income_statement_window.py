import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
from tkcalendar import DateEntry
import sqlite3
import datetime
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import xlsxwriter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import os
import sys
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Spacer
import arabic_reshaper
from bidi.algorithm import get_display
import db_config
# إعداد خطوط تدعم العربية للرسم البياني (اختياري حسب نظام التشغيل)
plt.rcParams['font.family'] = 'Arial'

from db_config import get_db_path, get_connection

class IncomeStatementWindow(ctk.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("قائمة الدخل - الأرباح")
        self.geometry("1100x800")
        
        self.db_path = get_db_path()
        # استخدام المسار الديناميكي للوصول لقاعدة البيانات الحقيقية
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
        self.db_path = os.path.join(base_dir, "supermarket.db")
        # === العنوان ===
        title_lbl = ctk.CTkLabel(self, text="قائمة الدخل - صافي الأرباح", font=("Arial", 24, "bold"))
        title_lbl.pack(pady=15)
        
        # === منطقة الفلاتر ===
        filter_frame = ctk.CTkFrame(self)
        filter_frame.pack(fill="x", padx=20, pady=10)
        
        # راديو بوتن للتصنيف (يومي، شهري، سنوي)
        # self.filter_var = ctk.StringVar(value="يومي")
        
        # radio_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        # radio_frame.pack(side="right", padx=20)
        
        # ctk.CTkRadioButton(radio_frame, text="سنوي", variable=self.filter_var, value="سنوي").pack(side="right", padx=10)
        # ctk.CTkRadioButton(radio_frame, text="شهري", variable=self.filter_var, value="شهري").pack(side="right", padx=10)
        # ctk.CTkRadioButton(radio_frame, text="يومي", variable=self.filter_var, value="يومي").pack(side="right", padx=10)
        
        # حقول التاريخ
        date_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        date_frame.pack(side="right", padx=20)
        
        ctk.CTkLabel(date_frame, text="إلى تاريخ:").pack(side="right", padx=5)
        self.date_to = DateEntry(date_frame, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.date_to.pack(side="right", padx=10)
        
        ctk.CTkLabel(date_frame, text="من تاريخ:").pack(side="right", padx=5)
        self.date_from = DateEntry(date_frame, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.date_from.pack(side="right", padx=10)
        
        # زر العرض
        # زر العرض (موجود مسبقاً في كودك)
        ctk.CTkButton(filter_frame, text="عرض التقرير", font=("Arial", 14, "bold"), command=self.generate_report).pack(side="left", padx=20)

        # ---------------------------------------------------------
        # انسخ من هنا واستبدل الكود القديم الخاص بالنتائج والرسم والتصدير
        # ---------------------------------------------------------

        # 1. === أزرار التصدير === (نحجز لها مساحة في الأسفل أولاً)
        export_frame = ctk.CTkFrame(self, fg_color="transparent")
        export_frame.pack(side="bottom", fill="x", padx=20, pady=10)
        
        ctk.CTkButton(export_frame, text="تصدير PDF", fg_color="#e74c3c", hover_color="#c0392b", command=self.export_pdf).pack(side="left", padx=10)
        ctk.CTkButton(export_frame, text="تصدير Excel", fg_color="#27ae60", hover_color="#2ecc71", command=self.export_excel).pack(side="left", padx=10)

        # 2. === منطقة النتائج (الجدول المالي) === (نضعها في الأعلى مباشرة تحت الفلاتر)
        self.results_frame = ctk.CTkFrame(self)
        self.results_frame.pack(side="top", fill="x", padx=20, pady=10)
        
        # 3. === منطقة الرسم البياني === (تأخذ كل المساحة المتبقية في المنتصف)
        self.chart_frame = ctk.CTkFrame(self)
        self.chart_frame.pack(side="top", fill="both", expand=True, padx=20, pady=10)
        
        # متغيرات لحفظ القيم لغرض التصدير
        self.report_data = {}
    def get_data_from_db(self, start_date, end_date):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 1. إجمالي المبيعات والخصم (استخدام الدالة date لتجاهل الوقت)
        cursor.execute("""
            SELECT COALESCE(SUM(total_amount), 0), COALESCE(SUM(discount), 0)
            FROM Invoices
            WHERE date(date_time) BETWEEN date(?) AND date(?)
        """, (start_date, end_date))
        total_sales, total_discount = cursor.fetchone()
        
        # 2. مرتجع المبيعات
        cursor.execute("""
            SELECT COALESCE(SUM(refund_amount), 0)
            FROM Sales_Returns
            WHERE date(date_time) BETWEEN date(?) AND date(?)
        """, (start_date, end_date))
        total_returns = cursor.fetchone()[0]
        
        # 3. تكلفة المبيعات الفعلية
        cursor.execute("""
            SELECT COALESCE(SUM(ii.quantity * ii.cost_price), 0)
            FROM Invoice_Items ii
            JOIN Invoices i ON ii.invoice_id = i.id
            WHERE date(i.date_time) BETWEEN date(?) AND date(?)
        """, (start_date, end_date))
        cost_of_sales = cursor.fetchone()[0]
        
        # 4. إجمالي المصروفات
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM Expenses
            WHERE date(date) BETWEEN date(?) AND date(?)
        """, (start_date, end_date))
        total_expenses = cursor.fetchone()[0]
        
        conn.close()
        
        # المعادلات المحاسبية النهائية
        net_sales = total_sales - total_returns
        gross_profit = net_sales - cost_of_sales - total_discount
        net_profit = gross_profit - total_expenses
        
        report_data = {
            "إجمالي المبيعات": total_sales,
            "مرتجع المبيعات": total_returns,
            "صافي المبيعات": net_sales,
            "تكلفة المبيعات": cost_of_sales,
            "الخصم الممنوح": total_discount,
            "صافي أرباح المبيعات (مجمل الربح)": gross_profit,
            "إجمالي المصروفات": total_expenses,
            "صافي الأرباح النهائي": net_profit
        }
        
        return report_data

    def generate_report(self):
        # مسح النتائج السابقة
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
            
        start_date = self.date_from.get_date().strftime('%Y-%m-%d')
        end_date = self.date_to.get_date().strftime('%Y-%m-%d')
        
        self.report_data = self.get_data_from_db(start_date, end_date)
        if not self.report_data:
            return
            
        # خريطة الألوان متطابقة 100% مع المفاتيح الجديدة
        colors_map = {
            "إجمالي المبيعات": "white",
            "مرتجع المبيعات": "#00FFFF", # Cyan
            "صافي المبيعات": "white",
            "تكلفة المبيعات": "#E5C494", # Light Brown
            "الخصم الممنوح": "white",
            "صافي أرباح المبيعات (مجمل الربح)": "#C0C0C0", # Gray
            "إجمالي المصروفات": "#FFFF00", # Yellow
            "صافي الأرباح النهائي": "#00FF00"  # Green
        }
        
        row = 0
        for key, value in self.report_data.items():
            bg_color = colors_map.get(key, "white")
            text_color = "black"
            
            # اسم الحقل
            lbl_key = tk.Label(self.results_frame, text=key, bg=bg_color, fg=text_color, font=("Arial", 14, "bold"), borderwidth=1, relief="solid", width=35, anchor="e")
            lbl_key.grid(row=row, column=1, sticky="nsew", ipady=5, ipadx=10)
            
            # القيمة
            lbl_val = tk.Label(self.results_frame, text=f"{value:,.2f}", bg=bg_color, fg=text_color, font=("Arial", 14), borderwidth=1, relief="solid", width=25, anchor="c")
            lbl_val.grid(row=row, column=0, sticky="nsew", ipady=5)
            row += 1
            
        self.results_frame.columnconfigure(0, weight=1)
        self.results_frame.columnconfigure(1, weight=1)
        
        self.draw_chart()

    def draw_chart(self):
        """ رسم الرسم البياني العمودي """
        fig, ax = plt.subplots(figsize=(6, 4))
        
        labels = ['صافي المبيعات', 'المصروفات', 'صافي الأرباح']
        values = [
            self.report_data['صافي المبيعات'], 
            self.report_data['إجمالي المصروفات'], 
            self.report_data['صافي الأرباح النهائي']
        ]
        
        colors_list = ['#3498db', '#e74c3c', '#2ecc71']
        
        bars = ax.bar(labels, values, color=colors_list)
        
        # إضافة القيم فوق الأعمدة
        for bar in bars:
            yval = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, yval, round(yval, 2), va='bottom', ha='center', fontsize=10, fontweight='bold')
            
        ax.set_ylabel('المبلغ')
        ax.set_title('مقارنة الإيرادات، المصروفات وصافي الربح')
        
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def export_excel(self):
        if not self.report_data:
            messagebox.showwarning("تنبيه", "الرجاء عرض التقرير أولاً")
            return
            
        filepath = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")], initialfile="Income_Statement.xlsx")
        if not filepath: return
        
        workbook = xlsxwriter.Workbook(filepath)
        worksheet = workbook.add_worksheet('صافي الأرباح')
        
        formats = {
            "white": workbook.add_format({'bg_color': '#FFFFFF', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 12}),
            "cyan": workbook.add_format({'bg_color': '#00FFFF', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 12}),
            "brown": workbook.add_format({'bg_color': '#E5C494', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 12}),
            "gray": workbook.add_format({'bg_color': '#C0C0C0', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 12}),
            "yellow": workbook.add_format({'bg_color': '#FFFF00', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 12}),
            "green": workbook.add_format({'bg_color': '#00FF00', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 12}),
            "header": workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 14, 'border': 0})
        }
        
        worksheet.set_column('A:A', 35)
        worksheet.set_column('B:B', 25)
        worksheet.right_to_left()
        
        worksheet.merge_range('A1:B1', 'قائمة الدخل - صافي الأرباح', formats['header'])
        
        row = 1
        colors_map = {
            "إجمالي المبيعات": "white", "مرتجع المبيعات": "cyan", "صافي المبيعات": "white",
            "تكلفة المبيعات": "brown", "الخصم الممنوح": "white", "صافي أرباح المبيعات (مجمل الربح)": "gray",
            "إجمالي المصروفات": "yellow", "صافي الأرباح النهائي": "green"
        }
        
        for key, value in self.report_data.items():
            fmt = formats.get(colors_map.get(key, "white"), formats["white"])
            worksheet.worksheet.write if hasattr(worksheet, 'worksheet') else worksheet.write(row, 0, key, fmt)
            worksheet.write(row, 1, value, fmt)
            row += 1
            
        workbook.close()
        messagebox.showinfo("نجاح", f"تم تصدير الإكسل بنجاح إلى:\n{filepath}")
    
    def export_pdf(self):
        if not self.report_data:
            messagebox.showwarning("تنبيه", "الرجاء عرض التقرير أولاً")
            return
            
        filepath = filedialog.asksaveasfilename(
            defaultextension=".pdf", 
            filetypes=[("PDF Files", "*.pdf")], 
            initialfile="Income_Statement.pdf"
        )
        if not filepath: 
            return

        # 1. دالة مساعدة لتشكيل النص العربي وضبط اتجاهه من اليمين لليسار
        def ar(text):
            if not text:
                return ""
            reshaped_text = arabic_reshaper.reshape(str(text))
            return get_display(reshaped_text)

        # 2. تسجيل خط يدعم اللغة العربية (استخدام Arial من مسارات النظام)
        font_name = "Helvetica" # الافتراضي في حال عدم وجود الخط
        font_paths = [
            "C:/Windows/Fonts/arial.ttf",           # Windows
            "/System/Library/Fonts/Supplemental/Arial.ttf", # macOS
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf" # Linux
        ]
        
        for path in font_paths:
            if os.path.exists(path):
                pdfmetrics.registerFont(TTFont('ArabicFont', path))
                font_name = 'ArabicFont'
                break

        doc = SimpleDocTemplate(filepath, pagesize=A4)
        elements = []

        # 3. إضافة العنوان في أعلى الصفحة
        styles = getSampleStyleSheet()
        title_style = styles['Title']
        title_style.fontName = font_name
        title_style.fontSize = 20
        title_style.leading = 24
        
        title_paragraph = Paragraph(ar("قائمة الدخل - صافي الأرباح"), title_style)
        elements.append(title_paragraph)
        elements.append(Spacer(1, 20)) # مسافة بين العنوان والجدول

        # 4. تحويل وتشكيل بيانات الجدول
        data = []
        for key, value in self.report_data.items():
            formatted_value = f"{value:,.2f}"
            formatted_key = ar(key)
            data.append([formatted_value, formatted_key])

        # 5. بناء الجدول وتنسيقه
        t = Table(data, colWidths=[200, 200])
        style = TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), font_name), # استخدام الخط العربي
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            # تلوين الصفوف
            ('BACKGROUND', (0, 0), (-1, 0), colors.white),
            ('BACKGROUND', (0, 1), (-1, 1), colors.cyan),
            ('BACKGROUND', (0, 2), (-1, 2), colors.white),
            ('BACKGROUND', (0, 3), (-1, 3), colors.bisque),
            ('BACKGROUND', (0, 4), (-1, 4), colors.white),
            ('BACKGROUND', (0, 5), (-1, 5), colors.silver),
            ('BACKGROUND', (0, 6), (-1, 6), colors.yellow),
            ('BACKGROUND', (0, 7), (-1, 7), colors.lime),
        ])
        t.setStyle(style)
        
        elements.append(t)
        doc.build(elements)
        messagebox.showinfo("نجاح", f"تم تصدير الـ PDF بنجاح إلى:\n{filepath}")
# للاختبار فقط عند تشغيل الملف بشكل منفصل
if __name__ == "__main__":
    app = ctk.CTk()
    app.geometry("200x200")
    btn = ctk.CTkButton(app, text="افتح قائمة الدخل", command=lambda: IncomeStatementWindow(app))
    btn.pack(expand=True)
    app.mainloop()