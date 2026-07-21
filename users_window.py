import customtkinter as ctk
from tkinter import messagebox, ttk
import sqlite3
import db_config
from db_config import get_db_path, get_connection

class UsersWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("إدارة المستخدمين والصلاحيات")
        self.geometry("900x600")
        
        # متغير لتتبع المستخدم المحدد (للتعديل أو الحذف)
        self.selected_user_id = None
        
        # إعدادات الواجهة
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # === لوحة إدخال البيانات (اليمين) ===
        input_frame = ctk.CTkFrame(self, width=300)
        input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(input_frame, text="إضافة / تعديل مستخدم", font=("Arial", 18, "bold")).pack(pady=20)

        self.username_entry = ctk.CTkEntry(input_frame, placeholder_text="اسم المستخدم (مطلوب)")
        self.username_entry.pack(pady=10, padx=20, fill="x")

        self.password_entry = ctk.CTkEntry(input_frame, placeholder_text="كلمة المرور (مطلوب)", show="*")
        self.password_entry.pack(pady=10, padx=20, fill="x")

        self.phone_entry = ctk.CTkEntry(input_frame, placeholder_text="رقم الهاتف")
        self.phone_entry.pack(pady=10, padx=20, fill="x")

        # قائمة الصلاحيات
        ctk.CTkLabel(input_frame, text="الصلاحية:").pack(anchor="e", padx=20)
        self.role_var = ctk.StringVar(value="كاشير")
        self.role_menu = ctk.CTkOptionMenu(input_frame, variable=self.role_var, values=["مدير", "كاشير"])
        self.role_menu.pack(pady=5, padx=20, fill="x")

        # أزرار التحكم
        ctk.CTkButton(input_frame, text="حفظ / تعديل", fg_color="#2ecc71", hover_color="#27ae60", command=self.save_user).pack(pady=15, padx=20, fill="x")
        ctk.CTkButton(input_frame, text="مسح الحقول", fg_color="#95a5a6", hover_color="#7f8c8d", command=self.clear_inputs).pack(pady=5, padx=20, fill="x")
        ctk.CTkButton(input_frame, text="حذف المستخدم", fg_color="#e74c3c", hover_color="#c0392b", command=self.delete_user).pack(pady=25, padx=20, fill="x")

        # === لوحة عرض المستخدمين (اليسار) ===
        view_frame = ctk.CTkFrame(self)
        view_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        # جدول عرض المستخدمين
        columns = ("id", "username", "role", "phone")
        self.tree = ttk.Treeview(view_frame, columns=columns, show="headings")
        self.tree.heading("id", text="الرقم")
        self.tree.heading("username", text="اسم المستخدم")
        self.tree.heading("role", text="الصلاحية")
        self.tree.heading("phone", text="الهاتف")
        
        # تنسيق عرض الأعمدة
        self.tree.column("id", width=50, anchor="center")
        self.tree.column("username", width=150, anchor="center")
        self.tree.column("role", width=100, anchor="center")
        self.tree.column("phone", width=150, anchor="center")
        
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        # ربط حدث النقر على الجدول بدالة استدعاء البيانات
        self.tree.bind('<ButtonRelease-1>', self.on_tree_select)

        # تهيئة قاعدة البيانات وعرض البيانات
        self.setup_db()
        self.load_users()

    # ================= الدوال البرمجية ================= #

    def setup_db(self):
        """إنشاء جدول المستخدمين إذا لم يكن موجوداً"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                phone TEXT
            )
        ''')
        # إضافة مستخدم مدير افتراضي إذا كان الجدول فارغاً
        cursor.execute("SELECT COUNT(*) FROM Users")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO Users (username, password, role) VALUES ('admin', 'admin', 'مدير')")
        
        conn.commit()
        conn.close()

    def load_users(self):
        """جلب بيانات المستخدمين وعرضها في الجدول"""
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, role, phone FROM Users")
        rows = cursor.fetchall()
        for row in rows:
            self.tree.insert("", "end", values=row)
        conn.close()

    def save_user(self):
        """إضافة مستخدم جديد أو تعديل مستخدم حالي"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        phone = self.phone_entry.get().strip()
        role = self.role_var.get()

        if not username:
            messagebox.showwarning("تنبيه", "اسم المستخدم مطلوب!")
            return

        conn = get_connection()
        cursor = conn.cursor()

        try:
            if self.selected_user_id is None:
                # إضافة مستخدم جديد
                if not password:
                    messagebox.showwarning("تنبيه", "كلمة المرور مطلوبة للمستخدم الجديد!")
                    conn.close()
                    return
                cursor.execute("INSERT INTO Users (username, password, role, phone) VALUES (?, ?, ?, ?)",
                               (username, password, role, phone))
                messagebox.showinfo("نجاح", "تمت إضافة المستخدم بنجاح.")
            else:
                # تعديل مستخدم موجود
                if password:
                    cursor.execute("UPDATE Users SET username=?, password=?, role=?, phone=? WHERE id=?",
                                   (username, password, role, phone, self.selected_user_id))
                else:
                    cursor.execute("UPDATE Users SET username=?, role=?, phone=? WHERE id=?",
                                   (username, role, phone, self.selected_user_id))
                messagebox.showinfo("نجاح", "تم تعديل بيانات المستخدم بنجاح.")
                
            conn.commit()
            self.clear_inputs()
            self.load_users()
            
        except sqlite3.IntegrityError:
            messagebox.showerror("خطأ", "اسم المستخدم موجود مسبقاً، يرجى اختيار اسم آخر.")
        finally:
            conn.close()

    def delete_user(self):
        """حذف المستخدم المحدد"""
        if self.selected_user_id is None:
            messagebox.showwarning("تنبيه", "يرجى تحديد مستخدم من الجدول أولاً!")
            return
            
        if messagebox.askyesno("تأكيد الحذف", "هل أنت متأكد من حذف هذا المستخدم؟ لا يمكن التراجع عن هذا الإجراء."):
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Users WHERE id=?", (self.selected_user_id,))
            conn.commit()
            conn.close()
            
            messagebox.showinfo("نجاح", "تم حذف المستخدم بنجاح.")
            self.clear_inputs()
            self.load_users()

    def on_tree_select(self, event):
        """جلب بيانات المستخدم عند النقر عليه في الجدول لتعديلها"""
        selected_item = self.tree.focus()
        if not selected_item:
            return
            
        values = self.tree.item(selected_item, "values")
        self.selected_user_id = values[0]
        
        self.clear_inputs(clear_id=False)
        self.username_entry.insert(0, values[1])
        self.role_var.set(values[2])
        if values[3] != 'None' and values[3] != '':
            self.phone_entry.insert(0, values[3])

    def clear_inputs(self, clear_id=True):
        """تفريغ جميع حقول الإدخال"""
        self.username_entry.delete(0, 'end')
        self.password_entry.delete(0, 'end')
        self.phone_entry.delete(0, 'end')
        self.role_var.set("كاشير")
        
        if clear_id:
            self.selected_user_id = None

if __name__ == "__main__":
    app = UsersWindow()
    app.mainloop()