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

REQ_INTERVAL = 3

def get_daily_trading_ym(conn, code, name, year, month):
    while True:
        time.sleep(REQ_INTERVAL)
        try:
            r = requests.get(f'https://www.twse.com.tw/en/exchangeReport/STOCK_DAY?response=json&date={year:0>4}{month:0>2}01&stockNo={code}')
        except:
            print(f'(X) {code} {name}: {year}-{month:0>2}')

        try:
            jv = json.loads(r.text)
            if 'fields' in jv:
                break
            if 'stat' in jv and jv['stat'] == 'No Data!':
                return []
            print(f'(X) {code} {name}: {year}-{month:0>2}')
            print(r.text)
        except:
            pass

    data = []

    f = jv['fields']
    for d in jv['data']:
        date, open, high, low, close, value, volume, transaction = (None, None, None, None, None, None, None, None)
        for i in range(len(f)):
            if f[i] == 'Date':
                date = '-'.join(d[i].split('/'))
            elif f[i] == 'Trade Volume':
                volume = int(d[i].replace(',', ''))
            elif f[i] == 'Trade Value':
                value = int(d[i].replace(',', ''))
            elif f[i] == 'Opening Price':
                open = decimal.Decimal(d[i].replace(',', '')) if d[i] != '--' else None
            elif f[i] == 'Highest Price':
                high = decimal.Decimal(d[i].replace(',', '')) if d[i] != '--' else None
            elif f[i] == 'Lowest Price':
                low = decimal.Decimal(d[i].replace(',', '')) if d[i] != '--' else None
            elif f[i] == 'Closing Price':
                close = decimal.Decimal(d[i].replace(',', '')) if d[i] != '--' else None
            elif f[i] == 'Transaction':
                transaction = int(d[i].replace(',', ''))
            elif not f[i] in ['Change']:
                raise Exception(f'unknown field: {f[i]}, {code}: {year}-{month:0>2}')
        data.append((code, date, open, high, low, close, value, volume, transaction))

    return data

def crawl_daily_trading(conn, code, name, start_date):
    with conn.cursor() as cursor:
        cursor.execute(f'''
            SELECT date FROM "{TAB}"
            WHERE code=%s AND value IS NOT NULL
            ORDER BY date DESC LIMIT 1
        ''', (code,))
        row = cursor.fetchone()
        date = row[0] + datetime.timedelta(days=1) if row else datetime.date(start_date.year, start_date.month, 1)

    with conn.cursor() as cursor:
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
        ''', (('上市', '上市ETF'),))

        from_date = datetime.date(2010, 1, 4)
        for code, name, date in cursor.fetchall():
            if date < from_date:
                date = from_date
            crawl_daily_trading(conn, code, name, date)

def crawl_single(conn, code):
    with conn.cursor() as cursor:
        cursor.execute(f'''
            SELECT name,date FROM "TWN:stock"
            WHERE code = %s
        ''', (code,))

        from_date = datetime.date(2010, 1, 4)
        name, date = cursor.fetchone()
        if date < from_date:
            date = from_date
        crawl_daily_trading(conn, code, name, date)

if __name__ == '__main__':
    with psycopg2.connect(sys.argv[1]) as conn:
        if len(sys.argv) == 2:
            crawl(conn)
        else:
            crawl_single(conn, sys.argv[2])
