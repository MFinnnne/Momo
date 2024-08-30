import logging
import sqlite3
from tkinter import filedialog, Tk, Toplevel, Label, messagebox

import pandas as pd

from util import singleton


@singleton
class DriverMap:
    def __init__(self):
        self.conn = sqlite3.connect("driver_map.db",check_same_thread = False)
        self.table = None

    def create_driver_map(self, table):
        self.table = table
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS driver_map (
                fake_name TEXT PRIMARY KEY,
                true_name TEXT,
                phone TEXT,
                car_model TEXT,
                car_color TEXT,
                license_plate TEXT
            )
        """)
        self.conn.commit()

    def create_driver(self, fake_name, true_name, phone='', car_model='', car_color='', license_plate=''):
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO driver_map (fake_name, true_name, phone, car_model, car_color, license_plate)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (fake_name, true_name, phone, car_model, car_color, license_plate))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def read_driver(self, fake_name):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM driver_map WHERE fake_name = ?", (fake_name,))
        result = cursor.fetchone()
        if result:
            columns = ["fake_name", "true_name", "phone", "car_model", "car_color", "license_plate"]
            driver_info = dict(zip(columns, result))
            return {k: (v if v is not None else '') for k, v in driver_info.items()}
        else:
            return None

    def update_driver(self, fake_name, true_name=None, phone=None, car_model=None, car_color=None, license_plate=None):
        cursor = self.conn.cursor()
        updates = []
        params = []

        if true_name is not None:
            updates.append("true_name = ?")
            params.append(true_name)
        if phone is not None:
            updates.append("phone = ?")
            params.append(phone)
        if car_model is not None:
            updates.append("car_model = ?")
            params.append(car_model)
        if car_color is not None:
            updates.append("car_color = ?")
            params.append(car_color)
        if license_plate is not None:
            updates.append("license_plate = ?")
            params.append(license_plate)

        if updates:
            params.append(fake_name)
            cursor.execute(f"""
                UPDATE driver_map
                SET {", ".join(updates)}
                WHERE fake_name = ?
            """, params)
            self.conn.commit()
            return cursor.rowcount > 0
        return False

    def delete_driver(self, fake_name):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM driver_map WHERE fake_name = ?", (fake_name,))
        self.conn.commit()
        return cursor.rowcount > 0

    def get_true_name(self, fake_name):
        cursor = self.conn.cursor()
        cursor.execute("SELECT true_name FROM driver_map WHERE fake_name = ?", (fake_name,))
        result = cursor.fetchone()
        return result[0] if result and result[0] is not None else None

    def get_driver_info(self, fake_name):
        return self.read_driver(fake_name)

    def update_or_add_name(self, fake_name, true_name, phone=None, car_model=None, car_color=None, license_plate=None):
        if self.read_driver(fake_name):
            return self.update_driver(fake_name, true_name, phone, car_model, car_color, license_plate)
        else:
            return self.create_driver(fake_name, true_name, phone, car_model, car_color, license_plate)

    def batch_update_or_insert(self, drivers):
        cursor = self.conn.cursor()
        for driver in drivers:
            fake_name = driver.get('fake_name')
            true_name = driver.get('true_name', '')
            phone = driver.get('phone', '')
            car_model = driver.get('car_model', '')
            car_color = driver.get('car_color', '')
            license_plate = driver.get('license_plate', '')

            if self.read_driver(fake_name):
                self.update_driver(fake_name, true_name, phone, car_model, car_color, license_plate)
            else:
                self.create_driver(fake_name, true_name, phone, car_model, car_color, license_plate)

        self.conn.commit()

    def show_loading(self, root):
        # Create a top-level window to act as the loading screen
        loading_window = Toplevel(root)
        loading_window.title("Loading...")
        loading_window.geometry("300x100")
        loading_window.resizable(False, False)

        # Center the loading window on the screen
        loading_window.update_idletasks()
        x = (loading_window.winfo_screenwidth() // 2) - (300 // 2)
        y = (loading_window.winfo_screenheight() // 2) - (100 // 2)
        loading_window.geometry(f"+{x}+{y}")

        # Display a loading label
        label = Label(loading_window, text="Syncing driver information, please wait...")
        label.pack(expand=True)

        # Disable the main window while loading
        loading_window.grab_set()

        return loading_window

    def sync_from_excel(self):
        # Initialize the Tkinter root window for the file dialog
        root = Tk()
        root.withdraw()  # Hide the root window

        # Open a file dialog to select an Excel file
        file_path = filedialog.askopenfilename(
            title="Select Excel File",
            filetypes=[("Excel files", "*.xlsx *.xls")]
        )
        loading_window = self.show_loading(root)

        if file_path:
            try:
                # Show the loading screen
                df = pd.read_excel(file_path)

                # Ensure that the necessary columns are present
                if 'fake_name' not in df.columns or 'true_name' not in df.columns:
                    raise ValueError("Excel file must contain at least 'fake_name' and 'true_name' columns")

                # Fill missing values with empty strings
                df = df.fillna('')

                drivers = df.to_dict(orient='records')
                self.batch_update_or_insert(drivers)
                self.table.sync_table()
                # Close the loading window after completion
                loading_window.destroy()
                # Optional: Show a message box to indicate success
                messagebox.showinfo(title="Success", message="司机信息同步完成")
            except Exception as e:
                logging.exception(e)
                # Close the loading window in case of an error
                loading_window.destroy()
                # Optional: Show a message box to indicate failure
                messagebox.showinfo(title="Error", message=f"司机信息同步错误")
        else:
            # messagebox.showinfo(title="Cancelled", message="选个文件啊倒是")
            pass
