"""项目配置：路径、中文字体、配色方案。

本文件不依赖任何业务数据，仅做全局常量与工具函数的定义。
"""
from pathlib import Path
import matplotlib

# ---------- 路径 ----------
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
CHARTS_DIR = OUTPUT_DIR / "charts"
DASHBOARD_PATH = OUTPUT_DIR / "dashboard.html"

for _d in (OUTPUT_DIR, CHARTS_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# 数据截止年份：分析窗口内的公开数据范围（≤2022）。
CUTOFF_YEAR = 2022

# ---------- 中文字体 ----------
# Windows 优先使用微软雅黑；若缺失则回退到黑体/SimHei。
def setup_chinese_font():
    """配置 matplotlib 中文字体，返回是否成功启用中文字体。"""
    candidates = ["Microsoft YaHei", "SimHei", "PingFang SC", "Arial Unicode MS"]
    available = {f.name for f in matplotlib.font_manager.fontManager.ttflist}
    chosen = next((c for c in candidates if c in available), None)
    if chosen:
        matplotlib.rcParams["font.sans-serif"] = [chosen]
        matplotlib.rcParams["axes.unicode_minus"] = False
        return chosen
    # 兜底：尝试让 matplotlib 自动发现系统中文字体
    matplotlib.rcParams["axes.unicode_minus"] = False
    return None

# ---------- 统一配色（旅游主题：海蓝 + 暖橙） ----------
PALETTE = [
    "#1f6f8b",  # 海蓝
    "#e07a3f",  # 暖橙
    "#2a9d8f",  # 青绿
    "#e9c46a",  # 沙金
    "#264653",  # 深蓝
    "#f4a261",  # 浅橙
    "#8ab17d",  # 草绿
    "#bc6c25",  # 赭石
]
