import customtkinter as ctk
import tkinter as tk


class NotificationManager:
    def __init__(self):
        self.notifications = []

    def show_notification(self, message, display_time=3000, width=600):
        notification = NotificationBar(message, display_time, width=width, manager=self)
        self.notifications.append(notification)
        self.update_notifications()
        notification.show()

    def remove_notification(self, notification):
        """从通知列表中移除通知栏并更新位置"""
        if notification in self.notifications:
            self.notifications.remove(notification)
            self.update_notifications()

    def update_notifications(self):
        """更新所有通知栏的位置"""
        if len(self.notifications) == 0:
            return
        screen_height = self.notifications[0].winfo_screenheight()
        max_visible_notifications = screen_height // 70

        for index, notification in enumerate(self.notifications[-max_visible_notifications:]):
            y_offset = index * 70  # 每个通知栏高度为 70 像素
            notification.update_position(y_offset)


class NotificationBar(ctk.CTkToplevel):
    def __init__(self, message, display_time=3000, width=600, manager=None, **kwargs):
        super().__init__(**kwargs)

        # Store the manager reference
        self.manager = manager

        # 设置消息栏的大小和位置
        self.width = width
        screen_width = self.winfo_screenwidth()
        self.geometry(f"{self.width}x30+{(screen_width - self.width) // 2}+0")
        self.overrideredirect(True)  # 去除窗口边框
        self.attributes("-topmost", True)  # 置顶显示

        # 设置消息文本及其样式
        self.message_label = ctk.CTkLabel(self, bg_color='red', text=message, text_color="black", font=("Helvetica", 16, "bold"))
        self.message_label.pack(expand=True)

        # 设置定时器，指定时间后隐藏消息提示栏
        self.after(display_time, self.hide)

    def show(self):
        """显示消息提示栏"""
        self.deiconify()

    def hide(self):
        """隐藏消息提示栏并通知管理器移除该通知"""
        self.withdraw()
        self.manager.remove_notification(self)

    def update_position(self, y_offset):
        """更新通知栏的位置"""
        screen_width = self.winfo_screenwidth()
        self.geometry(f"{self.width}x60+{(screen_width - self.width) // 2}+{y_offset}")


manager = NotificationManager()


def show_notification(msg, time=3000, width=400):
    manager.show_notification(msg, display_time=time, width=width)
