import customtkinter as ctk
import sqlite3
import os
import pandas as pd
import shutil
from datetime import datetime
from tkinter import messagebox, filedialog
from tkcalendar import Calendar
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

# Configuration
DB_PATH = os.path.join(os.path.dirname(__file__), 'inventory.db')
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")
FIXED_INVITE_CODE = os.getenv("INVITE_CODE", "")

class WarehouseApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Warehouse Pro - Quản lý Kho hàng")
        self.geometry("1100x850")
        
        self.current_user = None
        self.init_db()
        self.show_login()

    def show_login(self):
        self.clear_window()
        LoginFrame(self)

    def show_register(self):
        self.clear_window()
        RegisterFrame(self)

    def show_dashboard(self, user):
        self.current_user = user
        self.clear_window()
        self.setup_dashboard()

    def clear_window(self):
        for widget in self.winfo_children():
            widget.destroy()

    def setup_dashboard(self):
        self.editing_id = None
        self.current_search = None

        # UI Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        # 1. Header & Summary
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        
        self.title_label = ctk.CTkLabel(self.header_frame, text="Warehouse Dashboard", font=ctk.CTkFont(size=28, weight="bold"))
        self.title_label.pack(pady=(10, 10))

        self.summary_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.summary_frame.pack(fill="x")
        self.summary_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.total_products_card = self.create_card(self.summary_frame, "TỔNG MẶT HÀNG", "#6366f1", 0)
        self.total_stock_value_card = self.create_card(self.summary_frame, "GIÁ TRỊ TỒN KHO", "#10b981", 1)
        self.total_est_profit_card = self.create_card(self.summary_frame, "LÃI DỰ KIẾN", "#f59e0b", 2)

        # 2. Form Section
        self.form_frame = ctk.CTkFrame(self, corner_radius=15, border_width=1, border_color="#334155")
        self.form_frame.grid(row=1, column=0, padx=20, pady=5, sticky="ew")
        
        self.form_title = ctk.CTkLabel(self.form_frame, text="Thông tin Sản phẩm", font=ctk.CTkFont(weight="bold"))
        self.form_title.pack(pady=(10, 5))

        self.input_grid = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        self.input_grid.pack(padx=20, pady=5, fill="x")
        self.input_grid.grid_columnconfigure((0, 1, 2), weight=1)

        self.input_font = ctk.CTkFont(size=14)

        # Row 1: SKU, Name, Category
        self.sku_entry = ctk.CTkEntry(self.input_grid, placeholder_text="Mã hàng (SKU)...", height=35, font=self.input_font)
        self.sku_entry.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.name_entry = ctk.CTkEntry(self.input_grid, placeholder_text="Tên hàng...", height=35, font=self.input_font)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.category_entry = ctk.CTkEntry(self.input_grid, placeholder_text="Ngành hàng...", height=35, font=self.input_font)
        self.category_entry.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        # Row 2: Imported Price, Base Selling Price, Quantity
        self.import_price_entry = ctk.CTkEntry(self.input_grid, placeholder_text="Nhập Giá nhập...", height=35, font=self.input_font)
        self.import_price_entry.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        self.import_price_entry.bind("<KeyRelease>", lambda e: self.handle_price_input(self.import_price_entry))

        self.sell_price_entry = ctk.CTkEntry(self.input_grid, placeholder_text="Nhập Giá bán cơ sở...", height=35, font=self.input_font)
        self.sell_price_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.sell_price_entry.bind("<KeyRelease>", lambda e: self.handle_price_input(self.sell_price_entry))

        self.qty_entry = ctk.CTkEntry(self.input_grid, placeholder_text="Số lượng tồn...", height=35, font=self.input_font)
        self.qty_entry.grid(row=1, column=2, padx=5, pady=5, sticky="ew")

        # Row 3: Wholesale, Retail, Profit (Display)
        self.wholesale_entry = ctk.CTkEntry(self.input_grid, placeholder_text="Nhập Giá bán sỉ...", height=35, font=self.input_font)
        self.wholesale_entry.grid(row=2, column=0, padx=5, pady=5, sticky="ew")
        self.wholesale_entry.bind("<KeyRelease>", lambda e: self.handle_price_input(self.wholesale_entry))

        self.retail_entry = ctk.CTkEntry(self.input_grid, placeholder_text="Nhập Giá bán lẻ...", height=35, font=self.input_font)
        self.retail_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        self.retail_entry.bind("<KeyRelease>", lambda e: self.handle_price_input(self.retail_entry))

        self.profit_label = ctk.CTkLabel(self.input_grid, text="Lãi dự kiến: 0₫", font=ctk.CTkFont(weight="bold"), text_color="#10b981")
        self.profit_label.grid(row=2, column=2, padx=5, pady=5)

        # Buttons
        self.btn_frame = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        self.btn_frame.pack(pady=10)

        self.submit_btn = ctk.CTkButton(self.btn_frame, text="Lưu sản phẩm", width=150, height=40, font=ctk.CTkFont(size=14, weight="bold"), command=self.save_product)
        self.submit_btn.pack(side="left", padx=10)

        self.export_btn = ctk.CTkButton(self.btn_frame, text="Xuất Excel", width=120, height=40, fg_color="#1e293b", hover_color="#334155", command=self.export_to_excel)
        self.export_btn.pack(side="left", padx=10)

        self.import_excel_btn = ctk.CTkButton(self.btn_frame, text="Nhập Excel", width=120, height=40, fg_color="#1e293b", hover_color="#334155", command=self.import_excel)
        self.import_excel_btn.pack(side="left", padx=10)

        self.cancel_btn = ctk.CTkButton(self.btn_frame, text="Hủy", width=100, height=40, fg_color="gray", command=self.reset_form)
        self.cancel_btn.pack(side="left", padx=10)
        self.cancel_btn.configure(state="disabled")

        # 3. Search Section
        self.search_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.search_frame.grid(row=2, column=0, padx=20, pady=5, sticky="ew")
        
        self.search_entry = ctk.CTkEntry(self.search_frame, placeholder_text="Tìm kiếm theo Mã hàng hoặc Tên hàng...", height=35)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", lambda e: self.apply_search())

        self.backup_btn = ctk.CTkButton(self.search_frame, text="Backup", width=80, height=35, fg_color="#334155", command=self.backup_data)
        self.backup_btn.pack(side="right")

        # 4. List Section
        self.list_frame = ctk.CTkScrollableFrame(self, label_text="Danh sách Hàng hóa")
        self.list_frame.grid(row=4, column=0, padx=20, pady=5, sticky="nsew")

        self.list_header = ctk.CTkFrame(self.list_frame, fg_color="#1e293b")
        self.list_header.pack(fill="x", pady=2)
        
        headers = [("Mã hàng", 100), ("Tên hàng", 200), ("Ngành", 120), ("Giá nhập", 100), ("Giá bán", 100), ("Lãi", 100), ("SL", 60), ("Hành động", 120)]
        for text, width in headers:
            ctk.CTkLabel(self.list_header, text=text, width=width).pack(side="left", padx=5)

        self.load_data()

    def create_card(self, parent, label, color, col):
        card = ctk.CTkFrame(parent, corner_radius=15, border_width=1, border_color=color)
        card.grid(row=0, column=col, padx=10, sticky="ew")
        
        ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=12, weight="bold"), text_color="gray").pack(pady=(10, 0))
        value_label = ctk.CTkLabel(card, text="0", font=ctk.CTkFont(size=20, weight="bold"), text_color=color)
        value_label.pack(pady=(0, 10))
        return value_label

    def init_db(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT UNIQUE,
                name TEXT,
                category TEXT,
                imported_price REAL,
                selling_price REAL,
                wholesale_price REAL,
                retail_price REAL,
                quantity INTEGER,
                date TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def handle_price_input(self, entry):
        val = entry.get().replace(",", "")
        if not val:
            self.update_profit()
            return
        
        try:
            # Handle numeric part with focus preservation
            cursor_pos = entry._entry.index("insert")
            old_len = len(entry.get())
            
            numeric_value = int(''.join(filter(str.isdigit, val)))
            formatted = f"{numeric_value:,}"
            
            entry.delete(0, 'end')
            entry.insert(0, formatted)
            
            # Adjust cursor position
            new_len = len(formatted)
            new_pos = cursor_pos + (new_len - old_len)
            entry._entry.icursor(max(0, new_pos))
            
            self.update_profit()
        except: pass

    def update_profit(self):
        try:
            imp_str = self.import_price_entry.get().replace(",", "")
            sell_str = self.sell_price_entry.get().replace(",", "")
            
            imp = float(imp_str) if imp_str else 0
            sell = float(sell_str) if sell_str else 0
            
            profit = sell - imp
            self.profit_label.configure(text=f"Lãi dự kiến: {profit:,.0f}₫", text_color="#10b981" if profit >= 0 else "#ef4444")
        except:
            self.profit_label.configure(text="Lãi dự kiến: 0₫", text_color="#10b981")

    def apply_search(self, *args):
        self.current_search = self.search_entry.get().strip()
        self.load_data()

    def load_data(self):
        for widget in self.list_frame.winfo_children():
            if widget != self.list_header: widget.destroy()

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        query = "SELECT * FROM products"
        params = []
        if self.current_search:
            query += " WHERE sku LIKE ? OR name LIKE ?"
            params = [f"%{self.current_search}%", f"%{self.current_search}%"]
            
        query += " ORDER BY id DESC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        total_value = 0
        total_profit = 0
        
        for row in rows:
            id, sku, name, cat, imp, sell, whole, retail, qty, date = row
            profit = sell - imp
            total_value += (imp * qty)
            total_profit += (profit * qty)

            row_frame = ctk.CTkFrame(self.list_frame, fg_color="transparent")
            row_frame.pack(fill="x", pady=2)
            
            ctk.CTkLabel(row_frame, text=sku, width=100).pack(side="left", padx=5)
            ctk.CTkLabel(row_frame, text=name, width=200, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(row_frame, text=cat, width=120).pack(side="left", padx=5)
            ctk.CTkLabel(row_frame, text=f"{imp:,.0f}", width=100).pack(side="left", padx=5)
            ctk.CTkLabel(row_frame, text=f"{sell:,.0f}", width=100).pack(side="left", padx=5)
            
            p_color = "#10b981" if profit >= 0 else "#ef4444"
            ctk.CTkLabel(row_frame, text=f"{profit:,.0f}", width=100, text_color=p_color, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
            
            ctk.CTkLabel(row_frame, text=str(qty), width=60).pack(side="left", padx=5)

            actions = ctk.CTkFrame(row_frame, fg_color="transparent")
            actions.pack(side="left", padx=5)
            ctk.CTkButton(actions, text="Sửa", width=45, height=24, command=lambda r=row: self.start_edit(r)).pack(side="left", padx=2)
            ctk.CTkButton(actions, text="Xóa", width=45, height=24, fg_color="#ef4444", hover_color="#dc2626", 
                         command=lambda r_id=id: self.delete_product(r_id)).pack(side="left", padx=2)
        
        conn.close()

        self.total_products_card.configure(text=str(len(rows)))
        self.total_stock_value_card.configure(text=f"{total_value:,.0f}₫")
        self.total_est_profit_card.configure(text=f"{total_profit:,.0f}₫")

    def save_product(self):
        sku = self.sku_entry.get().strip()
        name = self.name_entry.get().strip()
        cat = self.category_entry.get().strip()
        imp_raw = self.import_price_entry.get().replace(",", "")
        sell_raw = self.sell_price_entry.get().replace(",", "")
        whole_raw = self.wholesale_entry.get().replace(",", "")
        retail_raw = self.retail_entry.get().replace(",", "")
        qty_raw = self.qty_entry.get().strip()

        if not sku or not name or not imp_raw:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập Mã hàng, Tên hàng và Giá nhập!")
            return

        try:
            imp = float(imp_raw)
            sell = float(sell_raw or 0)
            whole = float(whole_raw or 0)
            retail = float(retail_raw or 0)
            qty = int(qty_raw or 0)
        except ValueError:
            messagebox.showerror("Lỗi", "Các trường giá và số lượng phải là số!")
            return

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            if self.editing_id:
                cursor.execute('''UPDATE products SET sku=?, name=?, category=?, imported_price=?, 
                                 selling_price=?, wholesale_price=?, retail_price=?, quantity=? WHERE id=?''',
                              (sku, name, cat, imp, sell, whole, retail, qty, self.editing_id))
            else:
                cursor.execute('''INSERT INTO products (sku, name, category, imported_price, 
                                 selling_price, wholesale_price, retail_price, quantity, date) 
                                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                              (sku, name, cat, imp, sell, whole, retail, qty, datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
            messagebox.showinfo("Thành công", "Đã lưu sản phẩm thành công!")
            self.reset_form()
            self.load_data()
        except sqlite3.IntegrityError:
            messagebox.showerror("Lỗi", "Mã hàng (SKU) đã tồn tại!")
        finally:
            conn.close()

    def start_edit(self, row):
        id, sku, name, cat, imp, sell, whole, retail, qty, date = row
        self.editing_id = id
        self.reset_form()
        
        self.editing_id = id
        self.sku_entry.insert(0, sku)
        self.name_entry.insert(0, name)
        self.category_entry.insert(0, cat)
        self.import_price_entry.insert(0, f"{imp:,.0f}")
        self.sell_price_entry.insert(0, f"{sell:,.0f}")
        self.wholesale_entry.insert(0, f"{whole:,.0f}")
        self.retail_entry.insert(0, f"{retail:,.0f}")
        self.qty_entry.insert(0, str(qty))
        
        self.update_profit()
        self.form_title.configure(text="Sửa Sản phẩm", text_color="#6366f1")
        self.submit_btn.configure(text="Cập nhật")
        self.cancel_btn.configure(state="normal")

    def delete_product(self, id):
        if messagebox.askyesno("Xác nhận", "Xóa sản phẩm này sẽ không thể khôi phục. Bạn có chắc?"):
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM products WHERE id=?", (id,))
            conn.commit()
            conn.close()
            self.load_data()

    def reset_form(self):
        self.editing_id = None
        self.sku_entry.delete(0, 'end')
        self.name_entry.delete(0, 'end')
        self.category_entry.delete(0, 'end')
        self.import_price_entry.delete(0, 'end')
        self.sell_price_entry.delete(0, 'end')
        self.wholesale_entry.delete(0, 'end')
        self.retail_entry.delete(0, 'end')
        self.qty_entry.delete(0, 'end')
        self.profit_label.configure(text="Lãi dự kiến: 0₫", text_color="#10b981")
        self.form_title.configure(text="Thông tin Sản phẩm", text_color="white")
        self.submit_btn.configure(text="Lưu sản phẩm")
        self.cancel_btn.configure(state="disabled")

    def export_to_excel(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            df = pd.read_sql_query("SELECT * FROM products", conn)
            conn.close()
            if df.empty:
                messagebox.showwarning("Thông báo", "Không có dữ liệu để xuất!")
                return
            
            file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", 
                                                    filetypes=[("Excel files", "*.xlsx")],
                                                    initialfile=f"Bao_cao_ton_kho_{datetime.now().strftime('%Y%m%d')}.xlsx")
            if file_path:
                df.to_excel(file_path, index=False)
                messagebox.showinfo("Thành công", "Đã xuất file Excel thành công!")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xuất file: {str(e)}")

    def import_excel(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        if not file_path: return
        try:
            df = pd.read_excel(file_path)
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            count = 0
            for _, row in df.iterrows():
                try:
                    cursor.execute('''INSERT OR REPLACE INTO products (sku, name, category, imported_price, 
                                     selling_price, wholesale_price, retail_price, quantity, date) 
                                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                                  (str(row[0]), str(row[1]), str(row[2]), float(row[3]), 
                                   float(row[4]), float(row[5]), float(row[6]), int(row[7]), 
                                   datetime.now().strftime("%Y-%m-%d")))
                    count += 1
                except: continue
            conn.commit()
            conn.close()
            self.load_data()
            messagebox.showinfo("Thành công", f"Đã nhập thành công {count} sản phẩm!")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi nhập dữ liệu: {str(e)}")

    def backup_data(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".db", filetypes=[("Database", "*.db")])
        if file_path:
            shutil.copy2(DB_PATH, file_path)
            messagebox.showinfo("Thành công", "Đã sao lưu dữ liệu!")

class LoginFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.pack(expand=True)

        self.title_label = ctk.CTkLabel(self, text="Warehouse Pro", font=ctk.CTkFont(size=32, weight="bold"))
        self.title_label.pack(pady=(0, 10))
        
        self.subtitle_label = ctk.CTkLabel(self, text="Đăng nhập để vào kho", font=ctk.CTkFont(size=14), text_color="gray")
        self.subtitle_label.pack(pady=(0, 30))

        self.username_entry = ctk.CTkEntry(self, placeholder_text="Tên đăng nhập", width=300, height=45)
        self.username_entry.pack(pady=10)

        self.password_entry = ctk.CTkEntry(self, placeholder_text="Mật khẩu", width=300, height=45, show="*")
        self.password_entry.pack(pady=10)

        self.login_btn = ctk.CTkButton(self, text="Đăng nhập", width=300, height=45, font=ctk.CTkFont(weight="bold"), command=self.login)
        self.login_btn.pack(pady=20)

        self.register_btn = ctk.CTkButton(self, text="Chưa có tài khoản? Đăng ký", fg_color="transparent", hover_color="#334155", command=master.show_register)
        self.register_btn.pack()

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập đầy đủ thông tin!")
            return

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            self.master.show_dashboard(user)
        else:
            messagebox.showerror("Lỗi", "Sai tên đăng nhập hoặc mật khẩu!")

class RegisterFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.pack(expand=True)

        self.title_label = ctk.CTkLabel(self, text="Đăng ký tài khoản", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.pack(pady=(0, 10))
        
        self.subtitle_label = ctk.CTkLabel(self, text="Cần mã mời để đăng ký", font=ctk.CTkFont(size=14), text_color="gray")
        self.subtitle_label.pack(pady=(0, 20))

        self.username_entry = ctk.CTkEntry(self, placeholder_text="Tên đăng nhập mới", width=300, height=45)
        self.username_entry.pack(pady=10)

        self.password_entry = ctk.CTkEntry(self, placeholder_text="Mật khẩu mới", width=300, height=45, show="*")
        self.password_entry.pack(pady=10)

        self.invite_entry = ctk.CTkEntry(self, placeholder_text="Mã mời (Invitation Code)", width=300, height=45)
        self.invite_entry.pack(pady=10)

        self.register_btn = ctk.CTkButton(self, text="Đăng ký ngay", width=300, height=45, font=ctk.CTkFont(weight="bold"), command=self.register)
        self.register_btn.pack(pady=20)

        self.back_btn = ctk.CTkButton(self, text="Đã có tài khoản? Đăng nhập", fg_color="transparent", hover_color="#334155", command=master.show_login)
        self.back_btn.pack()

    def register(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        invite_code = self.invite_entry.get().strip()

        if not username or not password or not invite_code:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập đầy đủ thông tin!")
            return

        if invite_code != FIXED_INVITE_CODE:
            messagebox.showerror("Lỗi", "Mã mời không chính xác!")
            return

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        try:
            hashed_pw = generate_password_hash(password)
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hashed_pw))
            
            conn.commit()
            messagebox.showinfo("Thành công", "Đăng ký thành công! Hãy đăng nhập.")
            self.master.show_login()
        except sqlite3.IntegrityError:
            messagebox.showerror("Lỗi", "Tên đăng nhập đã tồn tại!")
        finally:
            conn.close()

if __name__ == "__main__":
    app = WarehouseApp()
    app.mainloop()
