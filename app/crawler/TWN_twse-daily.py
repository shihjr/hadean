import datetime
import json
import psycopg2
import re
import requests
import time
import sys

TAB = 'TWN:stock:daily'

REQ_INTERVAL = 3

def get_daily_trading_ym(conn, year, month):
    while True:
        time.sleep(REQ_INTERVAL)
        try:
            r = requests.get(f'https://www.twse.com.tw/en/exchangeReport/FMTQIK?response=json&date={year:0>4}{month:0>2}01')
        except:
            print(f'(X) IX0001: {year}-{month:0>2}')

        try:
            jv = json.loads(r.text)
            if 'fields' in jv:
                break
            if 'stat' in jv and jv['stat'] == 'NO Date!':
                return []
            print(f'(X) IX0001: {year}-{month:0>2}')
            print(r.text)
        except:
            pass

    data = []

    f = jv['fields']
    for d in jv['data']:
        date, value, volume, transaction = (None, None, None, None)
        for i in range(len(f)):
            if f[i] == 'Date':
                date = '-'.join(d[i].split('/'))
            elif f[i] == 'Trade Volume':
                volume = int(d[i].replace(',', ''))
            elif f[i] == 'Trade Value':
                value = int(d[i].replace(',', ''))
            elif f[i] == 'Transaction':
                transaction = int(d[i].replace(',', ''))
            elif not f[i] in ['TAIEX', 'Change']:
                raise Exception(f'unknown field: {f[i]}')
        data.append(('IX0001', date, value, volume, transaction))

    return data

def crawl_daily_trading(conn):
    with conn.cursor() as cursor:
        cursor.execute(f'''
            SELECT date FROM "{TAB}"
            WHERE code=%s AND value IS NOT NULL
            ORDER BY date DESC LIMIT 1
        ''', ('IX0001',))
        row = cursor.fetchone()
        date = row[0] + datetime.timedelta(days=1) if row else datetime.date(1990, 1, 1)

    now = datetime.date.today()
    while True:
        if date > now:
            break
        year, month = (date.year, date.month)

        d = get_daily_trading_ym(conn, year, month)
        print(f'(O) IX0001: {year}-{month:0>2}: {len(d)}')

        with conn.cursor() as cursor:
            cursor.executemany(f'''
                INSERT INTO "{TAB}" (code,date,value,volume,transaction)
                VALUES (%s,%s,%s,%s,%s)
                ON CONFLICT(code,date) DO UPDATE SET
                    value       = excluded.value,
                    volume      = excluded.volume,
                    transaction = excluded.transaction
                ''', d)
            conn.commit()

        if year == now.year and month == now.month:
            break
        month = month + 1
        if month > 12:
            year, month = (year + 1, 1)
        date = datetime.date(year, month, 1)

def crawl(conn):
    with conn.cursor() as cursor:
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS "{TAB}" (
                code        text,    -- 證券代號
                date        date,    -- 日期
                open        numeric, -- 開盤價
                high        numeric, -- 最高價
                low         numeric, -- 最低價
                close       numeric, -- 收盤價
                value       bigint,  -- 成交金額
                volume      bigint,  -- 成交股數
                transaction bigint,  -- 成交筆數
                PRIMARY KEY(code,date)
        )''')
        conn.commit()

    crawl_daily_trading(conn)

if __name__ == '__main__':
    with psycopg2.connect(sys.argv[1]) as conn:
        crawl(conn)
