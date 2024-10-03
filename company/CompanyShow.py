import datetime
import webbrowser
from datetime import date
from typing import List, Union

import requests
from django.http import HttpResponse
from pyecharts import options as opts
from pyecharts.charts import Kline, Line, Bar, Grid
from pyecharts.commons.utils import JsCode

from django.utils.safestring import mark_safe

from .CompanyProfile import CompanyProfile
from .Utils import *
from dateutil.relativedelta import relativedelta
from django.shortcuts import render
from urllib.parse import urlparse
from datetime import datetime as dt
import re


# 获取本地数据并解析
def get_local_data(file_path):
    """

    :param file_path:
    :return:
    """
    data = read_json_file(file_path)
    # 解析数据
    return split_data(data=data)


# 获取数据的函数，从指定URL获取数据并解析
def get_data():
    """

    :return:
    """
    response = requests.get(
        url="https://echarts.apache.org/examples/data/asset/data/stock-DJI.json"
    )
    json_response = response.json()
    # 解析数据
    return split_data(data=json_response)


# 将原始数据拆分成需要的格式
def split_data(data):
    """

    :param data:
    :return:
    """
    category_data = []  # 用于存储X轴（时间）数据
    values = []  # 存储K线图的OHLC数据
    volumes = []  # 存储交易量数据

    for i, tick in enumerate(data):
        category_data.append(tick[0])
        values.append(tick)
        # 1表示涨，-1表示跌
        volumes.append([i, tick[4], 1 if tick[1] > tick[2] else -1])
    return {"categoryData": category_data, "values": values, "volumes": volumes}


# 计算移动平均线的函数
def calculate_ma(day_count: int, data):
    """

    :param day_count:
    :param data:
    :return:
    """
    result: List[Union[float, str]] = []
    for i in range(len(data["values"])):
        if i < day_count:
            result.append("-")  # 前几天数据不足时用"-"填充
            continue
        sum_total = 0.0
        for j in range(day_count):
            sum_total += float(data["values"][i - j][1])
        result.append(abs(float("%.3f" % (sum_total / day_count))))
    return result


def kline_get(chart_data: List[Union[float, str]], title: str, style='red_green'):
    """

    :param chart_data:
    :param title:
    :param style:
    :return:
    """

    # 提取K线图数据
    kline_data = [data[1:-1] for data in chart_data["values"]]

    color2 = "#00da3c"
    color1 = "#ec0000"
    if style == "green":
        color1 = "#00da3c"
        color2 = "#00da3c"

    if style == "red":
        color1 = "#ec0000"
        color2 = "#ec0000"
    # 创建K线图对象
    kline = (
        Kline()
        .add_xaxis(xaxis_data=chart_data["categoryData"])
        .add_yaxis(
            series_name=title,
            y_axis=kline_data,
            itemstyle_opts=opts.ItemStyleOpts(color=color1, color0=color2,
                                              border_color=color1, border_color0=color2),
        )
        .set_global_opts(
            legend_opts=opts.LegendOpts(
                is_show=False, pos_bottom=10, pos_left="center"
            ),
            # 设置数据缩放、拖拽和切换显示的功能
            datazoom_opts=[
                opts.DataZoomOpts(
                    is_show=False,
                    type_="inside",
                    xaxis_index=[0, 1, 2],
                    range_start=0,
                    range_end=100,
                ),
                opts.DataZoomOpts(
                    is_show=True,
                    xaxis_index=[0, 1, 2],
                    type_="slider",
                    pos_top="85%",
                    range_start=0,
                    range_end=100,
                ),
            ],
            # 设置Y轴的一些参数
            yaxis_opts=opts.AxisOpts(
                is_scale=True,
                splitarea_opts=opts.SplitAreaOpts(
                    is_show=True, areastyle_opts=opts.AreaStyleOpts(opacity=1)
                ),
            ),
            # 设置提示框的样式
            tooltip_opts=opts.TooltipOpts(
                trigger="axis",
                axis_pointer_type="cross",
                background_color="rgba(245, 245, 245, 0.8)",
                border_width=1,
                position=JsCode(tool_tips_opts_pos_js_func),
                #position=['50%', '0%'],
                border_color="#ccc",
                textstyle_opts=opts.TextStyleOpts(color="#000"),
            ),
            # 设置视觉映射，用于表示涨跌情况

            visualmap_opts=opts.VisualMapOpts(
                is_show=False,
                dimension=2,
                series_index=5,
                is_piecewise=True,
                pieces=[
                    {"value": 1, "color": color1},
                    {"value": -1, "color": color2},
                ],
            ),
            # 设置坐标轴指示器
            axispointer_opts=opts.AxisPointerOpts(
                is_show=True,
                link=[{"xAxisIndex": "all"}],
                label=opts.LabelOpts(background_color="#777"),
            ),
            # 设置刷子，用于进行区域选择
            brush_opts=opts.BrushOpts(
                x_axis_index="all",
                brush_link="all",
                out_of_brush={"colorAlpha": 0.1},
                brush_type="lineX",
            ),
        )
    )
    return kline


def line_get(chart_data: List[Union[float, str]]):
    """

    :param chart_data:
    :return:
    """
    # 创建折线图对象
    line = (
        Line()
        .add_xaxis(xaxis_data=chart_data["categoryData"])
        .add_yaxis(
            series_name="MA5",
            y_axis=calculate_ma(day_count=5, data=chart_data),
            is_smooth=True,
            is_hover_animation=False,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            label_opts=opts.LabelOpts(is_show=False),
        )
        .add_yaxis(
            series_name="MA10",
            y_axis=calculate_ma(day_count=10, data=chart_data),
            is_smooth=True,
            is_hover_animation=False,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            label_opts=opts.LabelOpts(is_show=False),
        )
        .add_yaxis(
            series_name="MA20",
            y_axis=calculate_ma(day_count=20, data=chart_data),
            is_smooth=True,
            is_hover_animation=False,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            label_opts=opts.LabelOpts(is_show=False),
        )
        .add_yaxis(
            series_name="MA30",
            y_axis=calculate_ma(day_count=30, data=chart_data),
            is_smooth=True,
            is_hover_animation=False,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            label_opts=opts.LabelOpts(is_show=False),
        )
        .set_global_opts(xaxis_opts=opts.AxisOpts(type_="category"))
    )
    return line


def line_get_with_title(chart_data: List[Union[float, str]], title: str):
    """

    :param chart_data:
    :param title:
    :return:
    """
    # 提取线图数据
    line_data = [data[1:-1] for data in chart_data["values"]]
    # 创建折线图对象
    line = (
        Line()
        .add_xaxis(xaxis_data=chart_data["categoryData"])
        .add_yaxis(
            series_name=title,
            y_axis=line_data,
            is_smooth=True,
            is_hover_animation=False,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            label_opts=opts.LabelOpts(is_show=False),
        )

        .set_global_opts(xaxis_opts=opts.AxisOpts(type_="category"))
    )
    return line


def bar_get(chart_data: List[Union[float, str]], title: str, xaxis_index=1, transprenct=False,
            color='rgba(0, 0, 240, 0.2)'):
    """

    :param xaxis_index:
    :param chart_data:
    :param title:
    :return:
    """
    # 创建柱状图对象
    bar = (
        Bar()
        .add_xaxis(xaxis_data=chart_data["categoryData"])
        .add_yaxis(
            series_name=title,
            y_axis=chart_data["volumes"],
            xaxis_index=xaxis_index,
            yaxis_index=1,
            label_opts=opts.LabelOpts(is_show=False),
        )
        .set_global_opts(
            xaxis_opts=opts.AxisOpts(
                type_="category",
                is_scale=True,
                grid_index=1,
                boundary_gap=False,
                axisline_opts=opts.AxisLineOpts(is_on_zero=False),
                axistick_opts=opts.AxisTickOpts(is_show=False),
                splitline_opts=opts.SplitLineOpts(is_show=False),
                axislabel_opts=opts.LabelOpts(is_show=False),
                split_number=20,
                min_="dataMin",
                max_="dataMax",
            ),
            yaxis_opts=opts.AxisOpts(
                grid_index=1,
                is_scale=True,
                split_number=2,
                axislabel_opts=opts.LabelOpts(is_show=False),
                axisline_opts=opts.AxisLineOpts(is_show=False),
                axistick_opts=opts.AxisTickOpts(is_show=False),
                splitline_opts=opts.SplitLineOpts(is_show=False),
            ),
            legend_opts=opts.LegendOpts(is_show=False),
        )
    )
    if transprenct:
        bar.set_series_opts(
            itemstyle_opts=opts.ItemStyleOpts(color=color),
        )
    return bar


# 绘制K线图、折线图和柱状图
def draw_charts(chart_data):
    """

    :param chart_data:
    """
    # 创建K线图对象
    kline = kline_get(chart_data, title='test', style='red_green')

    # 创建折线图对象
    # line = line_get(chart_data)

    # 创建柱状图对象
    bar = bar_get(chart_data, title='成交量')

    # K线图和折线图的重叠
    # overlap_kline_line = kline.overlap(line)

    # 创建Grid图表，包含K线图和折线图的重叠部分以及柱状图
    grid_chart = Grid(
        init_opts=opts.InitOpts(
            width="1000px",
            height="500px",
            animation_opts=opts.AnimationOpts(animation=False),
        )
    )
    grid_chart.add(
        kline,
        grid_opts=opts.GridOpts(pos_left="10%", pos_right="8%", height="50%"),
    )
    grid_chart.add(
        bar,
        grid_opts=opts.GridOpts(
            pos_left="10%", pos_right="8%", pos_top="63%", height="16%"
        ),
    )

    # 渲染生成HTML文件
    grid_chart.render("professional_kline_brush.html")
    webbrowser.open_new_tab("professional_kline_brush.html")


def trade_day2non_recurring_profit_day(start_date: date, profit_type='roll_profit'):
    if start_date.month > 4:
        lrb_start_date = start_date
    else:
        if profit_type == 'roll_profit':
            lrb_start_date = start_date + relativedelta(months=-3)  # 只能看到前一季度的利润表
        else:
            lrb_start_date = start_date + relativedelta(years=-1)  # 只能看到前一年的利润表
    return lrb_start_date


def draw_charts_compare(company1: CompanyProfile, company2: CompanyProfile, period: str,
                        start_date: date, end_date: date, rand='', path='', request=None,
                        profit_type='roll_profit'):
    """

    :param company1:
    :param company2:
    :param period:
    :param start_date:
    :param end_date:
    :return:
    """
    print(run_info(company1), 'start_date', start_date, 'end_date', end_date, period)
    json_data1, json_data2 = company_sync_kline_data_get(company1=company1,
                                                         company2=company2,
                                                         period=period,
                                                         start_date=start_date,
                                                         end_date=end_date)
    if json_data1 is None or json_data2 is None:
        print(run_info(company1), 'invalid json data', json_data1, json_data2)
        return
    # 创建K线图对象
    chart_data1 = split_data(json_data1)
    chart_data2 = split_data(json_data2)
    try:
        kline1 = kline_get(chart_data1, title=company1.name, style='red')
        kline2 = kline_get(chart_data2, title=company2.name, style='green')
    except Exception as e:
        print(run_info(company2), str(e))
        return

    # 创建公司1的利润表
    lrb_start_date = trade_day2non_recurring_profit_day(start_date)
    lrb_data = company1.regular_non_recurring_profit_value_data_get(period=company1.market.season4,
                                                                    start_date=lrb_start_date, end_date=end_date,
                                                                    profit_type=profit_type)
    print(run_info(company1), company1.name, 'lrb_start_date', lrb_start_date, lrb_data)
    if lrb_data is None:
        print(run_info(company1), 'lrb data is None')
        lrb_bar = None
    else:
        lrb_data = profit_dates_values_sync(date_values=lrb_data, dates_sync_to=json_data1,
                                            profit_time=company1.profit_time)
        print(run_info(lrb_data), ' lrb_data1[0]', lrb_data[0])
        lrb_chart_data = split_data(lrb_data)

        lrb_bar = bar_get(chart_data=lrb_chart_data, title='扣非净利润')

    # 创建市盈率
    profit_rate_data = company1.profit_rate_get(period=period,
                                                start_date=start_date,
                                                end_date=end_date,
                                                factor=1)
    if profit_rate_data is None:
        print(run_info(company1), 'profit_rate_data is None')
        return

    lrb_rate_chart_data = split_data(profit_rate_data)

    lrb_rate_bar = bar_get(chart_data=lrb_rate_chart_data, title='市盈率', xaxis_index=2)

    # 创建柱状图对象
    # bar = bar_get(chart_data)

    # K线图和折线图的重叠
    overlap_kline_kline = kline2.overlap(kline1)

    # 创建Grid图表，包含K线图和折线图的重叠部分以及柱状图
    grid_chart = Grid(
        init_opts=opts.InitOpts(
            width="1000px",
            height="450px",
            animation_opts=opts.AnimationOpts(animation=False),
        )
    )


    grid_chart.add(
        overlap_kline_kline,
        grid_opts=opts.GridOpts(pos_left="10%", pos_right="8%", pos_top="5%", height="45%"),
    )
    # 利润表

    grid_chart.add(
        lrb_bar,
        grid_opts=opts.GridOpts(
            pos_left="10%", pos_right="8%", pos_top="53%", height="15%"
        ),
    )

    # 市盈率
    grid_chart.add(
        lrb_rate_bar,
        grid_opts=opts.GridOpts(
            pos_left="10%", pos_right="8%", pos_top="72%", height="10%"
        ),
    )

    # 渲染生成HTML文件
    html_file_name = company1.name + 'VS' + company2.name + '-' + start_date.strftime(
        '%Y-%m-%d') + '-' + period + '-' + end_date.strftime('%Y-%m-%d') + rand + '.html'
    if request == None:
        grid_chart.render(path + html_file_name)
    else:
        html_code = grid_chart.render_embed()
        #html_code = html_chart_id_replace(chart_id=grid_chart.chart_id, html_string=html_code)
        return html_code
    return html_file_name


def draw_charts_company(company1: CompanyProfile, period: str,
                        start_date: date, end_date: date, rand='', path='', request=None,
                        profit_type='roll_profit'):
    """

    :param company1:
    :param period:
    :param start_date:
    :param end_date:
    :return:
    """
    # 调整开始时间, 因为开始时间可能在股票上市之前
    if start_date < company1.ipo_date:
        start_date = company1.date_before_ipo_get(period=period)
    json_data1 = company1.regular_kline_data_get(period=period,
                                                 start_date=start_date,
                                                 end_date=end_date,
                                                 factor=1)

    if json_data1 is None:
        print(run_info(company1), 'regular_kline_data_get fail', company1.code)
        return None

    # 创建K线图对象
    chart_data1 = split_data(json_data1)
    try:
        kline1 = kline_get(chart_data1, title=company1.name)
    except Exception as e:
        print(run_info(company1), str(e))
        return

    # 创建公司1的利润表
    lrb_start_date = trade_day2non_recurring_profit_day(start_date)
    lrb_data = company1.regular_non_recurring_profit_value_data_get(period=company1.market.season4,
                                                                    start_date=lrb_start_date,
                                                                    end_date=end_date,
                                                                    factor=1 / 1000000,
                                                                    profit_type=profit_type)
    print(run_info(company1), company1.name, 'lrb_start_date', lrb_start_date, lrb_data)
    if lrb_data is None:
        print(run_info(company1), 'lrb data is None')
        lrb_bar = None
    else:
        lrb_data = profit_dates_values_sync(date_values=lrb_data, dates_sync_to=json_data1,
                                            profit_time=company1.profit_time)
        print(run_info(lrb_data), ' lrb_data1[0]', lrb_data[0])
        lrb_chart_data = split_data(lrb_data)

        lrb_bar = bar_get(chart_data=lrb_chart_data, title='扣非净利润(百万元)')

    # 创建市盈率
    profit_rate_data = company1.profit_rate_get(period=period,
                                                start_date=start_date,
                                                end_date=end_date,
                                                factor=1)
    if profit_rate_data is None:
        print(run_info(company1), 'profit_rate_data is None')
        return

    lrb_rate_chart_data = split_data(profit_rate_data)

    lrb_rate_bar = bar_get(chart_data=lrb_rate_chart_data, title='市盈率', xaxis_index=2)

    # 创建柱状图对象
    # bar = bar_get(chart_data)

    # K线图和折线图的重叠

    # 创建Grid图表，包含K线图和折线图的重叠部分以及柱状图
    grid_chart = Grid(
        init_opts=opts.InitOpts(
            width="1000px",
            height="450px",
            animation_opts=opts.AnimationOpts(animation=False),
        )
    )

    grid_chart.add(
        kline1,
        grid_opts=opts.GridOpts(pos_left="10%", pos_right="8%", pos_top="5%", height="45%"),
    )
    # 利润表

    grid_chart.add(
        lrb_bar,
        grid_opts=opts.GridOpts(
            pos_left="10%", pos_right="8%", pos_top="53%", height="15%"
        ),
    )

    # 市盈率
    grid_chart.add(
        lrb_rate_bar,
        grid_opts=opts.GridOpts(
            pos_left="10%", pos_right="8%", pos_top="72%", height="10%"
        ),
    )

    # 渲染生成HTML文件
    html_file_name = company1.name + '-' + start_date.strftime(
        '%Y-%m-%d') + '-' + period + '-' + end_date.strftime('%Y-%m-%d') + rand + '.html'
    logger.error("with request %s %s ", request, html_file_name)
    if request == None:
        grid_chart.render(path + html_file_name)
    else:
        html_code = grid_chart.render_embed()
        #html_code = html_chart_id_replace(chart_id=grid_chart.chart_id, html_string=html_code)
        return html_code
    return html_file_name


def draw_charts_company_regular0(company1: CompanyProfile, period: str,
                                 start_date: date, end_date: date, rand='', path='', request=None,
                                 profit_type='roll_profit'):
    """

    :param company1:
    :param period:
    :param start_date:
    :param end_date:
    :param profit_type: 'roll_profit', 'static_profit'
    :return:
    """
    # 调整开始时间, 因为开始时间可能在股票上市之前
    if start_date < company1.ipo_date:
        start_date = company1.date_before_ipo_get(period=period)
    json_data1 = company1.regular_kline_data_get(period=period,
                                                 start_date=start_date,
                                                 end_date=end_date,
                                                 first_data_zero=True)

    if json_data1 is None:
        print(run_info(company1), 'regular_kline_data_get fail', company1.code)
        return None

    # 创建K线图对象
    chart_data1 = split_data(json_data1)
    try:
        kline1 = kline_get(chart_data1, title=company1.name, style='red')
    except Exception as e:
        print(run_info(company1), str(e))
        return
    # 设置标题
    if 'roll_profit' == profit_type:
        rate_title = '滚动市盈率'
        income_title = '滚动营业总收入涨幅'
        profit_title = '滚动扣非净利润(百万元)'
        profit_growth_title = '滚动扣非净利润涨幅'
    else:
        rate_title = '静态市盈率'
        income_title = '营业总收入涨幅'
        profit_title = '扣非净利润(百万元)'
        profit_growth_title = '扣非净利润涨幅'

    # 创建公司的利润表
    lrb_start_date = trade_day2non_recurring_profit_day(start_date=start_date, profit_type=profit_type)
    lrb_data = company1.regular_non_recurring_profit_value_data_get(period=company1.market.season4,
                                                                    start_date=lrb_start_date,
                                                                    end_date=end_date,
                                                                    factor=1 / 1000000,
                                                                    profit_type=profit_type)
    print(run_info(company1), company1.name, 'lrb_start_date', lrb_start_date, lrb_data)
    if lrb_data is None:
        print(run_info(company1), 'lrb data is None')
        lrb_bar = None
    else:
        lrb_data = profit_dates_values_sync(date_values=lrb_data, dates_sync_to=json_data1,
                                            profit_time=company1.profit_time)
        print(run_info(lrb_data), ' lrb_data1[0]', lrb_data[0])
        lrb_chart_data = split_data(lrb_data)

        lrb_bar = bar_get(chart_data=lrb_chart_data, title=profit_title)

    # 创建公司1的归一化利润表
    regular_lrb_data = json_data_regularize(factor=1 / lrb_data[0][2], json_data=lrb_data, first_data_zero=True)
    regular_lrb_chart_data = split_data(regular_lrb_data)
    regular_lrb_bar = bar_get(chart_data=regular_lrb_chart_data, title=profit_growth_title,
                              transprenct=True, color='rgba(0,255,0, 0.5)')  # 绿色

    # 创建市盈率
    profit_rate_data = company1.profit_rate_get(period=period,
                                                start_date=start_date,
                                                end_date=end_date,
                                                factor=1,
                                                profit_type=profit_type)
    if profit_rate_data is None:
        print(run_info(company1), 'profit_rate_data is None')
        return

    lrb_rate_chart_data = split_data(profit_rate_data)

    lrb_rate_bar = bar_get(chart_data=lrb_rate_chart_data, title=rate_title, xaxis_index=2)

    # 创建柱状图对象
    # bar = bar_get(chart_data)
    # 创建营业额BAR
    income_data = company1.regular_income_data_get(season=company1.market.season4,
                                                   start_date=start_date,
                                                   end_date=end_date, profit_type=profit_type)
    if income_data is None:
        print(run_info(company1), 'income_bar data is None')
        income_bar = None
    else:
        income_data = profit_dates_values_sync(date_values=income_data, dates_sync_to=json_data1)
        print(run_info(income_data), ' income_data[0]', income_data[0])
        regular_income_data = json_data_regularize(factor=1 / income_data[0][2], json_data=income_data,
                                                   first_data_zero=True)
        print(run_info(regular_income_data), ' regular_income_data[0]', regular_income_data[0])
        income_chart_data = split_data(regular_income_data)

        income_bar = bar_get(chart_data=income_chart_data, title=income_title, transprenct=True,
                             color='rgba(0, 0, 255, 0.5)')  # blue

    # K线图和折线图的重叠
    overlap_kline_lrb = kline1.overlap(regular_lrb_bar)
    overlap_kline_lrb_income = overlap_kline_lrb.overlap(income_bar)

    # 创建Grid图表，包含K线图和折线图的重叠部分以及柱状图
    grid_chart = Grid(
        init_opts=opts.InitOpts(
            width="1000px",
            height="450px",
            animation_opts=opts.AnimationOpts(animation=False),
        )
    )
    grid_add_js_funcs(grid_chart)

    grid_chart.add(
        #kline1,
        #overlap_kline_lrb,
        overlap_kline_lrb_income,
        grid_opts=opts.GridOpts(pos_left="10%", pos_right="8%", pos_top="5%", height="45%"),
    )
    # 利润表

    grid_chart.add(
        lrb_bar,
        grid_opts=opts.GridOpts(
            pos_left="10%", pos_right="8%", pos_top="53%", height="15%"
        ),
    )

    # 市盈率
    grid_chart.add(
        lrb_rate_bar,
        grid_opts=opts.GridOpts(
            pos_left="10%", pos_right="8%", pos_top="72%", height="10%"
        ),
    )

    # 渲染生成HTML文件
    html_file_name = company1.name + '-' + start_date.strftime(
        '%Y-%m-%d') + '-' + period + '-' + end_date.strftime('%Y-%m-%d') + rand + '.html'
    logger.error("with request %s %s ", request, html_file_name)
    if request == None:
        grid_chart.render(path + html_file_name)
    else:
        html_code = grid_chart.render_embed()
        html_code = html_chart_id_replace(chart_id=grid_chart.chart_id, html_string=html_code)
        return html_code
    return html_file_name


def company_sync_kline_data_get(company1: CompanyProfile, company2: CompanyProfile, period: str,
                                start_date: date, end_date: date):
    """

    :param company1:
    :param company2:
    :param period:
    :param start_date:
    :param end_date:
    :return:
    """
    json_data1 = company1.regular_kline_data_get(period=period,
                                                 start_date=start_date,
                                                 end_date=end_date)
    # print(run_info(company1), company1.name, json_data1)

    if json_data1 is None:
        print(run_info(company1), 'regular_kline_data_get fail', company1.code)
        return None

    json_data2 = company2.regular_kline_data_get(period=period,
                                                 start_date=start_date,
                                                 end_date=end_date)

    print(run_info(company2), 'chart_data1 and chart_data2 are ready, date len',
          len(json_data1), len(json_data2), 'json_data type is ', type(json_data1))

    if len(json_data1) != len(json_data2):
        write_json_file('data/' + company1.code + '.json', json_data1)
        write_json_file('data/' + company2.code + '.json', json_data2)

    return json_data1, json_data2


def html_chart_id_replace(chart_id: str, html_string: str):
    # 使用正则表达式匹配ID
    match = re.search(r'id="([a-f0-9]+)"', html_string)

    if match:
        real_chart_id = match.group(1)
        print(run_info(chart_id), 'real_chart_id', real_chart_id)
    else:
        print("No match found.")
        return html_string

    new_string = re.sub(r'chart_([a-f0-9]+)', 'chart_'+real_chart_id,html_string)
    new_string = re.sub(r'option_([a-f0-9]+)', 'option_' + real_chart_id,new_string)
    return new_string


def grid_add_js_funcs(grid_chart: Grid):
    chart_id = grid_chart.chart_id
    print(run_info(chart_id), 'chart_id is ', chart_id)
    js_func_on_zoom = f"""
        chart_{chart_id}.on('dataZoom', function(params) {{
            if(area_selected){{
                opts = {{}};
                deepClone(opts_backup,opts);
                chart_{chart_id}.setOption(opts);
                area_selected = false;
            }}
        }});
        """
    js_func_on_brush_end = f"""
        chart_{chart_id}.on('brushEnd', function(params) {{

          var opts=option_{chart_id};
        
          if(!Object.keys(opts_backup).length){{
              deepClone(opts,opts_backup);               
          }}
          
          area_selected = true;
          opts = {{}};
          deepClone(opts_backup,opts);
        
          
          
          var series;
          var data0;
          var itemIndex;
          var startIndex = 0,endIndex = -1
          var factorNum;
          var factors=new Array(16);
          if(!params.areas.length || !params.areas[0].coordRange.length){{
            console.log('params brushEnd',params);
            return ;
          }}
          startIndex = params.areas[0].coordRange[0][0];
          endIndex = params.areas[0].coordRange[0][1];
          
          for(arrayNum=0;arrayNum<opts.series.length;arrayNum++){{
              series = opts.series[arrayNum];
              console.log("brushEnd series.name ",series.name);
              if(series.name=='扣非净利润(百万元)'){{
                continue;
              }}
              if(series.name=='滚动扣非净利润(百万元)'){{
                continue;
              }}
              if(series.name=='静态市盈率'){{
                continue;
              }}
              if(series.name=='滚动市盈率'){{
                continue;
              }}
              
              
              data0=series.data[startIndex];
              for(factorNum=0;factorNum<data0.length;factorNum++){{
                  factors[factorNum] = data0[factorNum];
              }}
              if('滚动扣非净利润涨幅'==series.name ||'滚动营业总收入涨幅'==series.name ||'营业总收入涨幅'==series.name ||'扣非净利润涨幅'==series.name){{
                factorNum = 1;
                for(itemIndex=0;itemIndex<series.data.length;itemIndex++){{                    
                    if(!isNaN(parseFloat(series.data[itemIndex][factorNum])) && isFinite(series.data[itemIndex][factorNum])&&factors[factorNum]!=0){{
                        series.data[itemIndex][factorNum] = Math.round(series.data[itemIndex][factorNum]/factors[factorNum]*100)/100;
                    }}                           
                    
                }}
                
              }}
              else{{
                for(itemIndex=0;itemIndex<series.data.length;itemIndex++){{
                    for(factorNum=0;factorNum<data0.length;factorNum++){{
                        if(!isNaN(parseFloat(series.data[itemIndex][factorNum])) && isFinite(series.data[itemIndex][factorNum])&&factors[factorNum]!=0){{
                            series.data[itemIndex][factorNum] = Math.round(series.data[itemIndex][factorNum]/factors[factorNum]*100)/100;
                        }}                           
                    }}
                }}
             }}   
        
          }}
        
          var length = opts.series[0].data.length;
          opts.dataZoom[0].start = startIndex*100/length;
          opts.dataZoom[0].end = endIndex*100/length;
          console.log("startIndex",startIndex,"endIndex",endIndex,"length ",length);
          chart_{chart_id}.setOption(opts);
          
        
        }});
        """
    grid_chart.add_js_funcs(js_func_on_zoom)
    grid_chart.add_js_funcs(js_func_on_brush_end)


tool_tips_opts_pos_js_func = '''
function tool_tips_opts_position (point, params, dom, rect, size) {

  var x = 0; 
  var y = 0; 

  var pointX = point[0];
  var pointY = point[1];
 
  var boxWidth = size.contentSize[0];
  var boxHeight = size.contentSize[1];
  var factor = 0.3;
  if (pointX > boxWidth*(1+factor)) {
    x = pointX - boxWidth*(1+factor);
  } else { 
    x = boxWidth*factor+pointX;
  }
 
  if (boxHeight > pointY) {
    y = 5;
  } else { 
    y = pointY - boxHeight;
  }
 
  return [x, y];
}
'''

# 适配django
import logging

# 生成一个以当前文件名为名字的logger实例
logger = logging.getLogger(__name__)
'''
# 由于扣非净利润是一个非常重要的参数，所以我们需要调整起始日期，暂定最早日期为有扣非净利润的年度的后4个月，
比如最早2010-12-31，那么开始时间为2011-04-30另外要考虑IPO日期，start_date最早不能超过IPO的前一个交易周期
'''


def stock_beacon(request: requests):
    logger.setLevel(logging.DEBUG)
    full_path = request.get_full_path()
    parsed_url = urlparse(full_path)
    index = 0

    params = parsed_url.query.split(sep='&')

    share_code = params[index].split(sep='share_code=')[1]
    index += 1

    period = params[index].split(sep='period=')[1]
    index += 1

    profit_type = params[index].split(sep='profit_type=')[1]
    index += 1

    profit_time = params[index].split(sep='profit_time=')[1]
    index += 1

    start_date = params[index].split(sep='start_date=')[1]
    index += 1

    end_date = params[index].split(sep='end_date=')[1]
    index += 1

    opponent_type = params[index].split(sep='opponent_type=')[1]
    index += 1

    opponent_share_code = params[index].split(sep='opponent_share_code=')[1]
    index += 1

    random = params[index]
    path_info = '.' + full_path.split('?')[0] + 'templates/'

    logger.debug('param %s', path_info, share_code, period, start_date, end_date, opponent_type, opponent_share_code,
                 random)
    is_index = False
    if opponent_type != 'other_stock' and opponent_type != 'none':
        is_index = True

    start_date = dt.strptime(start_date, '%Y-%m-%d').date()
    end_date = dt.strptime(end_date, '%Y-%m-%d').date()
    # 获得公司A的股票代码
    company_a = CompanyProfile(code=share_code, is_index=False)
    if not company_a.valid:
        logger.error('company_a is invalid %s', share_code)
        return None

    try:
        # 更新所有数据
        ret = company_a.update_all(start_date, profit_time=profit_time)
        if ret is False:
            logger.error('update_all ret %s %s', ret, company_a.code)
            return None
    except Exception as e:
        logger.error("更新股票交易数据失败 %s %s", company_a.code, str(e))
        return None

    start_date = company_a.start_date_adjust(start_date, period)
    print(run_info(company_a), company_a.code, 'after start_date_adjust', start_date)

    if opponent_type == 'growth_view':
        try:
            html_code = draw_charts_company_regular0(company_a, period, start_date, end_date,
                                                     rand=random, request=request,
                                                     profit_type=profit_type)
            mark_safe(html_code)
            response = render(request, 'company_valuation.html', {'html_code': html_code})
            return response
        except Exception as e:
            logger.error("draw_charts_company_regular0 %s", str(e))
            return None

    if opponent_type == 'none':
        try:
            html_code = draw_charts_company(company_a, period, start_date, end_date,
                                            rand=random, request=request)
            mark_safe(html_code)
            response = render(request, 'company_valuation.html', {'html_code': html_code})
            return response
        except Exception as e:
            logger.error("draw_charts_compare %s", str(e))
            return None
    # 选择公司B或者指数
    code_b = opponent_share_code
    if is_index:
        if opponent_type == 'sh_index':
            code_b = '000001'
        if opponent_type == 'sz_index':
            code_b = '399001'
        if opponent_type == 'innovation_index':
            code_b = '399006'

    company_b = CompanyProfile(code_b, is_index=is_index)
    if not company_b.valid:
        logger.error('company_b is invalid %s', code_b)
        return None

    try:
        # 更新所有数据
        ret = company_b.update_all(start_date, profit_time=profit_time)
        if ret is False:
            logger.error('update_all ret %s %s', ret, company_b.code)
            return None
    except Exception as e:
        logger.error("更新股票交易数据失败 %s %s", company_b.code, str(e))
        return None

    start_date = company_b.start_date_adjust(start_date, period)
    print(run_info(company_b), company_b.code, 'after start_date_adjust', start_date)

    try:
        # kline_json_file_path = company_c.kline_regular_market_value_json_file_path_get('daily')
        # chart_data = CompanyShow.get_local_data(kline_json_file_path)
        html_code = draw_charts_compare(company_a, company_b, period=period,
                                        start_date=start_date, end_date=end_date,
                                        rand=random, path=path_info, request=request)
        mark_safe(html_code)
        response = render(request, 'company_valuation.html', {'html_code': html_code})
        return response
    except Exception as e:
        logger.error("draw_charts_compare %s", str(e))
        return None


if __name__ == "__main__":
    main_chart_data = get_data()
    draw_charts(main_chart_data)
