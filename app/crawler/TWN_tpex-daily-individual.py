import datetime
import decimal
import json
import psycopg2
import re
import requests
import time
import sys

TAB_PREFIX = 'TWN:stock:'
TAB        = f'{TAB_PREFIX}daily'

REQ_INTERVAL = 0

def get_daily_trading_ym(conn, code, name, year, month):
    while True:
        time.sleep(REQ_INTERVAL)
        try:
            r = requests.get(f'https://www.tpex.org.tw/web/stock/aftertrading/daily_trading_info/st43_result.php?l=en-us&d={year:0>4}/{month:0>2}/01&stkno={code}')
        except:
            print(f'(X) {code} {name}: {year}-{month:0>2}')

        try:
            jv = json.loads(r.text)
            if 'aaData' in jv:
                break
            print(f'(X) {code} {name}: {year}-{month:0>2}')
            print(r.text)
        except:
            pass

    data = []

    for d in jv['aaData']:
        date, open, high, low, close, value, volume, transaction = (
            '-'.join(d[0].strip('＊').split('/')),
            decimal.Decimal(d[3].replace(',', '')) if d[3] != '--' else None,
            decimal.Decimal(d[4].replace(',', '')) if d[4] != '--' else None,
            decimal.Decimal(d[5].replace(',', '')) if d[5] != '--' else None,
            decimal.Decimal(d[6].replace(',', '')) if d[6] != '--' else None,
            int(d[2].replace(',', '')) * 1000,
            int(d[1].replace(',', '')) * 1000,
            int(d[8].replace(',', ''))
        )
        data.append((code, date, open, high, low, close, value, volume, transaction))

    return data

def crawl_daily_trading(conn, code, name, start_date, end_date=None):
    if end_date:
        date = start_date
    else:
        with conn.cursor() as cursor:
            cursor.execute(f'''
                SELECT date FROM "{TAB}"
                WHERE code=%s AND value IS NOT NULL
                ORDER BY date DESC LIMIT 1
            ''', (code,))
            row = cursor.fetchone()
            date = row[0] + datetime.timedelta(days=1) if row else datetime.date(start_date.year, start_date.month, 1)

    with conn.cursor() as cursor:
        if end_date:
            now = end_date
        else:
            cursor.execute(f'''
                SELECT date FROM "{TAB}"
                WHERE code=%s AND value IS NOT NULL
                ORDER BY date DESC LIMIT 1
            ''', ('IX0001',))
            now = cursor.fetchone()[0]

    while True:
        if date > now:
            break
        year, month = (date.year, date.month)

        d = get_daily_trading_ym(conn, code, name, year, month)
        print(f'(O) {code} {name}: {year}-{month:0>2}: {len(d)}')

        with conn.cursor() as cursor:
            cursor.executemany(f'''
                INSERT INTO "{TAB}" (code,date,open,high,low,close,value,volume,transaction)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT(code,date) DO UPDATE SET
                    open        = excluded.open,
                    high        = excluded.high,
                    low         = excluded.low,
                    close       = excluded.close,
                    value       = excluded.value,
                    volume      = excluded.volume,
                    transaction = excluded.transaction
                ''', d)
            conn.commit()

        month = month + 1
        if month > 12:
            year, month = (year + 1, 1)
        date = datetime.date(year, month, 1)

def crawl(conn):
    with conn.cursor() as cursor:
        cursor.execute(f'''
            SELECT code,name,date FROM "TWN:stock"
            WHERE market IN %s
            ORDER BY code
        ''', (('上櫃', '上櫃ETF'),))

        from_date = datetime.date(1994, 1, 1)
        for code, name, date in cursor.fetchall():
            if date < from_date:
                date = from_date
            crawl_daily_trading(conn, code, name, date)

def crawl_ex_otc(conn):
    from_date = datetime.date(1994, 1, 1)
    with conn.cursor() as cursor:
        cursor.execute(f'''
            SELECT code,name,date FROM "TWN:stock"
            WHERE market IN %s
            ORDER BY code
        ''', (('上市',),))

        for code, name, date in cursor.fetchall():
            crawl_daily_trading(conn, code, name, from_date, end_date=date)

def crawl_single(conn, code):
    with conn.cursor() as cursor:
        cursor.execute(f'''
            SELECT name,date FROM "TWN:stock"
            WHERE code = %s
        ''', (code,))

        from_date = datetime.date(1994, 1, 1)
        name, date = cursor.fetchone()
        if date < from_date:
            date = from_date
        crawl_daily_trading(conn, code, name, date)

if __name__ == '__main__':
    with psycopg2.connect(sys.argv[1]) as conn:
        if len(sys.argv) == 2:
            crawl(conn)
        else:
            if sys.argv[2] == 'ex-otc':
                crawl_ex_otc(conn)
            else:
                crawl_single(conn, sys.argv[2])
