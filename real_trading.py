import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "coin_auto_trade.settings")

import django
django.setup()

from trade.models import Entry_point
from trade.utils import Trading, Position, API_keys, get_budget

import django
import asyncio
import websockets
import json
import time
from asgiref.sync import sync_to_async


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "coin_auto_trade.settings")
django.setup()

API_KEY = os.environ['binance_api']
SECRET_KEY = os.environ['binance_secret']
keys = API_keys(API_KEY, SECRET_KEY)

triggered_entries = []

@sync_to_async
def get_entry_points():
    entrys = list(Entry_point.objects.all().order_by('tag'))
    ans = []
    for entry in entrys:
        if entry.gap < 4:
            ans.append(entry)
    return ans
@sync_to_async
def find_entrys(symbol):
    tag = symbol[:len(symbol)-4] # usdt 빼내기기

    entrys =  list(Entry_point.objects.filter(tag=tag))
    return entrys

# 메인 로직
async def monitor_book_ticker():
    while True:

        
        entry_points = await get_entry_points()
        try:
            budget=get_budget(keys)
            
        except:
            print('?')
            await asyncio.sleep(20)
            continue
        if not entry_points:
           
            await asyncio.sleep(5)
            continue

        symbols = list({entry.tag.upper() for entry in entry_points})
        streams = [f"{symbol.lower() + 'usdt'}@bookTicker" for symbol in symbols]
        stream_url = "wss://fstream.binance.com/stream?streams=" + "/".join(streams)
        now = time.time()
        print(f"🔌 Connecting to: {stream_url}")
        trash = []
        stack = 0
        try:
            async with websockets.connect(
            stream_url,
            ping_interval=50,    
            ping_timeout=10      
            ) as ws:
                print("✅ WebSocket connected.")
                while True:
           

                    try:
                        exit_flag = 0
                        message = await ws.recv()
                        data = json.loads(message)
              
                        if 'data' not in data: continue
                        d = data['data']
                        symbol = d['s']              
                        bid = float(d['b'])          # 최우선 매수호가
                        ask = float(d['a'])          # 최우선 매도호가
                        current_entries = await find_entrys(symbol)
           
                        if time.time() - now > 300:
                            stack += 1
                            if stack > 50:
                                print('entry_point changed')
                                stack = 0
                                break
                        for entry in current_entries:
                            
                            entry_symbol = entry.tag.upper()
                            if not entry_symbol.endswith("USDT"):
                                entry_symbol += "USDT"
                            #print(entry_symbol,symbol)
                            if entry_symbol != symbol: continue
                            if entry in triggered_entries: continue
                            
                            #if entry.direction == 'BUY' and (time.time() - now) % 5 < 0.015:# and (ask - entry.entry_price)/entry.entry_price*100 < 2:
                            #   print(f"[{symbol}] ask={ask} entry={entry.entry_price} gap={round((ask - entry.entry_price)/entry.entry_price*100,2)}%")
                            #if entry.direction == 'SELL'  and (time.time() - now) % 5 < 0.015:# (entry.entry_price - bid)/bid*100 < 2:
                            #    print(f"[{symbol}] bid={bid} entry={entry.entry_price} gap={round((entry.entry_price - bid)/bid*100,2)}%")
                            
                            # 진입 조건 확인
                            if entry.direction == 'BUY' and ask <= entry.entry_price and [entry.tag,entry.entry_price] not in triggered_entries:
                                
                                print(f"🚀 BUY Triggered {symbol} at ask={ask}")
                                triggered_entries.append([entry.tag,entry.entry_price])
                            elif entry.direction == 'SELL' and bid >= entry.entry_price and [entry.tag,entry.entry_price] not in triggered_entries:
                                
                                print(f"🚀 SELL Triggered {symbol} at bid={bid}")
                                triggered_entries.append([entry.tag,entry.entry_price])
                            else:
                                continue

                            try:
                                
                                if budget > 5.0 :
                                    if entry.direction == "BUY" and entry.take_profit / entry.entry_price > 1.2:
                                        budget = budget // 3
                                    elif entry.direction == "BUY" and entry.take_profit / entry.entry_price > 1.1:
                                        budget = budget // 2
                                    elif entry.direction == "SELL" and (entry.entry_price * 2 - entry.take_profit) / entry.entry_price > 1.2 :
                                        budget = budget // 3
                                    elif entry.direction == "SELL" and (entry.entry_price * 2 - entry.take_profit) / entry.entry_price > 1.1 :
                                        budget = budget // 2
                                    target = Position( entry_symbol, entry.direction, entry.entry_price, entry.stop_loss, budget=budget)
                                    Trading(target, keys)
                                    print(f"✅ Order placed for {symbol}")
                                    budget = 0.0
                                    
                                else :
                                    print('already in-position')
                                    exit_flag = 1
                                

                            except Exception as e:
                                print(f"[ERROR] Trade failed for {symbol}: {e}")
                        if exit_flag == 1:
                    
                            break
                        
                    except Exception as e:
                        print(f"[MESSAGE ERROR] {e}")
                        
                
                        break

        except Exception as e:
            print(f"[CONNECTION ERROR] {e}")
 
        

if __name__ == "__main__":
    asyncio.run(monitor_book_ticker())
