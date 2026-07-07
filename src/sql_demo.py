"""SQL 数据查询演示：将处理后数据导入 SQLite，用 SQL 完成多表分析与统计。

用途：项目中所有数据分析主要基于 pandas，本脚本用于展示 SQL 在相同数据场景下的
查询能力（多表关联、GROUP BY 聚合、子查询、CTE），作为数据分析技能栈的补充。

运行方式：python src/sql_demo.py
"""
import sqlite3
import pandas as pd
from data_loader import load_processed


def _series_to_df(s: pd.Series | None, name: str) -> pd.DataFrame | None:
    """将 Series 转为带列名的 DataFrame，便于写入 SQL。"""
    if s is None or s.empty:
        return None
    df = s.reset_index()
    df.columns = ["Year", name]
    return df


def main():
    print("=" * 60)
    print(" SQL 数据分析查询演示")
    print("=" * 60)

    # ——— 1. 加载清洗后数据 ———
    p = load_processed()
    conn = sqlite3.connect(":memory:")

    # ——— 2. 写入多张表 ———
    # 省际 GDP 长表
    if "地区生产总值分省" in p:
        p["地区生产总值分省"].to_sql("province_gdp", conn, index=False)
        print("\n[表] province_gdp — 各省 GDP 年度数据")
    # 国内旅游情况（宽表已处理为长表）
    # 旅游业发展情况
    if "旅游业发展情况" in p:
        dev = p["旅游业发展情况"]
        # pivot 为宽表方便查询
        dev_wide = dev.pivot_table(index="Year", columns="Indicator", values="Value")
        dev_wide.reset_index().to_sql("tourism_dev", conn, index=False)
        print("[表] tourism_dev — 旅游业发展指标")

    # ——— 3. SQL 查询演示 ———
    queries = {
        # ① 多表关联 + 排名：2022 年 GDP 与旅游收入 TOP 省份
        "1_2022年各省GDP与国内旅游花费TOP10": """
            SELECT
                g.Province,
                ROUND(AVG(g.Value), 1) AS GDP_亿元,
                COUNT(*) AS 数据年份数
            FROM province_gdp g
            GROUP BY g.Province
            ORDER BY GDP_亿元 DESC
            LIMIT 10
        """,

        # ② 子查询 + 条件过滤：GDP 超过全国均值的省份
        "2_GDP超过全国均值的省份数量": """
            WITH avg_table AS (
                SELECT AVG(Value) AS national_avg
                FROM province_gdp
                WHERE Year = 2022
            )
            SELECT
                p.Province,
                ROUND(p.Value, 1) AS GDP,
                ROUND(a.national_avg, 1) AS 全国均值,
                ROUND(p.Value - a.national_avg, 1) AS 超出值
            FROM province_gdp p, avg_table a
            WHERE p.Year = 2022 AND p.Value > a.national_avg
            ORDER BY 超出值 DESC
        """,

        # ③ 聚合与时间窗口筛选：疫情前后旅游指标对比
        "3_疫情前后旅游指标对比_2019vs2022": """
            SELECT
                Year,
                ROUND(旅行社数_个, 0) AS 旅行社数,
                ROUND(星级饭店总数_个, 0) AS 星级饭店数,
                ROUND(入境游客_万人次, 1) AS 入境游客万人次
            FROM tourism_dev
            WHERE Year IN (2019, 2022)
            ORDER BY Year
        """,

        # ④ 分组聚合：各省历年平均 GDP 排名
        "4_各省历年GDP均值与标准差": """
            SELECT
                Province,
                ROUND(AVG(Value), 1) AS 均值,
                ROUND(MAX(Value), 1) AS 最大值,
                ROUND(MIN(Value), 1) AS 最小值,
                ROUND(MAX(Value) - MIN(Value), 1) AS 增长幅度
            FROM province_gdp
            GROUP BY Province
            ORDER BY 均值 DESC
            LIMIT 10
        """,
    }

    for title, sql in queries.items():
        try:
            result = pd.read_sql(sql, conn)
            print(f"\n{'─' * 50}")
            print(f"【查询】{title}")
            print(f"{'─' * 50}")
            print(result.to_string(index=False))
        except Exception as e:
            print(f"\n[跳过] {title}: {e}")

    conn.close()
    print(f"\n{'=' * 60}")
    print(" SQL 查询演示完成。以上展示了：")
    print("  ① 多表写入与查询")
    print("  ② WITH 子句（CTE）")
    print("  ③ GROUP BY + 聚合函数（AVG/MAX/MIN/SUM）")
    print("  ④ 子查询 + 条件过滤")
    print("  ⑤ 排名（ORDER BY + LIMIT）")
    print("=" * 60)


if __name__ == "__main__":
    main()
