import customtkinter as ctk
from tkinter import messagebox
import sqlite3
import datetime
import os

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A7 # حجم صغير مناسب للإيصالات
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import arabic_reshaper
from bidi.algorithm import get_display

# استدعاء دالة الاتصال الموحدة من db_config
from db_config import get_connection, get_db_path

class FinanceWindow(ctk.CTkToplevel):
    def __init__(self):
        super().__init__()
        self.title("الإدارة المالية والوردية")
        self.geometry("600x700")
        self.grab_set()

        # --- قسم تسجيل المصروفات ---
        self.frame_expenses = ctk.CTkFrame(self)
        self.frame_expenses.pack(pady=20, padx=20, fill="x")
        
        ctk.CTkLabel(self.frame_expenses, text="تسجيل مصروف جديد", font=("Arial", 18, "bold")).pack(pady=10)
        
        self.entry_category = ctk.CTkEntry(self.frame_expenses, placeholder_text="نوع المصروف (مثال: كهرباء)")
        self.entry_category.pack(pady=5, padx=10, fill="x")
        
        self.entry_amount = ctk.CTkEntry(self.frame_expenses, placeholder_text="المبلغ")
        self.entry_amount.pack(pady=5, padx=10, fill="x")
        
        self.entry_note = ctk.CTkEntry(self.frame_expenses, placeholder_text="ملاحظات")
        self.entry_note.pack(pady=5, padx=10, fill="x")
        
        ctk.CTkButton(self.frame_expenses, text="حفظ المصروف", command=self.save_expense).pack(pady=10)

        # --- قسم تقفيل الوردية ---
        self.frame_shift = ctk.CTkFrame(self)
        self.frame_shift.pack(pady=20, padx=20, fill="x")
        
        ctk.CTkLabel(self.frame_shift, text="تقفيل الوردية (الكاشير)", font=("Arial", 18, "bold")).pack(pady=10)
        
        self.entry_actual_cash = ctk.CTkEntry(self.frame_shift, placeholder_text="المبلغ الفعلي في الدرج")
        self.entry_actual_cash.pack(pady=5, padx=10, fill="x")
        
        ctk.CTkButton(self.frame_shift, text="إغلاق الوردية وحساب الفرق", command=self.close_shift).pack(pady=10)

    def save_expense(self):
        cat = self.entry_category.get()
        amt = self.entry_amount.get()
        note = self.entry_note.get()
        
        if not cat or not amt:
            messagebox.showwarning("خطأ", "يجب إدخال النوع والمبلغ!")
            return
            
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Expenses (category, amount, note) VALUES (?, ?, ?)", (cat, amt, note))
        conn.commit()
        conn.close()
        messagebox.showinfo("نجاح", "تم حفظ المصروف بنجاح")
        self.entry_category.delete(0, 'end')
        self.entry_amount.delete(0, 'end')

    def close_shift(self):
        try:
            actual = float(self.entry_actual_cash.get())
            
            conn = get_connection()
            cursor = conn.cursor()
            
            # تاريخ آخر إغلاق وردية
            last_shift_time = cursor.execute("SELECT IFNULL(MAX(end_time), '1900-01-01') FROM Cashier_Shifts").fetchone()[0]

            # إجمالي المبيعات الكلية (كافة أنواع الدفع - للمعلومة فقط في التقرير)
            cursor.execute("SELECT IFNULL(SUM(total_amount), 0) FROM Invoices WHERE date_time > ?", (last_shift_time,))
            total_sales = cursor.fetchone()[0]

            # 1. النقد الفعلي الذي دخل الدرج (النقد + المدفوع من الجزئي/الآجل)
            cursor.execute("SELECT IFNULL(SUM(paid_amount), 0) FROM Invoices WHERE date_time > ? AND payment_type != 'بنكي'", (last_shift_time,))
            cash_sales = cursor.fetchone()[0]
            
            # 2. المبيعات البنكية (للمعلومة في التقرير)
            cursor.execute("SELECT IFNULL(SUM(total_amount), 0) FROM Invoices WHERE date_time > ? AND payment_type = 'بنكي'", (last_shift_time,))
            bank_sales = cursor.fetchone()[0]
            
            # 3. إجمالي الديون/الآجل المتبقية (للمعلومة في التقرير)
            cursor.execute("SELECT IFNULL(SUM(remaining_amount), 0) FROM Invoices WHERE date_time > ?", (last_shift_time,))
            credit_sales = cursor.fetchone()[0]

            # إجمالي المرتجعات (المبالغ التي دفعناها للعملاء من الدرج نقداً)
            cursor.execute("SELECT IFNULL(SUM(refund_amount), 0) FROM Sales_Returns WHERE date_time > ?", (last_shift_time,))
            total_returns = cursor.fetchone()[0]
            
            # إجمالي المصروفات (التي خرجت من الدرج)
            cursor.execute("SELECT IFNULL(SUM(amount), 0) FROM Expenses WHERE date > ?", (last_shift_time,))
            total_expenses = cursor.fetchone()[0]
            
            # سداد ديون العملاء
            cursor.execute("SELECT IFNULL(SUM(amount), 0) FROM Credit_Transactions WHERE date_time > ? AND type = 'payment'", (last_shift_time,))
            debt_payments = cursor.fetchone()[0]
            
            # المعادلة الصحيحة لدرج الكاشير: (النقد المستلم من المبيعات + النقد المستلم من الديون) - المرتجعات - المصروفات
            expected = (cash_sales + debt_payments - total_returns) - total_expenses
            diff = actual - expected
            
            # حفظ الوردية
            cursor.execute("""
                INSERT INTO Cashier_Shifts (expected_amount, actual_amount, difference, end_time) 
                VALUES (?, ?, ?, ?)
            """, (expected, actual, diff, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            
            conn.commit()
            conn.close()
            
            # تحديث التقرير ليشمل التفاصيل الجديدة
            self.generate_pdf_receipt(total_sales, cash_sales, bank_sales, credit_sales, total_returns, total_expenses, debt_payments, expected, actual, diff)
            messagebox.showinfo("الوردية", f"تم التقفيل.\nالمتوقع في الدرج: {expected:.2f}\nالفرق: {diff:.2f}")
            
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ: {e}")

    @staticmethod
    def fix_arabic(text):
        reshaped_text = arabic_reshaper.reshape(text)
        return get_display(reshaped_text)

    def generate_pdf_receipt(self, total_sales, cash_sales, bank_sales, credit_sales, returns, expenses, debt_payments=0, expected=0, actual=0, diff=0):
        try:
            pdfmetrics.registerFont(TTFont('Arabic', 'arial.ttf'))
            filename = f"shift_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            c = canvas.Canvas(filename, pagesize=A7)
            c.setFont("Arabic", 10)
            
            y = 230
            c.drawString(20, y, self.fix_arabic("تقرير الوردية المالي"))
            
            y -= 25
            c.drawString(20, y, self.fix_arabic(f"إجمالي المبيعات العام: {total_sales:.2f}"))
            y -= 15
            c.drawString(20, y, self.fix_arabic(f"مبيعات بنكية (خارج الدرج): {bank_sales:.2f}"))
            y -= 15
            c.drawString(20, y, self.fix_arabic(f"ديون متبقية (آجل): {credit_sales:.2f}"))
            
            y -= 20
            
            c.drawString(20, y, self.fix_arabic(f"نقد المبيعات (الدرج): {cash_sales:.2f}"))
            y -= 15
            c.drawString(20, y, self.fix_arabic(f"سداد ديون العملاء (الدرج): {debt_payments:.2f}"))
            y -= 15
            c.drawString(20, y, self.fix_arabic(f"إجمالي المرتجعات: -{returns:.2f}"))
            y -= 15
            c.drawString(20, y, self.fix_arabic(f"إجمالي المصروفات: -{expenses:.2f}"))
            
            y -= 15
            
            c.drawString(20, y, self.fix_arabic(f"المتوقع بالدرج: {expected:.2f}"))
            y -= 15
            c.drawString(20, y, self.fix_arabic(f"الفعلي بالدرج: {actual:.2f}"))
            y -= 15
            c.drawString(20, y, FinanceWindow.fix_arabic(f"عجز/زيادة (الفرق): {diff:.2f}"))
            
            y -= 15
            c.line(20, y+5, 180, y+5) # خط فاصل
            
            c.save()
            os.startfile(filename) # فتح التقرير تلقائياً بعد الإغلاق
            
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل إنشاء إيصال الوردية: {e}")