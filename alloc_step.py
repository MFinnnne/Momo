import logging
import threading
import time

from DrissionPage._pages.chromium_page import ChromiumPage

from car import Car
from driver_map import DriverMap
from notificationBar import show_notification
from record import Record
from request_handler import fetch_urls_concurrently, fetch_url
from util import singleton
import config
from datetime import datetime
from dateutil.relativedelta import relativedelta
import re


# https://merchant.klook.com/v2/privatetransfermerchantsrv/api/driver/manager/assign

@singleton
class AllocStep:
    def __init__(self):
        self.table = None
        self.order = None
        self.page = None
        self.app = self
        self.ignore_is_alloc = False
        self.cookie = None
        self.lock = threading.Lock()  # 创建一个锁对象
        self.select_purple_tag_count = 0

    def init(self, app, table):
        self.table = table
        self.app = app

    def single_alloc(self, item_data, ignore_is_alloc):
        self.ignore_is_alloc = ignore_is_alloc
        logging.info(f'f{item_data[1]} 开始分配，打开网页中')
        self.alloc(item_data[1], item_data[2])

    def start_alloc_check(self):
        # 启动一个新线程来运行 is_alloc_check 方法
        threading.Thread(target=self._is_alloc_check).start()

    def _is_alloc_check(self):
        with self.lock:
            # 获取当前时间
            current_time = datetime.now()

            # 计算 end_time 为今天的23:59:59
            end_time = current_time.replace(hour=23, minute=59, second=59, microsecond=0)

            # 计算 start_time 为一个月前的00:00:00
            start_time = current_time.replace(hour=00, minute=00, second=00, microsecond=0)
            # start_time = (current_time - relativedelta(days=1)).replace(hour=00, minute=00, second=00,
            #                                                             microsecond=0)

            # 格式化为字符串，匹配图片中的格式
            formatted_start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
            formatted_end_time = end_time.strftime('%Y-%m-%d %H:%M:%S')

            # 计算 UTC 时间并减去 8 小时
            utc_time_2 = (current_time - relativedelta(hours=8)).replace(second=00)
            utc_time_1 = utc_time_2 - relativedelta(months=1)

            # 将时间格式化为 ISO 8601 格式
            date_1 = utc_time_1.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] + 'Z'
            date_2 = utc_time_2.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] + 'Z'
            try:
                booking_info_list = self.table.get_all_data()
                if len(booking_info_list) == 0:
                    self.app.after(0, lambda: show_notification(f'表格里没数据，你是没导入数据吗'))
                    return
                logging.info(f'开始信息同步 时间范围 【{formatted_start_time}】->【{formatted_end_time}】')
                self.app.after(0, lambda: show_notification(
                    f'开始信息同步 时间范围 【{formatted_start_time}】->【{formatted_end_time}】 请等待结束提示在继续操作',
                    10000,
                    width=800))
                if not self.open_webpage():
                    return False

                url = config.get_booking_list.format(formatted_start_time, formatted_end_time, date_1, date_2, 1, 1)
                pre_fetch = fetch_url(url, self.cookie)
                total = 0
                if pre_fetch['content']['success'] and pre_fetch is not None:
                    total = pre_fetch['content']['result']['total']
                else:
                    logging.info('获取已确认订单错误')
                    self.app.after(0, lambda: show_notification(f'获取已确认订单错误，影响不大继续工作吧'))
                    return
                result = None
                if total <= 100:
                    url = config.get_booking_list.format(formatted_start_time, formatted_end_time, date_1, date_2,
                                                         1, 100)
                    result = fetch_url(url, self.cookie)
                    self.sync_info(booking_info_list, result)
                else:
                    for page_index in range(1, int(total / 100) + 1):
                        url = config.get_booking_list.format(formatted_start_time, formatted_end_time, date_1, date_2,
                                                             page_index, 100)
                        result = fetch_url(url, self.cookie)
                        self.sync_info(booking_info_list, result)
            except Exception as e:
                logging.error(f"发生错误：{e}")
                self.app.after(0, lambda: show_notification(f"发生错误：{e}"))
            finally:
                logging.info(
                    f'开始信息同步 时间范围 【{formatted_start_time}】->【{formatted_end_time}】 请等待结束提示在继续操作')
                self.app.after(0, lambda: show_notification(f"信息同步结束，继续工作吧"))

    def get_car_list(self):
        threading.Thread(target=self._get_car_list()).start()

    def _get_car_list(self):
        try:
            self.app.after(0, lambda: show_notification(f'开始获取车辆信息，请等待结束提示再操作'))
            if not self.open_webpage():
                logging.info('获取车辆信息失败，因为打开网站失败')
                return False
            url = config.get_car_list.format(1, 10)
            pre_fetch = fetch_url(url, self.cookie)
            total = 0
            if pre_fetch['content']['success'] and pre_fetch is not None:
                total = pre_fetch['content']['result']['total']
            else:
                logging.info('获取车辆信息错误')
                self.app.after(0, lambda: show_notification(f'获取车辆信息错误，影响不大继续工作吧'))
                return
            result = None
            if total <= 100:
                url = config.get_car_list.format(1, 100)
                result = fetch_url(url, self.cookie)
                Car().upsert_data_by_plate_and_update_time(result['content']['result']['list'])
            else:
                for page_index in range(1, int(total / 100) + 1):
                    url = config.get_car_list.format(page_index, 100)
                    result = fetch_url(url, self.cookie)
                    Car().upsert_data_by_plate_and_update_time(result['content']['result']['list'])
        except  Exception as e:
            logging.error(f"获取车辆信息错误：{e}")
            self.app.after(0, lambda: show_notification(f"获取车辆信息错误：{e}"))
        finally:
            self.app.after(0, lambda: show_notification(f"车辆信息获取完成，请继续操作"))

    def _get_driver_list(self):
        try:
            if not self.open_webpage():
                logging.info('获取车辆信息失败，因为打开网站失败')
                return False
            url = config.get_driver_list.format(1, 10)
            pre_fetch = fetch_url(url, self.cookie)
            total = 0
            if pre_fetch['content']['success'] and pre_fetch is not None:
                total = pre_fetch['content']['result']['total']
            else:
                logging.info('获取车辆信息错误')
                self.app.after(0, lambda: show_notification(f'获取车辆信息错误，影响不大继续工作吧'))
                return
            result = None
            if total <= 100:
                url = config.get_driver_list.format(1, 100)
                result = fetch_url(url, self.cookie)
                Car().upsert_data_by_plate_and_update_time(result['content']['result']['list'])
            else:
                for page_index in range(1, int(total / 100) + 1):
                    url = config.get_driver_list.format(page_index, 100)
                    result = fetch_url(url, self.cookie)
                    Car().upsert_data_by_plate_and_update_time(result['content']['result']['list'])
            print(result)
        except  Exception as e:
            logging.error(f"获取车辆信息错误：{e}")
            self.app.after(0, lambda: show_notification(f"获取车辆信息错误：{e}"))

    def sync_info(self, booking_info_list, result):
        if result['content']['success'] and result is not None:
            for book_info in result['content']['result']['booking_list']:
                order_num = book_info['booking_info']['booking_reference_number']
                item = next(filter(lambda n: n[1] == order_num, booking_info_list), None)
                if item is None:
                    logging.warning(f'订单: {order_num},未在表格中找到')
                    continue
                item = list(item)
                driver_info = book_info['common_info'][5]['field_list'][0]['field_value']
                logging.warning(f'开始同步订单: {order_num}')
                if driver_info is not None and driver_info != '':
                    name = re.search(r'名字:(.*?)<br />', driver_info)
                    name = name.group(1) if name else ""

                    phone = re.search(r'手机号码:(.*?)<br />', driver_info)
                    phone = phone.group(1) if phone else ""

                    car_model = re.search(r'车型:(.*?)<br />', driver_info)
                    car_model = car_model.group(1) if car_model else ""

                    car_color = re.search(r'车色:(.*?)<br />', driver_info)
                    car_color = car_color.group(1) if car_color else ""

                    license_plate = re.search(r'车牌号码:(.*?)$', driver_info)
                    license_plate = license_plate.group(1) if license_plate else ""

                    item[6] = phone
                    item[5] = license_plate
                    item[4] = 'YES'
                    self.table.highlight(item[1])
                    self.table.upsert(item)
                    Record().update_record_excel('是', item[1], item[2])
                    DriverMap().update_or_add_name(item[2], item[3], phone, car_model, car_color,
                                                   license_plate)
                    print(license_plate)
                else:
                    item[4] = 'NO'
                    self.table.highlight(item[1])
                    self.table.upsert(item)
                    Record().update_record_excel('否', item[1], item[2])
        else:
            logging.info('获取已确认订单错误')
            self.app.after(0, lambda: show_notification(f'获取已确认订单错误，影响不大继续工作吧'))

    def open_webpage(self):
        self.page = ChromiumPage()
        if self.page.get('https://merchant.klook.com/zh-CN/booking'):
            if self.page.wait.url_change(
                    'https://merchant.klook.com/zh-CN/login?redirect_url=https%3A%2F%2Fmerchant.klook.com%2Fzh-CN%2Fbooking',
                    timeout=3):
                self.app.after(0, lambda: show_notification(f'打开网页不可用，看看是不是没登录'))
                return False
            self.cookie = self.page.cookies(as_dict=True, all_info=True)
            return True
        return False

    def click_clear_button(self):
        # 点击清空
        clear = self.page.ele("@@text()=清空")
        clear.click()

    def input_order_number(self, num):
        order_num = self.page.ele('tag:label@@text()=订单编号')
        input_tag = order_num.parent(1).next().child(1).child(1).child(1)
        input_tag.clear()
        input_tag.input(num)
        self.order = list(self.table.find_by_order_num(num))

    def click_search_button(self):
        # 点击查询
        self.page.wait.ele_deleted("@class=ant-spin-dot ant-spin-dot-spin")
        query = self.page.ele("@@text()=查 询")
        query.click()

    def choose_purple_tag(self):
        self.page.wait.eles_loaded('tag:div@@class=booking-color-tag')
        self.page.ele("tag:div@@class=booking-color-tag").hover()
        time.sleep(1)
        select_purple_tag = f'''
                    // 查找具有 class 为 tag-item 的所有元素
                    var tagItems = document.querySelectorAll(".tag-item");
                    if (tagItems.length >= 4) {{
                        // 获取第三个 tag-item（索引为 2）
                        var tht git
                        irdTagItem = tagItems[2];

                        // 触发第三个 tag-item 的 click 事件
                        thirdTagItem.click();
                        console.log("Clicked on Tag Item 3:", thirdTagItem);
                    }} else {{
                        console.error("Less than three elements found with class 'tag-item'.");
                    }}
            '''
        self.page.run_js(select_purple_tag)
        # self.page.wait.eles_loaded('tag:div@@class=color-tag-list')
        # self.page.ele('@@class=ant-popover ant-popover-placement-left').wait.stop_moving()
        # purple_tag = self.page.eles("tag:div@@class=tag-item").filter_one(5).displayed()
        # purple_tag.click(by_js=None)

    def click_alloc_driver(self, k, v):
        # 指派司机
        alloc = self.page.ele("@text():指派司机")
        if alloc.text == '重新指派司机' and self.ignore_is_alloc != True:
            self.app.after(0, lambda: show_notification(f"{k} 已经指派司机: {v}，", 3000))
            Record().update_record_excel("是", k, v)
            self.order[4] = 'YES'
            self.table.update(self.order)
            return False
        alloc.click()
        return True

    def input_driver_name(self, nick):
        driver = self.page.ele("@@text()=按司机姓名搜索")
        driver.click()
        list_box = self.page.ele(
            "@@class=ant-select-dropdown ant-select-dropdown--single ant-select-dropdown-placement-bottomLeft")
        list_box.wait.displayed()
        searches = self.page.eles("@@class=ant-select-search__field")
        while len(searches) < 4:
            time.sleep(0.1)
        search = searches.filter_one(1).displayed()
        name = DriverMap().get_true_name(nick)
        if name is None:
            search.input(nick)
        else:
            self.app.after(0, lambda: show_notification(f"请注意司机 {nick} 已经被自动转换为了 {name} 请检查是否正确 "))
            search.input(name)

    def catch_driver_name(self, k, v):
        pre_name = ''
        while True:
            peer = self.page.ele('tag:div@text()=按司机姓名搜索')
            if peer.next().attrs['class'] == 'ant-select-selection-selected-value':
                true_name_tag = peer.next()
                DriverMap().update_or_add_name(v, true_name_tag.text)
                self.order[3] = true_name_tag.text
                if pre_name != true_name_tag.text:
                    pre_name = true_name_tag.text
                    self.app.after(0, lambda: show_notification(f"{v} -> {true_name_tag.text} 已经录入", 3000))

            modal = self.page.ele("@@class=ant-modal-mask")
            modal_display = modal.style("display")
            time.sleep(0.1)
            if modal_display == 'none':
                break

    def update_info(self, k, v):
        Record().update_record_excel("是", k, v)
        self.order[4] = 'YES'
        self.table.update(self.order)
        while True:
            modal = self.page.ele("@@class=ant-modal-mask")
            modal_display = modal.style("display")
            time.sleep(0.1)
            if modal_display == 'none':
                return

    def alloc(self, k, v):
        try:
            self.table.highlight(k)
            self.input_order_number(k)
            logging.info(f'已输入订单号')
            self.click_search_button()
            logging.info(f'已点击查找按钮')
            for i in range(3):
                if i >= 2:
                    self.app.after(0, lambda: show_notification(f"尝试重新选择紫色标签"))
                self.choose_purple_tag()
                cur_tag = self.page.ele("tag:div@@class=tag-item")
                color = cur_tag.attr('style').split(';')[0].split(':')[1]
                if color == ' rgb(116, 99, 189)':
                    self.app.after(0, lambda: show_notification(f"选中紫色标签成功"))
                    break
            else:
                self.choose_purple_tag()
                self.app.after(0, lambda: show_notification(f"选中紫色标签错误，请手动选中并完成当前此单"))
            # self.choose_purple_tag()
            logging.info(f'已选择紫色标签')
            if self.click_alloc_driver(k, v):
                logging.info(f'已点击指派司机按钮')
                self.input_driver_name(v)
                logging.info(f'已输入司机名')
                self.catch_driver_name(k, v)
                logging.info(f'已捕获司机名')
                self.update_info(k, v)
                logging.info(f'已更新信息')
        except Exception as e:
            logging.error(e)
        finally:
            return
