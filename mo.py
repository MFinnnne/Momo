import logging
import os
import sys
import threading
from tkinter import filedialog, messagebox

import customtkinter as ctk

from alloc_step import AllocStep
from car import Car
from driver_map import DriverMap
from notificationBar import show_notification
from order_map import OrderMap
from record import Record
from table import Table
from work_stream_control import add_control_key, wait_user_press
from datetime import datetime

alloc_working = False
table = None
log_filename = f"app_{datetime.now().strftime('%Y-%m-%d')}.log"
logging.basicConfig(
    level=logging.DEBUG,  # Set the minimum log level
    format='%(asctime)s - %(levelname)s - %(message)s',  # Log format
    datefmt='%Y-%m-%d %H:%M:%S',  # Date format
    handlers=[
        logging.FileHandler(log_filename),  # Log to a file with date-based name
        logging.StreamHandler()  # Log output to the console
    ]
)


def upload_file():
    file_path = filedialog.askopenfilename(
        filetypes=[("Excel files", "*.xls *.xlsx"), ("All files", "*.*")]
    )
    if file_path:  # 如果选择了文件
        if file_path.endswith(('.xls', '.xlsx')):  # 检查文件扩展名
            try:
                table.init_table(file_path)
                # 你可以在这里添加处理 DataFrame 的逻辑
            except Exception as e:
                messagebox.showerror("Error", f"Failed to read Excel file: {e}")  # 处理读取失败的情况

    else:
        messagebox.showwarning("Warning", "The selected file is not an Excel file.")


def global_exception_handler(exc_type, exc_value, exc_traceback):
    print("完犊子咯！这里捕获了异常：", exc_value)


def auto_alloc():
    global alloc_working
    if alloc_working:
        app.after(0, lambda: show_notification(
            "\t无法重复启动，请根据提示 按clt+f9关闭后再重新启动\t", 10000))
        return
    if table is not None and OrderMap().size() > 0:
        alloc_working = True
        if not AllocStep().open_webpage():
            alloc_working = False
            return
        for k, v in OrderMap().get_map().items():
            logging.info(f'=============== 【{k}】 订单分配开始================')
            order = list(table.find_by_order_num(k))
            if order is None:
                app.after(0, lambda: messagebox.showwarning("Warning", "表格数据不一致，请清空表格后重新导入"))
                break
            if order[4] == 'YES':
                logging.info(f'=============== 【{k}】 订单已分配，进行下一个================')
                continue
            try:
                logging.info(f'=============== 【{k}】 订单分配开始网页操作================')
                AllocStep().alloc(k, v)
                logging.info(f'=============== 【{k}】 订单分配正常结束操作================')

            except Exception as e:
                logging.error(e)
                app.after(0, lambda: show_notification("发生错误了，请找一下作者", 3000))
            finally:
                logging.info(f'=============== 【{k}】 订单结束分配================')
                if wait_user_press(app):
                    app.after(0, lambda: show_notification("继续下一个，", 3000))
                    continue
                else:
                    alloc_working = False
                    app.after(0, lambda: show_notification("退出分配程序，可以点击 从此开始分配 选项重新启动", 3000))
                    break
    else:
        app.after(0, lambda: messagebox.askyesno("Confirmation", "请先导入需要处理的excel文件"))

    alloc_working = False


def start_auto_alloc_thread():
    alloc_thread = threading.Thread(target=auto_alloc)
    alloc_thread.start()


def on_row_click_handler(item_data):
    print(f"Row clicked: {item_data}")


def on_closing():
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        app.destroy()


if __name__ == '__main__':
    sys.excepthook = global_exception_handler

    app = ctk.CTk()
    app.geometry("900x600")
    app.title("Mo🐟 🐟 🐟 🐟 🐟 🐟")

    # WM_DELETE_WINDOW 不能改变，这是捕获命令
    app.protocol('WM_DELETE_WINDOW', on_closing)

    # 配置整个布局的列比例
    app.grid_columnconfigure(0, weight=9)  # 表格区域占90%
    app.grid_columnconfigure(1, weight=1)  # 按钮区域占10%

    # 配置整个布局的行比例（假设只占一行）
    app.grid_rowconfigure(0, weight=1)

    # 初始化Table
    table_frame = ctk.CTkFrame(app)
    table_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
    columns = ["index", "Order Number", "Driver Nickname", "Driver Real Name", "Assigned", 'License Plate',
               'Phone Number']
    column_titles = ['#', "订单号", "司机昵称", "司机真名", "是否分配", '车牌', '电话号码']
    table = Table(table_frame, on_row_click_handler, columns, column_titles, [10, 50, 120, 120, 20, 100, 100])
    # 按钮区域
    button_frame = ctk.CTkFrame(app)
    button_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

    button_frame.grid_rowconfigure((0, 1, 2, 3, 4, 5), weight=1)
    # 创建一个按钮，用于选择文件
    upload_button = ctk.CTkButton(master=button_frame, text="导入文件", command=upload_file, width=70)
    upload_button.grid(row=0, column=0, padx=10, pady=5)

    upload_button = ctk.CTkButton(master=button_frame, text="清空表格", command=lambda: table.clear(), width=70)
    upload_button.grid(row=1, column=0, padx=10, pady=5)

    upload_button = ctk.CTkButton(master=button_frame, text="开始分配", command=start_auto_alloc_thread, width=70)
    upload_button.grid(row=2, column=0, padx=10, pady=5)

    upload_button = ctk.CTkButton(master=button_frame, text="信息同步", command=lambda: AllocStep().start_alloc_check(),
                                  width=70)
    upload_button.grid(row=3, column=0, padx=10, pady=5)

    upload_button = ctk.CTkButton(master=button_frame, text="司机信息迁移",
                                  command=lambda: DriverMap().sync_from_excel(),
                                  width=70)

    upload_button.grid(row=4, column=0, padx=10, pady=5)
    upload_button = ctk.CTkButton(master=button_frame, text="获取车辆信息",
                                  command=lambda: AllocStep().get_car_list(),
                                  width=70)

    upload_button.grid(row=4, column=0, padx=10, pady=5)
    DriverMap().create_driver_map(table)
    AllocStep().init(app, table)
    add_control_key()
    app.mainloop()
