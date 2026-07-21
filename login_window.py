import customtkinter as ctk
from tkinter import messagebox
import sqlite3
import os
import datetime
import main_dashboard
import pos_window 
import sys

# استدعاء دالة المسار ودالة الاتصال الموحدة من db_config
from db_config import get_db_path, get_connection

# إعداد المظهر العام
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

def check_system_license():
    """دالة التحقق من صلاحية النسخة (4 أشهر)"""
    db_path = get_db_path()
    
    # فحص وجود ملف قاعدة البيانات باستخدام المسار النصي
    if not os.path.exists(db_path):
        return True

    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # إنشاء جدول لتخزين تاريخ التثبيت وتاريخ انتهاء النسخة سراً
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS System_License (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                install_date TEXT,
                expiry_date TEXT
            )
        """)
        
        cursor.execute("SELECT install_date, expiry_date FROM System_License WHERE id = 1")
        row = cursor.fetchone()
        
        today = datetime.date.today()
        
        if not row:
            # أول تشغيل: تسجيل تاريخ اليوم وتحديد تاريخ الانتهاء بعد 4 أشهر (120 يوماً)
            install_date = today.strftime('%Y-%m-%d')
            expiry_date = (today + datetime.timedelta(days=120)).strftime('%Y-%m-%d')
            
            cursor.execute("INSERT INTO System_License (install_date, expiry_date) VALUES (?, ?)", (install_date, expiry_date))
            conn.commit()
            conn.close()
            return True
        else:
            _, expiry_date_str = row
            conn.close()
            
            expiry_date = datetime.datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
            
            if today > expiry_date:
                return False # انتهت المدة!
            return True
            
    except Exception as e:
        print(f"License check error: {e}")
        return True


class ActivationLockWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("تنبيه - انتهت الفترة التجريبية")
        self.geometry("550x600")
        self.resizable(False, False)
        
        # منع إغلاق النافذة بسهولة
        self.protocol("WM_DELETE_WINDOW", lambda: None)
        
        # عنوان تحذيري
        ctk.CTkLabel(
            self, 
            text="⚠️ انتهت الفترة التجريبية للنظام", 
            font=("Arial", 22, "bold"), 
            text_color="#e74c3c"
        ).pack(pady=20)
        
        photo_path = "my_photo.png"
        if os.path.exists(photo_path):
            try:
                from PIL import Image, ImageTk
                img = Image.open(photo_path).resize((130, 130))
                self.photo_img = ImageTk.PhotoImage(img)
                img_lbl = ctk.CTkLabel(self, image=self.photo_img, text="")
                img_lbl.pack(pady=10)
            except Exception:
                pass

        ctk.CTkLabel(
            self, 
            text="المهندس: مروان هادي الخشرفي", 
            font=("Arial", 20, "bold")
        ).pack(pady=5)
        
        ctk.CTkLabel(
            self, 
            text="لقد انتهت فترة التجربة المجانية (4 أشهر).\nيرجى التواصل مع المطور لتسديد المستحقات وتفعيل النسخة الدائمة.", 
            font=("Arial", 14), 
            justify="center",
            text_color="#bdc3c7"
        ).pack(pady=10)
        
        # صندوق معلومات التواصل
        contact_frame = ctk.CTkFrame(self, fg_color="#2c3e50", corner_radius=15)
        contact_frame.pack(fill="x", padx=40, pady=15, ipadx=10, ipady=15)
        
        self.code_entry = ctk.CTkEntry(self, placeholder_text="أدخل كود التفعيل هنا", width=250, height=40, show="*")
        self.code_entry.pack(pady=10)

        self.activate_btn = ctk.CTkButton(self, text="تفعيل النسخة", fg_color="#27ae60", command=self.verify_activation)
        self.activate_btn.pack(pady=5)
        
        ctk.CTkLabel(contact_frame, text="📞 وسائل التواصل والاتصال:", font=("Arial", 16, "bold"), text_color="white").pack(pady=5)
        ctk.CTkLabel(contact_frame, text="رقم الهاتف: 779637762 / واتساب: 00967779637762", font=("Arial", 15, "bold"), text_color="#1abc9c").pack(pady=5)
        ctk.CTkLabel(contact_frame, text="البريد الإلكتروني: mrwanalkhshrfy@gmail.com", font=("Arial", 14), text_color="#ecf0f1").pack(pady=5)
        
        ctk.CTkLabel(
            self, 
            text="🔒 اطمئن: كافة بياناتك، فواتيرك، ومخزونك محفوظة وآمنة تماماً في قاعدة البيانات.", 
            font=("Arial", 12), 
            text_color="#f1c40f"
        ).pack(side="bottom", pady=20)
        
    def verify_activation(self):
        entered_code = self.code_entry.get().strip()
        
        if entered_code == "VIP-779637762-mrwan":
            try:
                conn = get_connection()
                cursor = conn.cursor()
                
                # تمديد تاريخ الانتهاء لـ 5 سنوات قدماً
                new_expiry = (datetime.date.today() + datetime.timedelta(days=1825)).strftime('%Y-%m-%d')
                
                cursor.execute("UPDATE System_License SET expiry_date = ? WHERE id = 1", (new_expiry,))
                conn.commit()
                conn.close()
                
                messagebox.showinfo("نجاح", "تم تفعيل النظام بنجاح لنسخة دائمة!\nسيتم إعادة تشغيل البرنامج.")
                os.execl(sys.executable, sys.executable, *sys.argv)
            except Exception as e:
                messagebox.showerror("خطأ", f"حدث خطأ أثناء التفعيل: {e}")
        else:
            messagebox.showerror("خطأ", "كود التفعيل غير صحيح!")        
    
    
class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("تسجيل الدخول - نظام المحاسبة")
        self.geometry("400x500")
        self.resizable(False, False)

        self.frame = ctk.CTkFrame(self, corner_radius=15)
        self.frame.pack(pady=40, padx=40, fill="both", expand=True)

        self.title_label = ctk.CTkLabel(self.frame, text="تسجيل الدخول", font=("Arial", 26, "bold"))
        self.title_label.pack(pady=(40, 30))

        self.username_entry = ctk.CTkEntry(self.frame, placeholder_text="اسم المستخدم", height=40, justify="right")
        self.username_entry.pack(pady=15, padx=20, fill="x")

        self.password_entry = ctk.CTkEntry(self.frame, placeholder_text="كلمة المرور", height=40, show="*", justify="right")
        self.password_entry.pack(pady=15, padx=20, fill="x")

        self.login_button = ctk.CTkButton(self.frame, text="دخول", height=45, command=self.check_login)
        self.login_button.pack(pady=30, padx=20, fill="x")

    def check_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT username, phone, role FROM Users WHERE username = ? AND password = ?", (username, password))
            user = cursor.fetchone()
            conn.close()

            if user:
                user_info = {"username": user[0], "phone": user[1], "role": user[2]}
                self.destroy() 
                app = main_dashboard.MainDashboard(user_info)
                app.mainloop()
            else:
                messagebox.showerror("خطأ", "بيانات الدخول غير صحيحة!")
        except Exception as e:
            messagebox.showerror("خطأ في قاعدة البيانات", f"لم نتمكن من التحقق من بيانات الدخول:\n{e}")

if __name__ == "__main__":
    if check_system_license():
        LoginWindow().mainloop()
    else:
        ActivationLockWindow().mainloop()