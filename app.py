import tkinter as tk # button, label,entry main library for gui
from tkinter import ttk, messagebox, Toplevel # combobox table,treeview mssgebox toplevel errorpop
import mysql.connector # database connector queryrun
import pandas as pd # Table data result handle like table

# --- GUI FIXES ---
import matplotlib # graph plot show
matplotlib.use('TkAgg') # Prevents GUI from freezing
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import seaborn as sns # Better color and design
import warnings # Clean output

# Suppress warnings for cleaner terminal output
warnings.simplefilter(action='ignore', category=FutureWarning)

# --- CONFIGURATION ---
DB_CONFIG = {
    'host': "localhost",
    'user': "root",
    'password': "12345", # <mysql PASSWORD
    'database': "pizza_final"
}

class PizzaApp: # main class
    def __init__(self, root):
        self.root = root # main window reference for gui
        self.root.title("Pizza Sales Manager & Analytics Suite")
        self.root.geometry("1100x700") # Made window slightly larger

        # Database Connection
        try:
            self.conn = mysql.connector.connect(**DB_CONFIG) # try to connect to database
            self.cursor = self.conn.cursor()
        except mysql.connector.Error as err: # if connection fails
            messagebox.showerror("Connection Error", f"Could not connect to DB: {err}")
            root.destroy()
            return

        # --- LAYOUT ---
        # Left Side: Order Form
        self.frame_left = tk.Frame(root, width=350, bg="#ec8a8a", relief=tk.RIDGE, borderwidth=2)
        self.frame_left.pack(side=tk.LEFT, fill=tk.Y)
        
        # Right Side: Dashboard Hub
        self.frame_right = tk.Frame(root, bg="white")
        self.frame_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.build_order_form()
        self.build_dashboard_hub()
        
        # Load initial KPI numbers
        self.update_kpis()

    def build_order_form(self):
        # Header
        lbl_title = tk.Label(self.frame_left, text="🍕 New Order Entry", font=("Helvetica", 16, "bold"), bg="#ec8a8a", fg="#333")
        lbl_title.pack(pady=20)

        # Inputs
        pad_opts = {'padx': 20, 'pady': 5}
        
        tk.Label(self.frame_left, text="Date (YYYY-MM-DD):", bg="#ec8a8a").pack(anchor="w", **pad_opts)
        self.entry_date = tk.Entry(self.frame_left)
        self.entry_date.insert(0, "2015-01-01") 
        self.entry_date.pack(fill=tk.X, **pad_opts)

        tk.Label(self.frame_left, text="Time (HH:MM:SS):", bg="#ec8a8a").pack(anchor="w", **pad_opts)
        self.entry_time = tk.Entry(self.frame_left)
        self.entry_time.insert(0, "13:00:00")
        self.entry_time.pack(fill=tk.X, **pad_opts)

        tk.Label(self.frame_left, text="Select Pizza:", bg="#ec8a8a").pack(anchor="w", **pad_opts)
        self.pizza_var = tk.StringVar()
        self.pizza_dropdown = ttk.Combobox(self.frame_left, textvariable=self.pizza_var)
        self.populate_pizzas()
        self.pizza_dropdown.pack(fill=tk.X, **pad_opts)

        tk.Label(self.frame_left, text="Quantity:", bg="#ec8a8a").pack(anchor="w", **pad_opts)
        self.entry_qty = tk.Entry(self.frame_left)
        self.entry_qty.insert(0, "1")
        self.entry_qty.pack(fill=tk.X, **pad_opts)

        # Submit Button
        btn_order = tk.Button(self.frame_left, text="Confirm Order", bg="#28a745", fg="white", 
                              font=("Helvetica", 12, "bold"), command=self.place_order)
        btn_order.pack(pady=30, padx=20, fill=tk.X)

    def build_dashboard_hub(self):
        tk.Label(self.frame_right, text="Analytics Dashboard", font=("Helvetica", 20, "bold"), bg="white").pack(pady=(20, 10))
        
        # --- NEW KPI SECTION (Top Cards) ---
        self.kpi_frame = tk.Frame(self.frame_right, bg="white") # key business metrics
        self.kpi_frame.pack(fill=tk.X, padx=20, pady=10)

        # Total Revenue Card
        self.card_revenue = tk.Frame(self.kpi_frame, bg="#d4edda", borderwidth=1, relief="solid")
        self.card_revenue.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=10, pady=5)
        tk.Label(self.card_revenue, text="Total Revenue", bg="#d4edda", font=("Helvetica", 10)).pack(pady=(10,0))
        self.lbl_revenue_val = tk.Label(self.card_revenue, text="$0.00", bg="#d4edda", font=("Helvetica", 18, "bold"), fg="#155724")
        self.lbl_revenue_val.pack(pady=(0,10))

        # Total Pizzas Card
        self.card_pizza = tk.Frame(self.kpi_frame, bg="#cce5ff", borderwidth=1, relief="solid")
        self.card_pizza.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=10, pady=5)
        tk.Label(self.card_pizza, text="Total Pizzas Sold", bg="#cce5ff", font=("Helvetica", 10)).pack(pady=(10,0))
        self.lbl_pizza_val = tk.Label(self.card_pizza, text="0", bg="#cce5ff", font=("Helvetica", 18, "bold"), fg="#004085")
        self.lbl_pizza_val.pack(pady=(0,10))
        
        # --- BUTTONS SECTION ---
        btn_frame = tk.Frame(self.frame_right, bg="white")
        btn_frame.pack(expand=True, pady=20)

        # Button Styling
        btn_style = {'font': ("Helvetica", 11), 'width': 28, 'height': 2, 'bg': "#007bff", 'fg': "white"}
        
        # Row 1
        tk.Button(btn_frame, text="📈 Daily Trends (Busiest Days)", command=self.viz_busiest_days, **btn_style).grid(row=0, column=0, padx=10, pady=10)
        tk.Button(btn_frame, text="🕒 Hourly Trends (Peak Times)", command=self.viz_hourly_trends, **btn_style).grid(row=0, column=1, padx=10, pady=10)
        
        # Row 2
        tk.Button(btn_frame, text="🏆 Top 5 Best Sellers", command=self.viz_top_pizzas, **btn_style).grid(row=1, column=0, padx=10, pady=10)
        tk.Button(btn_frame, text="📉 Bottom 5 Worst Sellers", command=self.viz_worst_pizzas, **btn_style).grid(row=1, column=1, padx=10, pady=10)

        # Row 3
        tk.Button(btn_frame, text="🍕 Sales by Category (Pie)", command=self.viz_category_sales, **btn_style).grid(row=2, column=0, padx=10, pady=10)
        tk.Button(btn_frame, text="📏 Sales by Pizza Size", command=self.viz_size_sales, **btn_style).grid(row=2, column=1, padx=10, pady=10)

        tk.Label(self.frame_right, text="Live Dashboard: KPIs update automatically when orders are placed.", bg="white", fg="gray").pack(side=tk.BOTTOM, pady=20)

    # --- KPI LOGIC ---
    def update_kpis(self):
        """Fetches total revenue and total quantity from MySQL and updates the labels."""
        try:
            # 1. Total Revenue
            query_rev = """
                SELECT SUM(od.quantity * p.price) 
                FROM order_details od
                JOIN pizzas p ON od.pizza_id = p.pizza_id
            """
            self.cursor.execute(query_rev)
            res_rev = self.cursor.fetchone()[0]
            total_rev = res_rev if res_rev else 0.0
            self.lbl_revenue_val.config(text=f"${total_rev:,.2f}")

            # 2. Total Pizzas
            query_qty = "SELECT SUM(quantity) FROM order_details"
            self.cursor.execute(query_qty)
            res_qty = self.cursor.fetchone()[0]
            total_qty = res_qty if res_qty else 0
            self.lbl_pizza_val.config(text=f"{int(total_qty):,}")

        except Exception as e:
            print(f"Error updating KPIs: {e}")

    # --- DATABASE FUNCTIONS ---
    def populate_pizzas(self):
        query = """
            SELECT CONCAT(pt.name, ' (', p.size, ')'), p.pizza_id 
            FROM pizzas p 
            JOIN pizza_types pt ON p.pizza_type_id = pt.pizza_type_id
            ORDER BY pt.name
        """
        self.cursor.execute(query)
        self.pizza_map = {name: pid for name, pid in self.cursor.fetchall()}
        self.pizza_dropdown['values'] = list(self.pizza_map.keys())

    def place_order(self):
        date_val = self.entry_date.get()
        time_val = self.entry_time.get()
        pizza_name = self.pizza_var.get()
        qty = self.entry_qty.get()

        if not pizza_name or not qty:
            messagebox.showerror("Error", "All fields are required!")
            return

        try:
            self.cursor.execute("SELECT MAX(order_id) + 1 FROM orders")
            new_order_id = self.cursor.fetchone()[0] or 1

            self.cursor.execute("INSERT INTO orders (order_id, date, time) VALUES (%s, %s, %s)", 
                                (new_order_id, date_val, time_val))

            pizza_id = self.pizza_map[pizza_name]
            self.cursor.execute("INSERT INTO order_details (order_id, pizza_id, quantity) VALUES ( %s, %s, %s)", 
                                (new_order_id, pizza_id, int(qty)))

            self.conn.commit()
            messagebox.showinfo("Success", f"Order #{new_order_id} added!")
            
            # REFRESH THE KPI NUMBERS AUTOMATICALLY
            self.update_kpis()
            
        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    # --- VISUALIZATION HELPERS ---
    def create_new_window(self, title, fig):
        new_win = Toplevel(self.root)
        new_win.title(title)
        new_win.geometry("800x600")
        
        canvas = FigureCanvasTkAgg(fig, master=new_win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # --- CHART FUNCTIONS ---
    def viz_busiest_days(self):
        query = "SELECT DAYNAME(date) as Day, COUNT(DISTINCT order_id) as Orders FROM orders GROUP BY Day ORDER BY Orders DESC"
        df = pd.read_sql(query, self.conn)
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(x='Day', y='Orders', data=df, ax=ax, hue='Day', legend=False, palette='Blues_d')
        ax.set_title("Busiest Days of the Week")
        self.create_new_window("Daily Trends", fig)

    def viz_hourly_trends(self):
        query = "SELECT HOUR(time) as Hour, COUNT(DISTINCT order_id) as Orders FROM orders GROUP BY Hour ORDER BY Hour"
        df = pd.read_sql(query, self.conn)
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.lineplot(x='Hour', y='Orders', data=df, ax=ax, marker='o', color='orange', linewidth=2.5)
        ax.set_title("Hourly Sales Trend (Peak Times)")
        ax.set_xticks(range(0, 24))
        ax.grid(True, linestyle='--', alpha=0.7)
        self.create_new_window("Hourly Trends", fig)

    def viz_top_pizzas(self):
        query = """
            SELECT pt.name, SUM(od.quantity) as Total FROM order_details od
            JOIN pizzas p ON od.pizza_id = p.pizza_id
            JOIN pizza_types pt ON p.pizza_type_id = pt.pizza_type_id
            GROUP BY pt.name ORDER BY Total DESC LIMIT 5
        """
        df = pd.read_sql(query, self.conn)
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.barplot(y='name', x='Total', data=df, ax=ax, hue='name', legend=False, palette='Greens_r')
        ax.set_title("Top 5 Best Selling Pizzas")
        self.create_new_window("Best Sellers", fig)

    def viz_worst_pizzas(self):
        query = """
            SELECT pt.name, SUM(od.quantity) as Total FROM order_details od
            JOIN pizzas p ON od.pizza_id = p.pizza_id
            JOIN pizza_types pt ON p.pizza_type_id = pt.pizza_type_id
            GROUP BY pt.name ORDER BY Total ASC LIMIT 5
        """
        df = pd.read_sql(query, self.conn)
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.barplot(y='name', x='Total', data=df, ax=ax, hue='name', legend=False, palette='Reds_r')
        ax.set_title("Bottom 5 Worst Selling Pizzas")
        self.create_new_window("Worst Sellers", fig)

    def viz_category_sales(self):
        query = """
            SELECT pt.category, SUM(od.quantity * p.price) as Revenue FROM order_details od
            JOIN pizzas p ON od.pizza_id = p.pizza_id
            JOIN pizza_types pt ON p.pizza_type_id = pt.pizza_type_id
            GROUP BY pt.category
        """
        df = pd.read_sql(query, self.conn)
        fig, ax = plt.subplots(figsize=(7, 7))
        ax.pie(df['Revenue'], labels=df['category'], autopct='%1.1f%%', startangle=140, colors=sns.color_palette('pastel'))
        ax.set_title("Percentage of Sales by Category")
        self.create_new_window("Category Analytics", fig)

    def viz_size_sales(self):
        query = """
            SELECT p.size, SUM(od.quantity * p.price) as Revenue FROM order_details od
            JOIN pizzas p ON od.pizza_id = p.pizza_id
            GROUP BY p.size ORDER BY Revenue DESC
        """
        df = pd.read_sql(query, self.conn)
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(x='size', y='Revenue', data=df, ax=ax, hue='size', legend=False, palette='magma')
        ax.set_title("Total Revenue by Pizza Size")
        self.create_new_window("Size Analytics", fig)

if __name__ == "__main__":
    root = tk.Tk()
    app = PizzaApp(root)
    root.mainloop()