# 京东方A股票数据获取与可视化计划

## Context
用户需要获取京东方A（000725）过去一年的交易数据，绘制收盘价曲线图，保存为CSV格式，并创建一个HTML交易面板展示K线图和交易量图。用户已具备完整的Python环境和Tushare token配置。

## 实施方案

### 总体目标与交付物
1. 用 Tushare 拉取京东方A（000725）过去一年的逐日行情
2. 输出 CSV，并绘制每日收盘价曲线
3. 生成一个单文件 HTML 交易面板（K线 + 成交量），浏览器直接打开

### 文件结构
```
/Users/shuchen/Desktop/TESK1/沪深/
├── fetch_and_build.py          # 主脚本
├── jingdongfang_A_data.csv     # 数据文件
├── closing_price_chart.png     # 收盘价曲线图
└── trading_panel.html          # 单文件HTML面板
```

### 技术栈
- Python 3.x
- Tushare Pro API
- Pandas（数据处理）
- Matplotlib（Python图表）
- ECharts（HTML图表库，CDN加载）

## 详细实施步骤

### 1. 创建主脚本 `fetch_and_build.py`
脚本包含4个核心函数：
- `get_token()`：读取tushare token（优先环境变量，其次回退`ts.set_token`）
- `fetch_daily(ts_code, months=12)`：拉取日线数据并返回DataFrame
- `save_outputs(df, out_dir)`：保存CSV + 收盘价PNG
- `build_html(df, html_path)`：生成单文件HTML（ECharts）

### 2. 数据获取实现
- 使用`000725.SZ`（Tushare标准格式）
- 用`relativedelta(months=12)`计算"过去一年"（比`timedelta(days=365)`更稳定）
- 返回字段：`trade_date, open, high, low, close, vol, amount`
- 按`trade_date`升序排列

### 3. 图表绘制实现
- Matplotlib中文显示：设置`font.sans-serif`为`PingFang SC`、`Heiti TC`、`Arial Unicode MS`
- 绘制收盘价曲线并保存为PNG

### 4. HTML交易面板实现
- 使用ECharts库绘制专业金融图表
- K线图展示开盘价、收盘价、最高价、最低价
- 交易量柱状图
- 响应式设计，适应不同屏幕尺寸
- 数据提示框显示详细信息
- 支持交互式缩放

## 关键代码示例

### 数据获取
```python
from datetime import datetime
from dateutil.relativedelta import relativedelta
import tushare as ts
import pandas as pd

def get_token():
    import os
    token = os.getenv("TUSHARE_TOKEN", "")
    if token:
        ts.set_token(token)
    return ts.pro_api()

def fetch_daily(ts_code: str, months: int = 12) -> pd.DataFrame:
    pro = get_token()
    end = datetime.now().strftime("%Y%m%d")
    start = (datetime.now() - relativedelta(months=months)).strftime("%Y%m%d")
    df = pro.daily(ts_code=ts_code, start_date=start, end_date=end)
    if df is None or df.empty:
        raise RuntimeError(f"tushare daily 返回为空: {ts_code}")
    df["trade_date"] = pd.to_datetime(df["trade_date"])
    df = df.sort_values("trade_date").reset_index(drop=True)
    return df
```

### 图表绘制
```python
import matplotlib.pyplot as plt

def plot_closing(df: pd.DataFrame, png_path: str):
    plt.rcParams["font.sans-serif"] = ["PingFang SC", "Heiti TC", "Arial Unicode MS"]
    plt.rcParams["axes.unicode_minus"] = False
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df["trade_date"], df["close"])
    ax.set_title("京东方A（000725）每日收盘价")
    ax.set_xlabel("日期")
    ax.set_ylabel("收盘价（元）")
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(png_path, dpi=150)
    plt.close(fig)
```

### HTML生成
```python
import json

def build_html(df: pd.DataFrame, html_path: str):
    dates = df["trade_date"].dt.strftime("%Y-%m-%d").tolist()
    ohlc = df[["open", "close", "low", "high"]].round(2).values.tolist()
    vols = df["vol"].tolist()
    data_json = json.dumps({"dates": dates, "ohlc": ohlc, "vols": vols}, ensure_ascii=False)
    
    html_template = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"/>
<title>京东方A 交易面板</title>
<style>
  body{margin:0;font-family:system-ui,-apple-system,sans-serif;background:#f7f8fa;color:#222;}
  #app{max-width:1100px;margin:24px auto;padding:0 16px;}
  h1{font-size:22px;margin-bottom:16px;}
  .card{background:#fff;border-radius:12px;box-shadow:0 6px 24px rgba(0,0,0,.06);padding:12px;margin-bottom:16px;}
</style>
</head>
<body>
<div id="app">
  <h1>京东方A（000725）交易面板</h1>
  <div class="card"><div id="kline" style="width:100%;height:520px;"></div></div>
  <div class="card"><div id="volume" style="width:100%;height:220px;"></div></div>
</div>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<script>
const RAW = __DATA_JSON__;
const kline = echarts.init(document.getElementById('kline'));
const volume = echarts.init(document.getElementById('volume'));
kline.setOption({
  tooltip:{trigger:'axis'},
  xAxis:{type:'category',data:RAW.dates,boundaryGap:true},
  yAxis:{scale:true},
  dataZoom:[{type:'inside'},{type:'slider'}],
  series:[{type:'candlestick',data:RAW.ohlc}]
});
volume.setOption({
  tooltip:{trigger:'axis'},
  xAxis:{type:'category',data:RAW.dates},
  yAxis:{scale:true},
  dataZoom:[{type:'inside'},{type:'slider'}],
  series:[{type:'bar',data:RAW.vols}]
});
window.addEventListener('resize',()=>{kline.resize();volume.resize();});
</script>
</body>
</html>"""
    html_text = html_template.replace("__DATA_JSON__", data_json)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_text)
```

## 主程序调用顺序
```python
OUT_DIR = "/Users/shuchen/Desktop/TESK1/沪深"
CSV_PATH = f"{OUT_DIR}/jingdongfang_A_data.csv"
PNG_PATH = f"{OUT_DIR}/closing_price_chart.png"
HTML_PATH = f"{OUT_DIR}/trading_panel.html"

if __name__ == "__main__":
    df = fetch_daily("000725.SZ", months=12)
    df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")
    plot_closing(df, PNG_PATH)
    build_html(df, HTML_PATH)
    print("完成：", CSV_PATH, PNG_PATH, HTML_PATH)
```

## 验证方法
1. 运行`python fetch_and_build.py`脚本，确认数据获取成功并生成CSV文件
2. 检查CSV文件内容，确保包含完整的交易数据
3. 在浏览器中打开`trading_panel.html`，验证K线图和交易量图正常显示
4. 测试图表的交互功能（缩放、数据提示等）

## 注意事项
- Tushare token配置：优先从环境变量读取（如`TUSHARE_TOKEN`），避免明文写死
- 接口返回异常：网络波动时`pro.daily(...)`可能返回`None`，建议加上重试机制
- 日期计算：用`relativedelta(months=12)`比`timedelta(days=365)`更稳定
- 中文显示：Matplotlib中文乱码很常见，务必设置`font.sans-serif`
- CSV编码：Windows Excel打开中文CSV容易乱码，建议`utf-8-sig`
- HTML单文件：ECharts走CDN即可；如果需要完全离线，需要把`echarts.min.js`内联进HTML
- 数据字段一致性：Tushare的`vol`通常是"手"或"股"，展示时可加单位说明