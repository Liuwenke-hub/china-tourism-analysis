"""分析计算层：从清洗后的长表派生所有图表所需的指标。

本模块是「单一事实来源」——pyecharts 仪表盘与 matplotlib 细节图都从这里取数，
避免出现多套口径不一致的计算。
"""
from pathlib import Path
import numpy as np
import pandas as pd

from data_loader import load_processed, get_national_indicator, parse_hainan_raw
from config import DATA_DIR


def _yoy(series: pd.Series) -> pd.Series:
    """同比（较上年）增长率，单位 %。"""
    return series.pct_change() * 100


def build_analysis() -> dict:
    """返回所有图表所需的分析对象字典。"""
    p = load_processed()
    out = {}

    # 1) 宏观经济：GDP、收入、消费
    gdp = get_national_indicator(p, "国内生成总值", ["国内生产总值", "GDP"])
    income = get_national_indicator(p, "全国居民人均收入情况", ["居民人均可支配收入"])
    consume = get_national_indicator(p, "居民消费水平", ["居民消费水平"])
    out["gdp"] = gdp
    out["gdp_growth"] = _yoy(gdp)
    out["income"] = income
    out["consume"] = consume

    # 2) 国内旅游
    dom_tourists = get_national_indicator(p, "国内旅游情况", ["国内游客"])
    dom_spend = get_national_indicator(p, "国内旅游情况", ["国内旅游总花费", "国内旅游收入"])
    out["dom_tourists"] = dom_tourists
    out["dom_spend"] = dom_spend
    out["dom_tourists_growth"] = _yoy(dom_tourists)
    out["dom_spend_growth"] = _yoy(dom_spend)

    # 3) 国际旅游（分省汇总为全国）
    intl_income = (p["国际旅游外汇收入分省"].groupby("Year")["Value"].sum()
                   .rename("国际旅游外汇收入（百万美元）"))
    foreign_visitors = (p["接待国外游客分省"].groupby("Year")["Value"].sum()
                        .rename("接待国外游客（万人次）"))
    out["intl_income"] = intl_income
    out["foreign_visitors"] = foreign_visitors
    out["intl_income_growth"] = _yoy(intl_income)

    # 4) 旅游业发展综合指标（旅行社、星级饭店等）
    dev = p["旅游业发展情况"].pivot_table(index="Year", columns="Indicator", values="Value")
    out["tourism_dev"] = dev

    # 5) 相关性矩阵（国家级宏观 + 旅游指标）
    corr_df = pd.DataFrame({
        "GDP(亿元)": gdp,
        "居民人均可支配收入(元)": income,
        "居民消费水平(元)": consume,
        "国内游客(百万人次)": dom_tourists,
        "国内旅游总花费(亿元)": dom_spend,
        "国际旅游外汇收入(百万美元)": intl_income,
        "接待国外游客(万人次)": foreign_visitors,
    })
    # 入境游客（来自旅游业发展情况，单位万人次）
    inbound = get_national_indicator(p, "旅游业发展情况", ["入境游客"])
    if inbound is not None:
        corr_df["入境游客(万人次)"] = inbound
    corr_df = corr_df.dropna()
    out["corr_matrix"] = corr_df.corr(method="pearson").round(3)
    out["corr_df"] = corr_df

    # 6) 区域差异：省份透视表
    def _province_pivot(key):
        d = p[key]
        return d.pivot_table(index="Year", columns="Province", values="Value")
    out["prov_gdp"] = _province_pivot("地区生产总值分省")
    out["prov_intl_income"] = _province_pivot("国际旅游外汇收入分省")
    out["prov_foreign"] = _province_pivot("接待国外游客分省")

    # 7) 海南月度专题
    hainan = p.get("海南旅游统计数据")
    if hainan is None or hainan.empty:
        hainan = parse_hainan_raw()
    if hainan is not None and not hainan.empty:
        # 仅保留近年（2015+）且剔除明显异常（累计值混入）的月份，保证可视化质量
        hainan = hainan[hainan["Year"] >= 2015].copy()
        cap = hainan["游客人数"].quantile(0.99)
        hainan = hainan[hainan["游客人数"] <= cap]
        out["hainan"] = hainan
        # 季节性：按月份聚合均值
        out["hainan_season"] = (hainan.groupby("Month")[["游客人数", "总收入"]]
                                .mean().rename(index=lambda m: f"{m}月"))
    return out


if __name__ == "__main__":
    a = build_analysis()
    for k, v in a.items():
        print(f"\n=== {k} ===")
        if isinstance(v, pd.Series):
            print(v.tail(5).to_string())
        elif isinstance(v, pd.DataFrame):
            print("shape:", v.shape, "| cols:", list(v.columns)[:8])
            print(v.tail(3).to_string())
        else:
            print(v)
