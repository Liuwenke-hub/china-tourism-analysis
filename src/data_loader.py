"""数据加载与清洗层。

职责：
1. 读取 10 个原始 Excel 统计文件；
2. 将「地区/指标 × 年份」宽表 melt 为长表，便于分析；
3. 清洗省份名称、剔除汇总行；
4. 对海南月度数据做特殊解析；
5. 提供按指标名提取国家级时间序列的辅助函数。

数据源说明：所有 Excel 均来自公开的宏观经济与旅游行业统计年鉴/公报
（国家统计局、文化和旅游部），海南专题来自海南省旅游和文化广电体育厅
公开月度统计；原始网页文本存于 data/shuj.txt，由 parse_hainan_raw() 解析。
"""
from pathlib import Path
import re
import pandas as pd

from config import DATA_DIR, CUTOFF_YEAR

# 文件名 -> 简化后的键名（与原始项目保持一致，便于对照）
EXCEL_FILES = {
    "地区生产总值分省年度数据.xlsx": "地区生产总值分省",
    "国际旅游外汇收入（百万美元）分省年度数据.xlsx": "国际旅游外汇收入分省",
    "国内旅游情况年度数据.xlsx": "国内旅游情况",
    "国内生成总值年度数据.xlsx": "国内生成总值",
    "接待国外游客分省年度数据.xlsx": "接待国外游客分省",
    "接待外国人游客分省年度数据.xlsx": "接待外国人游客分省",
    "居民消费水平年度数据.xlsx": "居民消费水平",
    "旅游业发展情况年度数据.xlsx": "旅游业发展情况",
    "全国居民人均收入情况年度数据.xlsx": "全国居民人均收入情况",
    "海南旅游统计数据.xlsx": "海南旅游统计数据",
}


def load_raw() -> dict[str, pd.DataFrame]:
    """读取所有 Excel 为原始 DataFrame 字典。"""
    raw = {}
    for fname, key in EXCEL_FILES.items():
        path = DATA_DIR / fname
        if not path.exists():
            print(f"  [跳过] 文件不存在: {fname}")
            continue
        try:
            raw[key] = pd.read_excel(path)
        except Exception as e:  # noqa: BLE001
            print(f"  [错误] 读取失败 {fname}: {e}")
    return raw


def _clean_province(name: str) -> str:
    """去除行政区划后缀，统一为短名（保留民族自治区主体，如内蒙古/新疆）。"""
    s = str(name)
    for token in ("特别行政区", "自治区", "省", "市", "壮族", "回族", "维吾尔", "藏族"):
        s = s.replace(token, "")
    return s.strip()


def process_dataframe(key: str, df: pd.DataFrame) -> pd.DataFrame | None:
    """将单个原始 DataFrame 处理为长表。

    返回列：
      - 月度数据：月份, Date, Year, Month, 游客人数, 总收入, 人均消费
      - 年度数据：Province/Indicator, Year, Value
    """
    # ---- 月度数据（如海南）----
    date_col = "月份" if "月份" in df.columns else ("栏数" if "栏数" in df.columns else None)
    if date_col:
        try:
            df = df.rename(columns={date_col: "月份"}).copy()
            df["Date"] = pd.to_datetime(
                df["月份"].astype(str).str.replace("年", "-").str.replace("月", ""),
                errors="coerce",
            )
            df.dropna(subset=["Date"], inplace=True)
            df["Year"] = df["Date"].dt.year
            df["Month"] = df["Date"].dt.month
            df = df[df["Year"] <= CUTOFF_YEAR]   # 仅保留毕业前可得数据
            rename_map = {}
            for col in df.columns:
                if "游客" in str(col) or "总人数" in str(col):
                    rename_map[col] = "游客人数"
                elif "总收入" in str(col) or "总花费" in str(col):
                    rename_map[col] = "总收入"
                elif "人均消费" in str(col):
                    rename_map[col] = "人均消费"
            df.rename(columns=rename_map, inplace=True)
            for col in ("游客人数", "总收入", "人均消费"):
                if col in df.columns:
                    if df[col].dtype == "object":
                        df[col] = df[col].astype(str).str.replace(r"[^\d.-]", "", regex=True)
                    df[col] = pd.to_numeric(df[col], errors="coerce")
            val_cols = [c for c in ("游客人数", "总收入", "人均消费") if c in df.columns]
            if val_cols:
                df.dropna(subset=val_cols, how="all", inplace=True)
            df.sort_values(by="Date", inplace=True)
            return df
        except Exception as e:  # noqa: BLE001
            print(f"  [错误] 月度数据处理失败 {key}: {e}")
            return None

    # ---- 年度数据 ----
    id_vars = []
    if "地区" in df.columns:
        id_vars.append("地区")
    if "指标" in df.columns:
        id_vars.append("指标")

    year_cols = []
    for col in df.columns:
        if isinstance(col, str) and col.endswith("年") and col[:-1].isdigit():
            year_cols.append(col)
        elif isinstance(col, int) and 1900 <= col <= 2050:
            year_cols.append(col)
        elif isinstance(col, str) and col.isdigit() and 1900 <= int(col) <= 2050:
            year_cols.append(col)
    if not year_cols:
        print(f"  [警告] 未找到年份列，跳过: {key}")
        return None
    if not id_vars:
        print(f"  [警告] 未找到地区/指标列，跳过: {key}")
        return None

    year_cols = [str(c) for c in year_cols]
    year_cols.sort(key=lambda x: int(x.replace("年", "")))

    try:
        melted = df.melt(
            id_vars=id_vars, value_vars=year_cols,
            var_name="Year_Raw", value_name="Value",
        )
    except Exception as e:  # noqa: BLE001
        print(f"  [错误] melt 失败 {key}: {e}")
        return None

    melted["Year"] = melted["Year_Raw"].astype(str).str.replace("年", "").astype(int)
    melted.drop(columns=["Year_Raw"], inplace=True)
    if "地区" in melted.columns:
        melted.rename(columns={"地区": "Province"}, inplace=True)
    if "指标" in melted.columns:
        melted.rename(columns={"指标": "Indicator"}, inplace=True)

    if melted["Value"].dtype == "object":
        melted["Value"] = melted["Value"].astype(str).str.replace(r"[^\d.-]", "", regex=True)
    melted["Value"] = pd.to_numeric(melted["Value"], errors="coerce")
    melted.dropna(subset=["Value", "Year"], inplace=True)

    if "Province" in melted.columns:
        melted["Province"] = melted["Province"].apply(_clean_province)
        melted = melted[~melted["Province"].isin(
            ["全国", "合计", "全部", "总计", "港澳台地区", ""])].copy()

    # 去除重复 (省份/指标, 年份) 组合（原始表存在重复行）
    dedup_keys = [c for c in ("Province", "Indicator", "Year") if c in melted.columns]
    melted = melted.drop_duplicates(subset=dedup_keys, keep="first")

    # 仅保留毕业前可获得的公开数据（≤ CUTOFF_YEAR），保证时间线自洽
    melted = melted[melted["Year"] <= CUTOFF_YEAR]

    sort_by = ["Year", "Province"] if "Province" in melted.columns else (
        ["Year", "Indicator"] if "Indicator" in melted.columns else ["Year"])
    melted.sort_values(by=sort_by, inplace=True)
    return melted


def load_processed() -> dict[str, pd.DataFrame]:
    """返回清洗后的长表字典。"""
    raw = load_raw()
    processed = {}
    for key, df in raw.items():
        out = process_dataframe(key, df.copy())
        if out is not None and not out.empty:
            processed[key] = out
    return processed


# 国家级指标提取的优先级关键词（指标名越精确越优先）
_PRIORITY = [
    "国内生产总值(亿元)", "国内生产总值", "人均国内生产总值",
    "居民人均可支配收入(元)", "居民人均可支配收入",
    "居民消费水平(元)", "居民消费水平",
    "国内游客(百万人次)", "国内旅游人数", "国内游客",
    "国内旅游总花费(亿元)", "国内旅游收入",
    "入境游客(万人次)", "入境过夜游客(万人次)",
    "国民总收入(亿元)", "总",
]


def get_national_indicator(processed: dict, df_name: str, substrings: list[str]):
    """从「指标」类长表中提取匹配的时间序列。

    返回：以 Year 为索引的 Series 或透视后的 DataFrame。
    """
    df = processed.get(df_name)
    if df is None or df.empty or "Indicator" not in df.columns:
        print(f"  [警告] 数据集缺失或格式不符: {df_name}")
        return None

    filtered = df[df["Indicator"].astype(str).str.contains(
        "|".join(substrings), na=False, regex=True)].copy()
    if filtered.empty:
        if df["Indicator"].nunique() == 1:
            return df[["Year", "Value"]].set_index("Year").sort_index()["Value"]
        return None

    if filtered["Indicator"].nunique() > 1:
        primary = next((ind for kw in _PRIORITY
                        for ind in filtered["Indicator"].unique() if kw == ind), None)
        if not primary:
            primary = next((ind for kw in _PRIORITY
                            for ind in filtered["Indicator"].unique() if kw in ind), None)
        if primary:
            return filtered[filtered["Indicator"] == primary][["Year", "Value"]].set_index("Year").sort_index()["Value"]
        return filtered.pivot_table(index="Year", columns="Indicator", values="Value").sort_index()
    return filtered[["Year", "Value"]].set_index("Year").sort_index()["Value"]


def parse_hainan_raw(path: str | Path | None = None) -> pd.DataFrame:
    """ETL：从海南省旅文厅公开网页原始文本(shuj.txt)解析月度旅游统计。

    返回列：月份, 接待游客总人数（万人次）, 旅游总收入（亿元）
    """
    path = Path(path) if path else DATA_DIR / "shuj.txt"
    if not path.exists():
        return pd.DataFrame()
    text = path.read_text(encoding="utf-8")
    blocks = re.findall(r"<文本>(.*?)</文本>", text, re.DOTALL)
    rows = []
    skipped = 0
    for block in blocks:
        date_m = re.search(r"(\d{4}年\d{1,2}月)旅游统计", block)
        date_str = date_m.group(1) if date_m else "N/A"
        tourists_m = re.search(
            r"一、接待(?:游客总人数(?:（万人次）)?|旅游者总计|过夜旅游者总计(?:（万人次）)?|过夜人数合计(?:（万人次）)?)\s*(\d+\.?\d*)",
            block)
        spend_m = re.search(r"[二三四]、(?:游客总花费|旅游(?:总)?收入)（亿元）\s*(\d+\.?\d*)", block)
        if tourists_m is None and spend_m is None:
            skipped += 1
            continue
        rows.append({
            "月份": date_str,
            "接待游客总人数（万人次）": float(tourists_m.group(1)) if tourists_m else None,
            "旅游总收入（亿元）": float(spend_m.group(1)) if spend_m else None,
        })
    if skipped > 0:
        print(f"  [海南数据] 跳过 {skipped} 个无法解析的文本块（格式可能已变更）")
    df = pd.DataFrame(rows)

    def _parse(m):
        mm = re.search(r"(\d{4})年(\d{1,2})月", m)
        return (int(mm.group(1)), int(mm.group(2))) if mm else (0, 0)
    if not df.empty:
        df["Year"], df["Month"] = zip(*df["月份"].apply(_parse))
        df = df.sort_values(["Year", "Month"]).drop(columns=["Year", "Month"])
    return df
