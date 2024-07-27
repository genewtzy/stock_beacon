from datetime import datetime as dt
from datetime import date
import os
import akshare as ak
import pandas as pd
from .Utils import *
from dateutil.relativedelta import relativedelta


class MarketA(object):
    """
    实例化
    """

    def __init__(self):
        self.dir = 'data/MarketA'
        self.start_date = dt.strptime('19910101', '%Y%m%d').date()
        self.lrb_last_available_season = ''  # 利润表有效的最后一个周期 datetime, like '2024-03-31'
        self.season1 = '-03-31'
        self.season2 = '-06-30'
        self.season3 = '-09-30'
        self.season4 = '-12-31'
        # 创建市场股票信息的目录
        if not os.path.exists(self.dir):
            os.makedirs(self.dir)
            print('MarketA dir created')
        self.info_file = self.dir + '/MarketA.csv'

        self.lrb_dir = self.dir + '/lrb'
        print('lrb dir ', self.lrb_dir)
        if not os.path.exists(self.lrb_dir):
            os.makedirs(self.lrb_dir)
            print('MarketA lrb dir created', self.lrb_dir)
        #  不用每次都更新，应该放到后台更新
        self.update_info()

    def update_info(self):
        """
        更新市场信息
        """
        # 信息文件不存在则创建
        if not os.path.exists(self.info_file):
            try:
                stock_info = ak.stock_info_a_code_name()
                stock_info.to_csv(self.info_file, encoding='utf-8')
            except Exception as e:
                print(run_info(self), "An error occurred:", str(e))
        else:
            # 比较文件日期是否和当前日期一致，不一致则重新下载
            current_date = dt.now().date()
            updated_date_float = os.path.getmtime(self.info_file)
            updated_date = dt.fromtimestamp(updated_date_float).date()
            print('current_date', current_date, 'updated_date', updated_date)
            if updated_date < current_date:
                try:
                    stock_info = ak.stock_info_a_code_name()
                    stock_info.to_csv(self.info_file, encoding='utf-8')
                except Exception as e:
                    print(run_info(self), "An error occurred: ", str(e))
            else:
                print(run_info(self), 'MarketA info file update not necessary')

    def stock_exist(self, stock_code):
        """

        :param stock_code:
        :return:
        """
        stock_info = pd.read_csv(self.info_file, encoding='utf-8')
        stocks = stock_info.loc[stock_info['code'] == int(stock_code)]
        if len(stocks) >= 1:
            return True
        return False

    def stock_code2name(self, stock_code):
        """

        :param stock_code:
        :return:
        """
        stock_info = pd.read_csv(self.info_file, encoding='utf-8')
        stocks = stock_info.loc[stock_info['code'] == int(stock_code)]
        if len(stocks) >= 1:
            return stocks.to_dict('records')[0]['name']
        return '不存在'

    def lrb_update(self, start_date: date, end_date: date):
        """

        :param end_date:
        :param start_date:
        """
        start_date = start_date
        while start_date < end_date:
            update_date_str = start_date.strftime('%Y')
            self.lrb_update_season(date_str=update_date_str + self.season1)
            self.lrb_update_season(date_str=update_date_str + self.season2)
            self.lrb_update_season(date_str=update_date_str + self.season3)
            self.lrb_update_season(date_str=update_date_str + self.season4)
            start_date = start_date + relativedelta(years=1)

        print(run_info(self), 'lrb update finished lrb_last_available_season ', self.lrb_last_available_season)

    def lrb_update_season(self, date_str):
        """

        :param date_str:
        :return:
        """
        file_path = self.lrb_dir + '/' + date_str + '.csv'
        if os.path.exists(file_path):
            self.lrb_last_available_season = dt.strptime(date_str, '%Y-%m-%d').date()
            return True
        try:
            lrb_em_str = date_str.replace('-', '')
            print(run_info(self), file_path, lrb_em_str)
            stock_lrb_em_df = ak.stock_lrb_em(date=lrb_em_str)
        except Exception as e:
            print(run_info(self), "stock_lrb_em fail date ", date_str, str(e))
            return False
        stock_lrb_em_df.to_csv(file_path, encoding='utf-8', index=False)
        print(run_info(self), file_path, 'created')
        self.lrb_last_available_season = dt.strptime(date_str, '%Y-%m-%d').date()
        return True


if __name__ == "__main__":
    market_A = MarketA()
