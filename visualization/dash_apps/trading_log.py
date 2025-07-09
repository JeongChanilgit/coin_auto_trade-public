import dash
from dash import dcc, html, Input, Output
import plotly.graph_objs as go
import pandas as pd
from trade.models import Coin, TradeLog, Candle_stick,Order_block, Entry_point
from django_plotly_dash import DjangoDash
import datetime
from trade.utils import API_keys, get_server_time, generate_signature, get_trading_log, get_budget
import os
app = DjangoDash('trading_log')
import json, time, datetime as dt
from collections import Counter
import requests




API_KEY = os.environ['binance_api_key']
SECRET_KEY = os.environ['binance_secret_key']
keys = API_keys(API_KEY, SECRET_KEY)
day7_trade_logs = get_trading_log(keys)
# account_dashboard.py ― DjangoDash 앱

# ---------------------------------------------------------------------
# 1) Binance에서 최근 28일(기준 밀리초) 트레이드 내역 가져오기
# ---------------------------------------------------------------------
MILLI_DAY = 24*60*60*1000

# ────────────────────────── 1. 7일 트레이드 로그 ──────────────────────────
        # 1 day → ms

def get_trading_log_df(keys) -> pd.DataFrame:
    """
    최근 7일 트레이드 내역 → DataFrame 반환.
    (startTime만 지정: 7일 초과 범위는 자동 제한됨)
    """
    now_ms   = get_server_time()
    start_ms = now_ms - 7*MILLI_DAY

    url     = "https://fapi.binance.com/fapi/v1/userTrades"
    headers = {"X-MBX-APIKEY": keys.api_key}
    params  = {
        "startTime": start_ms,
        "timestamp": now_ms,
        "recvWindow": 60_000,
    }
    params["signature"] = generate_signature(params, keys.secret_key)

    raw = requests.get(url, headers=headers, params=params).json()
    if isinstance(raw, dict) and raw.get("code"):
        raise RuntimeError(raw)           # 에러 전파

    df = pd.json_normalize(raw)
    df = df.rename(columns={
        "time": "ts",
        "realizedPnl": "pnl",
        "buyer": "isBuyer",
    })
    df["ts"]   = pd.to_datetime(df["ts"], unit="ms")
    df["side"] = df["isBuyer"].map({True: "BUY", False: "SELL"})
    df["pnl"]  = df["pnl"].astype(float)
    return df[["ts", "side", "pnl"]]

# ──────────────────────── 2. 과거 잔고 계산 ─────────────────────────
def balance_7d_ago(df: pd.DataFrame, cur_balance: float) -> float:
    """현재 잔고와 7일간 realized P/L 로부터 7일 전 잔고 추정"""
    pnl_7d = df["pnl"].sum()
    return cur_balance - pnl_7d

# ───────────────────────── 3. Dash 앱 만들기 ─────────────────────────
app = DjangoDash("account_dashboard_7d")

app.layout = html.Div([
    dcc.Interval(id="refresh", interval=5*60*1000, n_intervals=0),   # 5 분마다
    html.Div(id="balance-board",
             style={"display":"flex",
                    "justifyContent":"space-around",
                    "fontWeight":"700",
                    "fontSize":"20px",
                    "marginBottom":"10px"}),
    html.Div([
        dcc.Graph(id="win-lose-pie", style={"width":"40%"}),
        dcc.Graph(id="balance-line",  style={"width":"60%"}),
    ], style={"display":"flex"}),
])

# ───────────────────────── 4. 콜백 ─────────────────────────
@app.callback(
    Output("balance-board", "children"),
    Output("win-lose-pie",  "figure"),
    Output("balance-line",  "figure"),
    Input("refresh", "n_intervals"),
)
def update(_):

    # ① 데이터 수집
    cur_bal = round(get_budget(keys), 2)         # 현재 잔고 (USDT)
    df      = get_trading_log_df(keys)           # 7일 트레이드 로그

    # ② 잔고 보드
    bal_7d_ago = balance_7d_ago(df, cur_bal)
    diff_usdt  = cur_bal - bal_7d_ago
    diff_pct   = diff_usdt / bal_7d_ago * 100 if bal_7d_ago else 0

    board = [
        html.Span(f"현재 잔고: {cur_bal:,.2f} USDT"),
        html.Span(f"7일 전: {bal_7d_ago:,.2f} USDT "
                  f"({diff_usdt:+.2f} USDT, {diff_pct:+.2f}%p)"),
        html.Span(f"총 트레이드 건수: {len(df):,}회"),
    ]

    # ③ 파이차트 (손익 분포)
    tag = df["pnl"].apply(lambda x: "이익" if x>0 else ("손실" if x<0 else "본전"))
    cnt = Counter(tag)

    pie_fig = go.Figure(go.Pie(
        labels=list(cnt.keys()),
        values=list(cnt.values()),
        hole=.35,
        textposition="inside",
        texttemplate="%{label}<br>%{percent:.1%}<br>(%{value}회)"
    ))
    pie_fig.update_layout(title="7일간 손익 분포", template="plotly_white")

    # ④ 라인차트 (7일 잔고 추이)
    df_day = df.copy()
    df_day["date"] = df_day["ts"].dt.date
    daily_pnl = df_day.groupby("date")["pnl"].sum()

    dates = pd.date_range(dt.date.today() - dt.timedelta(days=6),
                          periods=7).date                       # 최근 7일
    balances = [bal_7d_ago]
    for d in dates:
        balances.append(balances[-1] + daily_pnl.get(d, 0))

    line_fig = go.Figure(go.Scatter(
        x=[d.strftime("%m-%d") for d in dates] + ["오늘"],
        y=balances[1:] + [cur_bal],
        mode="lines+markers"
    ))
    line_fig.update_layout(
        title="7일간 계좌 잔고 변동",
        xaxis_title="날짜",
        yaxis_title="USDT",
        template="plotly_white"
    )

    return board, pie_fig, line_fig