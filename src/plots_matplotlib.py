"""matplotlib 一比一复刻：30 张静态图表，编号/命名对齐原项目。

运行：python src/plots_matplotlib.py  ->  output/charts/0X_*.png (300 DPI)
该模块与 pyecharts 交互仪表盘互补：静态图用于报告(docx)与论文，交互图用于演示。
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import FuncFormatter

from config import CHARTS_DIR, PALETTE, setup_chinese_font
from analysis import build_analysis

setup_chinese_font()
A = build_analysis()
DPI = 300
plt.rcParams["axes.grid"] = True
plt.rcParams["grid.alpha"] = 0.3
plt.rcParams["figure.autolayout"] = True


def _save(fig, name):
    path = CHARTS_DIR / name
    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  [保存] {name}")


def _years(s):
    return [int(y) for y in s.index]


# ---------- 1. GDP 总量趋势 ----------
def c01():
    g = A["gdp"]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(_years(g), g.values / 1e4, marker="o", color=PALETTE[0], lw=2)
    ax.set_title("中国GDP总量年度趋势")
    ax.set_xlabel("年份"); ax.set_ylabel("GDP（万亿元）")
    _save(fig, "01_中国GDP总量年度趋势.png")


# ---------- 2. GDP 增长率 ----------
def c02():
    g = A["gdp_growth"]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(_years(g), g.values, marker="o", color=PALETTE[1], lw=2)
    ax.axhline(0, color="grey", lw=0.8)
    ax.set_title("中国GDP年度增长率")
    ax.set_xlabel("年份"); ax.set_ylabel("同比增长率（%）")
    _save(fig, "02_中国GDP年度增长率.png")


# ---------- 3. 居民收入与消费 ----------
def c03():
    inc, con = A["income"], A["consume"]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(_years(inc), inc.values, marker="o", label="居民人均可支配收入", color=PALETTE[0])
    ax.plot(_years(con), con.values, marker="s", label="居民消费水平", color=PALETTE[1])
    ax.set_title("中国居民收入与消费趋势")
    ax.set_xlabel("年份"); ax.set_ylabel("金额（元）")
    ax.legend(); _save(fig, "03_中国居民收入与消费趋势.png")


# ---------- 4. 国内旅游人次与收入 ----------
def c04():
    dt, ds = A["dom_tourists"], A["dom_spend"]
    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax1.plot(_years(dt), dt.values, marker="o", color=PALETTE[0], label="国内游客(百万人次)")
    ax1.set_xlabel("年份"); ax1.set_ylabel("国内游客(百万人次)", color=PALETTE[0])
    ax2 = ax1.twinx()
    ax2.plot(_years(ds), ds.values, marker="s", color=PALETTE[1], label="国内旅游总花费(亿元)")
    ax2.set_ylabel("国内旅游总花费(亿元)", color=PALETTE[1])
    ax1.set_title("国内旅游人次与收入趋势")
    _save(fig, "04_国内旅游人次与收入趋势.png")


# ---------- 5. 国际旅游收入与游客 ----------
def c05():
    ii, fv = A["intl_income"], A["foreign_visitors"]
    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax1.plot(_years(ii), ii.values, marker="o", color=PALETTE[2], label="国际旅游外汇收入(百万美元)")
    ax1.set_xlabel("年份"); ax1.set_ylabel("外汇收入(百万美元)", color=PALETTE[2])
    ax2 = ax1.twinx()
    ax2.plot(_years(fv), fv.values, marker="s", color=PALETTE[3], label="接待国外游客(万人次)")
    ax2.set_ylabel("接待国外游客(万人次)", color=PALETTE[3])
    ax1.set_title("国际旅游收入与游客趋势")
    _save(fig, "05_国际旅游收入与游客趋势.png")


# ---------- 6. 国际旅游外汇收入增长率 ----------
def c06():
    g = A["intl_income_growth"]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(_years(g), g.values, marker="o", color=PALETTE[2], lw=2)
    ax.axhline(0, color="grey", lw=0.8)
    ax.set_title("国际旅游外汇收入增长率")
    ax.set_xlabel("年份"); ax.set_ylabel("同比增长率（%）")
    _save(fig, "06_国际旅游外汇收入增长率.png")


# ---------- 7. 接待国外游客增长率 ----------
def c07():
    fv = A["foreign_visitors"]
    g = fv.pct_change() * 100
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(_years(g), g.values, marker="o", color=PALETTE[3], lw=2)
    ax.axhline(0, color="grey", lw=0.8)
    ax.set_title("接待国外游客增长率")
    ax.set_xlabel("年份"); ax.set_ylabel("同比增长率（%）")
    _save(fig, "07_接待国外游客增长率.png")


# ---------- 8. 宏观+旅游相关性热力图 ----------
def c08():
    cm = A["corr_matrix"]
    labels = [c.split("(")[0] for c in cm.columns]
    fig, ax = plt.subplots(figsize=(9, 8))
    sns.heatmap(cm.values, annot=True, fmt=".2f", cmap="YlGnBu",
                xticklabels=labels, yticklabels=labels, ax=ax,
                vmin=-1, vmax=1, square=True,
                annot_kws={"size": 8})
    ax.set_title("国家宏观经济与旅游指标相关性热力图")
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    _save(fig, "08_国家宏观经济与旅游指标相关性热力图.png")


# ---------- 9. GDP vs 国际旅游外汇收入 散点 ----------
def c09():
    g, ii = A["gdp"], A["intl_income"]
    common = g.index.intersection(ii.index)
    x, y = g.loc[common].values.astype(float), ii.loc[common].values.astype(float)
    k, b0 = np.polyfit(x, y, 1)
    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.scatter(x, y, color=PALETTE[0], s=35)
    xs = np.linspace(x.min(), x.max(), 50)
    ax.plot(xs, k * xs + b0, "--", color=PALETTE[1])
    ax.set_title("GDP与国际旅游外汇收入散点图")
    ax.set_xlabel("GDP（亿元）"); ax.set_ylabel("国际旅游外汇收入(百万美元)")
    _save(fig, "09_GDP与国际旅游外汇收入散点图.png")


# ---------- 10. 人均收入 vs 国内旅游收入 散点 ----------
def c10():
    inc, ds = A["income"], A["dom_spend"]
    common = inc.index.intersection(ds.index)
    x, y = inc.loc[common].values.astype(float), ds.loc[common].values.astype(float)
    k, b0 = np.polyfit(x, y, 1)
    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.scatter(x, y, color=PALETTE[1], s=35)
    xs = np.linspace(x.min(), x.max(), 50)
    ax.plot(xs, k * xs + b0, "--", color=PALETTE[0])
    ax.set_title("人均收入与国内旅游收入散点图")
    ax.set_xlabel("居民人均可支配收入(元)"); ax.set_ylabel("国内旅游总花费(亿元)")
    _save(fig, "10_人均收入与国内旅游收入散点图.png")


# ---------- 11. GDP vs 国内旅游人次 散点 ----------
def c11():
    g, dt = A["gdp"], A["dom_tourists"]
    common = g.index.intersection(dt.index)
    x, y = g.loc[common].values.astype(float), dt.loc[common].values.astype(float)
    k, b0 = np.polyfit(x, y, 1)
    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.scatter(x, y, color=PALETTE[2], s=35)
    xs = np.linspace(x.min(), x.max(), 50)
    ax.plot(xs, k * xs + b0, "--", color=PALETTE[1])
    ax.set_title("GDP与国内旅游人次散点图")
    ax.set_xlabel("GDP（亿元）"); ax.set_ylabel("国内游客(百万人次)")
    _save(fig, "11_GDP与国内旅游人次散点图.png")


# ---------- 12. 国际旅游收入 vs 游客 散点 ----------
def c12():
    ii, fv = A["intl_income"], A["foreign_visitors"]
    common = ii.index.intersection(fv.index)
    x, y = ii.loc[common].values.astype(float), fv.loc[common].values.astype(float)
    k, b0 = np.polyfit(x, y, 1)
    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.scatter(x, y, color=PALETTE[3], s=35)
    xs = np.linspace(x.min(), x.max(), 50)
    ax.plot(xs, k * xs + b0, "--", color=PALETTE[1])
    ax.set_title("国际旅游收入与游客散点图")
    ax.set_xlabel("国际旅游外汇收入(百万美元)"); ax.set_ylabel("接待国外游客(万人次)")
    _save(fig, "12_国际旅游收入与游客散点图.png")


# ---------- 13. 各省 GDP 排名（动态取最新年份，截断后=2022） ----------
def c13():
    pg = A["prov_gdp"]; yr = pg.index.max()
    top = pg.loc[yr].dropna().sort_values(ascending=False).head(15)
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(top.index[::-1], top.values[::-1] / 1e4, color=PALETTE[0])
    ax.set_title(f"{int(yr)}年各省GDP排名")
    ax.set_xlabel("GDP（万亿元）")
    _save(fig, "13_2022年各省GDP排名.png")


# ---------- 14. 重点省份 GDP 年度趋势 ----------
def c14():
    pg = A["prov_gdp"]
    keys = [p for p in ["广东", "江苏", "山东", "浙江", "河南", "四川"] if p in pg.columns]
    fig, ax = plt.subplots(figsize=(10, 5.5))
    for i, p in enumerate(keys):
        s = pg[p].dropna()
        ax.plot(_years(s), s.values / 1e4, marker="o", ms=4, color=PALETTE[i % len(PALETTE)], label=p)
    ax.set_title("重点省份GDP年度趋势")
    ax.set_xlabel("年份"); ax.set_ylabel("GDP（万亿元）"); ax.legend()
    _save(fig, "14_重点省份GDP年度趋势.png")


# ---------- 15. 2019 各省国际旅游外汇收入排名 ----------
def c15():
    pi = A["prov_intl_income"]; yr = 2019 if 2019 in pi.index else pi.index.max()
    top = pi.loc[yr].dropna().sort_values(ascending=False).head(15)
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(top.index[::-1], top.values[::-1], color=PALETTE[1])
    ax.set_title(f"{int(yr)}年各省国际旅游外汇收入排名")
    ax.set_xlabel("国际旅游外汇收入(百万美元)")
    _save(fig, "15_2019年各省国际旅游外汇收入排名.png")


# ---------- 16. 各省国际旅游外汇收入分布 箱线图 ----------
def c16():
    pi = A["prov_intl_income"].dropna(how="all")
    data, cats = [], []
    for prov in pi.columns:
        vals = pi[prov].dropna().values.astype(float).tolist()
        if len(vals) >= 3:
            data.append(vals); cats.append(prov)
    fig, ax = plt.subplots(figsize=(14, 5.5))
    ax.boxplot(data, tick_labels=cats, vert=False, showfliers=False)
    ax.set_title("各省国际旅游外汇收入分布箱线图")
    ax.set_xlabel("国际旅游外汇收入(百万美元)")
    _save(fig, "16_各省国际旅游外汇收入分布箱线图.png")


# ---------- 17. 重点省份国际旅游外汇收入年度趋势 ----------
def c17():
    pi = A["prov_intl_income"]
    keys = [p for p in ["北京", "上海", "江苏", "广东", "浙江", "福建"] if p in pi.columns]
    fig, ax = plt.subplots(figsize=(10, 5.5))
    for i, p in enumerate(keys):
        s = pi[p].dropna()
        ax.plot(_years(s), s.values, marker="o", ms=4, color=PALETTE[i % len(PALETTE)], label=p)
    ax.set_title("重点省份国际旅游外汇收入年度趋势")
    ax.set_xlabel("年份"); ax.set_ylabel("国际旅游外汇收入(百万美元)"); ax.legend()
    _save(fig, "17_重点省份国际旅游外汇收入年度趋势.png")


# ---------- 18. 2019 各省接待国外游客排名 ----------
def c18():
    pf = A["prov_foreign"]; yr = 2019 if 2019 in pf.index else pf.index.max()
    top = pf.loc[yr].dropna().sort_values(ascending=False).head(15)
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(top.index[::-1], top.values[::-1], color=PALETTE[3])
    ax.set_title(f"{int(yr)}年各省接待国外游客排名")
    ax.set_xlabel("接待国外游客(万人次)")
    _save(fig, "18_2019年各省接待国外游客排名.png")


# ---------- 19. 各省接待国外游客分布 箱线图 ----------
def c19():
    pf = A["prov_foreign"].dropna(how="all")
    data, cats = [], []
    for prov in pf.columns:
        vals = pf[prov].dropna().values.astype(float).tolist()
        if len(vals) >= 3:
            data.append(vals); cats.append(prov)
    fig, ax = plt.subplots(figsize=(14, 5.5))
    ax.boxplot(data, tick_labels=cats, vert=False, showfliers=False)
    ax.set_title("各省接待国外游客分布箱线图")
    ax.set_xlabel("接待国外游客(万人次)")
    _save(fig, "19_各省接待国外游客分布箱线图.png")


# ---------- 20. 旅游业发展主要指标趋势（指数化） ----------
def c20():
    dev = A["tourism_dev"]
    keys = [k for k in ["国内游客(万人次)", "国内旅游总花费(亿元)", "国际旅游外汇收入(百万美元)", "入境游客(万人次)"] if k in dev.columns]
    fig, ax = plt.subplots(figsize=(10, 5.5))
    for i, k in enumerate(keys):
        s = dev[k].dropna()
        base = s.iloc[0]
        idx = s / base * 100
        ax.plot(_years(idx), idx.values, marker="o", ms=3, color=PALETTE[i % len(PALETTE)], label=k)
    ax.set_title("旅游业发展主要指标趋势（指数化，基期=100）")
    ax.set_xlabel("年份"); ax.set_ylabel("指数（基期=100）"); ax.legend()
    _save(fig, "20_旅游业发展主要指标趋势.png")


# ---------- 21. 旅游业发展指标相关性热力图 ----------
def c21():
    dev = A["tourism_dev"].select_dtypes(float).dropna()
    cm = dev.corr().round(2)
    short = [c.split("(")[0] for c in cm.columns]
    fig, ax = plt.subplots(figsize=(10, 9))
    sns.heatmap(cm.values, annot=True, fmt=".2f", cmap="YlGnBu",
                xticklabels=short, yticklabels=short, ax=ax, vmin=-1, vmax=1,
                annot_kws={"size": 7})
    ax.set_title("旅游业发展指标相关性热力图")
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    _save(fig, "21_旅游业发展指标相关性热力图.png")


# ---------- 22. 旅游总收入构成 堆叠面积 ----------
def c22():
    ds = A["dom_spend"]; ii = A["intl_income"]
    # 百万美元 → 亿元转换系数（≈7 CNY/USD ÷ 100 = 0.07）
    fx = 0.07
    common = ds.index.intersection(ii.index)
    dom = ds.loc[common]; intl = ii.loc[common] * fx
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.stackplot(_years(dom), dom.values, intl.values,
                 labels=["国内旅游总花费(亿元)", "国际旅游外汇收入(折算亿元)"],
                 colors=[PALETTE[0], PALETTE[1]], alpha=0.8)
    ax.set_title("旅游总收入构成（堆叠面积图，国际按1美元≈7元折算亿元）")
    ax.set_xlabel("年份"); ax.set_ylabel("亿元"); ax.legend(loc="upper left")
    _save(fig, "22_旅游总收入构成_堆叠面积图.png")


# ---------- 23. 重点省份 GDP 增长率趋势 ----------
def c23():
    pg = A["prov_gdp"]
    keys = [p for p in ["广东", "江苏", "山东", "浙江", "河南", "四川"] if p in pg.columns]
    fig, ax = plt.subplots(figsize=(10, 5.5))
    for i, p in enumerate(keys):
        s = pg[p].dropna(); g = s.pct_change() * 100
        ax.plot(_years(g), g.values, marker="o", ms=3, color=PALETTE[i % len(PALETTE)], label=p)
    ax.axhline(0, color="grey", lw=0.8)
    ax.set_title("重点省份GDP增长率趋势")
    ax.set_xlabel("年份"); ax.set_ylabel("增长率（%）"); ax.legend()
    _save(fig, "23_重点省份GDP增长率趋势.png")


# ---------- 24. 各省平均国际旅游外汇收入 ----------
def c24():
    pi = A["prov_intl_income"].dropna(how="all")
    mean = pi.mean().sort_values(ascending=False).head(15)
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(mean.index[::-1], mean.values[::-1], color=PALETTE[1])
    ax.set_title("各省平均国际旅游外汇收入")
    ax.set_xlabel("年均国际旅游外汇收入(百万美元)")
    _save(fig, "24_各省平均国际旅游外汇收入.png")


# ---------- 25. 2019 各省GDP vs 接待国外游客 散点 ----------
def c25():
    pg = A["prov_gdp"]; pf = A["prov_foreign"]
    yr = 2019
    if yr in pg.index and yr in pf.index:
        a = pg.loc[yr]; b = pf.loc[yr]
        df = pd.concat([a, b], axis=1).dropna()
        df.columns = ["GDP", "游客"]
        fig, ax = plt.subplots(figsize=(8, 5.5))
        ax.scatter(df["GDP"].values / 1e4, df["游客"].values, color=PALETTE[0], s=35)
        ax.set_title(f"{yr}年各省GDP与接待国外游客散点图")
        ax.set_xlabel("GDP（万亿元）"); ax.set_ylabel("接待国外游客(万人次)")
        _save(fig, "25_2019年各省GDP与接待国外游客散点图.png")


# ---------- 26. 各省接待国外游客平均增长率 ----------
def c26():
    pf = A["prov_foreign"].dropna(how="all")
    gr = pf.pct_change() * 100
    mean_g = gr.mean().sort_values(ascending=False).head(15)
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(mean_g.index[::-1], mean_g.values[::-1], color=PALETTE[3])
    ax.set_title("各省接待国外游客平均增长率")
    ax.set_xlabel("年均增长率（%）")
    _save(fig, "26_各省接待国外游客平均增长率.png")


# ---------- 27. 海南月度游客与收入趋势 ----------
def c27():
    h = A["hainan"].sort_values("Date")
    fig, ax1 = plt.subplots(figsize=(12, 5.5))
    ax1.plot(h["Date"], h["游客人数"], color=PALETTE[0], lw=1.2, label="接待游客(万人次)")
    ax1.set_xlabel("月份"); ax1.set_ylabel("游客(万人次)", color=PALETTE[0])
    ax2 = ax1.twinx()
    ax2.plot(h["Date"], h["总收入"], color=PALETTE[1], lw=1.2, label="旅游总收入(亿元)")
    ax2.set_ylabel("总收入(亿元)", color=PALETTE[1])
    ax1.set_title("海南月度游客与收入趋势")
    _save(fig, "27_海南月度游客与收入趋势.png")


# ---------- 28. 海南游客季节性分析 ----------
def c28():
    hs = A["hainan_season"]
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(list(hs.index), hs["游客人数"].values, marker="o", color=PALETTE[0])
    ax.set_title("海南游客季节性分析")
    ax.set_xlabel("月份"); ax.set_ylabel("月度平均游客(万人次)")
    _save(fig, "28_海南游客季节性分析.png")


# ---------- 29. 海南收入季节性分析 ----------
def c29():
    hs = A["hainan_season"]
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(list(hs.index), hs["总收入"].values, marker="o", color=PALETTE[1])
    ax.set_title("海南收入季节性分析")
    ax.set_xlabel("月份"); ax.set_ylabel("月度平均收入(亿元)")
    _save(fig, "29_海南收入季节性分析.png")


# ---------- 30. 海南年度旅游数据汇总 ----------
def c30():
    h = A["hainan"].copy()
    h["Year"] = h["Date"].dt.year
    annual = h.groupby("Year")[["游客人数", "总收入"]].sum()
    annual = annual[annual.index >= 2015]
    x = annual.index.astype(int)
    fig, ax1 = plt.subplots(figsize=(10, 5.5))
    ax1.bar(x, annual["游客人数"].values, color=PALETTE[0], alpha=0.8, label="游客(万人次)")
    ax1.set_xlabel("年份"); ax1.set_ylabel("游客(万人次)", color=PALETTE[0])
    ax2 = ax1.twinx()
    ax2.plot(x, annual["总收入"].values, color=PALETTE[1], marker="o", lw=2, label="收入(亿元)")
    ax2.set_ylabel("收入(亿元)", color=PALETTE[1])
    ax1.set_title("海南年度旅游数据汇总")
    _save(fig, "30_海南年度旅游数据汇总.png")


CHARTS = [c01, c02, c03, c04, c05, c06, c07, c08, c09, c10,
          c11, c12, c13, c14, c15, c16, c17, c18, c19, c20,
          c21, c22, c23, c24, c25, c26, c27, c28, c29, c30]


def main():
    print(f"生成 30 张 matplotlib 静态图表（命名对齐原项目）...")
    for fn in CHARTS:
        try:
            fn()
        except Exception as e:  # noqa: BLE001
            print(f"  [失败] {fn.__name__}: {e}")


if __name__ == "__main__":
    main()
