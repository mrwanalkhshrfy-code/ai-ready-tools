import customtkinter as ctk
from tkinter import ttk, messagebox
import sqlite3
import os
from datetime import datetime
from tkcalendar import DateEntry  # استيراد أداة التقويم

# استدعاء دالة الاتصال الموحدة ودالة المسار من db_config
from db_config import get_db_path, get_connection

class PurchasesWindow(ctk.CTkToplevel):
    def __init__(self, user_info):
        super().__init__()
        self.user_info = user_info  
        
        # التأكد من قاعدة البيانات
        self.ensure_database_schema()
        
        self.title("إدارة المشتريات وتوريد البضائع")
        self.geometry("1200x750")
        
        self.grab_set()
        self.focus()

        self.current_total_amount = 0.0
        self.cat_list = []

        # --- العنوان ---
        self.lbl_title = ctk.CTkLabel(self, text="لوحة إدارة المشتريات وتوريد المخزون", font=("Arial", 26, "bold"))
        self.lbl_title.pack(pady=10)

        # --- الحاوية الرئيسية ---
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=10)

        # تجهيز الواجهات
        self.setup_left_panel()
        self.setup_right_panel() 
        
        self.load_categories()
        self.load_inventory_data()
        self.load_suppliers()   

    def setup_left_panel(self):
        """اللوحة اليسرى: لإدخال المواد"""
        self.left_panel = ctk.CTkFrame(self.main_container, width=500)
        self.left_panel.pack(side="left", fill="both", expand=True, padx=10)

        ctk.CTkLabel(self.left_panel, text="تفاصيل الصنف للتوريد", font=("Arial", 18, "bold"), text_color="#3498db").pack(pady=10)

        self.entry_barcode = ctk.CTkEntry(self.left_panel, placeholder_text="باركود الصنف (اضغط Enter للبحث)", justify="right")
        self.entry_barcode.pack(pady=5, padx=20, fill="x")
        self.entry_barcode.bind("<Return>", self.fetch_product_by_barcode)

        self.entry_name = ctk.CTkEntry(self.left_panel, placeholder_text="اسم المنتج", justify="right")
        self.entry_name.pack(pady=5, padx=20, fill="x")

        self.combo_category = ctk.CTkComboBox(self.left_panel, values=["عام"], justify="right")
        self.combo_category.pack(pady=5, padx=20, fill="x")

        prices_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        prices_frame.pack(pady=5, padx=20, fill="x")
        
        self.entry_cost = ctk.CTkEntry(prices_frame, placeholder_text="سعر الشراء", justify="right")
        self.entry_cost.pack(side="left", fill="x", expand=True, padx=2)

        self.entry_sell = ctk.CTkEntry(prices_frame, placeholder_text="سعر البيع", justify="right")
        self.entry_sell.pack(side="right", fill="x", expand=True, padx=2)

        self.entry_qty = ctk.CTkEntry(self.left_panel, placeholder_text="الكمية الموردة", justify="right")
        self.entry_qty.pack(pady=5, padx=20, fill="x")

        # --- إطار تواريخ الإنتاج والانتهاء ---
        dates_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        dates_frame.pack(pady=10, padx=20, fill="x")

        self.entry_prod_date = DateEntry(
            dates_frame, 
            width=15, 
            background='#3498db', 
            foreground='white', 
            borderwidth=2,
            date_pattern='y-mm-dd',
            maxdate=datetime.now().date(),
            justify="center",
            font=('Arial', 12)
        )
        self.entry_prod_date.pack(side="right", fill="x", expand=True, padx=2, ipady=4)
        
        ctk.CTkLabel(dates_frame, text="تاريخ الإنتاج", font=("Arial", 10)).pack(side="right", before=self.entry_prod_date)
        
        self.combo_exp_date = ctk.CTkComboBox(dates_frame, values=["شهر", "شهرين", "6 أشهر", "سنة", "سنتين", "3 سنوات", "بدون انتهاء"], justify="center")
        self.combo_exp_date.set("سنة")
        self.combo_exp_date.pack(side="left", fill="x", expand=True, padx=2)
        
        ctk.CTkLabel(self.left_panel, text="اختر المورد:", font=("Arial", 12)).pack(pady=(5, 0), padx=20, anchor="e")
        self.combo_supplier = ctk.CTkComboBox(self.left_panel, values=["جاري التحميل..."], justify="right")
        self.combo_supplier.pack(pady=5, padx=20, fill="x")
        ctk.CTkLabel(dates_frame, text="مدة الصلاحية", font=("Arial", 10)).pack(side="left", before=self.combo_exp_date) 
        
        receiver_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        receiver_frame.pack(pady=5, padx=20, fill="x")
        
        # --- إطار اختيار نوع الدفع ---
        payment_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        payment_frame.pack(pady=10, padx=20, fill="x")

        ctk.CTkLabel(payment_frame, text="طريقة الدفع:", font=("Arial", 12)).pack(side="right", padx=5)

        self.payment_var = ctk.StringVar(value="نقدي")

        self.radio_cash = ctk.CTkRadioButton(payment_frame, text="نقدي", variable=self.payment_var, value="نقدي")
        self.radio_cash.pack(side="right", padx=10)

        self.radio_credit = ctk.CTkRadioButton(payment_frame, text="آجل", variable=self.payment_var, value="آجل")
        self.radio_credit.pack(side="right", padx=10)
        
        ctk.CTkLabel(receiver_frame, text="المستلم الحالي:", font=("Arial", 12, "bold")).pack(side="right", padx=5)
        self.entry_receiver = ctk.CTkEntry(receiver_frame, justify="center", fg_color="#e0e0e0", text_color="#2c3e50")
        self.entry_receiver.insert(0, self.user_info.get("username", "غير معروف"))
        self.entry_receiver.configure(state="readonly")
        self.entry_receiver.pack(side="left", fill="x", expand=True)

        self.btn_add_item = ctk.CTkButton(self.left_panel, text="إضافة للفاتورة الحالية ➕", fg_color="#2ecc71", hover_color="#27ae60", command=self.add_item_to_temp_list)
        self.btn_add_item.pack(pady=10, padx=20, fill="x")

        self.btn_save_invoice = ctk.CTkButton(self.left_panel, text="حفظ الفاتورة وتوريدها للمخزن 💾", fg_color="#3498db", hover_color="#2980b9", font=("Arial", 14, "bold"), command=self.save_purchase_invoice)
        self.btn_save_invoice.pack(pady=10, padx=20, fill="x")

        self.btn_return_invoice = ctk.CTkButton(self.left_panel, text="إرجاع الأصناف للمورد 📤", fg_color="#e74c3c", hover_color="#c0392b", font=("Arial", 14, "bold"), command=self.save_purchase_return)
        self.btn_return_invoice.pack(pady=(0, 10), padx=20, fill="x")
        
        # جدول الفاتورة المؤقتة
        self.temp_tree = ttk.Treeview(self.left_panel, columns=("total", "qty", "sell", "cost", "name", "barcode", "prod_date", "exp_date"), show="headings", height=8)
        self.temp_tree.heading("total", text="الإجمالي")
        self.temp_tree.heading("qty", text="الكمية")
        self.temp_tree.heading("sell", text="البيع")
        self.temp_tree.heading("cost", text="الشراء")
        self.temp_tree.heading("name", text="الاسم")
        self.temp_tree.heading("barcode", text="الباركود")
        self.temp_tree.heading("prod_date", text="الإنتاج")
        self.temp_tree.heading("exp_date", text="الانتهاء")
        
        for col in ("total", "qty", "sell", "cost", "name", "barcode", "prod_date", "exp_date"):
            width = 50 if col in ("qty", "prod_date", "exp_date") else 70
            self.temp_tree.column(col, anchor="center", width=width)
        self.temp_tree.pack(fill="both", expand=True, padx=20, pady=5)

    def setup_right_panel(self):
        """اللوحة اليمنى: لعرض المنتجات"""
        self.right_panel = ctk.CTkFrame(self.main_container)
        self.right_panel.pack(side="right", fill="both", expand=True, padx=10)

        ctk.CTkLabel(self.right_panel, text="عرض المنتجات المتوفرة بالمخازن", font=("Arial", 18, "bold"), text_color="#e67e22").pack(pady=10)

        self.entry_search = ctk.CTkEntry(self.right_panel, placeholder_text="ابحث باسم المنتج أو الباركود...", justify="right")
        self.entry_search.pack(pady=5, padx=20, fill="x")
        self.entry_search.bind("<KeyRelease>", self.search_inventory)

        self.inventory_tree = ttk.Treeview(self.right_panel, columns=("stock", "sell", "cost", "cat", "name", "barcode"), show="headings")
        self.inventory_tree.heading("stock", text="الكمية المتاحة")
        self.inventory_tree.heading("sell", text="سعر البيع")
        self.inventory_tree.heading("cost", text="سعر الشراء")
        self.inventory_tree.heading("cat", text="القسم")
        self.inventory_tree.heading("name", text="اسم المنتج")
        self.inventory_tree.heading("barcode", text="الباركود")

        for col in ("stock", "sell", "cost", "cat", "name", "barcode"):
            self.inventory_tree.column(col, anchor="center", width=80)
        
        self.inventory_tree.pack(fill="both", expand=True, padx=20, pady=10)
        self.inventory_tree.bind("<Double-1>", self.fill_form_from_click)

    def fetch_product_by_barcode(self, event=None):
        barcode = self.entry_barcode.get().strip()
        if not barcode: return

        try:
            conn = get_connection()
            cursor = conn.cursor()
            query = """
                SELECT p.name, c.name, p.cost_price, p.sell_price
                FROM Products p 
                LEFT JOIN Categories c ON p.category_id = c.id 
                WHERE p.barcode = ?
            """
            cursor.execute(query, (barcode,))
            row = cursor.fetchone()
            conn.close()

            if row:
                name, cat_name, cost, sell = row
                self.entry_name.delete(0, 'end')
                self.entry_name.insert(0, name)

                cat_name = cat_name if cat_name else "عام"
                if cat_name in self.cat_list:
                    self.combo_category.set(cat_name)
                else:
                    self.combo_category.set("عام")

                self.entry_cost.delete(0, 'end')
                self.entry_cost.insert(0, str(cost))
                self.entry_sell.delete(0, 'end')
                self.entry_sell.insert(0, str(sell))
                self.entry_qty.focus()
            else:
                self.entry_name.delete(0, 'end')
                self.entry_cost.delete(0, 'end')
                self.entry_sell.delete(0, 'end')
                self.combo_category.set("عام")
                self.entry_name.focus()
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ أثناء البحث: {e}")

    def load_categories(self):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM Categories")
            rows = cursor.fetchall()
            conn.close()
            self.cat_list = [row[0] for row in rows]
            if not self.cat_list:
                self.cat_list = ["عام"]
            self.combo_category.configure(values=self.cat_list)
            self.combo_category.set(self.cat_list[0])
        except Exception as e:
            self.combo_category.configure(values=["عام"])
            self.combo_category.set("عام")

    def load_inventory_data(self, search_term=""):
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)
        try:
            conn = get_connection()
            cursor = conn.cursor()
            if search_term:
                query = """
                    SELECT p.barcode, p.name, c.name, p.cost_price, p.sell_price, p.stock_quantity 
                    FROM Products p 
                    LEFT JOIN Categories c ON p.category_id = c.id
                    WHERE p.name LIKE ? OR p.barcode LIKE ?
                """
                cursor.execute(query, (f"%{search_term}%", f"%{search_term}%"))
            else:
                query = """
                    SELECT p.barcode, p.name, c.name, p.cost_price, p.sell_price, p.stock_quantity 
                    FROM Products p 
                    LEFT JOIN Categories c ON p.category_id = c.id
                """
                cursor.execute(query)
            rows = cursor.fetchall()
            conn.close()

            for row in rows:
                barcode, name, cat_name, cost, sell, stock = row
                cat_name = cat_name if cat_name else "عام"
                stock_val = stock if stock is not None else 0
                self.inventory_tree.insert("", "end", values=(str(stock_val), f"{sell:.2f}", f"{cost:.2f}", cat_name, name, barcode))
        except Exception as e:
            pass

    def search_inventory(self, event=None):
        search_term = self.entry_search.get().strip()
        self.load_inventory_data(search_term)

    def fill_form_from_click(self, event=None):
        selected = self.inventory_tree.focus()
        if not selected: return
        values = self.inventory_tree.item(selected, 'values')
        if values:
            self.entry_barcode.delete(0, 'end')
            self.entry_barcode.insert(0, values[5])
            self.entry_name.delete(0, 'end')
            self.entry_name.insert(0, values[4])
            cat_name = values[3]
            if cat_name in self.cat_list:
                self.combo_category.set(cat_name)
            self.entry_cost.delete(0, 'end')
            self.entry_cost.insert(0, values[2])
            self.entry_sell.delete(0, 'end')
            self.entry_sell.insert(0, values[1])
            self.entry_qty.focus()

    def calculate_expiry(self, prod_date_str, duration_str):
        if duration_str == "بدون انتهاء": return ""
        try:
            prod_date = datetime.strptime(prod_date_str, "%Y-%m-%d")
            months_to_add = 0
            
            if duration_str == "شهر": months_to_add = 1
            elif duration_str == "شهرين": months_to_add = 2
            elif duration_str == "6 أشهر": months_to_add = 6
            elif duration_str == "سنة": months_to_add = 12
            elif duration_str == "سنتين": months_to_add = 24
            elif duration_str == "3 سنوات": months_to_add = 36

            month = prod_date.month - 1 + months_to_add
            year = prod_date.year + month // 12
            month = month % 12 + 1
            day = min(prod_date.day, [31,29 if year%4==0 and not year%100==0 or year%400==0 else 28,31,30,31,30,31,31,30,31,30,31][month-1])
            
            exp_date = datetime(year, month, day)
            return exp_date.strftime("%Y-%m-%d")
        except:
            return ""

    def add_item_to_temp_list(self):
        barcode = self.entry_barcode.get().strip()
        name = self.entry_name.get().strip()
        category = self.combo_category.get()
        cost_str = self.entry_cost.get()
        sell_str = self.entry_sell.get()
        qty_str = self.entry_qty.get()
        
        prod_date_str = self.entry_prod_date.get()
        exp_duration = self.combo_exp_date.get()

        if not barcode or not name or not cost_str or not sell_str or not qty_str or not prod_date_str:
            messagebox.showerror("خطأ", "الرجاء تعبئة جميع الحقول!")
            return

        try:
            prod_date_obj = datetime.strptime(prod_date_str, "%Y-%m-%d")
            if prod_date_obj.date() > datetime.now().date():
                messagebox.showerror("خطأ", "لا يمكن أن يكون تاريخ الإنتاج في المستقبل!")
                return
        except ValueError:
            messagebox.showerror("خطأ", "تاريخ غير صالح!")
            return

        try:
            cost = float(cost_str)
            sell = float(sell_str)
            qty = int(qty_str)
        except ValueError:
            messagebox.showerror("خطأ", "الأسعار والكميات يجب أن تكون أرقام!")
            return

        total = cost * qty
        exp_date_str = self.calculate_expiry(prod_date_str, exp_duration)

        for item in self.temp_tree.get_children():
            val = self.temp_tree.item(item, 'values')
            if val[5] == barcode:
                self.temp_tree.delete(item)

        self.temp_tree.insert("", "end", values=(f"{total:.2f}", str(qty), f"{sell:.2f}", f"{cost:.2f}", name, barcode, prod_date_str, exp_date_str))
        
        self.entry_barcode.delete(0, 'end')
        self.entry_name.delete(0, 'end')
        self.entry_cost.delete(0, 'end')
        self.entry_sell.delete(0, 'end')
        self.entry_qty.delete(0, 'end')
        self.entry_barcode.focus()

    def save_purchase_invoice(self):
        temp_items = self.temp_tree.get_children()
        if not temp_items:
            messagebox.showwarning("تنبيه", "الفاتورة فارغة!")
            return

        supplier_name = self.combo_supplier.get() 
        payment_type = self.payment_var.get()
        
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM Suppliers WHERE name = ?", (supplier_name,))
            s_row = cursor.fetchone()
            supplier_id = s_row[0] if s_row else None

            total_invoice_cost = 0.0
            items_to_process = []
            for item in temp_items:
                val = self.temp_tree.item(item, 'values')
                total_invoice_cost += float(val[0])
                items_to_process.append(val)

            cursor.execute("""
                INSERT INTO Purchase_Invoices (supplier_id, total_amount, total_cost, receiver_name, payment_type) 
                VALUES (?, ?, ?, ?, ?)
            """, (supplier_id, total_invoice_cost, total_invoice_cost, self.entry_receiver.get(), payment_type))
            
            if payment_type == "آجل" and supplier_id:
                cursor.execute("UPDATE Suppliers SET balance = balance + ? WHERE id = ?", (total_invoice_cost, supplier_id))

            for val in items_to_process:
                total, qty, sell, cost, name, barcode, prod_date, exp_date = val
                qty = int(qty)
                sell = float(sell)
                cost = float(cost)

                cursor.execute("SELECT id, stock_quantity FROM Products WHERE barcode = ?", (barcode,))
                product = cursor.fetchone()

                if product:
                    product_id, current_stock = product
                    new_stock = (current_stock if current_stock else 0) + qty
                    cursor.execute("""
                        UPDATE Products 
                        SET name = ?, cost_price = ?, sell_price = ?, stock_quantity = ?, production_date = ?, expiry_date = ?
                        WHERE id = ?
                    """, (name, cost, sell, new_stock, prod_date, exp_date, product_id))
                else:
                    cursor.execute("SELECT id FROM Categories WHERE name = ?", (self.combo_category.get(),))
                    cat_res = cursor.fetchone()
                    cat_id = cat_res[0] if cat_res else None
                    
                    cursor.execute("""
                        INSERT INTO Products (barcode, name, category_id, cost_price, sell_price, stock_quantity, production_date, expiry_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (barcode, name, cat_id, cost, sell, qty, prod_date, exp_date))

            conn.commit()
            conn.close()

            messagebox.showinfo("نجاح", "تم حفظ الفاتورة وتحديث المخزون وحساب المورد بنجاح!")
            
            for item in self.temp_tree.get_children():
                self.temp_tree.delete(item)
            
            self.load_inventory_data()

        except Exception as e:
            messagebox.showerror("خطأ", f"فشل الحفظ: {e}")

    def ensure_database_schema(self):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''CREATE TABLE IF NOT EXISTS Purchase_Invoices (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                date_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                                total_amount REAL NOT NULL,
                                total_cost REAL DEFAULT 0.0,
                                receiver_name TEXT NOT NULL)''')
                                
            cursor.execute("CREATE TABLE IF NOT EXISTS Categories (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL)")
            
            cursor.execute('''CREATE TABLE IF NOT EXISTS Products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                barcode TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                category_id INTEGER,
                cost_price REAL,
                sell_price REAL,
                stock_quantity INTEGER,
                FOREIGN KEY(category_id) REFERENCES Categories(id)
            )''')
            
            cursor.execute("PRAGMA table_info(Products)")
            columns = [info[1] for info in cursor.fetchall()]
            
            if 'category_id' not in columns: cursor.execute("ALTER TABLE Products ADD COLUMN category_id INTEGER")
            if 'production_date' not in columns: cursor.execute("ALTER TABLE Products ADD COLUMN production_date TEXT")
            if 'expiry_date' not in columns: cursor.execute("ALTER TABLE Products ADD COLUMN expiry_date TEXT")
                
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Database update error: {e}")

    def load_suppliers(self):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM Suppliers")
            rows = cursor.fetchall()
            conn.close()
        
            supplier_names = [row[0] for row in rows]
        
            if not supplier_names:
                supplier_names = ["لا يوجد موردين"]
            
            self.combo_supplier.configure(values=supplier_names)
            self.combo_supplier.set(supplier_names[0])
        
        except Exception as e:
            print(f"خطأ في تحميل الموردين: {e}") 

    def save_purchase_return(self):
        temp_items = self.temp_tree.get_children()
        if not temp_items:
            messagebox.showwarning("تنبيه", "قائمة الأصناف فارغة!")
            return

        supplier_name = self.combo_supplier.get() 
        payment_type = self.payment_var.get()
        
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM Suppliers WHERE name = ?", (supplier_name,))
            s_row = cursor.fetchone()
            supplier_id = s_row[0] if s_row else None

            items_to_process = []
            total_return_amount = 0.0
            
            for item in temp_items:
                val = self.temp_tree.item(item, 'values')
                total_return_amount += float(val[0])
                items_to_process.append(val)
                
                barcode = val[5]
                qty_to_return = int(val[1])
                name = val[4]
                
                cursor.execute("SELECT stock_quantity FROM Products WHERE barcode = ?", (barcode,))
                product = cursor.fetchone()
                
                if not product or (product[0] is None) or (product[0] < qty_to_return):
                    messagebox.showerror("خطأ في المخزون", f"الكمية المتاحة من الصنف '{name}' لا تكفي لعملية الإرجاع!")
                    conn.close()
                    return

            cursor.execute("""
                INSERT INTO Purchase_Returns (supplier_id, total_amount, receiver_name, payment_type) 
                VALUES (?, ?, ?, ?)
            """, (supplier_id, total_return_amount, self.entry_receiver.get(), payment_type))
            
            if payment_type == "آجل" and supplier_id:
                cursor.execute("UPDATE Suppliers SET balance = balance - ? WHERE id = ?", (total_return_amount, supplier_id))

            for val in items_to_process:
                qty_to_return = int(val[1])
                barcode = val[5]

                cursor.execute("""
                    UPDATE Products 
                    SET stock_quantity = stock_quantity - ?
                    WHERE barcode = ?
                """, (qty_to_return, barcode))

            conn.commit()
            conn.close()

            messagebox.showinfo("نجاح", "تم إرجاع البضاعة للمورد، وخصم الكميات من المخزون، وتحديث الحساب بنجاح!")
            
            for item in self.temp_tree.get_children():
                self.temp_tree.delete(item)
            
            self.load_inventory_data()

        except Exception as e:
            messagebox.showerror("خطأ", f"فشل عملية الإرجاع: {e}")