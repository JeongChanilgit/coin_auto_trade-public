#!/usr/bin/env python
"""
Day_Candle_stick 데이터를 엑셀로 내보내는 스크립트
"""

import os
import sys
import django
import pandas as pd
from datetime import datetime

# Django 설정 초기화
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coin_auto_trade.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from trade.models import Day_Candle_stick, Coin


def export_day_candle_to_excel(coin_tag=None, output_filename=None):
    """
    Day_Candle_stick 데이터를 엑셀로 내보내기
    
    Args:
        coin_tag (str, optional): 특정 코인만 내보내기 (예: 'BTC', 'ETH')
        output_filename (str, optional): 출력 파일명. 기본값은 현재 시간 기반
    """
    try:
        # 쿼리셋 생성
        if coin_tag:
            queryset = Day_Candle_stick.objects.filter(coin__tag=coin_tag).select_related('coin')
            print(f"📊 {coin_tag} 코인 데이터를 내보내는 중...")
        else:
            queryset = Day_Candle_stick.objects.all().select_related('coin')
            print("📊 모든 코인의 일일 캔들스틱 데이터를 내보내는 중...")
        
        if not queryset.exists():
            print("❌ 내보낼 데이터가 없습니다.")
            return None
        
        # 데이터를 리스트로 변환
        data_list = []
        for candle in queryset:
            # open_time을 datetime으로 변환 (timestamp인 경우)
            try:
                if candle.open_time > 1000000000:  # timestamp in seconds
                    date_time = datetime.fromtimestamp(candle.open_time)
                else:  # timestamp in milliseconds
                    date_time = datetime.fromtimestamp(candle.open_time / 1000)
            except:
                date_time = candle.open_time
            
            data_list.append({
                'Coin': candle.coin.tag,
                'Date': date_time,
                'Open': candle.open,
                'High': candle.high,
                'Low': candle.low,
                'Close': candle.close,
                'Volume': candle.volume,
                'Direction': candle.direction,
                'Abnormal_Return': candle.abnormal_return,
                'AR_Upper': candle.ar_upper,
                'AR_Lower': candle.ar_lower,
                'VS_TSMOM': candle.vs_tsmom,
                'Open_Time_Raw': candle.open_time
            })
        
        # DataFrame 생성
        df = pd.DataFrame(data_list)
        
        # 데이터 정렬 (날짜순)
        df = df.sort_values(['Coin', 'Date'])
        
        # 출력 파일명 설정
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if coin_tag:
                output_filename = f"Day_Candle_{coin_tag}_{timestamp}.xlsx"
            else:
                output_filename = f"Day_Candle_All_{timestamp}.xlsx"
        
        # 엑셀 파일로 저장
        df.to_excel(output_filename, index=False, sheet_name='Day_Candle_Data')
        
        print(f"✅ 성공적으로 엑셀 파일을 생성했습니다: {output_filename}")
        print(f"📈 총 {len(df)} 개의 데이터를 내보냈습니다.")
        
        # 데이터 요약 정보 출력
        print("\n📊 데이터 요약:")
        print(f"- 코인 종류: {df['Coin'].nunique()}개 ({', '.join(df['Coin'].unique())})")
        print(f"- 데이터 기간: {df['Date'].min()} ~ {df['Date'].max()}")
        print(f"- 총 레코드 수: {len(df)}")
        
        return output_filename
        
    except Exception as e:
        print(f"❌ 오류가 발생했습니다: {str(e)}")
        return None


def get_available_coins():
    """사용 가능한 코인 목록 반환"""
    coins = Coin.objects.all()
    return [coin.tag for coin in coins]


if __name__ == "__main__":
    print("=== Day_Candle_stick 데이터 엑셀 내보내기 ===\n")
    
    # 사용 가능한 코인 목록 출력
    available_coins = get_available_coins()
    print(f"사용 가능한 코인: {', '.join(available_coins)}")
    print()
    
    # 사용자 입력 받기
    choice = input("모든 코인을 내보내시겠습니까? (y/N): ").strip().lower()
    
    if choice == 'y':
        # 모든 코인 내보내기
        export_day_candle_to_excel()
    else:
        # 특정 코인 선택
        coin_input = input(f"내보낼 코인을 입력하세요 ({', '.join(available_coins)}): ").strip().upper()
        
        if coin_input in available_coins:
            export_day_candle_to_excel(coin_tag=coin_input)
        else:
            print("❌ 유효하지 않은 코인입니다.")
            
        # 여러 코인을 한 번에 내보내기 옵션
        multiple_choice = input("여러 코인을 개별 파일로 내보내시겠습니까? (y/N): ").strip().lower()
        if multiple_choice == 'y':
            for coin in available_coins:
                print(f"\n--- {coin} 데이터 내보내기 ---")
                export_day_candle_to_excel(coin_tag=coin)

