import datetime
import json
import psycopg2
import re
import requests
import time
import sys

TAB = 'TWN:stock:daily'

REQ_INTERVAL = 0

def get_daily_trading_ym(conn, year, month):
    while True:
        time.sleep(REQ_INTERVAL)
        try:
            r = requests.get(f'https://www.tpex.org.tw/web/stock/aftertrading/daily_trading_index/st41_result.php?l=en-us&d={year:0>4}/{month:0>2}')
        except:
            print(f'(X) IX0043: {year}-{month:0>2}')

        try:
            jv = json.loads(r.text)
            if 'aaData' in jv:
                break
            print(f'(X) IX0043: {year}-{month:0>2}')
            print(r.text)
        except:
            pass

    data = []

    for d in jv['aaData']:
        date, value, volume, transaction = (
            '-'.join(d[0].split('/')),
            int(d[2].replace(',', '')) * 1000,
            int(d[1].replace(',', '')) * 1000,
            int(d[3].replace(',', ''))
        )
        data.append(('IX0043', date, value, volume, transaction))

    return data

def crawl_daily_trading(conn):
    with conn.cursor() as cursor:
        cursor.execute(f'''
            SELECT date FROM "{TAB}"
            WHERE code=%s AND value IS NOT NULL
            ORDER BY date DESC LIMIT 1
        ''', ('IX0043',))
        row = cursor.fetchone()
        date = row[0] + datetime.timedelta(days=1) if row else datetime.date(1999, 1, 1)

    now = datetime.date.today()
    while True:
        if date > now:
            break
        year, month = (date.year, date.month)

        d = get_daily_trading_ym(conn, year, month)
        print(f'(O) IX0043: {year}-{month:0>2}: {len(d)}')

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
    crawl_daily_trading(conn)

if __name__ == '__main__':
    with psycopg2.connect(sys.argv[1]) as conn:
        crawl(conn)
