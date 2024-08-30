from tkinter import messagebox

import pandas as pd

from util import singleton


@singleton
class OrderMap:

    def __init__(self):
        self.order_map = None

    def get_map(self):
        return self.order_map

    def size(self):
        return len(self.order_map)

    def pre_process(self, file_path):
        result = {}

        df = pd.read_excel(file_path)
        # 查找列名为 'cbk' 的列
        # 确保 'cbk' 和 'driver' 列都存在
        if 'cbk' in df.columns and 'driver' in df.columns and 'order_number' in df.columns:
            cbk_column = df['cbk']
            driver_column = df['driver']
            order_number_column = df['order_number']

            # 存储分割后的数据和对应的 driver 和 order_number 信息
            segments = []
            segment = []
            segment_driver = 'no driver'
            segment_order_numbers = []
            nan_count = 0

            # 遍历 cbk 列
            for i, value in enumerate(cbk_column):
                if pd.isna(value):
                    nan_count += 1
                else:
                    if 0 < nan_count <= 100:
                        # 如果有符合条件的 NaN，将当前 segment 存储并开始新的 segment
                        if segment:
                            segments.append((segment, segment_driver, segment_order_numbers))
                        segment = []
                        segment_driver = 'no driver'
                        segment_order_numbers = []
                    nan_count = 0
                    segment.append(value)

                    # 检查当前行的 driver 列
                    if pd.notna(driver_column[i]):
                        segment_driver = driver_column[i]

                    # 检查当前行的 order_number 列
                    if pd.notna(order_number_column[i]):
                        segment_order_numbers.append(order_number_column[i])
                    else:
                        segment_order_numbers.append('no order number')

            # 添加最后一个 segment
            if segment:
                segments.append((segment, segment_driver, segment_order_numbers))

            # 存储 cbk 列为 'K' 的数据，格式为 order_number -> driver

            for seg, d, orders in segments:
                for i, cbk_value in enumerate(seg):
                    if cbk_value == 'K':
                        order_num = orders[i]
                        result[order_num] = d
        else:
            messagebox.askyesno("Confirmation", "未找到列名为 'cbk', 'driver' 或 'order_number' 的列")
        self.order_map = result
