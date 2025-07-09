take_profit = 104

stop_loss = 96
entry_price = 100

p_win  = (take_profit / entry_price) - 1  #0.04     # 예상 이익률
p_lose = 1 - (stop_loss / entry_price)    #0.04        # 예상 손실률


if p_win >= 0.20:               # +20 % 이상 이익 구간이면 1/3만 베팅
    factor = 1/3
elif p_win >= 0.10:             # +10 % 이상이면 1/2만 베팅
    factor = 1/2
else:                           # 그 아래는 풀 베팅
    factor = 1

if_win  = (p_win  * factor) + 1 - FEE_WIN
if_lose = (p_lose * factor) + 1 - FEE_LOSE