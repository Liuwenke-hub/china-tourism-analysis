"""一键运行：全量构建（仪表盘 + 静态图 + Word 报告 + SQL 演示）。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

print("=" * 60)
print("  中国旅游经济分析 · 全量构建")
print("=" * 60)

from dashboard_pyecharts import main as gen_dashboard
from plots_matplotlib import main as gen_plots
from sql_demo import main as run_sql
import generate_report  # 导入即按现有图表生成 Word 报告

gen_dashboard()
gen_plots()
run_sql()
# generate_report 已在导入时生成 docx

print("\n✅ 全部完成！")
print(f"   交互仪表盘: {Path('output/dashboard.html').resolve()}")
print(f"   静态图表:    {len(list(Path('output/charts').glob('*.png')))} 张")
print(f"   Word 报告:   {Path('output/中国旅游与经济发展可视化分析报告.docx').resolve()}")
