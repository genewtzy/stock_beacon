# -*- coding: utf-8 -*-
# 公司类
# created Tang Zhiyong 2024.06-01
from __future__ import division

import os

import akshare as ak
from datetime import datetime as dt
from datetime import date
import json
import pandas as pd
from io import StringIO
import numpy as np
from dateutil.relativedelta import relativedelta
from .Utils import *
from .JsonUtils import *
from .MarketA import MarketA


def next_trade_date_try(period: str, trade_date: date):
    if period == 'daily':
        return trade_date + relativedelta(days=1)
    if period == 'weekly':
        return trade_date + relativedelta(weeks=1)
    return trade_date


class CompanyProfile(object):
    """
    instance
    """

    def __init__(self, code, is_index):
        self.valid = False  # 是否有效
        self.code = code  # 股票代码
        self.is_index = is_index
        if is_index:
            self.dir = 'data/index-' + code
        else:
            self.dir = 'data/' + code
        self.ipo_info_file = self.dir + "/IpoInfo.csv"
        self.finance_unit = 1000000  # 财务报表的单位为百万元
        self.finance_file = self.dir + "/finance_data.csv"
        self.total_share_after_ipo = 100  # 单位为股,IPO后的总股数
        self.ipo_price = 1  # 发行价 单位元
        self.equivalent_share = 100  # 根据后复权价格计算的股数
        self.current_market_value = 0  # 最新市值
        self.ipo_date = None
        self.profit_time = 'async'

        self.market = MarketA()  # 很多数据要用到

        if not is_index:
            try:
                code_name = pd.read_csv(self.market.info_file)
            except Exception as e:
                print(run_info(self), self.market.info_file, "读取失败", self.code, str(e))
                return
            try:
                self.name = code_name[code_name['code'] == int(self.code)]['name'].values[0]
            except Exception as e:
                print(run_info(self), self.market.info_file, "名称不存在", self.code, str(e))
                return
        else:  # 有的股票代码还在，但是退市了，名称里面就没有了比如葛洲坝600068
            self.index_name_set()
            self.index_ipo_date_set()
        # print(run_info(self), my_name, type(my_name))
        # my_name = my_name['name']
        # print(run_info(self), my_name, type(my_name))
        # my_name = my_name.values[0]
        print(run_info(self), self.name, type(self.name))
        # create directory if not exist
        if not os.path.exists(self.dir):
            os.makedirs(self.dir)
        # 更新IPO数据
        if not is_index:
            self.ipo_info_get()
        self.valid = True

    def update_all(self, start_date: date, end_date=dt.now().date(), profit_time='async'):
        """

        :param end_date:
        :param start_date:
        :param profit_time: 'sync','async'
        :return:
        """
        # A股市场的利润表，其实包含了营业收入等所有的财务数据
        # 指数不需要更新利润表
        if not self.is_index:
            self.market.lrb_update(start_date, end_date)
            self.profit_time = profit_time
        # 更新K线数据
        if self.update_kline_data('daily'):
            print(run_info(self), 'update_kline_data daily success')
        else:
            print(run_info(self), 'update_kline_data daily failed')
            return False

        if self.update_kline_data('weekly'):
            print(run_info(self), 'update_kline_data weekly success')
        else:
            print(run_info(self), 'update_kline_data weekly failed')
            return False

        # 指数更新已经完成了，以下是公司的一些初始化
        if self.is_index:
            print(run_info(self), 'this is index', self.code, self.name)
            return True

        # 更新季度营业收入等
        # end_date = datetime.now().date()
        if self.lrb_income_total_set(end_date=end_date, season=self.market.season1):
            print(run_info(self), 'lrb_income_total_set success', self.market.season1)
        else:
            print(run_info(self), 'lrb_income_total_set failed', self.market.season1)
            return False

        if self.lrb_income_total_set(end_date=end_date, season=self.market.season2):
            print(run_info(self), 'lrb_income_total_set success', self.market.season2)
        else:
            print(run_info(self), 'lrb_income_total_set failed', self.market.season2)
            return False

        if self.lrb_income_total_set(end_date=end_date, season=self.market.season3):
            print(run_info(self), 'lrb_income_total_set success', self.market.season3)
        else:
            print(run_info(self), 'lrb_income_total_set failed', self.market.season3)
            return False

        if self.lrb_income_total_set(end_date=end_date, season=self.market.season4):
            print(run_info(self), 'lrb_income_total_set success', self.market.season4)
        else:
            print(run_info(self), 'lrb_income_total_set failed', self.market.season4)
            return False

        # 更新营业收入表
        if self.income_total_overview_set():
            print(run_info(self), 'roll_income_total_set success')
        else:
            print(run_info(self), 'roll_income_total_set failed')
            return False



        # 获得财务数据
        self.stock_finance_data_set(end_date)

        # 更新扣非净利润数据
        if self.non_recurring_profit_data_update(self.market.season1):
            print(run_info(self), 'profit_data_update success', self.market.season1)
        else:
            print(run_info(self), 'profit_data_update failed', self.market.season1)
            return False

        if self.non_recurring_profit_data_update(self.market.season2):
            print(run_info(self), 'profit_data_update success', self.market.season2)
        else:
            print(run_info(self), 'profit_data_update failed', self.market.season2)
            return False

        if self.non_recurring_profit_data_update(self.market.season3):
            print(run_info(self), 'profit_data_update success', self.market.season3)
        else:
            print(run_info(self), 'profit_data_update failed', self.market.season3)
            return False

        if self.non_recurring_profit_data_update(self.market.season4):
            print(run_info(self), 'profit_data_update success', self.market.season4)
        else:
            print(run_info(self), 'profit_data_update failed', self.market.season4)
            return False

        # 更新滚动利润表
        item = '扣除非经常性损益后的净利润(元)'
        indexes = '日期'
        df = pd.read_csv(self.finance_file)
        if self.roll_item_update(item=item,df=df,indexes=indexes):
            print(run_info(self), 'roll_non_recurring_profit_update success', item,indexes)
        else:
            print(run_info(self), 'roll_non_recurring_profit_update failed', item, indexes)
            return False

        # 更新滚动营业收入表
        item = '营业总收入'
        indexes = '报告日期'
        df = pd.read_csv(self.lrb_csv_file_path_get(season=''))
        if self.roll_item_update(item=item, df=df, indexes=indexes):
            print(run_info(self), 'roll_non_recurring_profit_update success', item, indexes)
        else:
            print(run_info(self), 'roll_non_recurring_profit_update failed', item, indexes)
            return False

        # 生成市值相关的文件
        if self.kline_market_value_set(period='daily'):
            print(run_info(self), 'kline_market_value_set daily success', self.market.season4)
        else:
            print(run_info(self), 'kline_market_value_set daily failed', self.market.season4)
            return False

        if self.kline_market_value_set(period='weekly'):
            print(run_info(self), 'kline_market_value_set weekly success', self.market.season4)
        else:
            print(run_info(self), 'kline_market_value_set weekly failed', self.market.season4)
            return False
        # 更新静态市盈率
        profit_type = 'static_profit'
        if self.profit_rate_set(period='daily',profit_type=profit_type):
            print(run_info(self), 'profit_rate_set daily success',profit_type)
        else:
            print(run_info(self), 'profit_rate_set daily fail',profit_type)
            return False

        if self.profit_rate_set(period='weekly',profit_type=profit_type):
            print(run_info(self), 'profit_rate_set weekly success',profit_type)
        else:
            print(run_info(self), 'profit_rate_set weekly fail',profit_type)
            return False

        # 更新滚动市盈率
        profit_type = 'roll_profit'
        if self.profit_rate_set(period='daily', profit_type=profit_type):
            print(run_info(self), 'profit_rate_set daily success', profit_type)
        else:
            print(run_info(self), 'profit_rate_set daily fail', profit_type)
            return False

        if self.profit_rate_set(period='weekly', profit_type=profit_type):
            print(run_info(self), 'profit_rate_set weekly success', profit_type)
        else:
            print(run_info(self), 'profit_rate_set weekly fail', profit_type)
            return False


        return True

    def update_kline_data(self, period):
        """
        :param period: one of 'daily' 'weekly'
        :return:
        """
        ret = self.kline_data_update_csv_ak(period=period)
        if ret < 0:
            print(run_info(self), 'kline_data_update_json_ak ret = ', ret)
            return False

        # 更新KLine数据文件
        if ret == 0:
            self.kline_data_combine(period=period)

        return True

    def kline_data_update_csv_ak(self, period):
        """
        :param period: one of 'daily' 'weekly'
        :return:
        """
        # 检查股票是否存在
        if not self.is_index:
            if not self.market.stock_exist(stock_code=self.code):
                print(run_info(self), "股票不存在", self.code)
                return -1

        # 获取更新的日期
        kline_csv_file_path = self.kline_csv_file_path_get(period=period)
        update_date = file_modify_date_get(kline_csv_file_path)

        # 获取当前日期
        current_date = dt.now().date()
        current_date_str = current_date.strftime('%Y%m%d')
        updated_date_str = update_date.strftime('%Y%m%d')

        print(run_info(self), kline_csv_file_path, "Update date:", updated_date_str)
        print(run_info(self), "Current date:", current_date_str)
        if current_date <= update_date:
            print(run_info(self), "Updating KLineData not necessary")
            return 1

        # 股票的历史交易数据
        ret = self.kline_update_csv_data_get_history(period=period, start_date=updated_date_str,
                                                     end_date=current_date_str)
        if ret is False:
            return -1
        return 0

    def kline_data_combine(self, period):
        """
        :param period: one of 'daily' 'weekly'
        :return:
        """
        # 读取以前的CSV
        old_csv_path = self.kline_csv_file_path_get(period=period)
        updated_csv_path = self.kline_update_csv_file_path_get(period=period)

        old_csv_data = None
        try:
            old_csv_data = pd.read_csv(old_csv_path, encoding='utf-8')
        except Exception as e:
            print(run_info(self), 'read_csv', old_csv_path, str(e))

        updated_csv_data = None
        try:
            updated_csv_data = pd.read_csv(updated_csv_path, encoding='utf-8')
        except Exception as e:
            print(run_info(self), 'read_csv', updated_csv_path, str(e))

        # 清洗并合并数据
        # print(run_info(self), 'old_csv_data', old_csv_data, 'updated_csv_data', updated_csv_data)
        if old_csv_data is None:
            if updated_csv_data is None:
                print(run_info(self), 'no data')
                return None
            else:
                combined_csv_data = updated_csv_data
        else:
            if updated_csv_data is None:
                combined_csv_data = old_csv_data
            else:
                # 进行数据清洗
                for item in updated_csv_data:
                    if item not in old_csv_data:
                        old_csv_data.add(item)
                combined_csv_data = old_csv_data

        # 按日期进行排序
        combined_csv_data['日期'] = pd.to_datetime(combined_csv_data['日期'], format='%Y-%m-%d')
        # to_datetime会产生一列Unnamed: 0
        combined_csv_data = combined_csv_data.drop(columns='Unnamed: 0')
        combined_csv_data = combined_csv_data.sort_values(['日期'], axis='index')

        # 删除更新的csv文件
        try:
            os.remove(updated_csv_path)
        except OSError as e:
            print(run_info(self), 'remove ', updated_csv_path, str(e))

        # 删除原先的csv文件
        try:
            os.remove(old_csv_path)
        except OSError as e:
            print(run_info(self), 'remove ', old_csv_path, str(e))

        # 生成 json 文件
        dates = combined_csv_data['日期'].values
        opens = combined_csv_data['开盘'].values
        closes = combined_csv_data['收盘'].values
        highs = combined_csv_data['最高'].values
        lows = combined_csv_data['最低'].values
        amounts = combined_csv_data['成交额'].values

        # 排序的时候日期被转换成了numpy.datetime64,这里要转换成字符串
        dates = np.datetime_as_string(dates, 'D')

        print(run_info(self), 'dates[0]', dates[0], type[dates[0]])
        json_data = self.trade_data2json(dates=dates, opens=opens, closes=closes, lows=lows, highs=highs,
                                         volumes=amounts)
        if not self.is_index:
            ipo_before_json_data = self.ipo_before_json_data_get(period=period, first_date=dates[0])
            # 转换成json需要的格式
            json_data = ipo_before_json_data + json_data

        # 处理停牌的情况
        if not self.is_index:
            new_json_data = self.kline_pause_json_data_update(period=period, json_data=json_data)
            print(run_info(self), 'new data len', len(new_json_data), 'old len', len(json_data))
            json_data = new_json_data
        # 写入到更新的文件
        json_path = self.kline_json_file_path_get(period=period)
        try:
            write_json_file(json_path, data=json_data)
        except Exception as e:
            print(run_info(self), 'write_json_file ', json_path, str(e))

        # 生成价格归一化的json 文件
        path = self.kline_regular_data_json_file_path_get(period=period)
        factor_regular = 1 / float(json_data[0][1])
        kline_regular_data = json_data_regularize(factor=factor_regular, json_data=json_data)
        write_json_file(path, kline_regular_data)

        # 保存到到原先的 文件，这个要放最后，因为是根据这个文件的更新来确定是否要继续更新数据的
        combined_csv_data.to_csv(old_csv_path, encoding='utf-8')
        return 0

    def kline_pause_json_data_update(self, period: str, json_data: list):
        """

        :param period:
        :param json_data:
        :return:
        """
        new_json_data = []
        temp_json_data = self.make_temp_json_data(len(json_data) * 2)
        i = 0
        j = 0
        while i < len(json_data) - 1:
            item = json_data[i]
            i += 1
            next_item = json_data[i]

            new_json_data.append(item)
            item_date = dt.strptime(item[0], '%Y-%m-%d').date()
            next_item_date = dt.strptime(next_item[0], '%Y-%m-%d').date()

            next_date = market_next_open_day_get(period=period, today=item_date)
            # K线数据可能和指数的日期不一致，以指数为准
            temp_date = next_trade_date_try(period=period, trade_date=item_date)
            if temp_date > next_date:
                next_date = market_next_open_day_get(period=period, today=temp_date)
            while next_date < next_item_date:
                temp_item = temp_json_data[j]
                temp_item[1] = item[1]
                temp_item[2] = item[2]
                temp_item[3] = item[3]
                temp_item[4] = item[4]
                temp_item[0] = next_date.strftime('%Y-%m-%d')
                new_json_data.append(temp_item)
                j += 1
                next_date = market_next_open_day_get(period=period, today=next_date)
                print(run_info(temp_item), 'next_date', next_date, 'next_item_date', next_item_date)

        # 最后一个数据
        new_json_data.append(json_data[len(json_data) - 1])
        return new_json_data

    def kline_market_value_set(self, period: str):
        """
        :param period:
        """
        market_value = self.stock_current_market_value_get()
        if market_value <= 0:
            print(run_info(self), 'invalid market value', market_value)
            return False
        print(run_info(self), 'market_value', market_value)
        kline_json_path = self.kline_json_file_path_get(period=period)
        json_data = read_json_file(kline_json_path)
        # 当前市值除以最后的收市后复权价格得到后复权下的等效股本
        self.equivalent_share = market_value / json_data[len(json_data) - 1][2]
        print(run_info(self), 'equivalent_share', self.equivalent_share)

        # 计算每个交易日的市值
        for item in json_data:
            item[2] = item[2] * self.equivalent_share  # 2是收市价格
            item[1] = item[2]
            item[3] = item[2]
            item[4] = item[2]
            item[5] = item[2]
        # 生成市值的K线数据

        file_path = self.kline_market_value_json_file_path_get(period=period)
        write_json_file(file_path, json_data)

        # 生成归一化的市值数据
        file_path = self.kline_regular_market_value_json_file_path_get(period=period)
        factor_market = 1 / json_data[0][1]
        regular_market_value = json_data_regularize(factor=factor_market,
                                                    json_data=json_data)
        write_json_file(file_path, regular_market_value)
        return True

    def profit_rate_set(self, period: str, profit_type: str):
        """

        :param period:
        :param profit_type 'roll_profit','static_profit'
        :return:
        """
        start_date = self.start_date_adjust(period=period, start_date=self.market.start_date)
        end_date = dt.now().date()

        file_path = self.kline_profit_rate_json_file_path_get(period=period, profit_type=profit_type)
        if not self.file_update_necessary(file_path, end_date):
            print(run_info(self), file_path, 'update not necessary')
            return True
        # 生成市盈率文件
        market_values = self.regular_market_value_data_get(period=period, start_date=start_date, end_date=end_date,
                                                           factor=1)
        profit_values = self.regular_non_recurring_profit_value_data_get(period='-12-31', start_date=start_date,
                                                                         end_date=end_date, factor=1,
                                                                         profit_type=profit_type)
        if market_values is None:
            print(run_info(self), file_path, 'market_values', market_values)
            return False
        if profit_values is None:
            print(run_info(self), file_path, 'profit_values', profit_values)
            return False

        profit_values = profit_dates_values_sync(date_values=profit_values, dates_sync_to=market_values,
                                                 date_sync=True, profit_time=self.profit_time)
        # market_values 的内存实际上是被profit_values占了，怎么改都不行，暂时这样重新装载一遍。。。
        market_values = self.regular_market_value_data_get(period=period, start_date=start_date, end_date=end_date,
                                                           factor=1)
        i = 0
        print(run_info(self), 'profit_values[0]', profit_values[0], 'market_values[0]', market_values[0])
        while i < len(profit_values) and i < len(market_values):
            profit = profit_values[i]
            market = market_values[i]
            profit[1] = round(market[2] / profit[2], 1)
            profit[2] = profit[1]
            profit[3] = profit[1]
            profit[4] = profit[1]
            profit[5] = profit[1]
            i += 1
        print(run_info(self), file_path, 'profit_values[0]', profit_values[0])
        write_json_file(file_path, profit_values)

        return True

    def profit_rate_get(self, period: str, start_date: date, end_date: date, factor=0, profit_type='static_profit'):
        """

        :param factor:
        :param end_date:
        :param start_date:
        :param period: 'daily' or 'weekly'
        :return: json_data list
        """
        path = self.kline_profit_rate_json_file_path_get(period=period,profit_type=profit_type)

        return self.regular_data_get(path=path, start_date=start_date, end_date=end_date, factor=factor)

    def kline_update_csv_data_get_history(self, period: str, start_date: str, end_date: str):
        """
        功能： 生成 更新的KLINE CSV和JSON文件
        :param period: one of 'daily' 'weekly'
        :param start_date:
        :param end_date:
        :return:
        """
        try:
            if self.is_index:
                stock_data = ak.index_zh_a_hist(symbol=self.code, period=period,
                                                start_date=start_date,
                                                end_date=end_date)

            else:
                stock_data = ak.stock_zh_a_hist(symbol=self.code,
                                                period=period,
                                                start_date=start_date,
                                                end_date=end_date,
                                                adjust="hfq")
        except Exception as e:
            print("获取股票交易数据失败", self.code, str(e))
            return False

        # 写入到更新的csv文件
        update_csv_path = self.kline_update_csv_file_path_get(period=period)
        try:
            stock_data.to_csv(path_or_buf=update_csv_path, encoding='utf-8')
        except Exception as e:
            print(run_info(self), 'write ', update_csv_path, str(e))
            return False

        return True

    def trade_data2json(self, dates: list, opens: list, closes: list,
                        lows: list, highs: list, volumes: list):
        """

        :param dates: 日期列表
        :param opens: 开盘价格列表
        :param closes: 收盘价格列表
        :param lows: 最低价格列表
        :param highs: 最高价格列表
        :param volumes: 成交量列表
        :return:
        """
        # 创建一个StringIO对象,按照companyShow的格式打印数据
        buffer = StringIO()
        i = 0
        print('[', file=buffer)
        while i < len(dates) - 1:
            print("\t[\n\t\t\"%10s\",\n\t\t%16.2f,\n\t\t%16.2f,\n\t\t%16.2f,\n\t\t%16.2f,\n\t\t%16.0f\n\t],"
                  % (dates[i], float(opens[i]), float(closes[i]), float(lows[i]), float(highs[i]), float(volumes[i])),
                  file=buffer)
            i += 1
        # the last one
        if i < len(dates):
            print("[\n\t\t\"%10s\",\n\t\t%16.2f,\n\t\t%16.2f,\n\t\t%16.2f,\n\t\t%16.2f,\n\t\t%16.0f\n\t]"
                  % (dates[i], float(opens[i]), float(closes[i]), float(lows[i]), float(highs[i]), float(volumes[i])),
                  file=buffer)
        print(']', file=buffer)

        json_data = json.loads(buffer.getvalue())
        print(run_info(self), 'json_data[0]', json_data[0])

        return json_data

    def ipo_info_get(self):
        """

        :return:
        """
        if not os.path.exists(self.ipo_info_file):
            try:
                ipo_info = ak.stock_ipo_info(self.code)

                print(run_info(self), ipo_info)
                ipo_info.to_csv(self.ipo_info_file)
            except Exception as e:
                print(run_info(self), 'stock_ipo_info', str(e))
                return
        try:
            ipo_info = pd.read_csv(self.ipo_info_file)
        except Exception as e:
            print(run_info(self), 'ipo_info', str(e))
            return

        self.ipo_price = float(ipo_info[ipo_info['item'] == '发行价(元)']['value'].iloc[0])
        ipo_date = ipo_info[ipo_info['item'] == '上市日期']['value']
        self.ipo_date = dt.strptime(str(ipo_date.iloc[0]), '%Y-%m-%d').date()

    def lrb_json_file_update_necessary(self, item, season):
        """

        :param item:
        :param season:
        :return:
        """
        file_path = self.lrb_json_file_path_get(item=item, season=season)

        if not os.path.exists(file_path):
            print(run_info(self), 'file_path ', file_path, 'not exist')
            return True
        last_update_date_float = os.path.getmtime(file_path)
        last_update_date = dt.fromtimestamp(last_update_date_float).date()
        if last_update_date >= self.market.lrb_last_available_season:
            print(run_info(self), 'lrb updated at ', self.market.lrb_last_available_season, file_path,
                  ' update not necessary')
            return False

        return True

    def file_update_necessary(self, file_path, last_available_date):
        """

        :param file_path:
        :param last_available_date: the last date data available

        :return:
        """
        print(run_info(self), 'file_path ', file_path)
        if not os.path.exists(file_path):
            print(run_info(self), 'file_path ', file_path, 'not exist')
            return True
        last_update_date_float = os.path.getmtime(file_path)
        last_update_date = dt.fromtimestamp(last_update_date_float).date()
        if last_update_date >= last_available_date:
            print(run_info(self), 'lrb updated at ', self.market.lrb_last_available_season, file_path,
                  ' update not necessary')
            return False

        return True

    def lrb_income_total_set(self, end_date: date, season):
        """

        :type end_date: datetime
        :param end_date: date like '2009-09-01
        :param season: the date of a season end, like '-03-31'
        """

        # 检查是否必要更新财务数据
        lrb_update = self.lrb_json_file_update_necessary(item='净利润', season=season)
        income_update = self.lrb_json_file_update_necessary(item='营业总收入', season=season)

        if not lrb_update and not income_update:
            print(run_info(self), 'lrb update is unnecessary')
            return True

        start_date = self.market.start_date
        lrb_data_combine = None
        while start_date < end_date:
            lrb_data = self.lrb_elem_get(this_date=start_date, season=season)
            start_date = start_date + relativedelta(years=1)
            if lrb_data is None:
                print(run_info(self), start_date, 'lrb_data is ', lrb_data)
                continue

            lrb_data_combine = pd.concat([lrb_data_combine, lrb_data])

        lrb_data_combine.to_csv(self.lrb_csv_file_path_get(season=season))

        # 转换成JSON格式
        report_date_title = '报告日期'
        item_title = '净利润'
        report_dates = lrb_data_combine[report_date_title].values
        values = lrb_data_combine[item_title].values
        report_dates, values = dates_values_illegal_item_remove(dates=report_dates, values=values)
        file_path = self.lrb_json_file_path_get(item=item_title, season=season)
        json_data = self.trade_data2json(dates=report_dates, opens=values, closes=values,
                                         lows=values, highs=values, volumes=values)
        write_json_file(file_path, json_data)

        item_title = '营业总收入'
        report_dates = lrb_data_combine[report_date_title].values
        values = lrb_data_combine[item_title].values
        report_dates, values = dates_values_illegal_item_remove(dates=report_dates, values=values)
        file_path = self.lrb_json_file_path_get(item=item_title, season=season)
        json_data = self.trade_data2json(dates=report_dates, opens=values, closes=values,
                                         lows=values, highs=values, volumes=values)
        write_json_file(file_path, json_data)
        return True

    def income_total_overview_set(self):
        """
        """

        # 检查是否必要更新财务数据
        item = '营业总收入'
        income_update = self.lrb_json_file_update_necessary(item=item, season='')

        if not income_update:
            print(run_info(self), 'income_update is unnecessary')
            return True

        file_path = self.lrb_csv_file_path_get( season='')
        s1_csv_path = self.lrb_csv_file_path_get(season=self.market.season1)
        s2_csv_path = self.lrb_csv_file_path_get(season=self.market.season2)
        s3_csv_path = self.lrb_csv_file_path_get(season=self.market.season3)
        s4_csv_path = self.lrb_csv_file_path_get(season=self.market.season4)

        s1_df = pd.read_csv(s1_csv_path)
        s2_df = pd.read_csv(s2_csv_path)
        s3_df = pd.read_csv(s3_csv_path)
        s4_df = pd.read_csv(s4_csv_path)

        df = pd.concat([s1_df, s2_df, s3_df, s4_df])
        col = '报告日期'
        df[col] = pd.to_datetime(df[col],format='%Y-%m-%d')
        df = df.sort_values(by=col,ascending=False)

        df.to_csv(file_path, index=False)
        return True

    def lrb_item_to_json(self, dates: np.ndarray, values: np.ndarray, file_path):
        """

        :param dates:
        :param values:
        :param file_path:
        :return:
        """
        # 数据清洗
        print(run_info(self), type(dates), type(values))

        dates, values = dates_values_illegal_item_remove(dates=dates.tolist(), values=values.tolist())
        # 创建一个StringIO对象,按照json的格式打印数据
        buffer = StringIO()
        i = 0
        print('[', file=buffer)
        while i < len(dates) - 1:
            try:
                print("\t[\n\t\t\"%s\", \n\t\t%12.2f\n\t],"
                      % (dates[i], float(values[i]) / self.finance_unit),
                      file=buffer)
            except Exception as e:
                print(run_info(self), dates[i], values[i], str(e))

            i += 1
        # the last one
        if i < len(dates):
            try:
                print("[\n\t\t\"%s\",\n\t\t%12.2f\n\t]"
                      % (dates[i], float(values[i]) / self.finance_unit),
                      file=buffer)
            except Exception as e:
                print(run_info(self), dates[i], values[i], str(e))

        print(']', file=buffer)

        json_data = json.loads(buffer.getvalue())
        print(run_info(self), 'json_data[0]', json_data[0])
        # 写入到更新的文件
        write_json_file(file_path, data=json_data)
        return json_data

    def lrb_elem_get(self, this_date: date, season):
        """

        :param this_date: datetime
        :param season: the date of a season end, like 0331
        :return:
        """
        report_date_str = this_date.strftime('%Y') + season
        file_path = self.market.lrb_dir + '/' + report_date_str + '.csv'
        try:
            lrb_season = pd.read_csv(file_path, encoding='utf-8')
        except Exception as e:
            print(run_info(self), "read_csv fail", file_path, str(e))
            return None

        lrb_data = lrb_season[lrb_season['股票代码'] == int(self.code)]
        report_date = dt.strptime(report_date_str, '%Y-%m-%d').date()
        lrb_data.insert(lrb_data.shape[1], '报告日期', report_date.strftime('%Y-%m-%d'))
        return lrb_data

    def lrb_csv_file_path_get(self, season):
        """

        :param season: '0331','0630','0930','1231' available
        :return: file_path
        """

        return self.dir + '/lrb' + season + '.csv'

    def lrb_json_file_path_get(self, item, season):
        """

        :param item:  营业收入、扣非净利润 等
        :param season: '-03-31','06-30','-09-30','-12-31' available
        :return: file_path, str
        """
        return self.dir + '/' + item + season + '.json'

    def kline_csv_file_path_get(self, period):
        """

        :param period:  daily, weekly, monthly
        :return: file_path, str
        """
        return self.dir + '/kline-' + period + '.csv'

    def profile_csv_file_path_get(self):
        """

        :return: file_path, str
        """
        return self.dir + '/profile' + '.csv'

    def kline_json_file_path_get(self, period):
        """

        :param period:  daily, weekly, monthly
        :return: file_path, str
        """
        return self.dir + '/kline-' + period + '.json'

    def kline_regular_data_json_file_path_get(self, period):
        """

        :param period:  daily, weekly, monthly
        :return: file_path, str
        """
        return self.dir + '/kline-regular-data-' + period + '.json'

    def kline_market_value_json_file_path_get(self, period):
        """

        :param period:  daily, weekly, monthly
        :return: file_path, str
        """
        return self.dir + '/kline-market-' + period + '.json'

    def kline_profit_rate_json_file_path_get(self, period, profit_type: str):
        """

        :param period:  daily, weekly, monthly
        :return: file_path, str
        """
        return self.dir + '/kline-rate-' + profit_type + period + '.json'

    def kline_regular_market_value_json_file_path_get(self, period):
        """

        :param period:  daily, weekly, monthly
        :return: file_path, str
        """
        return self.dir + '/kline-regular-market-' + period + '.json'

    def kline_update_info_file_path_get(self, period):
        """

        :param period:  daily, weekly, monthly
        :return: file_path, str
        """
        return self.dir + '/kline-' + period + '-update-info.txt'

    def kline_update_csv_file_path_get(self, period):
        """

        :param period:  daily, weekly, monthly
        :return: file_path, str
        """
        return self.dir + '/kline-' + period + '-update.csv'

    def kline_update_json_file_path_get(self, period):
        """

        :param period:  daily, weekly, monthly
        :return: file_path, str
        """
        return self.dir + '/kline-' + period + '-update.csv'

    def non_recurring_csv_file_path_get(self, season):
        """

        :param season: '0331','0630','0930','1231' available
        :return: file_path
        """

        return self.dir + '/non_recurring' + season + '.csv'

    def non_recurring_profit_data_update(self, season):
        """

        :param season:
        :return:
        """
        item = '扣除非经常性损益后的净利润(元)'
        file_path = self.lrb_json_file_path_get(item=item, season=season)
        year_str = dt.strftime(self.market.start_date, '%Y')
        print(run_info(self), "start_year start", year_str, self.code)

        # 更新财务报表
        if self.file_update_necessary(file_path=self.finance_file,
                                      last_available_date=self.market.lrb_last_available_season):
            try:
                # 下载开始至今的金融数据
                finance_data = ak.stock_financial_analysis_indicator(symbol=self.code, start_year=year_str)
                finance_data.to_csv(self.finance_file, encoding='utf-8')
            except Exception as e:
                print(run_info(self), "stock_financial_analysis_indicator start_year fail", year_str, str(e))
                return False

        if not self.lrb_json_file_update_necessary(item=item, season=season):
            print(run_info(self), file_path, "update not necessary")
            return True

        try:
            finance_data = pd.read_csv(self.finance_file, encoding='utf-8')
        except Exception as e:
            print(run_info(self), "read file_path fail", file_path, str(e))
            return False

        # 处理数据
        self.non_recurring_profit_data2json(finance_data=finance_data, title=item, season=season)
        return True

    def non_recurring_profit_data2json(self, finance_data: pd.DataFrame, title: str, season: str):
        """

        :param finance_data:
        :param title:
        :param season:
        :return:
        """
        first_date = self.market.start_date
        last_date = dt.now().date()
        date_str = dt.strftime(first_date, '%Y') + season
        combine_item = finance_data.loc[finance_data['日期'] == date_str]
        print(run_info(self), 'combine_item ', combine_item, date_str)

        while first_date < last_date:
            first_date = first_date + relativedelta(years=1)
            date_str = dt.strftime(first_date, '%Y') + season
            item = finance_data.loc[finance_data['日期'] == date_str]
            if item is None:
                continue

            combine_item = pd.concat([combine_item, item], ignore_index=True)

        combine_item = combine_item[['日期', title]]

        file_path = self.non_recurring_csv_file_path_get(season=season)
        combine_item.to_csv(file_path)
        dates = combine_item['日期'].values.tolist()
        values = combine_item[title].values.tolist()
        dates, values = dates_values_illegal_item_remove(dates=dates, values=values)
        file_path = self.lrb_json_file_path_get(item=title, season=season)
        profit_data_json = self.trade_data2json(dates=dates, opens=values, closes=values,
                                                lows=values, highs=values, volumes=values)
        print(run_info(self), 'profit_data_json', profit_data_json, 'file_path', file_path)
        write_json_file(file_path, data=profit_data_json)
        return profit_data_json

    def stock_finance_data_set(self, end_date: date):
        """

        :return:
        """
        file_path = self.profile_csv_file_path_get()
        if not self.file_update_necessary(file_path=file_path, last_available_date=end_date):
            print(run_info(self), file_path, 'update not necessary')
            df = pd.read_csv(file_path)
            self.current_market_value = float(df[df['item'] == '总市值']['value'])
            print(run_info(self), 'current_market_value', self.current_market_value)
            return True

        try:
            df = ak.stock_individual_info_em(self.code)
        except Exception as e:
            print(run_info(self), 'stock_individual_info_em', str(e))
            return False

        df.to_csv(file_path)
        self.current_market_value = float(df[df['item'] == '总市值']['value'])
        print(run_info(self), 'current_market_value', self.current_market_value)
        return self.current_market_value

    def stock_current_market_value_get(self):
        """

        :return:
        """
        file_path = self.profile_csv_file_path_get()
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            print(run_info(self), 'read_csv', str(e))
            return 0
        self.current_market_value = float(df[df['item'] == '总市值']['value'])
        print(run_info(self), 'current_market_value', self.current_market_value)
        return self.current_market_value

    def date_before_ipo_get(self, period: str, first_date=''):
        """

        :param first_date:
        :param period:
        :return:
        """
        # 计算日期
        ipo_date_before = dt.strptime(self.ipo_date.strftime('%Y-%m-%d'), '%Y-%m-%d').date()
        if 'daily' == period:
            ipo_date_before = ipo_date_before + relativedelta(days=-1)
        else:
            if 'weekly' == period:
                ipo_date_before = ipo_date_before + relativedelta(weeks=-1)
        print(run_info(self), 'ipo_date_before', ipo_date_before, 'first_date', first_date)
        return ipo_date_before

    def ipo_before_json_data_get(self, period: str, first_date: str):
        """

        :param first_date:
        :param period:
        :return:
        """
        # 计算日期
        ipo_date_before = self.last_trade_datetime_before_ipo_get(period=period,
                                                                  first_trade_date=first_date)
        # 创建一个StringIO对象,按照companyShow的格式打印数据
        buffer = StringIO()

        print("[\n\t[\n\t\t\"%s\",\n\t\t%10.2f,\n\t\t%10.2f,\n\t\t%10.2f,\n\t\t%10.2f,\n\t\t%12.0f\n\t]\n\t]"
              % (
                  ipo_date_before.strftime('%Y-%m-%d'), self.ipo_price, self.ipo_price, self.ipo_price, self.ipo_price,
                  0),
              file=buffer)

        json_data = json.loads(buffer.getvalue())
        print(run_info(self), 'json_data[0]', json_data[0])

        return json_data

    def regular_data_get(self, path: str, start_date: date, end_date: date, factor=0.0, first_data_zero=False):
        """

        :param factor: 0表示用第一个元素作为factor，
        :param path: 需要打开的文件路径
        :param start_date:
        :param end_date:
        """
        total_data = read_json_file(file_path=path)
        if total_data is None:
            print(run_info(self), path, 'total_data', total_data)
            return None
        i = 0
        end_index = -1
        start_index = 0
        while i < len(total_data):
            item = total_data[i]

            this_date = dt.strptime(item[0], '%Y-%m-%d').date()

            if this_date <= start_date:
                start_index = i
            if this_date <= end_date:
                end_index = i
            else:
                break
            i += 1

        print(run_info(self), self.code, 'total data len', len(total_data),
              'start_date', start_date, 'end_date', end_date,
              'start_index', start_index, 'end_index', end_index,
              'item num', end_index - start_index + 1)
        if -1 == start_index or -1 == end_index:
            return None

        regular_data = total_data[start_index:end_index]
        print(run_info(self), self.code, 'regular_data[0]', regular_data[0])
        if end_index < len(total_data):
            regular_data.append(total_data[end_index])
        print(run_info(self), self.code, 'end_index', end_index, 'len', len(regular_data))
        if factor == 0:
            factor = 1 / float(regular_data[0][1])
        return json_data_regularize(factor=factor, json_data=regular_data, first_data_zero=first_data_zero)

    def regular_kline_data_get(self, period: str, start_date: date, end_date: date, factor=0.0, first_data_zero=False):
        """

        :param factor:
        :param end_date:
        :param start_date:
        :param period: 'daily' or 'weekly'
        :return: json_data list
        """
        path = self.kline_json_file_path_get(period=period)

        return self.regular_data_get(path=path, start_date=start_date, end_date=end_date, factor=factor,
                                     first_data_zero=first_data_zero)

    def regular_income_data_get(self, season: str, start_date: date, end_date: date, factor=0.0,
                                first_data_zero=False,profit_type='static_profit'):
        """

        :param factor:
        :param end_date:
        :param start_date:
        :param season: '-12-31','-06-31'
        :return: json_data list
        """
        if 'static_profit' == profit_type:
            path = self.lrb_json_file_path_get('营业总收入', season=season)
        else:
            path = self.lrb_json_file_path_get('营业总收入', season='')

        return self.regular_data_get(path=path, start_date=start_date, end_date=end_date, factor=factor,
                                     first_data_zero=first_data_zero)

    def regular_market_value_data_get(self, period: str, start_date: date, end_date: date, factor=0):
        """

        :param factor:
        :param end_date:
        :param start_date:
        :param period: 'daily' or 'weekly'
        :return: json_data list
        """
        path = self.kline_market_value_json_file_path_get(period=period)

        return self.regular_data_get(path=path, start_date=start_date, end_date=end_date, factor=factor)

    def regular_non_recurring_profit_value_data_get(self, period: str, start_date: date, end_date: date,
                                                    factor=0, first_data_zero=False,
                                                    profit_type='roll_profit'):
        """

        :param factor:
        :param end_date:
        :param start_date:
        :param period: 'daily' or 'weekly'
        :param profit_type: 'roll_profit', 'static_profit'
        :return: json_data list
        """
        item = '扣除非经常性损益后的净利润(元)'
        print(run_info(self), 'start_date ', start_date, 'end_date ', end_date, item)
        if 'roll_profit' == profit_type:
            path = self.lrb_json_file_path_get(item=item, season='')
        else:
            path = self.lrb_json_file_path_get(item=item, season=period)

        print(run_info(self), self.code, 'path', path)

        return self.regular_data_get(path=path, start_date=start_date, end_date=end_date, factor=factor,
                                     first_data_zero=first_data_zero)

    def index_name_set(self):
        """
        设置指数名称

        """
        self.name = '指数'
        if '399006' == self.code:
            self.name = '创业板指'
        else:
            if '000001' == self.code:
                self.name = '上证综指'
            else:
                if '399001' == self.code:
                    self.name = '深圳成指'

    def index_ipo_date_set(self):
        """
        设置指数名称

        """
        self.ipo_date = dt.strptime('2010-06-01', '%Y-%m-%d').date()
        if '399006' == self.code:
            self.ipo_date = dt.strptime('2010-06-01', '%Y-%m-%d').date()
        else:
            if '000001' == self.code:
                self.ipo_date = dt.strptime('1991-01-03', '%Y-%m-%d').date()
            else:
                if '399001' == self.code:
                    self.ipo_date = dt.strptime('1991-04-30', '%Y-%m-%d').date()

    def last_trade_datetime_before_ipo_get(self, period: str, first_trade_date: str):
        """

        :param period:
        :param first_trade_date:
        :return:
        """
        first_day = market_first_open_day_get(period)
        trade_date = dt.strptime(first_trade_date, '%Y-%m-%d').date()
        if 'daily' == period:
            trade_date = trade_date + relativedelta(days=-1)
            while not is_market_a_open_day_bisect(period=period, today=trade_date):
                trade_date = trade_date + relativedelta(days=-1)
                if trade_date <= first_day:
                    break

        if 'weekly' == period:
            trade_date = trade_date + relativedelta(weeks=-1)
            while not is_market_a_open_day_bisect(period=period, today=trade_date):
                trade_date = trade_date + relativedelta(weeks=-1)
                if trade_date <= first_day:
                    break
        return trade_date

    def first_trade_datetime_get(self, period: str):
        """

        :param period:
        :return:
        """
        file_path = self.kline_json_file_path_get(period=period)
        json_data = read_json_file(file_path)
        item = json_data[0]
        return dt.strptime(item[0], '%Y-%m-%d').date()

    def first_non_recurring_profit_date_get(self):
        item = '扣除非经常性损益后的净利润(元)'
        file_path = self.lrb_json_file_path_get(item, self.market.season4)
        json_data = read_json_file(file_path)
        first_non_recurring_profit_date = dt.strptime(json_data[0][0], "%Y-%m-%d").date()
        return first_non_recurring_profit_date

    def make_temp_json_data(self, list_len):
        dates = ['2001-03-04' for i in range(list_len)]
        opens = [0.0 for i in range(list_len)]

        json_data = self.trade_data2json(dates=dates, opens=opens, closes=opens, lows=opens, highs=opens,
                                         volumes=opens)
        return json_data

    def start_date_adjust(self, start_date: date, period: str):
        if self.is_index:
            days = 1
            if period == 'weekly':
                days = 7
            while start_date < self.ipo_date:
                start_date += relativedelta(days=days)
            return start_date

        start_date_before_ipo = start_date
        if start_date < self.ipo_date:
            start_date_before_ipo = self.date_before_ipo_get(period=period)

        non_recurring_profit_date = self.first_non_recurring_profit_date_get() + relativedelta(
            years=1) + relativedelta(
            months=4)
        print(run_info(self), 'non_recurring_profit_date', non_recurring_profit_date, 'start_date_before_ipo',
              start_date_before_ipo)
        if non_recurring_profit_date > start_date_before_ipo:
            return non_recurring_profit_date
        else:
            return start_date_before_ipo

    def roll_item_update(self, item: str, indexes: str, df: pd.DataFrame):
        file_path = self.lrb_json_file_path_get(item=item, season='')
        if not self.file_update_necessary(file_path=file_path,
                                          last_available_date=self.market.lrb_last_available_season):
            print(run_info(self), file_path, "update not necessary")
            return True

        dates = df[indexes]
        values = df[item]
        dates, values = dates_values_illegal_item_remove(dates=dates, values=values)

        # 补齐数据，如果没有1/2/3 季度的数据就拿年度指标/4来补充
        roll_dates = []
        roll_values = []
        i = 0
        while i < len(dates):
            roll_dates.append(dates[i])
            roll_values.append(float(values[i]))
            if self.market.season4 in dates[i]:
                s4_date = dt.strptime(dates[i], '%Y-%m-%d').date()
                profit = float(values[i]) / 4
                year_str = s4_date.strftime('%Y')

                # 季度数据不存在的情况
                s3_str = year_str + self.market.season3
                if s3_str not in dates:
                    roll_dates.append(s3_str)
                    roll_values.append(profit * 3)
                s2_str = year_str + self.market.season2
                if s2_str not in dates:
                    roll_dates.append(s2_str)
                    roll_values.append(profit * 2)
                s1_str = year_str + self.market.season1
                if s1_str not in dates:
                    roll_dates.append(s1_str)
                    roll_values.append(profit * 1)
            i += 1

        #  计算每个季度的扣非净利润
        data_len = len(roll_values)
        season_values = [roll_values[data_len - 1]]
        i = len(roll_values) - 2
        while i >= 0:
            if self.market.season1 not in roll_dates[i]:
                season_values.append(roll_values[i] - roll_values[i + 1])
            else:
                season_values.append(roll_values[i])
            i -= 1

        # 计算滚动扣非净利润
        last_values = []
        index = 0
        last_values.append(season_values[index] * 4)
        index = 1
        last_values.append(season_values[index] + season_values[index + 1] * 3)
        index = 2
        last_values.append(season_values[index] + season_values[index - 1] + season_values[index - 2] * 2)
        index = 3
        while index < data_len:
            last_values.append(
                season_values[index] + season_values[index - 1] + season_values[index - 2] + season_values[index - 3])
            index += 1

        last_dates = []
        for roll_date in roll_dates:
            last_dates.insert(0, roll_date)

        profit_data_json = self.trade_data2json(dates=last_dates, opens=last_values, closes=last_values,
                                                lows=last_values, highs=last_values, volumes=last_values)
        write_json_file(file_path, data=profit_data_json)
        return True


if __name__ == "__main__":
    # 初始化开市时间列表
    start_date = dt.strptime('1997-12-01', '%Y-%m-%d').date()
    index = CompanyProfile(code='000001', is_index=True)
    index.update_all(start_date)
    market_open_days_init('daily')
    market_open_days_init('weekly')

    company = CompanyProfile(code='300253', is_index=False)
    # company.Kline_update_json_data_get_history(period='daily',start_date='20110101',end_date='20240601')
    # company.update_kline_data('daily')
    # company.stock_profile_values_get()
    # company.update_kline_data('weekly')
    # company.updateKLineData()
    # end_date = datetime.now().date()
    # company.lrb_total_get(end_date=end_date, season='-03-31')
    # company.lrb_total_get(end_date=end_date, season='-06-30')
    # company.lrb_total_get(end_date=end_date, season='-09-30')
    # company.lrb_total_get(end_date=end_date, season='-12-31')
    print(run_info(company), 8004 * 10000 / 0.69)
    ret = company.update_all(dt.strptime('1997-12-01', '%Y-%m-%d').date())
    if not ret:
        print(run_info(company), 'update_all failed')
        exit(0)
    exit(0)
    test_period = 'weekly'
    company.update_kline_data(test_period)
    test_start_date = dt.strptime('2015-01-01', '%Y-%m-%d')
    test_end_date = dt.strptime('2018-01-01', '%Y-%m-%d')  # datetime.now()
    test_json_data = company.regular_kline_data_get(
        period=test_period, start_date=test_start_date, end_date=test_end_date)

    # company.profit_data_update('-03-31')
