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

def get_index_taiex_ym(conn, year, month):
    while True:
        time.sleep(REQ_INTERVAL)
        try:
            r = requests.get(f'https://www.twse.com.tw/en/indicesReport/MI_5MINS_HIST?response=json&date={year:0>4}{month:0>2}01')
        except:
            print(f'(X) [TAIEX] IX0001: {year}-{month:0>2}')

        try:
            jv = json.loads(r.text)
            if 'fields' in jv:
                break
            if 'stat' in jv and jv['stat'] == 'NO Date!':
                return []
            print(f'(X) [TAIEX] IX0001: {year}-{month:0>2}')
            print(r.text)
        except:
            pass

    data = []

    f = jv['fields']
    for d in jv['data']:
        date, open, high, low, close = (None, None, None, None, None)
        for i in range(len(f)):
            if f[i] == 'Date':
                date = '-'.join(d[i].split('/'))
            elif f[i] == 'Opening Index':
                open = decimal.Decimal(d[i].replace(',', ''))
            elif f[i] == 'Highest Index':
                high = decimal.Decimal(d[i].replace(',', ''))
            elif f[i] == 'Lowest Index':
                low = decimal.Decimal(d[i].replace(',', ''))
            elif f[i] == 'Closing Index':
                close = decimal.Decimal(d[i].replace(',', ''))
            elif not f[i] in []:
                raise Exception(f'unknown field: {f[i]}')
        data.append(('IX0001', date, open, high, low, close))

    return data

def crawl_index_taiex(conn):
    with conn.cursor() as cursor:
        cursor.execute(f'''
            SELECT date FROM "{TAB}"
            WHERE code=%s AND open IS NULL AND date >= %s
            ORDER BY date LIMIT 1
        ''', ('IX0001', datetime.date(1999, 1, 5)))
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

        d = get_index_taiex_ym(conn, year, month)
        print(f'(O) [TAIEX] IX0001: {year}-{month:0>2}: {len(d)}')

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
    crawl_index_taiex(conn)

if __name__ == '__main__':
    with psycopg2.connect(sys.argv[1]) as conn:
        crawl(conn)
