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

def get_index_tpex_ym(conn, year, month):
    while True:
        time.sleep(REQ_INTERVAL)
        try:
            r = requests.get(f'https://www.tpex.org.tw/web/stock/iNdex_info/inxh/Inx_result.php?l=en-us&d={year:0>4}/{month:0>2}')
        except:
            print(f'(X) [TPEX] IX0043: {year}-{month:0>2}')

        try:
            jv = json.loads(r.text)
            if 'aaData' in jv:
                break
            print(f'(X) [TPEX] IX0043: {year}-{month:0>2}')
            print(r.text)
        except:
            pass

    data = []

    for d in jv['aaData']:
        date, open, high, low, close = (
            '-'.join(d[0].split('/')),
            decimal.Decimal(d[1].replace(',', '')),
            decimal.Decimal(d[2].replace(',', '')),
            decimal.Decimal(d[3].replace(',', '')),
            decimal.Decimal(d[4].replace(',', ''))
        )
        data.append(('IX0043', date, open, high, low, close))

    return data

def crawl_index_tpex(conn):
    with conn.cursor() as cursor:
        cursor.execute(f'''
            SELECT date FROM "{TAB}"
            WHERE code=%s AND open IS NULL AND date >= %s
            ORDER BY date LIMIT 1
        ''', ('IX0043', datetime.date(1999, 9, 1)))
        row = cursor.fetchone()
        if not row:
            return
        date = row[0]

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

        d = get_index_tpex_ym(conn, year, month)
        print(f'(O) [TPEX] IX0043: {year}-{month:0>2}: {len(d)}')

        with conn.cursor() as cursor:
            cursor.executemany(f'''
                INSERT INTO "{TAB}" (code,date,open,high,low,close)
                VALUES (%s,%s,%s,%s,%s,%s)
                ON CONFLICT(code,date) DO UPDATE SET
                    open  = excluded.open,
                    high  = excluded.high,
                    low   = excluded.low,
                    close = excluded.close
                ''', d)
            conn.commit()

        if year == now.year and month == now.month:
            break
        month = month + 1
        if month > 12:
            year, month = (year + 1, 1)
        date = datetime.date(year, month, 1)

def crawl(conn):
    crawl_index_tpex(conn)

if __name__ == '__main__':
    with psycopg2.connect(sys.argv[1]) as conn:
        crawl(conn)
