#!/usr/bin/env python
"""
Day와 Hour 캔들스틱 데이터를 빠르게 엑셀로 내보내기
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

from trade.models import Day_Candle_stick, Hour_Candle_stick, Coin

def quick_all_candle_export():
    """Day와 Hour 캔들스틱 데이터를 빠르게 내보내기"""
    
    print("📊 모든 캔들스틱 데이터를 엑셀로 내보내는 중...\n")
    
    # 파일명 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"Complete_Candle_Data_{timestamp}.xlsx"
    
    try:
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            
            # Day Candle 데이터 처리
            print("📅 일일 캔들 데이터 처리 중...")
            day_data = []
            for candle in Day_Candle_stick.objects.all().select_related('coin').order_by('coin__tag', 'open_time'):
                try:
                    if candle.open_time > 1000000000000:
                        date_time = pd.to_datetime(candle.open_time, unit='ms')
                    else:
                        date_time = pd.to_datetime(candle.open_time, unit='s')
                    date_str = date_time.strftime('%Y-%m-%d')
                    datetime_str = date_time.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    date_str = str(candle.open_time)
                    datetime_str = str(candle.open_time)
                
                day_data.append({
                    '코인': candle.coin.tag,
                    '날짜': date_str,
                    '일시': datetime_str,
                    '시가': candle.open,
                    '고가': candle.high,
                    '저가': candle.low,
                    '종가': candle.close,
                    '거래량': candle.volume,
                    '방향': candle.direction or '',
                    '비정상수익률': candle.abnormal_return or '',
                    'VS_TSMOM': candle.vs_tsmom or ''
                })
            
            if day_data:
                day_df = pd.DataFrame(day_data)
                day_df.to_excel(writer, sheet_name='일일캔들', index=False)
                print(f"✅ 일일 캔들: {len(day_df)}개")
            
            # Hour Candle 데이터 처리
            print("🕐 시간 캔들 데이터 처리 중...")
            hour_data = []
            for candle in Hour_Candle_stick.objects.all().select_related('day_candle_stick__coin').order_by('day_candle_stick__coin__tag', 'open_time'):
                try:
                    if candle.open_time > 1000000000000:
                        date_time = pd.to_datetime(candle.open_time, unit='ms')
                    else:
                        date_time = pd.to_datetime(candle.open_time, unit='s')
                    date_str = date_time.strftime('%Y-%m-%d')
                    datetime_str = date_time.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    date_str = str(candle.open_time)
                    datetime_str = str(candle.open_time)
                
                hour_data.append({
                    '코인': candle.day_candle_stick.coin.tag,
                    '날짜': date_str,
                    '시간': datetime_str,
                    '시가': candle.open,
                    '고가': candle.high,
                    '저가': candle.low,
                    '종가': candle.close,
                    '거래량': candle.volume,
                    '방향': candle.direction or '',
                    '구조': candle.structure or ''
                })
            
            if hour_data:
                hour_df = pd.DataFrame(hour_data)
                hour_df.to_excel(writer, sheet_name='시간캔들', index=False)
                print(f"✅ 시간 캔들: {len(hour_df)}개")
                
            # 자동 열 너비 조정 함수
            def adjust_column_width(worksheet):
                for column in worksheet.columns:
                    max_length = 0
                    column_name = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_name].width = adjusted_width
            
            # 모든 시트에 대해 열 너비 조정
            for sheet_name in writer.sheets:
                adjust_column_width(writer.sheets[sheet_name])
        
        print(f"\n🎉 완료! 파일: {filename}")
        if day_data:
            print(f"📅 일일 데이터: {len(day_data)}개 ({day_df['날짜'].min()} ~ {day_df['날짜'].max()})")
        if hour_data:
            print(f"🕐 시간 데이터: {len(hour_data)}개 ({hour_df['날짜'].min()} ~ {hour_df['날짜'].max()})")
        
        print(f"\n📁 저장 위치: {os.path.abspath(filename)}")
        
    except Exception as e:
        print(f"❌ 오류: {str(e)}")

if __name__ == "__main__":
    print("=== 캔들스틱 데이터 빠른 내보내기 ===\n")
    quick_all_candle_export()

