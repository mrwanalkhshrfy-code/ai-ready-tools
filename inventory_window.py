import customtkinter as ctk
from tkinter import ttk, messagebox
import sqlite3
import os
from datetime import datetime
from tkcalendar import DateEntry
import csv

# استدعاء دالة الاتصال الموحدة من db_config
from db_config import get_db_path, get_connection

class InventoryWindow(ctk.CTkToplevel):
    def __init__(self):
        super().__init__()
        
        self.title("إدارة المخزون والتنبيهات")
        self.geometry("1200x750")
        self.grab_set()
        self.focus()

        self.cat_list = []
        self.cat_dict = {} # للربط بين اسم القسم والـ ID الخاص به

        # --- العنوان ---
        self.lbl_title = ctk.CTkLabel(self, text="نظام إدارة المخزون والمراقبة", font=("Arial", 26, "bold"))
        self.lbl_title.pack(pady=10)

        # --- الحاوية الرئيسية ---
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=10)

        self.setup_left_panel()  
        self.setup_right_panel() 
        
        self.load_categories()
        self.load_all_data()

    def setup_left_panel(self):
        """لوحة التحكم: إضافة، تعديل، وحذف"""
        self.left_panel = ctk.CTkFrame(self.main_container, width=350)
        self.left_panel.pack(side="left", fill="y", padx=10)

        ctk.CTkLabel(self.left_panel, text="بيانات المنتج", font=("Arial", 18, "bold"), text_color="#3498db").pack(pady=15)

        # الحقول
        self.entry_barcode = ctk.CTkEntry(self.left_panel, placeholder_text="الباركود", justify="right")
        self.entry_barcode.pack(pady=5, padx=20, fill="x")

        self.entry_name = ctk.CTkEntry(self.left_panel, placeholder_text="اسم المنتج", justify="right")
        self.entry_name.pack(pady=5, padx=20, fill="x")

        self.combo_category = ctk.CTkComboBox(self.left_panel, values=["عام"], justify="right")
        self.combo_category.pack(pady=5, padx=20, fill="x")

        self.entry_qty = ctk.CTkEntry(self.left_panel, placeholder_text="الكمية المتوفرة", justify="right")
        self.entry_qty.pack(pady=5, padx=20, fill="x")

        prices_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        prices_frame.pack(pady=5, padx=20, fill="x")
        self.entry_cost = ctk.CTkEntry(prices_frame, placeholder_text="سعر الشراء", justify="right")
        self.entry_cost.pack(side="left", fill="x", expand=True, padx=2)
        self.entry_sell = ctk.CTkEntry(prices_frame, placeholder_text="سعر البيع", justify="right")
        self.entry_sell.pack(side="right", fill="x", expand=True, padx=2)

        # تواريخ
        dates_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        dates_frame.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(dates_frame, text="الإنتاج:", font=("Arial", 12)).grid(row=0, column=1, padx=5, sticky="e")
        self.entry_prod_date = DateEntry(dates_frame, width=12, background='#3498db', foreground='white', borderwidth=2, date_pattern='y-mm-dd')
        self.entry_prod_date.grid(row=0, column=0, padx=5, pady=5)

        ctk.CTkLabel(dates_frame, text="الانتهاء:", font=("Arial", 12)).grid(row=1, column=1, padx=5, sticky="e")
        self.entry_exp_date = DateEntry(dates_frame, width=12, background='#e74c3c', foreground='white', borderwidth=2, date_pattern='y-mm-dd')
        self.entry_exp_date.grid(row=1, column=0, padx=5, pady=5)

        # أزرار التحكم
        buttons_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        buttons_frame.pack(pady=20, padx=20, fill="x")

        self.btn_add = ctk.CTkButton(buttons_frame, text="إضافة منتج", fg_color="#2ecc71", hover_color="#27ae60", command=self.add_product)
        self.btn_add.pack(pady=5, fill="x")

        self.btn_edit = ctk.CTkButton(buttons_frame, text="تعديل المنتج", fg_color="#f39c12", hover_color="#d35400", command=self.edit_product)
        self.btn_edit.pack(pady=5, fill="x")
        
        self.btn_print = ctk.CTkButton(buttons_frame, text="طباعة التقرير 🖨️", fg_color="#34495e", hover_color="#2c3e50", command=self.print_inventory_report)
        self.btn_print.pack(pady=5, fill="x")
        
        self.btn_delete = ctk.CTkButton(buttons_frame, text="حذف المنتج", fg_color="#e74c3c", hover_color="#c0392b", command=self.delete_product)
        self.btn_delete.pack(pady=5, fill="x")

        self.btn_clear = ctk.CTkButton(buttons_frame, text="تفريغ الحقول", fg_color="#7f8c8d", hover_color="#95a5a6", command=self.clear_fields)
        self.btn_clear.pack(pady=5, fill="x")

    def setup_right_panel(self):
        """اللوحة اليمنى: نظام التبويبات لعرض البيانات والتنبيهات"""
        self.right_panel = ctk.CTkFrame(self.main_container)
        self.right_panel.pack(side="right", fill="both", expand=True, padx=10)

        # التبويبات (Tabs)
        self.tabview = ctk.CTkTabview(self.right_panel)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_inventory = self.tabview.add("قائمة المخزون")
        self.tab_low_stock = self.tabview.add("تنبيهات النواقص ⚠️")
        self.tab_expiry = self.tabview.add("تنبيهات الصلاحية ⏳")

        # --- تبويب المخزون ---
        self.entry_search = ctk.CTkEntry(self.tab_inventory, placeholder_text="ابحث بالاسم أو الباركود...", justify="right")
        self.entry_search.pack(pady=5, fill="x")
        self.entry_search.bind("<KeyRelease>", lambda e: self.load_inventory_data(self.entry_search.get()))

        self.tree_inv = self.create_treeview(self.tab_inventory, ("الانتهاء", "الإنتاج", "الكمية", "البيع", "الشراء", "القسم", "الاسم", "الباركود"))
        self.tree_inv.bind("<Double-1>", self.fill_form_from_click)

        # --- تبويب النواقص ---
        ctk.CTkLabel(self.tab_low_stock, text="المنتجات التي أوشكت على النفاذ (الكمية 10 أو أقل)", text_color="#e74c3c", font=("Arial", 14, "bold")).pack(pady=5)
        self.tree_low_stock = self.create_treeview(self.tab_low_stock, ("الكمية المتبقية", "القسم", "الاسم", "الباركود"))

        # --- تبويب الصلاحية ---
        ctk.CTkLabel(self.tab_expiry, text="المنتجات المنتهية أو التي ستنتهي خلال 30 يوماً", text_color="#e74c3c", font=("Arial", 14, "bold")).pack(pady=5)
        self.tree_expiry = self.create_treeview(self.tab_expiry, ("تاريخ الانتهاء", "الكمية", "القسم", "الاسم", "الباركود"))

    def create_treeview(self, parent, columns):
        """دالة مساعدة لإنشاء الجداول بسرعة"""
        cols_ids = [f"col_{i}" for i in range(len(columns))]
        tree = ttk.Treeview(parent, columns=cols_ids, show="headings")
        
        for i, col_name in enumerate(columns):
            tree.heading(cols_ids[i], text=col_name)
            tree.column(cols_ids[i], anchor="center", width=100)
            
        tree.pack(fill="both", expand=True, pady=5)
        return tree

    def load_categories(self):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM Categories")
            rows = cursor.fetchall()
            conn.close()
            
            self.cat_dict = {row[1]: row[0] for row in rows}
            self.cat_list = list(self.cat_dict.keys())
            
            if not self.cat_list:
                self.cat_list = ["عام"]
                self.cat_dict = {"عام": 1}
                
            self.combo_category.configure(values=self.cat_list)
            self.combo_category.set(self.cat_list[0])
        except Exception as e:
            print(f"Error loading categories: {e}")

    def load_all_data(self):
        """تحميل جميع البيانات والجداول"""
        self.load_inventory_data()
        self.load_low_stock_alerts()
        self.load_expiry_alerts()

    def load_inventory_data(self, search_term=""):
        for item in self.tree_inv.get_children(): 
            self.tree_inv.delete(item)
        try:
            conn = get_connection()
            cursor = conn.cursor()
            query = """
                SELECT p.expiry_date, p.production_date, p.stock_quantity, p.sell_price, p.cost_price, c.name, p.name, p.barcode
                FROM Products p LEFT JOIN Categories c ON p.category_id = c.id
            """
            if search_term:
                query += " WHERE p.name LIKE ? OR p.barcode LIKE ?"
                cursor.execute(query, (f"%{search_term}%", f"%{search_term}%"))
            else:
                cursor.execute(query)

            for row in cursor.fetchall():
                self.tree_inv.insert("", "end", values=row)
            conn.close()
        except Exception as e:
            print(f"Error loading inventory: {e}")

    def load_low_stock_alerts(self):
        """جلب البضائع التي كميتها أقل من 10"""
        for item in self.tree_low_stock.get_children(): 
            self.tree_low_stock.delete(item)
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.stock_quantity, c.name, p.name, p.barcode
                FROM Products p LEFT JOIN Categories c ON p.category_id = c.id
                WHERE p.stock_quantity <= 10
            """)
            for row in cursor.fetchall():
                self.tree_low_stock.insert("", "end", values=row)
            conn.close()
        except Exception as e:
            print(f"Error loading low stock: {e}")

    def load_expiry_alerts(self):
        """جلب البضائع التي ستنتهي صلاحيتها خلال شهر"""
        for item in self.tree_expiry.get_children(): 
            self.tree_expiry.delete(item)
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.expiry_date, p.stock_quantity, c.name, p.name, p.barcode
                FROM Products p LEFT JOIN Categories c ON p.category_id = c.id
                WHERE p.expiry_date IS NOT NULL AND p.expiry_date != '' 
                AND p.expiry_date <= date('now', '+30 days')
            """)
            for row in cursor.fetchall():
                self.tree_expiry.insert("", "end", values=row)
            conn.close()
        except Exception as e:
            print(f"Error loading expiry: {e}")

    def fill_form_from_click(self, event=None):
        selected = self.tree_inv.focus()
        if not selected: 
            return
        val = self.tree_inv.item(selected, 'values')
        if val:
            self.clear_fields()
            self.entry_barcode.insert(0, val[7])
            self.entry_name.insert(0, val[6])
            
            if val[5] in self.cat_list:
                self.combo_category.set(val[5])
                
            self.entry_cost.insert(0, val[4])
            self.entry_sell.insert(0, val[3])
            self.entry_qty.insert(0, val[2])
            
            if val[1]: 
                self.entry_prod_date.set_date(val[1])
            if val[0]: 
                self.entry_exp_date.set_date(val[0])
            
            self.entry_barcode.configure(state="disabled")

    def add_product(self):
        barcode = self.entry_barcode.get().strip()
        name = self.entry_name.get().strip()
        cat_id = self.cat_dict.get(self.combo_category.get(), 1)
        cost = self.entry_cost.get()
        sell = self.entry_sell.get()
        qty = self.entry_qty.get()
        p_date = self.entry_prod_date.get()
        e_date = self.entry_exp_date.get()

        if not barcode or not name:
            messagebox.showerror("خطأ", "الباركود والاسم مطلوبان!")
            return

        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Products (barcode, name, category_id, cost_price, sell_price, stock_quantity, production_date, expiry_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                           (barcode, name, cat_id, cost, sell, qty, p_date, e_date))
            conn.commit()
            conn.close()
            messagebox.showinfo("نجاح", "تمت إضافة المنتج بنجاح!")
            self.clear_fields()
            self.load_all_data()
        except sqlite3.IntegrityError:
            messagebox.showerror("خطأ", "هذا الباركود موجود مسبقاً في المستودع!")
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ: {e}")

    def edit_product(self):
        self.entry_barcode.configure(state="normal")
        barcode = self.entry_barcode.get().strip()
        
        if not barcode:
            messagebox.showwarning("تنبيه", "يرجى تحديد منتج من الجدول لتعديله.")
            return

        name = self.entry_name.get().strip()
        cat_id = self.cat_dict.get(self.combo_category.get(), 1)
        cost = self.entry_cost.get()
        sell = self.entry_sell.get()
        qty = self.entry_qty.get()
        p_date = self.entry_prod_date.get()
        e_date = self.entry_exp_date.get()

        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE Products 
                SET name=?, category_id=?, cost_price=?, sell_price=?, stock_quantity=?, production_date=?, expiry_date=?
                WHERE barcode=?
            """, (name, cat_id, cost, sell, qty, p_date, e_date, barcode))
            conn.commit()
            conn.close()
            messagebox.showinfo("نجاح", "تم التعديل بنجاح!")
            self.clear_fields()
            self.load_all_data()
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ أثناء التعديل: {e}")

    def delete_product(self):
        self.entry_barcode.configure(state="normal")
        barcode = self.entry_barcode.get().strip()
        
        if not barcode:
            messagebox.showwarning("تنبيه", "يرجى تحديد منتج من الجدول لحذفه.")
            return
            
        confirm = messagebox.askyesno("تأكيد الحذف", f"هل أنت متأكد من حذف المنتج ذو الباركود ({barcode})؟")
        if confirm:
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM Products WHERE barcode=?", (barcode,))
                conn.commit()
                conn.close()
                messagebox.showinfo("نجاح", "تم حذف المنتج.")
                self.clear_fields()
                self.load_all_data()
            except Exception as e:
                messagebox.showerror("خطأ", f"حدث خطأ أثناء الحذف: {e}")

    def clear_fields(self):
        self.entry_barcode.configure(state="normal")
        self.entry_barcode.delete(0, 'end')
        self.entry_name.delete(0, 'end')
        self.entry_cost.delete(0, 'end')
        self.entry_sell.delete(0, 'end')
        self.entry_qty.delete(0, 'end')
        
        self.entry_prod_date.set_date(datetime.now())
        self.entry_exp_date.set_date(datetime.now())

    def print_inventory_report(self):
        file_path = "inventory_report.csv"
        try:
            with open(file_path, mode='w', newline='', encoding='utf-8-sig') as file:
                writer = csv.writer(file)
                writer.writerow(["الانتهاء", "الإنتاج", "الكمية", "البيع", "الشراء", "القسم", "الاسم", "الباركود"])
                for item in self.tree_inv.get_children():
                    writer.writerow(self.tree_inv.item(item, 'values'))
            
            messagebox.showinfo("نجاح", "تم تصدير التقرير إلى ملف Excel بنجاح!")
            os.startfile(file_path)
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل التصدير: {e}")