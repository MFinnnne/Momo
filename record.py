import os
from datetime import datetime

import pandas as pd

from util import singleton


@singleton
class Record(object):

    def __init__(self):
        self.current_date = datetime.now().strftime("%Y-%m-%d")
        self.record = None
        self.file_name = None

    def is_alloc(self, order_num):
        if order_num in self.record["订单号"].values:
            existing_status = self.record.loc[self.record["订单号"] == order_num, "是否分配"].values[0]
            if existing_status == '是':
                return True
            return False

    def create_work_record_excel(self, record_excel_name):
        self.file_name = f"{record_excel_name}_record.xlsx"
        # 检查文件是否存在
        if os.path.exists(self.file_name):
            # 文件存在，读取它
            self.record = pd.read_excel(self.file_name)
        else:
            # 文件不存在，创建一个带有指定列头的空 DataFrame
            self.record = pd.DataFrame(columns=["订单号", "司机", "是否分配", "分配时间"])

    def update_record_excel(self, assigned_status, k, v):
        assigned_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if k in self.record["订单号"].values:
            # 如果订单号存在，更新对应的行
            self.record.loc[self.record["订单号"] == k, "司机"] = v
            self.record.loc[self.record["订单号"] == k, "是否分配"] = assigned_status
            self.record.loc[self.record["订单号"] == k, "分配时间"] = assigned_time
        else:
            # 如果订单号不存在，添加新行
            new_row = pd.DataFrame({
                "订单号": [k],
                "司机": [v],
                "是否分配": [assigned_status],
                "分配时间": [assigned_time]
            })
            self.record = pd.concat([self.record, new_row], ignore_index=True)
            self.record.to_excel(self.file_name, index=False)
