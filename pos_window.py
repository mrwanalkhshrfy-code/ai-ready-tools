import customtkinter as ctk
from tkinter import ttk, messagebox
import sqlite3
import os
import customers_window
import inventory_window
import returns_window

# استدعاء دالة الاتصال الموحدة من db_config
from db_config import get_connection, get_db_path

class POSApp(ctk.CTkToplevel):
    def __init__(self, user_info):
        super().__init__()
        self.user_info = user_info
        self.title("نظام الكاشير - واجهة المبيعات")
        self.geometry("1200x700")

        # أوامر لضمان فتح الشاشة فوق الشاشة الرئيسية وتركيز الماوس عليها
        self.grab_set() 
        self.focus_force()
        self.attributes("-topmost", True)
        self.after(200, lambda: self.attributes("-topmost", False))

        # إعدادات التخطيط (RTL)
        self.grid_columnconfigure(0, weight=0) # اللوحة الجانبية
        self.grid_columnconfigure(1, weight=1) # منطقة الجدول
        self.grid_rowconfigure(0, weight=1)

        self.setup_ui()
        self.toggle_customer_entry()

    def setup_ui(self):
        # --- اللوحة الجانبية (يمين) ---
        self.side_panel = ctk.CTkFrame(self)
        self.side_panel.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(self.side_panel, text="الإجمالي الكلي", font=("Arial", 20, "bold")).pack(pady=10)
        self.total_label = ctk.CTkLabel(self.side_panel, text="0.00 ر.ي", font=("Arial", 40, "bold"), text_color="#2ecc71")
        self.total_label.pack(pady=(0, 20))
        
        self.payment_type = ctk.StringVar(value="نقد")
        self.payment_frame = ctk.CTkFrame(self.side_panel)
        self.payment_frame.pack(pady=10, padx=10, fill="x")
        
        ctk.CTkRadioButton(self.payment_frame, text="نقد", variable=self.payment_type, value="نقد", command=self.toggle_customer_entry).pack(side="left", padx=5)
        ctk.CTkRadioButton(self.payment_frame, text="آجل", variable=self.payment_type, value="آجل", command=self.toggle_customer_entry).pack(side="left", padx=5)
        ctk.CTkRadioButton(self.payment_frame, text="بنكي", variable=self.payment_type, value="بنكي", command=self.toggle_customer_entry).pack(side="left", padx=5)
        ctk.CTkRadioButton(self.payment_frame, text="دفع جزئي", variable=self.payment_type, value="جزئي", command=self.toggle_customer_entry).pack(side="left", padx=5)
        
        # --- إطار للبحث وزر الإضافة (العميل) ---
        self.cust_frame = ctk.CTkFrame(self.side_panel, fg_color="transparent")
        
        # نص توضيحي للعميل
        ctk.CTkLabel(self.cust_frame, text="اسم العميل:", font=("Arial", 12, "bold")).pack(anchor="e", padx=5)
        
        self.cust_inner_frame = ctk.CTkFrame(self.cust_frame, fg_color="transparent")
        self.cust_inner_frame.pack(fill="x")
        
        self.customer_entry = ttk.Combobox(self.cust_inner_frame, font=("Arial", 12))
        self.customer_entry.pack(side="right", fill="x", expand=True, padx=(0, 5))
        self.customer_entry.bind("<KeyRelease>", self.on_key_release)

        self.btn_add_cust = ctk.CTkButton(self.cust_inner_frame, text="+", width=30, command=self.open_add_customer)
        self.btn_add_cust.pack(side="right")
        # -----------------------------
        
        # حقل الخصم مع نص توضيحي
        ctk.CTkLabel(self.side_panel, text="الخصم (ر.ي):", font=("Arial", 12, "bold")).pack(anchor="e", padx=10, pady=(10, 0))
        self.discount_entry = ctk.CTkEntry(self.side_panel, placeholder_text="0.0")
        self.discount_entry.pack(pady=(2, 5), padx=10, fill="x")
        self.discount_entry.bind("<KeyRelease>", lambda event: self.update_total())
        
        # حقل المبلغ المدفوع مع نص توضيحي
        ctk.CTkLabel(self.side_panel, text="المبلغ المدفوع نقداً (ر.ي):", font=("Arial", 12, "bold")).pack(anchor="e", padx=10, pady=(10, 0))
        self.paid_amount_entry = ctk.CTkEntry(self.side_panel, placeholder_text="0.0")
        self.paid_amount_entry.pack(pady=(2, 5), padx=10, fill="x")
        
        # زر مدمج للحفظ والطباعة
        self.btn_checkout = ctk.CTkButton(self.side_panel, text="طباعة وحفظ الفاتورة 🖨️", fg_color="#27ae60", hover_color="#2ecc71", height=60, font=("Arial", 18, "bold"), command=self.print_and_save_invoice)
        self.btn_checkout.pack(pady=20, padx=10, fill="x")
      
        self.btn_returns = ctk.CTkButton(self.side_panel, text="مرتجع ", fg_color="#e69c13", hover_color="#df3907", height=60, font=("Arial", 18, "bold"), command=self.open_returns_window)
        self.btn_returns.pack(pady=25, padx=11, fill="x")
        
        # زر الإلغاء
        ctk.CTkButton(self.side_panel, text="إلغاء الفاتورة 🗑️", fg_color="#e74c3c", height=50, font=("Arial", 14, "bold"), command=self.clear_invoice).pack(pady=5, padx=10, fill="x")
        
        # --- منطقة الإدخال والجدول (يسار) ---
        self.main_panel = ctk.CTkFrame(self)
        self.main_panel.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        # حقول الإدخال مع النصوص التوضيحية
        ctk.CTkLabel(self.main_panel, text="باركود الصنف:", font=("Arial", 14, "bold")).pack(anchor="e", padx=20, pady=(10, 0))
        self.barcode_entry = ctk.CTkEntry(self.main_panel, placeholder_text="اضغط Enter للإضافة", justify="right", font=("Arial", 14))
        self.barcode_entry.pack(pady=(5, 10), padx=20, fill="x")
        self.barcode_entry.bind("<Return>", lambda event: self.add_to_cart())

        ctk.CTkLabel(self.main_panel, text="الكمية:", font=("Arial", 14, "bold")).pack(anchor="e", padx=20)
        self.qty_entry = ctk.CTkEntry(self.main_panel, placeholder_text="1", justify="right", font=("Arial", 14))
        self.qty_entry.pack(pady=(5, 10), padx=20, fill="x")
        self.qty_entry.insert(0, "1")

        # الجدول
        self.tree = ttk.Treeview(self.main_panel, columns=("total", "price", "qty", "name", "barcode"), displaycolumns=("total", "price", "qty", "name"), show="headings")
        self.tree.heading("name", text="اسم الصنف")
        self.tree.heading("qty", text="الكمية")
        self.tree.heading("price", text="السعر")
        self.tree.heading("total", text="الإجمالي")
        
        # تنسيق حجم الأعمدة
        self.tree.column("name", anchor="center", width=250)
        self.tree.column("qty", anchor="center", width=80)
        self.tree.column("price", anchor="center", width=100)
        self.tree.column("total", anchor="center", width=120)

        # ستايل الجدول
        style = ttk.Style()
        style.configure("Treeview", font=("Arial", 12), rowheight=35)
        style.configure("Treeview.Heading", font=("Arial", 14, "bold"))
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)

    def add_to_cart(self):
        barcode = self.barcode_entry.get().strip()
        qty_str = self.qty_entry.get() or "1"
        
        try:
            qty = int(qty_str)
        except ValueError:
            messagebox.showerror("خطأ", "الكمية يجب أن تكون رقماً صحيحاً!")
            return

        if qty <= 0:
            messagebox.showerror("خطأ", "الكمية يجب أن تكون أكبر من الصفر!")
            return

        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name, sell_price, stock_quantity FROM Products WHERE barcode = ?", (barcode,))
            product = cursor.fetchone()
            conn.close()

            if product:
                name, price, stock = product
                stock = stock if stock is not None else 0

                existing_qty = 0
                for item in self.tree.get_children():
                    values = self.tree.item(item, 'values')
                    if values[4] == barcode:  
                        existing_qty += int(values[2])

                total_requested = existing_qty + qty

                if total_requested > stock:
                    messagebox.showwarning("نفاد الكمية", f"عذراً! الكمية المتوفرة في المخزن ({stock}) لا تكفي لطلبك.")
                    return

                total = price * qty
                self.tree.insert("", 0, values=(total, price, qty, name, barcode))
                self.update_total()
                self.barcode_entry.delete(0, 'end')
                self.qty_entry.delete(0, 'end')
                self.qty_entry.insert(0, "1")
                self.barcode_entry.focus()
            else:
                messagebox.showerror("خطأ", "الصنف غير موجود في قاعدة البيانات!")
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ أثناء الاتصال بقاعدة البيانات: {e}")

    def update_total(self):
        subtotal = sum(float(self.tree.item(item, 'values')[0]) for item in self.tree.get_children())
        try:
            discount = float(self.discount_entry.get() or 0)
        except ValueError:
            discount = 0.0
            
        final_total = subtotal - discount
        self.total_label.configure(text=f"{final_total:.2f} ر.ي")
        
    def print_and_save_invoice(self):
        items = [self.tree.item(item, 'values') for item in self.tree.get_children()]
        if not items:
            messagebox.showwarning("تنبيه", "الفاتورة فارغة!")
            return

        subtotal = sum(float(item[0]) for item in items)
        try:
            discount = float(self.discount_entry.get() or 0)
        except ValueError:
            discount = 0.0
            
        total_amount = subtotal - discount

        try:
            paid_amount = float(self.paid_amount_entry.get() or 0)
        except ValueError:
            paid_amount = 0.0

        if self.payment_type.get() in ["نقد", "بنكي"]:
            paid_amount = total_amount
            
        remaining_amount = total_amount - paid_amount

        cashier = self.user_info.get('username', 'كاشير')
        payment = self.payment_type.get()
        cust_name = self.customer_entry.get() if payment not in ["نقد", "بنكي"] else "كاش"

        try:
            conn = get_connection()
            cursor = conn.cursor()

            cart_summary = {}
            for item in items:
                bcode = item[4]
                qty = int(item[2])
                cart_summary[bcode] = cart_summary.get(bcode, 0) + qty

            for bcode, req_qty in cart_summary.items():
                cursor.execute("SELECT name, stock_quantity FROM Products WHERE barcode = ?", (bcode,))
                res = cursor.fetchone()
                if not res:
                    messagebox.showerror("خطأ", f"أحد الأصناف (الباركود: {bcode}) لم يعد موجوداً!")
                    conn.close()
                    return
                name, stock = res
                stock = stock if stock is not None else 0
                
                if req_qty > stock:
                    messagebox.showerror("خطأ", f"فشل الحفظ! الكمية المتوفرة من '{name}' هي ({stock}) فقط.")
                    conn.close()
                    return
                 
            customer_id = None
            if payment not in ["نقد", "بنكي"] and cust_name != "كاش":
                cursor.execute("SELECT id FROM Customers WHERE name = ?", (cust_name,))
                result = cursor.fetchone()
                if result:
                    customer_id = result[0]

            # إدخال الفاتورة الرئيسية والحصول على رقمها
            cursor.execute("""
                INSERT INTO Invoices 
                (total_amount, payment_type, customer_phone, cashier_name, discount, paid_amount, remaining_amount, customer_id) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (total_amount, payment, cust_name, cashier, discount, paid_amount, remaining_amount, customer_id))
            invoice_id = cursor.lastrowid
            
            # إدخال تفاصيل الأصناف المباعة
            for item in items:
                sell_price_item = float(item[0])
                qty_item = int(item[2])
                bcode_item = item[4]
                
                cursor.execute("SELECT id, cost_price FROM Products WHERE barcode = ?", (bcode_item,))
                prod_data = cursor.fetchone()
                
                if prod_data:
                    prod_id, prod_cost = prod_data
                    prod_cost = prod_cost if prod_cost is not None else 0.0
                    
                    cursor.execute("""
                        INSERT INTO Invoice_Items (invoice_id, product_id, quantity, sell_price, cost_price)
                        VALUES (?, ?, ?, ?, ?)
                    """, (invoice_id, prod_id, qty_item, sell_price_item, prod_cost))
            
            if payment in ["آجل", "جزئي"]:
                if remaining_amount > 0:
                    cursor.execute("UPDATE Customers SET balance = balance + ? WHERE name = ?", (remaining_amount, cust_name))
                
                cursor.execute("INSERT INTO Credit_Transactions (customer_id, amount, type) VALUES ((SELECT id FROM Customers WHERE name=?), ?, 'sale')", (cust_name, remaining_amount))
            
            for bcode, req_qty in cart_summary.items():
                cursor.execute("UPDATE Products SET stock_quantity = stock_quantity - ? WHERE barcode = ?", (req_qty, bcode))

            conn.commit()
            conn.close()

            self.show_preview(items, total_amount, invoice_id, cust_name, payment, discount, paid_amount, remaining_amount)
            self.clear_invoice()

        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ غير متوقع: {e}")
            
    def execute_print(self, items, total_amount, invoice_id, cust_name, payment, discount, paid_amount, remaining_amount):
        try:
            import win32print
            import win32ui
            printer_name = win32print.GetDefaultPrinter()
            hDC = win32ui.CreateDC()
            hDC.CreatePrinterDC(printer_name)
            hDC.StartDoc("Invoice")
            hDC.StartPage()
            
            font = win32ui.CreateFont({"name": "Arial", "height": 22, "weight": 700})
            hDC.SelectObject(font)
            
            y = 20
            hDC.TextOut(150, y, "--- سوبر ماركت الاقصى ---")
            
            font_normal = win32ui.CreateFont({"name": "Arial", "height": 18, "weight": 400})
            hDC.SelectObject(font_normal)
            
            y += 40
            hDC.TextOut(50, y, f"رقم الفاتورة: {invoice_id}")
            y += 30
            hDC.TextOut(50, y, f"العميل: {cust_name}")
            hDC.TextOut(250, y, f"الدفع: {payment}")
            y += 30
            hDC.TextOut(50, y, "----------------------------------------------------")
            
            y += 30
            hDC.TextOut(50, y, "الصنف")
            hDC.TextOut(200, y, "السعر")
            hDC.TextOut(280, y, "الكمية")
            hDC.TextOut(350, y, "الإجمالي")
            
            y += 30
            hDC.TextOut(50, y, "----------------------------------------------------")
            
            for item in items:
                y += 30
                name_short = str(item[3])[:15]
                hDC.TextOut(50, y, name_short)
                hDC.TextOut(200, y, str(item[1]))
                hDC.TextOut(280, y, str(item[2]))
                hDC.TextOut(350, y, str(item[0]))
            
            y += 30
            hDC.TextOut(50, y, "----------------------------------------------------")
            
            y += 30
            hDC.TextOut(50, y, f"الخصم: {discount} ر.ي")
            y += 30
            
            font_bold = win32ui.CreateFont({"name": "Arial", "height": 20, "weight": 700})
            hDC.SelectObject(font_bold)
            hDC.TextOut(50, y, f"الإجمالي النهائي: {total_amount:.2f} ر.ي")
            
            y += 50
            hDC.SelectObject(font_normal)
            y += 30
            hDC.TextOut(50, y, f"المدفوع: {paid_amount:.2f} ر.ي")
            y += 30
            hDC.TextOut(50, y, f"المتبقي: {remaining_amount:.2f} ر.ي")
            
            y += 50
            font_normal = win32ui.CreateFont({"name": "Arial", "height": 18, "weight": 400})
            hDC.SelectObject(font_normal)
            hDC.TextOut(150, y, "شكراً لزيارتكم!")
            
            hDC.EndPage()
            hDC.EndDoc()
            hDC.DeleteDC()
        except Exception as e:
            messagebox.showwarning("تنبيه الطابعة", f"تم الحفظ وخصم المخزون، لكن تعذر الاتصال بالطابعة.\nالسبب: {e}")
            
    def clear_invoice(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        self.discount_entry.delete(0, 'end')
        self.paid_amount_entry.delete(0, 'end')
        self.customer_entry.set("")
        self.barcode_entry.delete(0, 'end')
        self.qty_entry.delete(0, 'end')
        self.qty_entry.insert(0, "1")
        
        self.payment_type.set("نقد")
        self.toggle_customer_entry()
        
        self.update_total()
        self.barcode_entry.focus()

    def toggle_customer_entry(self):
        if self.payment_type.get() not in ["نقد", "بنكي"]:
            self.cust_frame.pack(pady=5, padx=10, fill="x")
        else:
            self.cust_frame.pack_forget()

    def search_customer(self, event):
        if event.keysym == "Return":
            keyword = self.customer_entry.get()
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM Customers WHERE name = ?", (keyword,))
                customer = cursor.fetchone()
                conn.close()
                
                if not customer:
                    if messagebox.askyesno("عميل غير موجود", "العميل غير موجود، هل تريد إضافة عميل جديد؟"):
                        import customers_window1
                        win = customers_window1.CustomersWindow()
                        win.wait_window()
            except Exception as e:
                print(f"خطأ في البحث عن عميل: {e}")

    def on_key_release(self, event):
        if event.keysym in ('Up', 'Down', 'Return'):
            return

        keyword = self.customer_entry.get()
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM Customers WHERE name LIKE ?", (keyword + '%',))
            results = [row[0] for row in cursor.fetchall()]
            conn.close()

            self.customer_entry['values'] = results
            
            if results:
                self.customer_entry.event_generate('<Down>')
        except Exception as e:
            print(f"خطأ أثناء الاقتراح الآلي لأسماء العملاء: {e}")
    
    def open_add_customer(self):
        import customers_window1
        win = customers_window1.CustomersWindow()
        win.wait_window()
        
    def show_preview(self, items, total_amount, invoice_id, cust_name, payment, discount, paid_amount, remaining_amount):
        preview_win = ctk.CTkToplevel(self)
        preview_win.title("معاينة الفاتورة")
        preview_win.geometry("450x700")
        preview_win.attributes("-topmost", True)
        
        preview_win.grab_set()
        preview_win.focus_force()

        receipt_text = f"{'='*40}\n"
        receipt_text += f"          سوبر ماركت الأقصى\n"
        receipt_text += f"{'='*40}\n"
        receipt_text += f"رقم الفاتورة: {invoice_id}\n"
        receipt_text += f"العميل: {cust_name}  |  الدفع: {payment}\n"
        receipt_text += f"{'-'*40}\n"
        receipt_text += f"{'الصنف':<20} | {'الكمية':<6} | {'السعر':<6} | {'الإجمالي'}\n"
        receipt_text += f"{'-'*40}\n"
        
        for item in items:
            name_str = str(item[3])[:18] 
            receipt_text += f"{name_str:<20} | {item[2]:<6} | {item[1]:<6} | {item[0]}\n"
            
        receipt_text += f"{'-'*40}\n"
        receipt_text += f"الخصم: {discount} ر.ي\n"
        receipt_text += f"الإجمالي النهائي: {total_amount:.2f} ر.ي\n"
        receipt_text += f"المدفوع: {paid_amount:.2f} ر.ي\n"
        receipt_text += f"المتبقي (آجل): {remaining_amount:.2f} ر.ي\n"
        receipt_text += f"{'='*40}\n"
        receipt_text += f"       شكراً لزيارتكم!\n"

        textbox = ctk.CTkTextbox(preview_win, font=("Courier", 14), width=400, height=500)
        textbox.pack(pady=10, padx=10)
        textbox.insert("1.0", receipt_text)
        textbox.configure(state="disabled") 

        btn_frame = ctk.CTkFrame(preview_win, fg_color="transparent")
        btn_frame.pack(pady=10, fill="x")

        btn_print = ctk.CTkButton(btn_frame, text="طباعة الفاتورة 🖨️", fg_color="#2ecc71", hover_color="#27ae60",
                                  command=lambda: [self.execute_print(items, total_amount, invoice_id, cust_name, payment, discount, paid_amount, remaining_amount), preview_win.destroy()])
        btn_print.pack(side="right", padx=20, expand=True)

        btn_close = ctk.CTkButton(btn_frame, text="إغلاق المعاينة", fg_color="#e74c3c", hover_color="#c0392b",
                                  command=preview_win.destroy)
        btn_close.pack(side="left", padx=20, expand=True)

    def open_returns_window(self, *args):
        import returns_window
        win = returns_window.ReturnsWindow()
        win.wait_window()