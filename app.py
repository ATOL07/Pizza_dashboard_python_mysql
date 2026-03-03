import tkinter as tk
from tkinter import ttk, messagebox, Toplevel
import mysql.connector
import pandas as pd

# --- GUI FIXES ---
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import seaborn as sns
import warnings
warnings.simplefilter(action="ignore", category=FutureWarning)

# --- CONFIGURATION ---
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "12345",
    "database": "pizza_final"
}


class PizzaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pizza Sales Manager & Analytics Suite")
        self.root.geometry("1200x720")
        self.root.configure(bg="white")

        # --- Modern Styling (Industry Look) ---
        style = ttk.Style(self.root)
        style.theme_use("clam")

        # Global font
        style.configure(".", font=("Segoe UI", 10))

        # Inputs
        style.configure("TEntry", padding=6)
        style.configure("TCombobox", padding=6)

        # Modern Buttons
        style.configure("Primary.TButton", font=("Segoe UI", 11, "bold"), padding=(14, 10))
        style.map("Primary.TButton",
                  background=[("active", "#0b5ed7"), ("!active", "#0d6efd")],
                  foreground=[("active", "white"), ("!active", "white")])

        style.configure("Danger.TButton", font=("Segoe UI", 11, "bold"), padding=(14, 10))
        style.map("Danger.TButton",
                  background=[("active", "#bb2d3b"), ("!active", "#dc3545")],
                  foreground=[("active", "white"), ("!active", "white")])

        # Treeview modern table
        style.configure("Treeview",
                        rowheight=30,
                        font=("Segoe UI", 10),
                        borderwidth=0)
        style.configure("Treeview.Heading",
                        font=("Segoe UI", 10, "bold"),
                        padding=8)
        style.map("Treeview",
                  background=[("selected", "#cfe2ff")],
                  foreground=[("selected", "#0b2e5f")])

        # Database Connection
        try:
            self.conn = mysql.connector.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor()
        except mysql.connector.Error as err:
            messagebox.showerror("Connection Error", f"Could not connect to DB: {err}")
            root.destroy()
            return

        # --- LAYOUT ---
        self.frame_left = tk.Frame(root, width=360, bg="#f2f4f8", relief=tk.RIDGE, borderwidth=1)
        self.frame_left.pack(side=tk.LEFT, fill=tk.Y)

        self.frame_right = tk.Frame(root, bg="white")
        self.frame_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.build_order_form()
        self.build_dashboard_hub()

        # Initial load
        self.update_kpis()
        self.load_recent_orders()

    # ---------------- LEFT PANEL ----------------
    def build_order_form(self):
        tk.Label(
            self.frame_left,
            text="🍕 New Order Entry",
            font=("Segoe UI", 16, "bold"),
            bg="#f2f4f8",
            fg="#222"
        ).pack(pady=20)

        pad_opts = {"padx": 20, "pady": 6}

        # Customer Name
        tk.Label(self.frame_left, text="Customer Name:", bg="#f2f4f8").pack(anchor="w", **pad_opts)
        self.entry_customer = ttk.Entry(self.frame_left)
        self.entry_customer.insert(0, "Customer")
        self.entry_customer.pack(fill=tk.X, **pad_opts)

        # Date
        tk.Label(self.frame_left, text="Date (YYYY-MM-DD):", bg="#f2f4f8").pack(anchor="w", **pad_opts)
        self.entry_date = ttk.Entry(self.frame_left)
        self.entry_date.insert(0, "2015-01-01")
        self.entry_date.pack(fill=tk.X, **pad_opts)

        # Time
        tk.Label(self.frame_left, text="Time (HH:MM:SS):", bg="#f2f4f8").pack(anchor="w", **pad_opts)
        self.entry_time = ttk.Entry(self.frame_left)
        self.entry_time.insert(0, "13:00:00")
        self.entry_time.pack(fill=tk.X, **pad_opts)

        # Pizza dropdown
        tk.Label(self.frame_left, text="Select Pizza:", bg="#f2f4f8").pack(anchor="w", **pad_opts)
        self.pizza_var = tk.StringVar()
        self.pizza_dropdown = ttk.Combobox(self.frame_left, textvariable=self.pizza_var, state="readonly")
        self.populate_pizzas()
        self.pizza_dropdown.pack(fill=tk.X, **pad_opts)

        # Quantity
        tk.Label(self.frame_left, text="Quantity:", bg="#f2f4f8").pack(anchor="w", **pad_opts)
        self.entry_qty = ttk.Entry(self.frame_left)
        self.entry_qty.insert(0, "1")
        self.entry_qty.pack(fill=tk.X, **pad_opts)

        # Submit button (keep as tk.Button for custom green look)
        btn_order = tk.Button(
            self.frame_left,
            text="✅ Confirm Order",
            bg="#28a745",
            fg="white",
            font=("Segoe UI", 12, "bold"),
            relief="flat",
            command=self.place_order
        )
        btn_order.pack(pady=25, padx=20, fill=tk.X)

        tk.Label(
            self.frame_left,
            #text="Tip: KPIs & Recent Orders update automatically.",
            bg="#f2f4f8",
            fg="gray",
            font=("Segoe UI", 9)
        ).pack(pady=5)

    # ---------------- RIGHT PANEL ----------------
    def build_dashboard_hub(self):
        # Header
        header = tk.Frame(self.frame_right, bg="#111827", height=60)
        header.pack(fill=tk.X)
        tk.Label(
            header,
            text="Pizza Sales Analytics Dashboard",
            font=("Segoe UI", 18, "bold"),
            bg="#111827",
            fg="white"
        ).pack(pady=12)

        # KPI Frame
        self.kpi_frame = tk.Frame(self.frame_right, bg="white")
        self.kpi_frame.pack(fill=tk.X, padx=20, pady=15)

        # Revenue Card
        self.card_revenue = tk.Frame(self.kpi_frame, bg="#d1fae5", borderwidth=1, relief="solid")
        self.card_revenue.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=10, pady=5)
        tk.Label(self.card_revenue, text="💰 Total Revenue", bg="#d1fae5", font=("Segoe UI", 11, "bold")).pack(pady=(10, 0))
        self.lbl_revenue_val = tk.Label(self.card_revenue, text="$0.00", bg="#d1fae5",
                                        font=("Segoe UI", 20, "bold"), fg="#065f46")
        self.lbl_revenue_val.pack(pady=(0, 10))

        # Pizzas Card
        self.card_pizza = tk.Frame(self.kpi_frame, bg="#dbeafe", borderwidth=1, relief="solid")
        self.card_pizza.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=10, pady=5)
        tk.Label(self.card_pizza, text="🍕 Total Pizzas Sold", bg="#dbeafe", font=("Segoe UI", 11, "bold")).pack(pady=(10, 0))
        self.lbl_pizza_val = tk.Label(self.card_pizza, text="0", bg="#dbeafe",
                                      font=("Segoe UI", 20, "bold"), fg="#1e3a8a")
        self.lbl_pizza_val.pack(pady=(0, 10))

        # Recent Orders Title
        tk.Label(
            self.frame_right,
            text="Recent Orders (Last 10)",
            bg="white",
            font=("Segoe UI", 12, "bold"),
            fg="#111827"
        ).pack(anchor="w", padx=25, pady=(5, 0))

        # Table frame + scrollbars
        table_frame = tk.Frame(self.frame_right, bg="white")
        table_frame.pack(fill=tk.BOTH, expand=False, padx=20, pady=8)

        cols = ("Order ID", "Customer", "Date", "Time", "Pizza", "Qty")
        self.orders_table = ttk.Treeview(table_frame, columns=cols, show="headings", height=8)

        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.orders_table.yview)
        self.orders_table.configure(yscrollcommand=y_scroll.set)

        # headings + columns
        for c in cols:
            self.orders_table.heading(c, text=c)

        self.orders_table.column("Order ID", anchor="center", width=90)
        self.orders_table.column("Customer", anchor="center", width=160)
        self.orders_table.column("Date", anchor="center", width=120)
        self.orders_table.column("Time", anchor="center", width=110)
        self.orders_table.column("Pizza", anchor="w", width=250)
        self.orders_table.column("Qty", anchor="center", width=70)

        self.orders_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Alternating row colors (industry feel)
        self.orders_table.tag_configure("oddrow", background="#f8f9fa")
        self.orders_table.tag_configure("evenrow", background="white")

        # Buttons Frame
        btn_frame = tk.Frame(self.frame_right, bg="white")
        btn_frame.pack(expand=True, pady=10)

        ttk.Button(btn_frame, text="📈 Daily Trends (Busiest Days)",
                   command=self.viz_busiest_days, style="Primary.TButton") \
            .grid(row=0, column=0, padx=10, pady=10)

        ttk.Button(btn_frame, text="🕒 Hourly Trends (Peak Times)",
                   command=self.viz_hourly_trends, style="Primary.TButton") \
            .grid(row=0, column=1, padx=10, pady=10)

        ttk.Button(btn_frame, text="🏆 Top 5 Best Sellers",
                   command=self.viz_top_pizzas, style="Primary.TButton") \
            .grid(row=1, column=0, padx=10, pady=10)

        ttk.Button(btn_frame, text="📉 Bottom 5 Worst Sellers",
                   command=self.viz_worst_pizzas, style="Danger.TButton") \
            .grid(row=1, column=1, padx=10, pady=10)

        ttk.Button(btn_frame, text="🍕 Sales by Category (Pie)",
                   command=self.viz_category_sales, style="Primary.TButton") \
            .grid(row=2, column=0, padx=10, pady=10)

        ttk.Button(btn_frame, text="📏 Sales by Pizza Size",
                   command=self.viz_size_sales, style="Primary.TButton") \
            .grid(row=2, column=1, padx=10, pady=10)

        tk.Label(
            self.frame_right,
            #text="Live Dashboard: KPIs & recent orders update automatically.",
            bg="white",
            fg="gray",
            font=("Segoe UI", 9)
        ).pack(side=tk.BOTTOM, pady=10)

    # ---------------- KPI LOGIC ----------------
    def update_kpis(self):
        try:
            query_rev = """
                SELECT SUM(od.quantity * p.price)
                FROM order_details od
                JOIN pizzas p ON od.pizza_id = p.pizza_id
            """
            self.cursor.execute(query_rev)
            res_rev = self.cursor.fetchone()[0]
            total_rev = res_rev if res_rev else 0.0
            self.lbl_revenue_val.config(text=f"${total_rev:,.2f}")

            query_qty = "SELECT SUM(quantity) FROM order_details"
            self.cursor.execute(query_qty)
            res_qty = self.cursor.fetchone()[0]
            total_qty = res_qty if res_qty else 0
            self.lbl_pizza_val.config(text=f"{int(total_qty):,}")

        except Exception as e:
            print(f"Error updating KPIs: {e}")

    # ---------------- RECENT ORDERS TABLE ----------------
    def load_recent_orders(self):
        for item in self.orders_table.get_children():
            self.orders_table.delete(item)

        query = """
            SELECT
                o.order_id,
                o.customer_name,
                o.date,
                o.time,
                CONCAT(pt.name, ' (', p.size, ')') AS pizza,
                od.quantity
            FROM orders o
            JOIN order_details od ON o.order_id = od.order_id
            JOIN pizzas p ON od.pizza_id = p.pizza_id
            JOIN pizza_types pt ON p.pizza_type_id = pt.pizza_type_id
            ORDER BY o.order_id DESC
            LIMIT 10
        """
        df = pd.read_sql(query, self.conn)

        # Fix "0 days" problem if pandas reads TIME as timedelta
        if "time" in df.columns:
            df["time"] = df["time"].astype(str).str.replace("0 days ", "", regex=False)

        for i, (_, row) in enumerate(df.iterrows()):
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            self.orders_table.insert("", "end", values=list(row.values), tags=(tag,))

    # ---------------- DATABASE FUNCTIONS ----------------
    def populate_pizzas(self):
        query = """
            SELECT CONCAT(pt.name, ' (', p.size, ')') AS display_name, p.pizza_id
            FROM pizzas p
            JOIN pizza_types pt ON p.pizza_type_id = pt.pizza_type_id
            ORDER BY pt.name, p.size
        """
        self.cursor.execute(query)
        results = self.cursor.fetchall()
        self.pizza_map = {display: pid for display, pid in results}
        self.pizza_dropdown["values"] = list(self.pizza_map.keys())

    def place_order(self):
        customer_name = self.entry_customer.get().strip()
        date_val = self.entry_date.get().strip()
        time_val = self.entry_time.get().strip()
        pizza_name = self.pizza_var.get().strip()
        qty = self.entry_qty.get().strip()

        if not customer_name:
            messagebox.showerror("Error", "Customer name is required!")
            return
        if not date_val or not time_val or not pizza_name or not qty:
            messagebox.showerror("Error", "All fields are required!")
            return

        try:
            qty_int = int(qty)
            if qty_int <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Quantity must be a positive integer!")
            return

        try:
            self.cursor.execute("SELECT MAX(order_id) + 1 FROM orders")
            new_order_id = self.cursor.fetchone()[0] or 1

            self.cursor.execute(
                "INSERT INTO orders (order_id, date, time, customer_name) VALUES (%s, %s, %s, %s)",
                (new_order_id, date_val, time_val, customer_name)
            )

            pizza_id = self.pizza_map[pizza_name]
            self.cursor.execute(
                "INSERT INTO order_details (order_id, pizza_id, quantity) VALUES (%s, %s, %s)",
                (new_order_id, pizza_id, qty_int)
            )

            self.conn.commit()
            messagebox.showinfo("Success", f"Order #{new_order_id} added for {customer_name}!")

            self.update_kpis()
            self.load_recent_orders()

        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    # ---------------- CHART STYLE HELPERS ----------------
    def style_ax(self, ax, title, xlabel, ylabel):
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.grid(True, linestyle="--", alpha=0.25)

    def add_bar_labels(self, ax, fmt="{:.0f}"):
        # Works for vertical + horizontal bars
        for p in ax.patches:
            # If horizontal barplot
            if p.get_width() > p.get_height():
                val = p.get_width()
                ax.text(p.get_width() + (0.02 * max(1, val)),
                        p.get_y() + p.get_height() / 2,
                        fmt.format(val),
                        va="center",
                        fontsize=10)
            else:
                val = p.get_height()
                ax.text(p.get_x() + p.get_width() / 2,
                        p.get_height() + (0.02 * max(1, val)),
                        fmt.format(val),
                        ha="center",
                        fontsize=10)

    # ---------------- VISUALIZATION WINDOW ----------------
    def create_new_window(self, title, fig):
        new_win = Toplevel(self.root)
        new_win.title(title)
        new_win.geometry("980x680")
        new_win.configure(bg="white")

        # Header bar (modern)
        header = tk.Frame(new_win, bg="#111827", height=48)
        header.pack(fill=tk.X)
        tk.Label(header, text=title, bg="#111827", fg="white",
                 font=("Segoe UI", 12, "bold")).pack(side=tk.LEFT, padx=14, pady=10)

        body = tk.Frame(new_win, bg="white")
        body.pack(fill=tk.BOTH, expand=True)

        canvas = FigureCanvasTkAgg(fig, master=body)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Matplotlib toolbar (zoom/pan/save)
        toolbar = NavigationToolbar2Tk(canvas, body)
        toolbar.update()
        toolbar.pack(fill=tk.X)

    # ---------------- CHART FUNCTIONS ----------------
    def viz_busiest_days(self):
        query = """
            SELECT DAYNAME(date) as Day, COUNT(DISTINCT order_id) as Orders
            FROM orders
            GROUP BY Day
            ORDER BY Orders DESC
        """
        df = pd.read_sql(query, self.conn)

        fig, ax = plt.subplots(figsize=(9, 5))
        sns.barplot(x="Day", y="Orders", data=df, ax=ax)
        self.style_ax(ax, "Busiest Days of the Week", "Day", "Orders")
        self.add_bar_labels(ax, fmt="{:.0f}")
        fig.tight_layout()
        self.create_new_window("Daily Trends", fig)

    def viz_hourly_trends(self):
        query = """
            SELECT HOUR(time) as Hour, COUNT(DISTINCT order_id) as Orders
            FROM orders
            GROUP BY Hour
            ORDER BY Hour
        """
        df = pd.read_sql(query, self.conn)

        fig, ax = plt.subplots(figsize=(10, 5))
        sns.lineplot(x="Hour", y="Orders", data=df, ax=ax, marker="o", linewidth=2.5)
        self.style_ax(ax, "Hourly Sales Trend (Peak Times)", "Hour", "Orders")
        ax.set_xticks(range(0, 24))
        fig.tight_layout()
        self.create_new_window("Hourly Trends", fig)

    def viz_top_pizzas(self):
        query = """
            SELECT pt.name, SUM(od.quantity) as Total
            FROM order_details od
            JOIN pizzas p ON od.pizza_id = p.pizza_id
            JOIN pizza_types pt ON p.pizza_type_id = pt.pizza_type_id
            GROUP BY pt.name
            ORDER BY Total DESC
            LIMIT 5
        """
        df = pd.read_sql(query, self.conn)

        fig, ax = plt.subplots(figsize=(10, 5))
        sns.barplot(y="name", x="Total", data=df, ax=ax)
        self.style_ax(ax, "Top 5 Best Selling Pizzas", "Total Sold", "Pizza Name")
        self.add_bar_labels(ax, fmt="{:.0f}")
        fig.tight_layout()
        self.create_new_window("Best Sellers", fig)

    def viz_worst_pizzas(self):
        query = """
            SELECT pt.name, SUM(od.quantity) as Total
            FROM order_details od
            JOIN pizzas p ON od.pizza_id = p.pizza_id
            JOIN pizza_types pt ON p.pizza_type_id = pt.pizza_type_id
            GROUP BY pt.name
            ORDER BY Total ASC
            LIMIT 5
        """
        df = pd.read_sql(query, self.conn)

        fig, ax = plt.subplots(figsize=(10, 5))
        sns.barplot(y="name", x="Total", data=df, ax=ax)
        self.style_ax(ax, "Bottom 5 Worst Selling Pizzas", "Total Sold", "Pizza Name")
        self.add_bar_labels(ax, fmt="{:.0f}")
        fig.tight_layout()
        self.create_new_window("Worst Sellers", fig)

    def viz_category_sales(self):
        query = """
            SELECT pt.category, SUM(od.quantity * p.price) as Revenue
            FROM order_details od
            JOIN pizzas p ON od.pizza_id = p.pizza_id
            JOIN pizza_types pt ON p.pizza_type_id = pt.pizza_type_id
            GROUP BY pt.category
        """
        df = pd.read_sql(query, self.conn)

        fig, ax = plt.subplots(figsize=(7.5, 7.5))
        ax.pie(df["Revenue"], labels=df["category"], autopct="%1.1f%%", startangle=140)
        ax.set_title("Percentage of Sales by Category", fontsize=14, fontweight="bold")
        fig.tight_layout()
        self.create_new_window("Category Analytics", fig)

    def viz_size_sales(self):
        query = """
            SELECT p.size, SUM(od.quantity * p.price) as Revenue
            FROM order_details od
            JOIN pizzas p ON od.pizza_id = p.pizza_id
            GROUP BY p.size
            ORDER BY Revenue DESC
        """
        df = pd.read_sql(query, self.conn)

        fig, ax = plt.subplots(figsize=(9, 5))
        sns.barplot(x="size", y="Revenue", data=df, ax=ax)
        self.style_ax(ax, "Total Revenue by Pizza Size", "Size", "Revenue")
        self.add_bar_labels(ax, fmt="{:.0f}")
        fig.tight_layout()
        self.create_new_window("Size Analytics", fig)


if __name__ == "__main__":
    root = tk.Tk()
    app = PizzaApp(root)
    root.mainloop()