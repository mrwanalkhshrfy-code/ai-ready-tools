import customtkinter as ctk
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A7
import os
import subprocess
from db_config import get_db_path, get_connection

class PrintPreviewWindow(ctk.CTkToplevel):
    def __init__(self, items, total, invoice_id, cust_name, payment, discount):
        super().__init__()
        self.title("معاينة الفاتورة")
        self.geometry("300x500")
        
        # إنشاء ملف مؤقت للعرض
        self.temp_pdf = "temp_invoice.pdf"
        self.generate_pdf(items, total, invoice_id, cust_name, payment, discount)
        
        # عرض نصي بسيط أو صورة للمعاينة
        ctk.CTkLabel(self, text="معاينة الفاتورة قبل الطباعة", font=("Arial", 16, "bold")).pack(pady=10)
        ctk.CTkButton(self, text="طباعة الآن", command=self.print_file).pack(pady=20)
        ctk.CTkButton(self, text="إغلاق", command=self.destroy).pack()

    def generate_pdf(self, items, total, invoice_id, cust_name, payment, discount):
        c = canvas.Canvas(self.temp_pdf, pagesize=A7)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(20, 230, "سوبر ماركت الهدى")
        c.setFont("Helvetica", 8)
        c.drawString(20, 215, f"فاتورة رقم: {invoice_id}")
        c.drawString(20, 205, f"العميل: {cust_name}")
        c.drawString(20, 195, f"الدفع: {payment}")
        
        y = 175
        for item in items:
            c.drawString(20, y, f"{item[3]} | {item[2]}x{item[1]} | {item[0]} ر.ي")
            y -= 15
        
        c.setFont("Helvetica-Bold", 8)
        c.drawString(20, y-10, f"الخصم: {discount} ر.ي")
        c.drawString(20, y-25, f"الإجمالي النهائي: {total} ر.ي")
        c.save()

    def print_file(self):
        # أمر طباعة الملف افتراضياً في ويندوز
        os.startfile(self.temp_pdf, "print")