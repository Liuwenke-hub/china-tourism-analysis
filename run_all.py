"""一键运行：生成仪表盘 + 静态图。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

print("=" * 60)
print("  中国旅游经济分析 · 全量构建")
print("=" * 60)

from dashboard_pyecharts import main as gen_dashboard
from plots_matplotlib import main as gen_plots

gen_dashboard()
gen_plots()

print("\n✅ 全部完成！")
print(f"   交互仪表盘: {Path('output/dashboard.html').resolve()}")
print(f"   静态图表:    {list(Path('output/charts').glob('*.png'))}")
