import logging
import os
import threading
import time
from tkinter import ttk, Menu, font

import customtkinter as ctk
import pyperclip
from driver_map import DriverMap
from notificationBar import show_notification
from order_map import OrderMap
from record import Record
from work_stream_control import wait_user_press


class Table:

    def __init__(self, app, callback, columns, column_titles, column_widths=None, row_height=50):
        self.parent = app
        self.tree = None
        self.row_click_callback = callback  # 用于存储回调函数
        self.context_menu = None
        self.chose_data = None
        self.lock = threading.Lock()  # 创建一个锁对象
        self.columns = columns
        self.column_titles = column_titles
        self.column_widths = column_widths
        self.row_height = row_height
        style = ttk.Style()
        # style.configure("Treeview", rowheight=row_height)
        style.configure("Treeview", padding=(10, 20))  # 设置单元格的内边距 (左右, 上下)
        style.configure("Treeview.Heading", font=("Arial", 14))  #
        style.configure("Treeview", font=("Arial", 14))
        style.map('Treeview', background=[('selected', 'gray')], foreground=[('selected', 'white')])
        style.configure("Treeview.Highlight", background="yellow", foreground="black")

        self.tree = ttk.Treeview(self.parent, columns=columns, show='headings', style='Treeview')

        # 创建并配置滚动条
        self.vsb = ttk.Scrollbar(self.parent, orient="vertical", command=self.tree.yview)
        self.hsb = ttk.Scrollbar(self.parent, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=self.vsb.set, xscrollcommand=self.hsb.set)

        # 斑马纹样式
        self.tree.tag_configure('oddrow', background='lightblue')
        self.tree.tag_configure('evenrow', background='white')
        self.tree.tag_configure('highlight', background='yellow')

        # 配置grid布局使表格能够自动扩展
        self.parent.grid_rowconfigure(0, weight=1)
        self.parent.grid_columnconfigure(0, weight=1)

        self.tree.grid(row=0, column=0, sticky="nsew")  # 使用 grid 布局
        # 将滚动条和Treeview放置到网格中
        self.vsb.grid(row=0, column=1, sticky="ns")
        self.hsb.grid(row=1, column=0, sticky="ew")
        # 绑定鼠标点击事件
        self.tree.bind("<ButtonRelease-1>", self.on_row_click)  # 绑定左键点击事件
        self.tree.bind("<ButtonRelease-3>", self.on_row_click)  # 绑定右键点击事件
        self.create_context_menu()
        self.create()

    def create(self):
        """创建表格，传入列名、列标题、列宽和行高"""
        if self.tree is not None:
            for idx, (col, title) in enumerate(zip(self.columns, self.column_titles)):
                width = self.column_widths[idx] if self.column_widths and len(
                    self.column_widths) > idx else 100  # 默认宽度为100
                self.tree.column(col, anchor=ctk.CENTER, width=width)
                self.tree.heading(col, text=title, anchor=ctk.CENTER)

    def create_context_menu(self):
        custom_font = font.Font(family="Tahoma", size=14)
        """创建右键点击菜单"""
        self.context_menu = Menu(self.parent, tearoff=0, font=custom_font)
        self.context_menu.add_command(label="单独分配司机",
                                      command=lambda: self.run_in_thread(self.assign_driver, False))
        self.context_menu.add_command(label="重新分配司机",
                                      command=lambda: self.run_in_thread(self.assign_driver, True))
        self.context_menu.add_command(label="从此开始分配", command=lambda: self.run_in_thread(self.assign_from_here))
        self.context_menu.add_command(label="删除司机信息",
                                      command=self.delete_driver_info)
        self.context_menu.add_command(label="复制司机昵称", command=lambda: self.copy_info(2))
        self.context_menu.add_command(label="复制司机真名", command=lambda: self.copy_info(3))
        self.context_menu.add_command(label="复制订单号", command=lambda: self.copy_info(1))
        self.context_menu.add_command(label="复制车牌", command=lambda: self.copy_info(5))
        self.context_menu.add_command(label="复制号码", command=lambda: self.copy_info(6))

    def copy_info(self, index):
        selected_item = self.tree.selection()[0]
        item_data = list(self.tree.item(selected_item, "values"))
        pyperclip.copy(item_data[index])
        self.parent.after(0, lambda: show_notification(f'{item_data[index]} 已复制到剪贴板'))

    def delete_driver_info(self):
        selected_item = self.tree.selection()[0]
        item_data = list(self.tree.item(selected_item, "values"))
        self.upsert([item_data[0], item_data[1], item_data[2], '', '', ''])
        DriverMap().delete_driver(item_data[2])

    def run_in_thread(self, target, *args):
        """在新线程中运行目标函数，并确保线程安全"""
        thread = threading.Thread(target=self.thread_safe_wrapper, args=(target, *args))
        thread.start()

    def thread_safe_wrapper(self, target, *args):
        with self.lock:
            target(*args)

    def assign_driver(self, ignore_is_alloc=False):
        from alloc_step import AllocStep

        """处理分配司机的逻辑"""
        from alloc_step import AllocStep
        selected_item = self.tree.selection()[0]
        item_data = self.tree.item(selected_item, "values")
        if AllocStep().open_webpage():
            AllocStep().single_alloc(item_data, ignore_is_alloc)

    def assign_from_here(self):
        from alloc_step import AllocStep

        selected_item = self.tree.selection()[0]
        item_index = self.tree.index(selected_item)  # 获取选中行的索引

        # 获取从选中行开始到最后所有行的值
        all_items = self.tree.get_children()  # 获取所有行的ID
        data_from_selected_to_end = []

        for i in range(item_index, len(all_items)):
            item_data = self.tree.item(all_items[i], "values")
            data_from_selected_to_end.append(item_data)
        if len(data_from_selected_to_end) == 0:
            self.parent.after(0, lambda: show_notification(f'后面没有订单了，无法从此开始分配'))
            logging.info(f"后面没有订单了,无法从此开始分配")
            return
        logging.info(f"从{data_from_selected_to_end[0][1]}开始分配")
        logging.info("开始打开网页")
        if AllocStep().open_webpage():
            logging.info("打开网页结束")
            for e in data_from_selected_to_end:
                AllocStep().single_alloc(e, False)
                if wait_user_press(self.parent):
                    continue
                else:
                    break

    def sync_table(self):
        self.clear()
        for k, v in OrderMap().get_map().items():
            driver_info = DriverMap().get_driver_info(v)
            if driver_info is not None:
                if Record().is_alloc(k):
                    self.upsert(
                        [k, v, driver_info['true_name'], 'YES', driver_info['license_plate'],
                         driver_info['phone']])
                else:
                    self.upsert(
                        [k, v, driver_info['true_name'], 'NO', driver_info['license_plate'],
                         driver_info['phone']])
            else:
                if Record().is_alloc(k):
                    self.upsert([k, v, '', 'YES', '', ''])
                else:
                    self.upsert([k, v, '', 'NO', '', ''])

    def init_table(self, file_path):
        OrderMap().pre_process(file_path)
        file_name_with_extension = os.path.basename(file_path)
        file_name, _ = os.path.splitext(file_name_with_extension)
        Record().create_work_record_excel(file_name)
        self.sync_table()

    def get_all_data(self):
        """返回当前表格中的所有行信息"""
        all_data = []
        for item in self.tree.get_children():
            item_data = self.tree.item(item, "values")
            all_data.append(item_data)
        return all_data

    def highlight(self, order_number):
        """高亮指定订单号的行"""
        if self.tree:
            for idx, item in enumerate(self.tree.get_children()):
                values = self.tree.item(item, "values")
                current_tags = list(self.tree.item(item, "tags"))
                if values[1] == order_number:
                    if 'highlight' not in current_tags:
                        self.tree.item(item, tags=('highlight',))
                    self._scroll_to_item(item)  # 确保 item 被传递给 _scroll_to_item
                else:
                    if 'highlight' in current_tags:
                        current_tags.remove('highlight')
                        current_tags.append('evenrow' if idx % 2 == 0 else 'oddrow')
                        current_tags.append('custom_font')
                        self.tree.item(item, tags=(*current_tags,))

    def _scroll_to_item(self, item):
        """滚动到指定项并将其置于中间"""
        # 强制显示项目
        self.tree.see(item)

        # 使用 after 延迟处理滚动，确保布局已经更新
        # self.tree.after(10, self._scroll_to_item_after, item)

    def _scroll_to_item_after(self, item):
        """滚动逻辑的延迟执行版本"""
        bbox = self.tree.bbox(item)
        if not bbox:
            return  # 如果 bbox 仍然为空，说明有其他问题

        visible_height = int(self.tree.winfo_height())
        row_y, row_height = bbox[1], bbox[3]

        # 计算 Treeview 中行的总高度
        total_rows = len(self.tree.get_children())

        # 计算目标行在整个 Treeview 中的位置比例
        target_index = self.tree.index(item)
        target_position = target_index / total_rows
        # 将 Treeview 滚动到目标位置
        self.tree.yview_moveto(target_position)

    def find_by_order_num(self, order_number):
        """根据订单号查找并返回对应数据"""
        if self.tree:
            for item in self.tree.get_children():
                if self.tree.item(item, "values")[1] == order_number:
                    return self.tree.item(item, "values")
        return None

    def upsert(self, values):
        """插入或更新指定订单号的行，传入一个数组"""
        order_number = values[1]
        for item in self.tree.get_children():
            if self.tree.item(item, "values")[1] == order_number:
                self.update(values)
                return
        self.insert(values)

    def clear(self):
        """清空表格"""
        if self.tree:
            for item in self.tree.get_children():
                self.tree.delete(item)

    def insert(self, values):
        """插入数据，传入一个数组"""
        nv = [self.count() + 1] + values
        if self.tree:
            row_count = len(self.tree.get_children())
            tag = 'evenrow' if row_count % 2 == 0 else 'oddrow'
            self.tree.insert("", ctk.END, values=nv, tags=(tag, 'custom_font',))

    def delete(self, order_number):
        """删除指定订单号的行"""
        if self.tree:
            for item in self.tree.get_children():
                if self.tree.item(item, "values")[1] == order_number:
                    self.tree.delete(item)
                    self._refresh_tags()  # 删除后刷新标签以保持斑马纹样式
                    break

    def on_row_click(self, event):
        """处理行点击事件"""
        selected_item = self.tree.selection()  # 获取选中的行
        if selected_item:
            item_data = self.tree.item(selected_item, "values")
            if self.row_click_callback:  # 检查是否设置了回调函数
                region = self.tree.identify("region", event.x, event.y)
                col = self.tree.identify_column(event.x)
                row = self.tree.identify_row(event.y)

                print(f"Clicked region: {region}, column: {col}, row: {row}")
                self.row_click_callback(item_data)  # 调用回调函数并传入行数据
                self.chose_data = item_data
                # event.num == 3 表示右键点击
                if event.num == 3:
                    self.context_menu.post(event.x_root, event.y_root)

    def update(self, values):
        """更新指定订单号的行，传入一个数组，假设第一个元素为订单号"""
        if self.tree:
            for item in self.tree.get_children():
                if self.tree.item(item, "values")[1] == values[1]:
                    self.tree.item(item, values=values)
                    break

    def count(self):
        """获取当前表格中的数据行数"""
        if self.tree:
            return len(self.tree.get_children())
        return 0

    def find_first(self, condition):
        """根据传入的lambda条件函数查找数据"""
        if self.tree:
            for item in self.tree.get_children():
                values = self.tree.item(item, "values")
                if condition(values):
                    return values
        return None

    def _refresh_tags(self):
        """刷新所有行的标签以保持斑马纹样式"""
        for idx, item in enumerate(self.tree.get_children()):
            current_tags = list(self.tree.item(item, "tags"))
            tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
            if 'highlight' in current_tags:
                self.tree.item(item, tags=('highlight', tag))
            else:
                self.tree.item(item, tags=(tag,))
