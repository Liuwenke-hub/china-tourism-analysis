"""pyecharts 交互式仪表盘：核心图表输出为单个可交互 HTML。

运行：python src/dashboard_pyecharts.py  ->  output/dashboard.html
浏览器打开即可悬停查看数值、缩放、联动，适合作为简历作品集现场演示。
"""
from pathlib import Path
import numpy as np
from pyecharts import options as opts
from pyecharts.charts import Line, Bar, Scatter, HeatMap, Boxplot, Page
from pyecharts.globals import ThemeType

from config import DASHBOARD_PATH, PALETTE
from analysis import build_analysis

A = build_analysis()
C = PALETTE


def _years(series):
    return [str(int(y)) for y in series.index]


def _line(title, series_dict, y_name="数值"):
    """通用折线图：series_dict = {name: Series}，自动对齐不同年份范围。"""
    all_years = sorted(set().union(*[set(s.index) for s in series_dict.values()]))
    xs = [str(int(y)) for y in all_years]
    line = (
        Line()
        .add_xaxis(xs)
        .set_global_opts(
            title_opts=opts.TitleOpts(title=title),
            tooltip_opts=opts.TooltipOpts(trigger="axis"),
            legend_opts=opts.LegendOpts(pos_top="8%"),
            xaxis_opts=opts.AxisOpts(name="年份"),
            yaxis_opts=opts.AxisOpts(name=y_name),
            datazoom_opts=[opts.DataZoomOpts(type_="inside")],
        )
    )
    for name, s in series_dict.items():
        vals = [round(float(s[y]), 2) if y in s.index else None for y in all_years]
        line.add_yaxis(name, vals, symbol="circle", symbol_size=5)
    return line


def main():
    page = Page(page_title="中国旅游经济分析 · 交互仪表盘", layout=Page.SimplePageLayout)
    charts = []

    # 1) GDP 总量与增长率（双轴）
    try:
        gdp, gr = A["gdp"], A["gdp_growth"]
        c = (
            Line()
            .add_xaxis(_years(gdp))
            .add_yaxis("GDP总量(亿元)", [round(float(v), 1) for v in gdp.values],
                       yaxis_index=0, symbol="circle")
            .add_yaxis("GDP增长率(%)", [round(float(v), 2) for v in gr.values],
                       yaxis_index=1, symbol="circle")
            .set_global_opts(
                title_opts=opts.TitleOpts(title="① 中国GDP总量与年度增长率（2005–2022）"),
                tooltip_opts=opts.TooltipOpts(trigger="axis"),
                xaxis_opts=opts.AxisOpts(name="年份"),
                yaxis_opts=opts.AxisOpts(name="GDP(亿元)", position="left"),
                datazoom_opts=[opts.DataZoomOpts(type_="inside")],
            )
            .extend_axis(yaxis=opts.AxisOpts(name="增长率(%)", position="right"))
        )
        charts.append(c)
    except Exception as e:  # noqa: BLE001
        print("chart1 GDP failed:", e)

    # 2) 居民收入 vs 消费
    try:
        charts.append(_line("② 全国居民人均可支配收入与消费水平（元）",
                            {"居民人均可支配收入": A["income"], "居民消费水平": A["consume"]}))
    except Exception as e:  # noqa: BLE001
        print("chart2 income failed:", e)

    # 3) 国内旅游人次 & 收入（双轴，凸显疫情冲击与复苏）
    try:
        dt, ds = A["dom_tourists"], A["dom_spend"]
        c = (
            Line()
            .add_xaxis(_years(dt))
            .add_yaxis("国内游客(百万人次)", [round(float(v), 1) for v in dt.values],
                       yaxis_index=0, symbol="circle")
            .add_yaxis("国内旅游总花费(亿元)", [round(float(v), 1) for v in ds.values],
                       yaxis_index=1, symbol="circle")
            .set_global_opts(
                title_opts=opts.TitleOpts(title="③ 国内旅游市场：人次与花费（2005–2022，含疫情冲击）"),
                tooltip_opts=opts.TooltipOpts(trigger="axis"),
                xaxis_opts=opts.AxisOpts(name="年份"),
                yaxis_opts=opts.AxisOpts(name="游客(百万人次)", position="left"),
                datazoom_opts=[opts.DataZoomOpts(type_="inside")],
            )
            .extend_axis(yaxis=opts.AxisOpts(name="花费(亿元)", position="right"))
        )
        charts.append(c)
    except Exception as e:  # noqa: BLE001
        print("chart3 domestic failed:", e)

    # 4) 国际旅游（2005–2019）
    try:
        ii, fv = A["intl_income"], A["foreign_visitors"]
        charts.append(_line("④ 国际旅游：外汇收入与接待国外游客（2005–2019）",
                            {"国际旅游外汇收入(百万美元)": ii, "接待国外游客(万人次)": fv}))
    except Exception as e:  # noqa: BLE001
        print("chart4 intl failed:", e)

    # 5) 相关性热力图
    try:
        cm = A["corr_matrix"]
        cols = list(cm.columns)
        data = [[j, i, cm.iloc[i, j]] for i in range(len(cols)) for j in range(len(cols))]
        short = [c.split("(")[0] for c in cols]
        c = (
            HeatMap()
            .add_xaxis(short)
            .add_yaxis("相关系数", short, data,
                       label_opts=opts.LabelOpts(is_show=True, formatter="{c}", font_size=9))
            .set_global_opts(
                title_opts=opts.TitleOpts(title="⑤ 宏观经济与旅游指标相关性热力图"),
                tooltip_opts=opts.TooltipOpts(trigger="item"),
                visualmap_opts=opts.VisualMapOpts(
                    min_=-1, max_=1, dimension=2,
                    pos_left="center", pos_bottom="5%",
                    range_color=["#2a9d8f", "#e9c46a", "#e07a3f", "#1f6f8b"]),
                xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=45)),
                yaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=0)),
            )
        )
        charts.append(c)
    except Exception as e:  # noqa: BLE001
        print("chart5 heatmap failed:", e)

    # 6) GDP vs 国际旅游外汇收入 散点 + 回归
    try:
        gdp, ii = A["gdp"], A["intl_income"]
        common = gdp.index.intersection(ii.index)
        x = gdp.loc[common].values.astype(float)
        y = ii.loc[common].values.astype(float)
        pts = [[round(float(a), 1), round(float(b), 1)] for a, b in zip(x, y)]
        k, b0 = np.polyfit(x, y, 1)
        xr = [float(np.min(x)), float(np.max(x))]
        reg = [[round(v, 1), round(float(k * v + b0), 1)] for v in xr]
        scatter = (
            Scatter()
            .add_xaxis([p[0] for p in pts])
            .add_yaxis("观测值", pts, symbol_size=8,
                       label_opts=opts.LabelOpts(is_show=False))
            .set_global_opts(
                title_opts=opts.TitleOpts(title="⑥ GDP 与国际旅游外汇收入关系（散点+线性拟合）"),
                tooltip_opts=opts.TooltipOpts(trigger="item"),
                xaxis_opts=opts.AxisOpts(name="GDP(亿元)"),
                yaxis_opts=opts.AxisOpts(name="国际旅游外汇收入(百万美元)"),
            )
        )
        line_reg = (
            Line()
            .add_xaxis([p[0] for p in reg])
            .add_yaxis("回归线", [p[1] for p in reg], symbol="none",
                       linestyle_opts=opts.LineStyleOpts(color=C[1], width=2, type_="dashed"))
        )
        scatter.overlap(line_reg)
        charts.append(scatter)
    except Exception as e:  # noqa: BLE001
        print("chart6 scatter failed:", e)

    # 7) 各省 GDP Top15（动态取最新年份，截断后=2022）
    try:
        pg = A["prov_gdp"]
        last_year = pg.index.max()
        top = pg.loc[last_year].dropna().sort_values(ascending=False).head(15)
        c = (
            Bar()
            .add_xaxis([str(p) for p in top.index][::-1])
            .add_yaxis(f"{int(last_year)}年GDP(亿元)", [round(float(v), 1) for v in top.values][::-1],
                       itemstyle_opts=opts.ItemStyleOpts(color=C[0]))
            .set_global_opts(
                title_opts=opts.TitleOpts(title=f"⑦ {int(last_year)}年各省GDP排名 Top15"),
                tooltip_opts=opts.TooltipOpts(trigger="axis"),
                xaxis_opts=opts.AxisOpts(name="省份"),
                yaxis_opts=opts.AxisOpts(name="GDP(亿元)"),
            )
            .reversal_axis()
        )
        charts.append(c)
    except Exception as e:  # noqa: BLE001
        print("chart7 prov gdp failed:", e)

    # 8) 2019 各省国际旅游外汇收入 Top15
    try:
        pi = A["prov_intl_income"]
        yr = 2019 if 2019 in pi.index else pi.index.max()
        top = pi.loc[yr].dropna().sort_values(ascending=False).head(15)
        c = (
            Bar()
            .add_xaxis([str(p) for p in top.index][::-1])
            .add_yaxis(f"{int(yr)}年国际旅游外汇收入(百万美元)", [round(float(v), 1) for v in top.values][::-1],
                       itemstyle_opts=opts.ItemStyleOpts(color=C[1]))
            .set_global_opts(
                title_opts=opts.TitleOpts(title=f"⑧ {int(yr)}年各省国际旅游外汇收入 Top15"),
                tooltip_opts=opts.TooltipOpts(trigger="axis"),
                xaxis_opts=opts.AxisOpts(name="省份"),
                yaxis_opts=opts.AxisOpts(name="百万美元"),
            )
            .reversal_axis()
        )
        charts.append(c)
    except Exception as e:  # noqa: BLE001
        print("chart8 prov intl failed:", e)

    # 9) 各省国际旅游外汇收入分布 箱线图
    try:
        pi = A["prov_intl_income"].dropna(how="all")
        # 每省逐年数值列表（剔除缺失）
        box_data = []
        cats = []
        for prov in pi.columns:
            vals = pi[prov].dropna().values.astype(float).tolist()
            if len(vals) >= 3:
                box_data.append(vals)
                cats.append(str(prov))
        prep = Boxplot.prepare_data(box_data)
        c = (
            Boxplot()
            .add_xaxis(cats)
            .add_yaxis("省份分布", prep)
            .set_global_opts(
                title_opts=opts.TitleOpts(title="⑨ 各省国际旅游外汇收入分布（箱线图，2005–2019）"),
                tooltip_opts=opts.TooltipOpts(trigger="item"),
                xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=90), name="省份"),
                yaxis_opts=opts.AxisOpts(name="百万美元"),
                datazoom_opts=[opts.DataZoomOpts(type_="inside")],
            )
        )
        charts.append(c)
    except Exception as e:  # noqa: BLE001
        print("chart9 boxplot failed:", e)

    # 10) 旅游业发展：旅行社 & 星级饭店
    try:
        dev = A["tourism_dev"]
        s = {"旅行社数(个)": dev["旅行社数(个)"], "星级饭店总数(个)": dev["星级饭店总数(个)"]}
        charts.append(_line("⑩ 旅游产业供给：旅行社与星级饭店数量（2005–2022）", s))
    except Exception as e:  # noqa: BLE001
        print("chart10 dev failed:", e)

    # 11) 海南月度趋势
    try:
        h = A["hainan"]
        hs = h.sort_values("Date")
        c = (
            Line()
            .add_xaxis([d.strftime("%Y-%m") for d in hs["Date"]])
            .add_yaxis("接待游客(万人次)", [round(float(v), 1) for v in hs["游客人数"].values],
                       symbol="none", linestyle_opts=opts.LineStyleOpts(width=1.5, color=C[0]))
            .add_yaxis("旅游总收入(亿元)", [round(float(v), 1) for v in hs["总收入"].values],
                       symbol="none", linestyle_opts=opts.LineStyleOpts(width=1.5, color=C[1]),
                       yaxis_index=1)
            .set_global_opts(
                title_opts=opts.TitleOpts(title="⑪ 海南旅游月度趋势（2015–2022）"),
                tooltip_opts=opts.TooltipOpts(trigger="axis"),
                xaxis_opts=opts.AxisOpts(name="月份", axislabel_opts=opts.LabelOpts(rotate=45)),
                yaxis_opts=opts.AxisOpts(name="游客(万人次)", position="left"),
                datazoom_opts=[opts.DataZoomOpts(type_="inside")],
            )
            .extend_axis(yaxis=opts.AxisOpts(name="收入(亿元)", position="right"))
        )
        charts.append(c)
    except Exception as e:  # noqa: BLE001
        print("chart11 hainan failed:", e)

    # 12) 海南季节性
    try:
        hs = A["hainan_season"]
        c = (
            Line()
            .add_xaxis(list(hs.index))
            .add_yaxis("月度平均游客(万人次)", [round(float(v), 1) for v in hs["游客人数"].values],
                       symbol="circle", areastyle_opts=opts.AreaStyleOpts(opacity=0.25))
            .set_global_opts(
                title_opts=opts.TitleOpts(title="⑫ 海南旅游季节性：月度平均接待量"),
                tooltip_opts=opts.TooltipOpts(trigger="axis"),
                xaxis_opts=opts.AxisOpts(name="月份"),
                yaxis_opts=opts.AxisOpts(name="游客(万人次)"),
            )
        )
        charts.append(c)
    except Exception as e:  # noqa: BLE001
        print("chart12 season failed:", e)

    # 13) 旅游总收入构成（国内 vs 国际折算亿元）堆叠面积
    try:
        ds = A["dom_spend"]                      # 亿元
        ii = A["intl_income"]                    # 百万美元
        # 百万美元 → 亿元转换系数（≈7 CNY/USD ÷ 100 = 0.07）
        # 2005-2022年人民币汇率在6.1~7.2区间波动，取0.07作为近似折算系数
        fx = 0.07
        common = ds.index.intersection(ii.index)
        dom = ds.loc[common]
        intl_conv = (ii.loc[common] * fx)
        c = (
            Line()
            .add_xaxis(_years(dom))
            .add_yaxis("国内旅游总花费(亿元)", [round(float(v), 1) for v in dom.values],
                       stack="t", areastyle_opts=opts.AreaStyleOpts(opacity=0.6))
            .add_yaxis("国际旅游外汇收入(折算亿元)", [round(float(v), 1) for v in intl_conv.values],
                       stack="t", areastyle_opts=opts.AreaStyleOpts(opacity=0.6))
            .set_global_opts(
                title_opts=opts.TitleOpts(title="⑬ 旅游总收入构成：国内 vs 国际（亿元，国际按1美元≈7元折算）"),
                tooltip_opts=opts.TooltipOpts(trigger="axis"),
                xaxis_opts=opts.AxisOpts(name="年份"),
                yaxis_opts=opts.AxisOpts(name="亿元"),
                datazoom_opts=[opts.DataZoomOpts(type_="inside")],
            )
        )
        charts.append(c)
    except Exception as e:  # noqa: BLE001
        print("chart13 composition failed:", e)

    for c in charts:
        page.add(c)
    page.render(str(DASHBOARD_PATH))

    # 注入标题与旅游管理视角解读
    _inject_header()
    print(f"\n✅ 仪表盘已生成：{DASHBOARD_PATH}（共 {len(charts)} 张交互图表）")


def _inject_header():
    header = """
<div style="font-family:'Microsoft YaHei','PingFang SC',sans-serif;
            max-width:1180px;margin:0 auto;padding:24px 16px 0;">
  <h1 style="color:#1f6f8b;margin:0 0 6px;">中国旅游经济分析 · 交互式数据仪表盘</h1>
  <p style="color:#555;font-size:14px;line-height:1.7;margin:0 0 10px;">
    基于国家统计局、文化和旅游部公开年鉴，以及海南省旅游和文化广电体育厅月度统计，
    用 Python（pandas + pyecharts）构建的多维分析。覆盖宏观经济、国内/国际旅游、区域差异与海南专题。
  </p>
  <p style="background:#f3f7f9;border-left:4px solid #1f6f8b;padding:10px 14px;
            color:#333;font-size:13px;line-height:1.7;margin:0 0 6px;">
    <b>旅游管理视角解读：</b>数据清晰呈现「收入增长→旅游消费升级」的正向传导，以及 2020–2022 年疫情对
    国内游的断崖式冲击与持续承压（2022 年再度同比 -22%）；区域上东部沿海在旅游外汇收入上显著领先，印证目的地
    资源禀赋与基础设施的门槛效应。这为文旅目的地运营、客源结构优化与淡旺季调度提供了量化依据。
  </p>
</div>
"""
    html = DASHBOARD_PATH.read_text(encoding="utf-8")
    html = html.replace("<body>", "<body>" + header, 1)
    DASHBOARD_PATH.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()
