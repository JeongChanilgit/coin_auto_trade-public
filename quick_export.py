#!/usr/bin/env python
"""
Day_Candle_stick 데이터를 빠르게 엑셀로 내보내는 간단한 스크립트
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

def quick_export():
    """모든 Day_Candle_stick 데이터를 빠르게 엑셀로 내보내기"""
    
    print("📊 Day_Candle_stick 데이터를 엑셀로 내보내는 중...")
    
    try:
        # 모든 데이터 가져오기
        queryset = Day_Candle_stick.objects.all().select_related('coin').order_by('coin__tag', 'open_time')
        
        if not queryset.exists():
            print("❌ 내보낼 데이터가 없습니다.")
            return
        
        # 데이터를 리스트로 변환
        data_list = []
        for candle in queryset:
            # timestamp를 적절한 날짜 형식으로 변환
            try:
                # timestamp가 1000000000보다 크면 초 단위, 작으면 밀리초 단위로 가정
                if candle.open_time > 1000000000000:  # milliseconds
                    date_time = pd.to_datetime(candle.open_time, unit='ms')
                else:  # seconds
                    date_time = pd.to_datetime(candle.open_time, unit='s')
                
                date_str = date_time.strftime('%Y-%m-%d')
                datetime_str = date_time.strftime('%Y-%m-%d %H:%M:%S')
            except:
                date_str = str(candle.open_time)
                datetime_str = str(candle.open_time)
            profit_loss = 0
            if candle.ar_upper and candle.ar_lower and candle.vs_tsmom:
                if candle.high > candle.ar_upper:
                        profit_loss = (candle.close - candle.ar_upper)/candle.ar_upper
                        profit_loss += 0.998
                else:profit_loss = 1
            else:profit_loss = 1
                # elif candle.low < candle.ar_lower:
                #        profit_loss = (candle.ar_lower - candle.close)/candle.ar_lower*100
                #        profit_loss = 1 if profit_loss > 0 else -1
                        
                    
                    
            data_list.append({
                '코인': candle.coin.tag,
                '날짜': date_str,
                '일시': datetime_str,
                '시가': candle.open,
                '고가': candle.high,
                '저가': candle.low,
                '종가': candle.close,
                '거래량': candle.volume,
                '방향': candle.direction if candle.direction else '',
                '비정상수익률': candle.abnormal_return if candle.abnormal_return else '',
                'AR_Upper': candle.ar_upper if candle.ar_upper else '',
                'AR_Lower': candle.ar_lower if candle.ar_lower else '',
                'VS_TSMOM': candle.vs_tsmom if candle.vs_tsmom else '',
                '수익률': profit_loss
            })
        
        # DataFrame 생성
        df = pd.DataFrame(data_list)
        
        # 파일명 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Day_Candle_Data_{timestamp}.xlsx"
        
        # 엑셀 파일로 저장 (with formatting)
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='일일캔들데이터', index=False)
            
            # 워크시트 가져와서 열 너비 자동 조정
            worksheet = writer.sheets['일일캔들데이터']
            for column in worksheet.columns:
                max_length = 0
                column_name = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)  # 최대 50으로 제한
                worksheet.column_dimensions[column_name].width = adjusted_width
        
        # 결과 출력
        print(f"✅ 성공! 엑셀 파일을 생성했습니다 : {filename}")
        print(f"📈 총 {len(df)} 개의 데이터를 내보냈습니다.")
        
        # 코인별 데이터 개수
        coin_counts = df.groupby('코인').size()
        print(f"📊 코인별 데이터 개수 :")
        for coin, count in coin_counts.items():
            print(f"  - {coin}: {count}개")
        
        print(f"📅 데이터 기간 : {df['날짜'].min()} ~ {df['날짜'].max()}")
        print(f"\n💡 파일 위치 : {os.path.abspath(filename)}")
        
    except Exception as e:
        print(f"❌ 오류가 발생했습니다 : {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    print("=== Day_Candle_stick 데이터 빠른 내보내기 ===\n")
    quick_export()

