#!/usr/bin/env python
"""
Day_Candle_stick과 Hour_Candle_stick 데이터를 모두 엑셀로 내보내는 스크립트
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

def export_all_candle_data():
    """Day_Candle_stick과 Hour_Candle_stick 데이터를 모두 엑셀로 내보내기"""
    
    print("📊 Day 및 Hour 캔들스틱 데이터를 엑셀로 내보내는 중...")
    
    try:
        # 파일명 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"All_Candle_Data_{timestamp}.xlsx"
        
        # Excel Writer 생성
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            
            # === Day Candle 데이터 처리 ===
            print("📅 Day Candle 데이터 처리 중...")
            day_queryset = Day_Candle_stick.objects.all().select_related('coin').order_by('coin__tag', 'open_time')
            
            if day_queryset.exists():
                day_data = []
                for candle in day_queryset:
                    # timestamp를 날짜 형식으로 변환
                    try:
                        if candle.open_time > 1000000000000:  # milliseconds
                            date_time = pd.to_datetime(candle.open_time, unit='ms')
                        else:  # seconds
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
                        '방향': candle.direction if candle.direction else '',
                        '비정상수익률': candle.abnormal_return if candle.abnormal_return else '',
                        'VS_TSMOM': candle.vs_tsmom if candle.vs_tsmom else '',
                        '원본시간': candle.open_time
                    })
                
                # Day DataFrame 생성 및 저장
                day_df = pd.DataFrame(day_data)
                day_df.to_excel(writer, sheet_name='일일캔들데이터', index=False)
                print(f"✅ Day Candle 데이터 {len(day_df)}개 처리 완료")
                
                # 열 너비 조정
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
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_name].width = adjusted_width
            
            # === Hour Candle 데이터 처리 ===
            print("🕐 Hour Candle 데이터 처리 중...")
            hour_queryset = Hour_Candle_stick.objects.all().select_related('day_candle_stick__coin').order_by('day_candle_stick__coin__tag', 'open_time')
            
            if hour_queryset.exists():
                hour_data = []
                for candle in hour_queryset:
                    # timestamp를 날짜 형식으로 변환
                    try:
                        if candle.open_time > 1000000000000:  # milliseconds
                            date_time = pd.to_datetime(candle.open_time, unit='ms')
                        else:  # seconds
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
                        '방향': candle.direction if candle.direction else '',
                        '구조': candle.structure if candle.structure else '',
                        '소속_일일캔들_ID': candle.day_candle_stick.id,
                        '원본시간': candle.open_time
                    })
                
                # Hour DataFrame 생성 및 저장
                hour_df = pd.DataFrame(hour_data)
                hour_df.to_excel(writer, sheet_name='시간캔들데이터', index=False)
                print(f"✅ Hour Candle 데이터 {len(hour_df)}개 처리 완료")
                
                # 열 너비 조정
                worksheet = writer.sheets['시간캔들데이터']
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
            
            # === 요약 시트 생성 ===
            print("📋 요약 정보 생성 중...")
            summary_data = []
            
            # 전체 요약 정보
            if day_queryset.exists():
                day_coins = day_df['코인'].nunique()
                day_count = len(day_df)
                day_date_range = f"{day_df['날짜'].min()} ~ {day_df['날짜'].max()}"
                
                summary_data.append({
                    '데이터타입': '일일 캔들',
                    '총_레코드수': day_count,
                    '코인종류수': day_coins,
                    '데이터기간': day_date_range
                })
            
            if hour_queryset.exists():
                hour_coins = hour_df['코인'].nunique()
                hour_count = len(hour_df)
                hour_date_range = f"{hour_df['날짜'].min()} ~ {hour_df['날짜'].max()}"
                
                summary_data.append({
                    '데이터타입': '시간 캔들',
                    '총_레코드수': hour_count,
                    '코인종류수': hour_coins,
                    '데이터기간': hour_date_range
                })
            
            if summary_data:
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='데이터요약', index=False)
                
                # 요약 시트 열 너비 조정
                worksheet = writer.sheets['데이터요약']
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
        
        # 결과 출력
        print(f"\n🎉 성공! 통합 엑셀 파일을 생성했습니다: {filename}")
        
        if day_queryset.exists():
            day_coin_counts = day_df.groupby('코인').size()
            print(f"📅 일일 캔들 데이터 ({len(day_df)}개):")
            for coin, count in day_coin_counts.items():
                print(f"  - {coin}: {count}개")
        
        if hour_queryset.exists():
            hour_coin_counts = hour_df.groupby('코인').size()
            print(f"🕐 시간 캔들 데이터 ({len(hour_df)}개):")
            for coin, count in hour_coin_counts.items():
                print(f"  - {coin}: {count}개")
        
        print(f"\n💡 파일 위치: {os.path.abspath(filename)}")
        print(f"📊 엑셀 시트 구성:")
        print(f"  1. 일일캔들데이터 - Day_Candle_stick 데이터")
        print(f"  2. 시간캔들데이터 - Hour_Candle_stick 데이터")
        print(f"  3. 데이터요약 - 전체 데이터 요약")
        
        return filename
        
    except Exception as e:
        print(f"❌ 오류가 발생했습니다: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None

def export_hour_only():
    """Hour_Candle_stick 데이터만 빠르게 내보내기"""
    
    print("🕐 Hour Candle 데이터만 엑셀로 내보내는 중...")
    
    try:
        # Hour Candle 데이터 가져오기
        queryset = Hour_Candle_stick.objects.all().select_related('day_candle_stick__coin').order_by('day_candle_stick__coin__tag', 'open_time')
        
        if not queryset.exists():
            print("❌ 내보낼 Hour Candle 데이터가 없습니다.")
            return None
        
        # 데이터를 리스트로 변환
        data_list = []
        for candle in queryset:
            try:
                if candle.open_time > 1000000000000:  # milliseconds
                    date_time = pd.to_datetime(candle.open_time, unit='ms')
                else:  # seconds
                    date_time = pd.to_datetime(candle.open_time, unit='s')
                
                date_str = date_time.strftime('%Y-%m-%d')
                datetime_str = date_time.strftime('%Y-%m-%d %H:%M:%S')
            except:
                date_str = str(candle.open_time)
                datetime_str = str(candle.open_time)
            
            data_list.append({
                '코인': candle.day_candle_stick.coin.tag,
                '날짜': date_str,
                '시간': datetime_str,
                '시가': candle.open,
                '고가': candle.high,
                '저가': candle.low,
                '종가': candle.close,
                '거래량': candle.volume,
                '방향': candle.direction if candle.direction else '',
                '구조': candle.structure if candle.structure else '',
                '소속_일일캔들_ID': candle.day_candle_stick.id,
                '원본시간': candle.open_time
            })
        
        # DataFrame 생성
        df = pd.DataFrame(data_list)
        
        # 파일명 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Hour_Candle_Data_{timestamp}.xlsx"
        
        # 엑셀 파일로 저장
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='시간캔들데이터', index=False)
            
            # 열 너비 자동 조정
            worksheet = writer.sheets['시간캔들데이터']
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
        
        # 결과 출력
        print(f"✅ Hour Candle 엑셀 파일을 생성했습니다: {filename}")
        print(f"📈 총 {len(df)} 개의 데이터를 내보냈습니다.")
        
        # 코인별 데이터 개수
        coin_counts = df.groupby('코인').size()
        print(f"📊 코인별 데이터 개수:")
        for coin, count in coin_counts.items():
            print(f"  - {coin}: {count}개")
        
        print(f"📅 데이터 기간: {df['날짜'].min()} ~ {df['날짜'].max()}")
        print(f"\n💡 파일 위치: {os.path.abspath(filename)}")
        
        return filename
        
    except Exception as e:
        print(f"❌ 오류가 발생했습니다: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None

if __name__ == "__main__":
    print("=== 캔들스틱 데이터 내보내기 ===\n")
    print("1. 모든 데이터 (Day + Hour) - 권장")
    print("2. Hour Candle 데이터만")
    print()
    
    choice = input("선택하세요 (1 또는 2): ").strip()
    
    if choice == "1":
        export_all_candle_data()
    elif choice == "2":
        export_hour_only()
    else:
        print("기본값으로 모든 데이터를 내보냅니다...")
        export_all_candle_data()

