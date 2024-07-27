import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox

import CompanyShow
from MainWindow import *

from CompanyShow import *
import Utils as Ut
from datetime import datetime as dt


class MyWindow(QMainWindow, Ui_MainWindow):
    """

    """

    def __init__(self, parent=None):
        super(MyWindow, self).__init__(parent)
        self.setupUi(self)
        self.pushButton_CompanyChg.clicked.connect(self.company_develop_start)
        self.pushBotton_CVsC.clicked.connect(self.company_vs_company_start)
        self.dateEdit_EndDate.setDate(dt.now().date())
        self.dateEdit_start_date.setDate(dt.strptime('2020-12-31', '%Y-%m-%d'))

        # 先创建上证综指，因为判断是否开市需要用到其数据
        index_sh = CompanyProfile.CompanyProfile(code='000001', is_index=True)
        try:
            # 更新所有数据

            ret = index_sh.update_all(dt.strptime('1997-01-01', '%Y-%m-%d').date())
            if ret is False:
                print(Ut.run_info(self), 'update_all ret', ret, index_sh.code)
                return
        except Exception as e:
            print(Ut.run_info(self), "更新股票交易数据失败", index_sh.code, str(e))
            return

        # 初始化开市时间列表
        Ut.market_open_days_init('daily')
        Ut.market_open_days_init('weekly')

    def company_vs_company_start(self):
        """

        :return:
        """

        #

        # 获得公司A的股票代码
        code_a = self.companyA.toPlainText()
        company_a = CompanyProfile.CompanyProfile(code=code_a, is_index=False)
        if not company_a.valid:
            print(Ut.run_info(self), 'company_a is invalid')
            return False


        print(Ut.run_info(self), 'company_a code', company_a.code, company_a.ipo_date, type(company_a.ipo_date))

        # 选择公司B或者指数
        if self.radioButton_CompanyB.isChecked():
            code_b = self.companyB.toPlainText()
            is_index = False

        else:
            code_b = '000001'
            index = self.indexSelector.currentIndex()
            is_index = True
            if index == 0:
                code_b = '000001'
            if index == 1:
                code_b = '399001'
            if index == 2:
                code_b = '399006'

        company_b = CompanyProfile.CompanyProfile(code_b, is_index=is_index)
        if not company_b.valid:
            print(Ut.run_info(self), 'company_b is invalid')
            return False
        print(Ut.run_info(self), 'company_b code', company_b.code)

        # 获得比较的时间
        # start_date_str = '2011-01-01'
        start_date_str = self.dateEdit_start_date.date().toString(Qt.ISODate)
        end_date_str = self.dateEdit_EndDate.date().toString(Qt.ISODate)
        start_date = dt.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = dt.strptime(end_date_str, '%Y-%m-%d').date()
        print(Ut.run_info(self), 'start_date', start_date, 'end_date', end_date)

        # 选择周期
        if self.radioButton_daily_kline.isChecked():
            period = 'daily'
        else:
            period = 'weekly'

        try:
            # 更新所有数据
            ret = company_a.update_all(start_date)
            if ret is False:
                print(Ut.run_info(self), 'update_all ret', ret, company_a.code)
                return None
        except Exception as e:
            print(Ut.run_info(self), "更新股票交易数据失败", company_a.code, str(e))
            return None

        try:
            # 更新所有数据
            ret = company_b.update_all(start_date)
            if ret is False:
                print(Ut.run_info(self), 'update_all ret', ret, company_b.code)
                return None
        except Exception as e:
            print(Ut.run_info(self), "更新股票交易数据失败", company_b.code, str(e))
            return None

        # 调整开始时间, 因为开始时间可能在股票上市之前
        if not company_a.is_index:
            if start_date < company_a.ipo_date:
                start_date = company_a.first_trade_datetime_get(period=period)

        if not company_b.is_index:
            if start_date < company_b.ipo_date:
                start_date = company_b.first_trade_datetime_get(period=period)

            print(Ut.run_info(self), 'start_date', start_date, type(start_date))
        try:
            # kline_json_file_path = company_c.kline_regular_market_value_json_file_path_get('daily')
            # chart_data = CompanyShow.get_local_data(kline_json_file_path)
            CompanyShow.draw_charts_compare(company_a, company_b, period=period,
                                            start_date=start_date, end_date=end_date)
        except Exception as e:
            print(Ut.run_info(self), "draw_charts_compare", str(e))
            return None
        '''
        try:
            CompanyShow.draw_charts(chart_data)
        except Exception as e:
            print(Ut.run_info(self), "draw_charts ", str(e))
            return None
        '''

    def company_develop_start(self):
        """

        """
        QMessageBox.about(self, '登陆', '请输入姓名')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    myWin = MyWindow()
    myWin.show()
    sys.exit(app.exec_())
