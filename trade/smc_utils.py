import math
from datetime import datetime, timezone
from django.db import transaction
from django.db import models

from trade.models import Coin, Day_Candle_stick

def _as_dt(ts_float):
    if isinstance(ts_float, datetime):
        return ts_float
    return datetime.utcfromtimestamp(float(ts_float)).replace(tzinfo=timezone.utc)

def logret(c2, c1):
    if c2 is None or c1 is None or c1 <= 0:
        return None
    return math.log(c2 / c1)

@transaction.atomic
def compute_vw_tsmom_and_ar(
    tag: str = "BTC",
    candle_size: str = "1d",
    lookback_vw: int = 20,          # VW-TSMOM 가중 수익 창(일)
    vtsmom_z_window: int = 60,      # VW-TSMOM z-score 롤링 창
    ar_window: int = 60,            # AR μ,σ 롤링 창
    ar_k: float = 2.0,              # AR 경계 계수 k
    min_rows: int = 60             # 최소 데이터(안전 여유 포함)
):
    """
    BTC 일봉 전체에 대해 각 일자별로 다음을 저장:
      - direction: 'bullish'/'bearish' (VW-TSMOM 기준)
      - vs_tsmom:  VW-TSMOM의 z-score
      - abnormal_return: (r_t - μ)/σ (z-score)
      - ar_upper, ar_lower: μ±kσ을 '가격 경계'로 변환한 값 (전일 종가 기준)
    """
    coin = Coin.objects.get(tag=tag, candle_size=candle_size)

    # 필요한 필드 모두 로딩(only로 누락되면 저장 시 무시됨)
    rows = list(
        Day_Candle_stick.objects
        .filter(coin=coin)
        .order_by("open_time")
        .only("id","open_time","open","high","low","close","volume",
              "direction","abnormal_return","ar_upper","ar_lower","vs_tsmom")
    )
    n = len(rows)
    if n < min_rows:
        return {"updated": 0, "message": f"not enough rows: {n} < {min_rows}"}

    closes = [r.close for r in rows]
    vols   = [r.volume for r in rows]

    # 일간 로그수익 r_t
    rets = [None] * n
    for i in range(1, n):
        rets[i] = logret(closes[i], closes[i-1])

    # --- VW-TSMOM 원시 점수(가중 로그수익 합) ---
    vw_raw = [None] * n
    for t in range(1, n):
        start = t - lookback_vw
        if start < 1:
            continue
        rw = rets[start:t]           # r_{t-L} .. r_{t-1}
        vw = vols[start:t]
        if any(r is None for r in rw):
            continue
        v_sum = sum(vw)
        if v_sum is None or v_sum <= 0:
            continue
        w = [v / v_sum for v in vw]
        vw_raw[t] = sum(w[i] * rw[i] for i in range(len(w)))

    # --- VW-TSMOM z-score (롤링) ---
    vs_tsmom_z = [None] * n
    for t in range(n):
        start = t - vtsmom_z_window + 1
        if start < 1:
            continue
        series = [vw_raw[j] for j in range(start, t+1) if vw_raw[j] is not None]
        if len(series) < int(vtsmom_z_window * 0.8):
            continue
        mu = sum(series) / len(series)
        var = sum((x - mu) ** 2 for x in series) / len(series)
        sigma = math.sqrt(var)
        if sigma and vw_raw[t] is not None:
            vs_tsmom_z[t] = (vw_raw[t] - mu) / sigma

    # --- AR: z-score 및 가격 경계 ---
    ar_z = [None] * n
    ar_upper_price = [None] * n
    ar_lower_price = [None] * n

    for t in range(1, n):
        # μ,σ는 "직전까지" 창으로 계산
        start = t - ar_window
        if start < 1:
            continue
        series = [rets[j] for j in range(start, t) if rets[j] is not None]  # t-1까지
        if len(series) < int(ar_window * 0.8):
            continue
        mu = sum(series) / len(series)
        var = sum((x - mu) ** 2 for x in series) / len(series)
        sigma = math.sqrt(var)
        r_t = rets[t]
        if sigma and r_t is not None:
            ar_z[t] = (r_t - mu) / sigma
            upper_r = mu + ar_k * sigma
            lower_r = mu - ar_k * sigma
            prev_close = closes[t-1]
            # 경계 '가격'으로 변환 (전일 종가 기준)
            ar_upper_price[t] = prev_close * math.exp(upper_r)
            ar_lower_price[t] = prev_close * math.exp(lower_r)

    # --- 저장: direction, vs_tsmom(z), abnormal_return(z), ar_upper/lower(가격) ---
    for t in range(n):
        row = rows[t]

        # direction은 VW-TSMOM 기준(원시 또는 z 중 택1). 여기서는 z 기준.
        if vs_tsmom_z[t] is None:
            direction = None
        else:
            direction = "bullish" if vs_tsmom_z[t] > 0 else "bearish"

        row.direction = direction
        row.vs_tsmom = vs_tsmom_z[t] if vs_tsmom_z[t] is not None else None
        row.abnormal_return = ar_z[t] if ar_z[t] is not None else None
        row.ar_upper = ar_upper_price[t] if ar_upper_price[t] is not None else None
        row.ar_lower = ar_lower_price[t] if ar_lower_price[t] is not None else None

    # 한번에 반영(성능)
    Day_Candle_stick.objects.bulk_update(
        rows,
        ["direction","vs_tsmom","abnormal_return","ar_upper","ar_lower"],
        batch_size=1000,
    )
    return {"updated": n}
