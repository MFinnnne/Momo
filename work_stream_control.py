import time

import keyboard

import config
from notificationBar import show_notification


def set_exit_flag():
    config.exit_flag = 1


def continue_process():
    config.exit_flag = 0


def add_control_key():
    # 注册热键
    keyboard.add_hotkey('alt+f9', set_exit_flag)
    keyboard.add_hotkey('f9', continue_process)


def wait_user_press(app):
    # 保存更新后的 DataFrame 到 Excel
    app.after(0, lambda: show_notification("alt+f9 退出程序，alt+w 继续下一个，", 3000))
    while True:
        if config.exit_flag == -1:
            time.sleep(0.1)
        else:
            break
    if config.exit_flag == 1:
        config.exit_flag = -1
        return False

    if config.exit_flag == 0:
        config.exit_flag = -1
        return True
