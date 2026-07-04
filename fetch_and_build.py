#!/usr/bin/env python3
"""
京东方A（000725）股票数据获取与可视化脚本
功能：
1. 通过Tushare获取过去一年的每日交易数据
2. 绘制每日收盘价曲线图
3. 保存为CSV格式
4. 生成HTML交易面板（K线图和交易量图）
"""

import os
import json
import getpass
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from dateutil.relativedelta import relativedelta
import tushare as ts


def get_token():
    """获取Tushare token，优先从环境变量读取，其次提示用户输入"""
    token = os.getenv("TUSHARE_TOKEN", "")
    if token:
        ts.set_token(token)
        print(f"使用环境变量中的Tushare token: {token[:8]}...")
        return ts.pro_api()
    
    print("未找到环境变量TUSHARE_TOKEN")
    print("请输入您的Tushare Pro token（输入不会显示在屏幕上）：")
    try:
        token = getpass.getpass("Token: ")
        if token:
            ts.set_token(token)
            print(f"已设置Tushare token: {token[:8]}...")
            return ts.pro_api()
        else:
            raise ValueError("Token不能为空")
    except Exception as e:
        print(f"获取token失败: {e}")
        raise RuntimeError("无法初始化Tushare API，请提供有效的token")


def fetch_daily(ts_code: str, months: int = 12) -> pd.DataFrame:
    """
    获取股票日线数据
    
    Args:
        ts_code: 股票代码（如 '000725.SZ'）
        months: 获取最近几个月的数据
    
    Returns:
        DataFrame: 包含交易数据的DataFrame
    """
    print(f"正在获取 {ts_code} 最近 {months} 个月的日线数据...")
    
    pro = get_token()
    end = datetime.now().strftime("%Y%m%d")
    start = (datetime.now() - relativedelta(months=months)).strftime("%Y%m%d")
    
    print(f"日期范围: {start} 至 {end}")
    
    try:
        df = pro.daily(ts_code=ts_code, start_date=start, end_date=end)
        if df is None or df.empty:
            raise RuntimeError(f"tushare daily 返回为空: {ts_code}")
        
        # 转换日期格式并排序
        df["trade_date"] = pd.to_datetime(df["trade_date"])
        df = df.sort_values("trade_date").reset_index(drop=True)
        
        print(f"成功获取 {len(df)} 条交易记录")
        return df
        
    except Exception as e:
        print(f"获取数据失败: {e}")
        raise


def plot_closing(df: pd.DataFrame, png_path: str):
    """
    绘制收盘价曲线图
    
    Args:
        df: 交易数据DataFrame
        png_path: PNG文件保存路径
    """
    print("正在绘制收盘价曲线图...")
    
    # 设置中文字体
    plt.rcParams["font.sans-serif"] = ["PingFang SC", "Heiti TC", "Arial Unicode MS"]
    plt.rcParams["axes.unicode_minus"] = False
    
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df["trade_date"], df["close"], linewidth=1.5, color="#1f77b4")
    ax.set_title("京东方A（000725）每日收盘价", fontsize=14, fontweight="bold")
    ax.set_xlabel("日期", fontsize=12)
    ax.set_ylabel("收盘价（元）", fontsize=12)
    ax.grid(True, alpha=0.3)
    
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(png_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    
    print(f"收盘价曲线图已保存到: {png_path}")


def build_html(df: pd.DataFrame, html_path: str):
    """
    生成HTML交易面板
    
    Args:
        df: 交易数据DataFrame
        html_path: HTML文件保存路径
    """
    print("正在生成HTML交易面板...")
    
    # 准备数据
    dates = df["trade_date"].dt.strftime("%Y-%m-%d").tolist()
    ohlc = df[["open", "close", "low", "high"]].round(2).values.tolist()
    vols = df["vol"].tolist()
    
    # 准备表格数据
    table_data = []
    for i, row in df.iterrows():
        table_data.append({
            "date": row["trade_date"].strftime("%Y-%m-%d"),
            "open": round(row["open"], 2),
            "high": round(row["high"], 2),
            "low": round(row["low"], 2),
            "close": round(row["close"], 2),
            "vol": row["vol"]
        })
    
    data_json = json.dumps({
        "dates": dates,
        "ohlc": ohlc,
        "vols": vols,
        "tableData": table_data
    }, ensure_ascii=False)
    
    html_template = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>京东方A 交易面板</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    padding: 20px;
  }
  #app {
    max-width: 1200px;
    margin: 0 auto;
  }
  .header {
    text-align: center;
    color: white;
    margin-bottom: 30px;
  }
  .header h1 {
    font-size: 28px;
    font-weight: 600;
    margin-bottom: 10px;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
  }
  .header .subtitle {
    font-size: 16px;
    opacity: 0.9;
  }
  .card {
    background: white;
    border-radius: 16px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.15);
    padding: 24px;
    margin-bottom: 24px;
    transition: transform 0.3s ease;
  }
  .card:hover {
    transform: translateY(-5px);
  }
  .card-title {
    font-size: 18px;
    font-weight: 600;
    color: #333;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 2px solid #f0f0f0;
  }
  .chart-container {
    width: 100%;
    height: 500px;
  }
  .volume-container {
    width: 100%;
    height: 200px;
  }
  .stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
    margin-bottom: 24px;
  }
  .stat-card {
    background: white;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
  }
  .stat-value {
    font-size: 24px;
    font-weight: 700;
    color: #333;
    margin-bottom: 5px;
  }
  .stat-label {
    font-size: 14px;
    color: #666;
  }
  .positive { color: #e74c3c; }
  .negative { color: #27ae60; }
  .footer {
    text-align: center;
    color: white;
    opacity: 0.8;
    margin-top: 30px;
    font-size: 14px;
  }
  .table-container {
    max-height: 400px;
    overflow-y: auto;
    border-radius: 8px;
    border: 1px solid #e0e0e0;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
  }
  th, td {
    padding: 12px 15px;
    text-align: right;
    border-bottom: 1px solid #f0f0f0;
  }
  th {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    font-weight: 600;
    position: sticky;
    top: 0;
    z-index: 10;
  }
  th:first-child,
  td:first-child {
    text-align: left;
  }
  tr:hover {
    background-color: #f8f9fa;
  }
  tr:nth-child(even) {
    background-color: #fafafa;
  }
  .table-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 16px;
    padding-top: 16px;
    border-top: 2px solid #f0f0f0;
  }
  .table-footer span {
    color: #666;
    font-size: 14px;
  }
  .pagination {
    display: flex;
    gap: 8px;
  }
  .pagination button {
    padding: 8px 12px;
    border: 1px solid #ddd;
    background: white;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
    color: #333;
    transition: all 0.3s;
  }
  .pagination button:hover {
    background: #667eea;
    color: white;
    border-color: #667eea;
  }
  .pagination button.active {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-color: #667eea;
  }
  .pagination button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  @media (max-width: 768px) {
    body { padding: 10px; }
    .header h1 { font-size: 22px; }
    .chart-container { height: 400px; }
    .volume-container { height: 150px; }
    .stats { grid-template-columns: repeat(2, 1fr); }
    .table-container { max-height: 300px; }
    th, td { padding: 8px 10px; font-size: 12px; }
    .pagination button { padding: 6px 10px; font-size: 12px; }
  }
</style>
</head>
<body>
<div id="app">
  <div class="header">
    <h1>京东方A（000725）交易面板</h1>
    <div class="subtitle">过去一年交易数据可视化</div>
  </div>
  
  <div class="stats" id="stats"></div>
  
  <div class="card">
    <div class="card-title">📈 K线图</div>
    <div id="kline" class="chart-container"></div>
  </div>
  
  <div class="card">
    <div class="card-title">📊 成交量</div>
    <div id="volume" class="volume-container"></div>
  </div>
  
  <div class="card">
    <div class="card-title">📋 交易数据</div>
    <div class="table-container">
      <table id="dataTable">
        <thead>
          <tr>
            <th>日期</th>
            <th>开盘价</th>
            <th>最高价</th>
            <th>最低价</th>
            <th>收盘价</th>
            <th>成交量</th>
          </tr>
        </thead>
        <tbody></tbody>
      </table>
    </div>
    <div class="table-footer">
      <span id="tableInfo"></span>
      <div class="pagination" id="pagination"></div>
    </div>
  </div>
  
  <div class="footer">
    数据来源：Tushare Pro | 生成时间：""" + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """
  </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<script>
const RAW = """ + data_json + """;

// 计算统计数据
function calculateStats() {
  const closes = RAW.ohlc.map(d => d[1]);
  const vols = RAW.vols;
  
  const latest = closes[closes.length - 1];
  const prev = closes[closes.length - 2] || latest;
  const change = latest - prev;
  const changePercent = (change / prev * 100).toFixed(2);
  
  const max = Math.max(...closes);
  const min = Math.min(...closes);
  const avgVol = Math.round(vols.reduce((a, b) => a + b, 0) / vols.length);
  
  return {
    latest: latest.toFixed(2),
    change: change.toFixed(2),
    changePercent: changePercent,
    max: max.toFixed(2),
    min: min.toFixed(2),
    avgVol: avgVol.toLocaleString(),
    totalDays: closes.length
  };
}

// 渲染统计卡片
function renderStats() {
  const stats = calculateStats();
  const isPositive = parseFloat(stats.change) >= 0;
  
  document.getElementById('stats').innerHTML = `
    <div class="stat-card">
      <div class="stat-value">${stats.latest}</div>
      <div class="stat-label">最新价（元）</div>
    </div>
    <div class="stat-card">
      <div class="stat-value ${isPositive ? 'positive' : 'negative'}">
        ${isPositive ? '+' : ''}${stats.change} (${isPositive ? '+' : ''}${stats.changePercent}%)
      </div>
      <div class="stat-label">涨跌幅</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">${stats.max}</div>
      <div class="stat-label">最高价（元）</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">${stats.min}</div>
      <div class="stat-label">最低价（元）</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">${stats.avgVol}</div>
      <div class="stat-label">平均成交量（手）</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">${stats.totalDays}</div>
      <div class="stat-label">交易天数</div>
    </div>
  `;
}

// 初始化K线图
function initKline() {
  const kline = echarts.init(document.getElementById('kline'));
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#ccc',
      borderWidth: 1,
      textStyle: {
        color: '#333'
      },
      formatter: function(params) {
        const data = params[0];
        const date = data.axisValue;
        const ohlc = data.data;
        return `
          <div style="font-weight:bold;margin-bottom:5px;">${date}</div>
          <div>开盘: ${ohlc[0]}</div>
          <div>收盘: ${ohlc[1]}</div>
          <div>最低: ${ohlc[2]}</div>
          <div>最高: ${ohlc[3]}</div>
        `;
      }
    },
    legend: {
      data: ['K线'],
      top: 10
    },
    grid: {
      left: '10%',
      right: '10%',
      bottom: '15%'
    },
    xAxis: {
      type: 'category',
      data: RAW.dates,
      boundaryGap: true,
      axisLine: { lineStyle: { color: '#999' } },
      axisLabel: {
        color: '#666',
        rotate: 45
      }
    },
    yAxis: {
      scale: true,
      splitArea: {
        show: true,
        areaStyle: {
          color: ['rgba(250,250,250,0.3)', 'rgba(200,200,200,0.3)']
        }
      },
      axisLine: { lineStyle: { color: '#999' } },
      axisLabel: {
        color: '#666'
      }
    },
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100
      },
      {
        show: true,
        type: 'slider',
        bottom: 20,
        height: 30,
        start: 0,
        end: 100
      }
    ],
    series: [
      {
        name: 'K线',
        type: 'candlestick',
        data: RAW.ohlc,
        itemStyle: {
          color: '#e74c3c',
          color0: '#27ae60',
          borderColor: '#e74c3c',
          borderColor0: '#27ae60'
        }
      }
    ]
  };
  
  kline.setOption(option);
  
  window.addEventListener('resize', () => kline.resize());
  
  return kline;
}

// 初始化成交量图
function initVolume() {
  const volume = echarts.init(document.getElementById('volume'));
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#ccc',
      borderWidth: 1,
      textStyle: {
        color: '#333'
      },
      formatter: function(params) {
        const data = params[0];
        return `
          <div style="font-weight:bold;margin-bottom:5px;">${data.axisValue}</div>
          <div>成交量: ${data.value.toLocaleString()} 手</div>
        `;
      }
    },
    grid: {
      left: '10%',
      right: '10%',
      bottom: '15%'
    },
    xAxis: {
      type: 'category',
      data: RAW.dates,
      axisLine: { lineStyle: { color: '#999' } },
      axisLabel: {
        color: '#666',
        rotate: 45
      }
    },
    yAxis: {
      scale: true,
      splitArea: {
        show: true,
        areaStyle: {
          color: ['rgba(250,250,250,0.3)', 'rgba(200,200,200,0.3)']
        }
      },
      axisLine: { lineStyle: { color: '#999' } },
      axisLabel: {
        color: '#666',
        formatter: function(value) {
          if (value >= 10000) {
            return (value / 10000).toFixed(1) + '万';
          }
          return value;
        }
      }
    },
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100
      },
      {
        show: true,
        type: 'slider',
        bottom: 20,
        height: 30,
        start: 0,
        end: 100
      }
    ],
    series: [
      {
        name: '成交量',
        type: 'bar',
        data: RAW.vols,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#3498db' },
            { offset: 1, color: '#2980b9' }
          ])
        },
        emphasis: {
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#2ecc71' },
              { offset: 1, color: '#27ae60' }
            ])
          }
        }
      }
    ]
  };
  
  volume.setOption(option);
  
  window.addEventListener('resize', () => volume.resize());
  
  return volume;
}

// 联动K线图和成交量图
function linkCharts(kline, volume) {
  kline.on('datazoom', function(params) {
    volume.dispatchAction({
      type: 'dataZoom',
      start: params.start,
      end: params.end
    });
  });
  
  volume.on('datazoom', function(params) {
    kline.dispatchAction({
      type: 'dataZoom',
      start: params.start,
      end: params.end
    });
  });
}

// 表格分页和渲染
function initTable() {
  const tableData = RAW.tableData;
  const rowsPerPage = 20;
  let currentPage = 1;
  let filteredData = [...tableData];
  
  function renderTable() {
    const tbody = document.querySelector('#dataTable tbody');
    const start = (currentPage - 1) * rowsPerPage;
    const end = start + rowsPerPage;
    const pageData = filteredData.slice(start, end);
    
    tbody.innerHTML = pageData.map(row => `
      <tr>
        <td>${row.date}</td>
        <td>${row.open}</td>
        <td>${row.high}</td>
        <td>${row.low}</td>
        <td>${row.close}</td>
        <td>${row.vol.toLocaleString()}</td>
      </tr>
    `).join('');
    
    // 更新表格信息
    const tableInfo = document.getElementById('tableInfo');
    tableInfo.textContent = `显示 ${start + 1}-${Math.min(end, filteredData.length)} 条，共 ${filteredData.length} 条`;
    
    // 渲染分页
    renderPagination();
  }
  
  function renderPagination() {
    const totalPages = Math.ceil(filteredData.length / rowsPerPage);
    const pagination = document.getElementById('pagination');
    
    let buttons = [];
    
    // 上一页按钮
    buttons.push(`<button onclick="changePage(${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>上一页</button>`);
    
    // 页码按钮
    const maxVisiblePages = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);
    
    if (endPage - startPage + 1 < maxVisiblePages) {
      startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }
    
    if (startPage > 1) {
      buttons.push(`<button onclick="changePage(1)">1</button>`);
      if (startPage > 2) {
        buttons.push(`<button disabled>...</button>`);
      }
    }
    
    for (let i = startPage; i <= endPage; i++) {
      buttons.push(`<button onclick="changePage(${i})" class="${i === currentPage ? 'active' : ''}">${i}</button>`);
    }
    
    if (endPage < totalPages) {
      if (endPage < totalPages - 1) {
        buttons.push(`<button disabled>...</button>`);
      }
      buttons.push(`<button onclick="changePage(${totalPages})">${totalPages}</button>`);
    }
    
    // 下一页按钮
    buttons.push(`<button onclick="changePage(${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>下一页</button>`);
    
    pagination.innerHTML = buttons.join('');
  }
  
  window.changePage = function(page) {
    const totalPages = Math.ceil(filteredData.length / rowsPerPage);
    if (page < 1 || page > totalPages) return;
    currentPage = page;
    renderTable();
  };
  
  // 初始渲染
  renderTable();
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
  renderStats();
  const kline = initKline();
  const volume = initVolume();
  linkCharts(kline, volume);
  initTable();
});
</script>
</body>
</html>"""
    
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_template)
    
    print(f"HTML交易面板已保存到: {html_path}")


def main():
    """主函数"""
    print("=" * 60)
    print("京东方A（000725）股票数据获取与可视化")
    print("=" * 60)
    
    # 设置路径
    OUT_DIR = "/Users/shuchen/Desktop/TESK1/沪深"
    CSV_PATH = f"{OUT_DIR}/jingdongfang_A_data.csv"
    PNG_PATH = f"{OUT_DIR}/closing_price_chart.png"
    HTML_PATH = f"{OUT_DIR}/trading_panel.html"
    
    # 确保输出目录存在
    os.makedirs(OUT_DIR, exist_ok=True)
    
    try:
        # 1. 获取数据
        df = fetch_daily("000725.SZ", months=12)
        
        # 2. 保存CSV
        print("\n正在保存CSV文件...")
        df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")
        print(f"CSV文件已保存到: {CSV_PATH}")
        
        # 3. 绘制收盘价曲线图
        print("\n正在绘制收盘价曲线图...")
        plot_closing(df, PNG_PATH)
        
        # 4. 生成HTML交易面板
        print("\n正在生成HTML交易面板...")
        build_html(df, HTML_PATH)
        
        print("\n" + "=" * 60)
        print("✅ 所有任务完成！")
        print("=" * 60)
        print(f"\n生成的文件：")
        print(f"  1. CSV数据文件: {CSV_PATH}")
        print(f"  2. 收盘价曲线图: {PNG_PATH}")
        print(f"  3. HTML交易面板: {HTML_PATH}")
        print(f"\n请用浏览器打开 {HTML_PATH} 查看交互式图表")
        
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        print("\n可能的原因：")
        print("  1. Tushare token未配置或无效")
        print("  2. 网络连接问题")
        print("  3. 股票代码错误")
        print("\n请检查Tushare token配置：")
        print("  - 设置环境变量: export TUSHARE_TOKEN='your_token_here'")
        print("  - 或在代码中直接设置: ts.set_token('your_token_here')")
        raise


if __name__ == "__main__":
    main()