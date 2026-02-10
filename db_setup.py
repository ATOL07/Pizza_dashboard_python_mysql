import mysql.connector
import pandas as pd
import os

#  CONFIGURATION 
DB_HOST = "localhost"
DB_USER = "root"
DB_PASS = "12345" # my_sql_ PASSWORD
DB_NAME = "pizza_final"

def create_database(): # Function to create the database
    conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASS)
    cursor = conn.cursor()
    cursor.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
    cursor.execute(f"CREATE DATABASE {DB_NAME}")
    print(f"Database '{DB_NAME}' created.")
    conn.close()

def create_tables_and_load_data(): # Function to create tables and load data
    conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME)
    cursor = conn.cursor()

    # 1. Create Tables
    # pizza_types
    cursor.execute("""
        CREATE TABLE pizza_types (
            pizza_type_id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(100),
            category VARCHAR(50),
            ingredients TEXT
        )
    """)
    
    # pizzas
    cursor.execute("""
        CREATE TABLE pizzas (
            pizza_id VARCHAR(50) PRIMARY KEY,
            pizza_type_id VARCHAR(50),
            size VARCHAR(5),
            price DECIMAL(5,2),
            FOREIGN KEY (pizza_type_id) REFERENCES pizza_types(pizza_type_id)
        )
    """)

    # orders
    cursor.execute("""
        CREATE TABLE orders (
            order_id INT PRIMARY KEY,
            date DATE,
            time TIME
        )
    """)

    # order_details
    cursor.execute("""
        CREATE TABLE order_details (
            order_details_id INT PRIMARY KEY AUTO_INCREMENT,
            order_id INT,
            pizza_id VARCHAR(50),
            quantity INT,
            FOREIGN KEY (order_id) REFERENCES orders(order_id),
            FOREIGN KEY (pizza_id) REFERENCES pizzas(pizza_id)
        )
    """)
    print("Tables created successfully.")

    # 2. Load CSV Data
    # Helper function to insert data
    def insert_csv(file, query, col_count, date_col=None): # Helper function to insert data
        if os.path.exists(file):
            df = pd.read_csv(file, encoding='latin1')
            
            # Fix Date Format for orders table ()
            if date_col:
                df[date_col] = pd.to_datetime(df[date_col]).dt.strftime('%Y-%m-%d')
            
            # Convert dataframe to list of tuples
            data = [tuple(x) for x in df.to_numpy()]
            
            cursor.executemany(query, data)
            conn.commit()
            print(f"Loaded {len(data)} rows from {file}")
        else:
            print(f"WARNING: Could not find {file}")

    # Execution of loading
    # Make sure your CSV filenames match exactly what is in your folder
    insert_csv('pizza_types.csv', "INSERT INTO pizza_types VALUES (%s, %s, %s, %s)", 4)
    insert_csv('pizzas.csv', "INSERT INTO pizzas VALUES (%s, %s, %s, %s)", 4)
    insert_csv('orders.csv', "INSERT INTO orders VALUES (%s, %s, %s)", 3, date_col='date')
    insert_csv('order_details.csv', "INSERT INTO order_details VALUES (%s, %s, %s, %s)", 4)

    conn.close()

if __name__ == "__main__":
    create_database()
    create_tables_and_load_data()
    print("Setup Complete! Ready for the App.")