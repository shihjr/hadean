import datetime
import psycopg2
import re
import requests
import time
import sys

TAB = 'TWN:stock'

REQ_INTERVAL = 3

def get_isin(ctx, mode, start_tag, end_tag):
    r = ctx
    while True:
        time.sleep(REQ_INTERVAL)
        try:
            r = requests.get(f'https://isin.twse.com.tw/isin/C_public.jsp?strMode={mode}')
            break
        except:
            print(f'failed: mode={mode}')

    start = r.text.find(start_tag)
    end = r.text.find(end_tag, start)

    d = re.findall(r'</tr><tr><td bgcolor=#FAFAD2>(.*?)\u3000(.*?)</td>.*?#FAFAD2>(\d{4}/\d{2}/\d{2})', r.text[start:end])
    return (r, map(lambda x: (x[0].strip(), x[1].strip(), '-'.join(x[2].split('/'))), d))

def count(conn, market):
    with conn.cursor() as cursor:
        cursor.execute(f'SELECT COUNT(code) FROM "{TAB}" WHERE market=%s', (market,))
        row = cursor.fetchone()
        return row[0] if row else 0

def crawl_isin(conn):
    ctx_cache = {}
    isin_list = [
        ('公開發行', (1, '備註', '</tr></table>')),
        ('上市', (2, '股票', '上市認購')),
        ('上市ETF', (2, 'ETF', 'ETN')),
        ('上櫃', (4, '股票', '特別股')),
        ('上櫃ETF', (4, 'ETF', '股票')),
        ('興櫃', (5, '股票', '</tr></table>')),
        ('創櫃板', (8, '普通股', '</tr></table>')),
        ('指數', (11, '備註', '</tr></table>')),
    ]
    for market, args in isin_list:
        c0 = count(conn, market)

        if args[0] in ctx_cache:
            ctx, d = get_isin(ctx_cache[args[0]], *args)
        else:
            ctx, d = get_isin(None, *args)
        ctx_cache[args[0]] = ctx

        d = map(lambda x: (*x, market), d)
        with conn.cursor() as cursor:
            cursor.execute(f'DELETE FROM "{TAB}" WHERE market=%s', (market,))
            cursor.executemany(f'''
                INSERT INTO "{TAB}" (code,name,date,market)
                VALUES (%s,%s,%s,%s)
                ON CONFLICT (code) DO UPDATE SET
                    code   = EXCLUDED.code,
                    name   = EXCLUDED.name,
                    date   = EXCLUDED.date,
                    market = EXCLUDED.market
                ''', d)
            conn.commit()

        c1 = count(conn, market)
        print(f'{market}: {c1-c0}/{c1}')

def crawl(conn):
    with conn.cursor() as cursor:
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS "{TAB}" (
                code   text,          -- 證券代號
                name   text NOT NULL, -- 名稱
                date   date NOT NULL, -- 上市日
                market text NOT NULL, -- 市場別
                PRIMARY KEY(code)
        )''')
        conn.commit()

    crawl_isin(conn)

if __name__ == '__main__':
    with psycopg2.connect(sys.argv[1]) as conn:
        crawl(conn)
