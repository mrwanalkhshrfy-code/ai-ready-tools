import customtkinter as ctk
import tkinter as tk # مكتبة الواجهات الأساسية لإنشاء القائمة المنسدلة
from tkinter import messagebox
import os
import sys

# استيراد ملفات النظام
import pos_window
import reports_window 
import suppliers_window
import finance_window
import purchases_window
from inventory_window import InventoryWindow

class MainDashboard(ctk.CTk):
    def __init__(self, user_info):
        super().__init__()
        self.user_info = user_info
        
        # جلب صلاحية المستخدم
        user_role = self.user_info.get('role', 'كاشير')
        
        # إعدادات الشاشة
        self.title("لوحة التحكم الرئيسية - نظام السوبر ماركت")
        self.geometry("1000x700")

        # === الشريط العلوي ===
        header = ctk.CTkFrame(self, height=80, fg_color="#2c3e50")
        header.pack(fill="x", side="top")

        # 1. زر قائمة الإعدادات ≡ (يظهر في جهة اليمين للمدير فقط)
        if user_role == 'مدير':
            self.settings_btn = ctk.CTkButton(
                header, 
                text="⚙️ ≡", 
                width=60, 
                font=("Arial", 20, "bold"), 
                fg_color="#34495e", 
                hover_color="#1abc9c", 
                command=self.show_settings_menu
            )
            self.settings_btn.pack(side="right", padx=20, pady=20)
            self.setup_settings_menu() # تهيئة القائمة المنسدلة

        # 2. زر تسجيل الخروج (يظهر في جهة اليسار)
        ctk.CTkButton(
            header, 
            text="تسجيل خروج", 
            fg_color="#c0392b", 
            hover_color="#e74c3c", 
            font=("Arial", 14, "bold"), 
            width=120, 
            command=self.logout
        ).pack(side="left", padx=20, pady=20)

        # 3. رسالة الترحيب (تظهر في المنتصف تماماً بين الزرين)
        ctk.CTkLabel(
            header, 
            text=f"أهلاً بك: {self.user_info['username']} | الصلاحية: {user_role}", 
            font=("Arial", 20, "bold"), 
            text_color="white"
        ).pack(expand=True, pady=20)

        # === حاوية الأزرار الرئيسية ===
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=40, padx=40, fill="both", expand=True)

        # تعريف كل الأزرار المتاحة في النظام
        all_buttons_config = [
            ("المبيعات (الكاشير)", "#2ecc71", self.open_sales),
            ("الفواتير والتقارير", "#9b59b6", self.open_reports),
            ("المشتريات وتوريد البضائع", "#e67e22", self.open_purchases),
            ("المصروفات", "#e74c3c", self.open_expenses),
            ("الموردون", "#1abc9c", self.open_suppliers),
            ("إدارة المخازن", "#34495e", self.open_inventory),
            ("إدارة المستخدمين", "#f1c40f", self.open_users),
            # ("العملاء والديون", "#f1c40f", self.open_users2),
            (" العملاء والديون", "#3498db", self.open_users2),
            
        ]

        # فلترة الأزرار حسب الصلاحية
        if user_role == 'مدير':
            buttons_config = all_buttons_config
        else:
            allowed_for_cashier = ["المبيعات (الكاشير)", "العملاء والديون", "المصروفات"]
            buttons_config = [btn for btn in all_buttons_config if btn[0] in allowed_for_cashier]

        # توزيع الأزرار 
        for i, (text, color, cmd) in enumerate(buttons_config):
            row = i // 3
            col = i % 3
            btn = ctk.CTkButton(
                btn_frame, text=text, fg_color=color, hover_color=color, 
                height=120, font=("Arial", 18, "bold"), command=cmd
            )
            btn.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")        
            
        for r in range(3):
            btn_frame.rowconfigure(r, weight=1)
        for c in range(3):
            btn_frame.columnconfigure(c, weight=1)

    # ==================== إعدادات القائمة المنسدلة ====================

    def setup_settings_menu(self):
        """تهيئة وتنسيق عناصر القائمة المنسدلة بشكل احترافي"""
        self.settings_menu = tk.Menu(
            self, 
            tearoff=0, 
            font=("Arial", 14, "bold"), 
            bg="#ffffff",               # لون الخلفية أبيض
            fg="#2c3e50",               # لون الخط كحلي غامق
            activebackground="#1abc9c", # لون التحديد أخضر
            activeforeground="#ffffff", # لون الخط عند التحديد أبيض
            bd=1, 
            relief="solid"
        )
        
        # إضافة العناصر مع الأيقونات (Emojis)
        self.settings_menu.add_command(label="💾   حفظ نسخة احتياطية", command=self.action_backup)
        self.settings_menu.add_command(label="🔄   استعادة النسخة الاحتياطية", command=self.action_restore)
        self.settings_menu.add_separator() # خط فاصل
        
        # self.settings_menu.add_command(label="📊   رسوم بيانية", command=self.action_charts)
        # self.settings_menu.add_command(label="📦   ملف الأصناف", command=self.action_items_file)
        # self.settings_menu.add_command(label="📋   حركات الأصناف التفصيلية", command=self.action_items_movement)
        # self.settings_menu.add_separator()
        
        self.settings_menu.add_command(label="💰   تقارير رأس المال", command=self.action_capital_reports)
        self.settings_menu.add_command(label="📈   قائمة الدخل - الأرباح", command=self.action_income_statement)
        self.settings_menu.add_separator()
        
        self.settings_menu.add_command(label="🎧   التواصل والدعم", command=self.action_support)
        self.settings_menu.add_command(label="🎥   فيديو تعليمي", command=self.action_tutorial)

    def show_settings_menu(self):
        """عرض القائمة المنسدلة تحت الزر مباشرة عند النقر"""
        x = self.settings_btn.winfo_rootx()
        y = self.settings_btn.winfo_rooty() + self.settings_btn.winfo_height()
        self.settings_menu.post(x, y)

    # ==================== دوال أزرار القائمة المنسدلة ====================
    
    def action_backup(self):
        """دالة حفظ نسخة احتياطية لقاعدة البيانات"""
        import shutil
        from tkinter import filedialog
        import datetime

        # تحديد اسم قاعدة البيانات المستخدمة في النظام
        db_name = "supermarket_4.db"  # يمكنك تغييرها إلى "supermarket.db" حسب اسم قاعدة البيانات لديك
        if not os.path.exists(db_name):
            db_name = "supermarket.db"

        if not os.path.exists(db_name):
            messagebox.showerror("خطأ", "لم يتم العثور على ملف قاعدة البيانات!")
            return

        # اقتراح اسم افتراضي للنسخة الاحتياطية مدمج معه التاريخ والوقت
        default_filename = f"supermarket_backup_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.db"

        # فتح نافذة اختيار مكان حفظ الملف
        backup_path = filedialog.asksaveasfilename(
            defaultextension=".db",
            filetypes=[("Database Files", "*.db"), ("All Files", "*.*")],
            initialfile=default_filename
        )

        if backup_path:
            try:
                # نسخ ملف قاعدة البيانات إلى الوجهة التي اختارها المستخدم
                shutil.copy(db_name, backup_path)
                messagebox.showinfo("نجاح", f"تم حفظ النسخة الاحتياطية بنجاح في:\n{backup_path}")
            except Exception as e:
                messagebox.showerror("خطأ", f"حدث خطأ أثناء حفظ النسخة الاحتياطية:\n{e}")
    def action_restore(self):
        """دالة استعادة النسخة الاحتياطية لقاعدة البيانات"""
        import shutil
        from tkinter import filedialog

        # رسالة تحذيرية لتأكيد العملية لأنها ستستبدل البيانات الحالية بالكامل
        if not messagebox.askyesno(
            "تحذير هام", 
            "استعادة النسخة الاحتياطية ستؤدي إلى استبدال كافة البيانات الحالية بالبيانات الموجودة في الملف المختار!\nهل أنت متأكد من المتابعة؟",
            icon="warning"
        ):
            return

        # فتح نافذة اختيار ملف النسخة الاحتياطية
        restore_path = filedialog.askopenfilename(
            title="اختر ملف النسخة الاحتياطية للاستعادة",
            filetypes=[("Database Files", "*.db"), ("All Files", "*.*")]
        )

        if restore_path:
            try:
                # تحديد اسم قاعدة البيانات النشطة في النظام
                db_name = "supermarket_4.db"
                if not os.path.exists(db_name) and os.path.exists("supermarket.db"):
                    db_name = "supermarket.db"

                # نسخ ملف النسخة الاحتياطية فوق قاعدة البيانات الحالية
                shutil.copy(restore_path, db_name)
                
                messagebox.showinfo("نجاح", "تمت استعادة النسخة الاحتياطية بنجاح!\nسيتم إعادة تشغيل النظام لتطبيق التغييرات.")
                
                # إعادة تشغيل التطبيق بالكامل لتحديث الاتصال وقراءة البيانات الجديدة
                os.execl(sys.executable, sys.executable, *sys.argv)
                
            except Exception as e:
                messagebox.showerror("خطأ", f"حدث خطأ أثناء استعادة النسخة الاحتياطية:\n{e}")
                
    # def action_charts(self): messagebox.showinfo("إعدادات", "فتح شاشة الرسوم البيانية...")
    # def action_items_file(self): messagebox.showinfo("إعدادات", "فتح ملف الأصناف...")
    # def action_items_movement(self): messagebox.showinfo("إعدادات", "فتح شاشة حركات الأصناف التفصيلية...")
    def action_capital_reports(self):
        # استدعاء ملف تقرير رأس المال الجديد
        from capital_report_window import CapitalReportWindow
        report_win = CapitalReportWindow()
        report_win.mainloop()
    def action_income_statement(self): 
        from income_statement_window import IncomeStatementWindow
        income_win = IncomeStatementWindow(self)
        income_win.grab_set() # لجعل النافذة فوق النافذة الرئيسية
    def action_support(self): messagebox.showinfo("دعم فني", "للتواصل والدعم: 000000000")
    def action_tutorial(self): messagebox.showinfo("تعليم", "جاري تشغيل الفيديو التعليمي...")

    # ==================== دوال الشاشات الرئيسية ====================

    def open_sales(self):
        self.withdraw()
        pos = pos_window.POSApp(self.user_info)
        pos.protocol("WM_DELETE_WINDOW", lambda: self.on_close_child(pos))
        pos.mainloop()

    def open_reports(self):
        import reports_window
        report_win = reports_window.ReportsWindow()
        report_win.mainloop()

    def open_purchases(self):
        purchases_win = purchases_window.PurchasesWindow(self.user_info)
        purchases_win.mainloop()

    def open_inventory(self):
        inv_win = InventoryWindow()
        inv_win.mainloop()

    def open_expenses(self):
        from finance_window import FinanceWindow
        fin_win = FinanceWindow()
        fin_win.mainloop()

    def open_suppliers(self):
        suppliers_win = suppliers_window.SuppliersWindow()
        suppliers_win.mainloop()

    # def open_finance(self): 
    #     messagebox.showinfo("المالية", "فتح شاشة الإدارة المالية...")
        
    def open_users(self):
        import users_window
        win = users_window.UsersWindow()
        win.mainloop()
        
    def open_users2(self):
        import customers_window
        win = customers_window.CustomersWindow()
        win.mainloop()

    def on_close_child(self, child_window):
        child_window.destroy()
        self.deiconify()

    def logout(self):
        if messagebox.askyesno("تسجيل خروج", "هل أنت متأكد من رغبتك في تسجيل الخروج؟"):
            self.destroy()
            os.execl(sys.executable, sys.executable, *sys.argv)