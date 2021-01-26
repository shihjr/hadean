import datetime
import psycopg2
import re
import requests
import time
import sys

FAIL_INTERVAL = 5

def get_ym_param(prefix, year, month, dropdownlist, hidden, append):
    param = {
        f'{prefix}Control_history{append}$DropDownList1': dropdownlist,
        f'{prefix}Control_history{append}$chk': 'radYM',
        f'{prefix}Control_history{append}$dropYear': str(year-1911),
        f'{prefix}Control_history{append}$dropMonth': str(month),
        f'{prefix}Control_history{append}$btnSubmit': '查詢',
    }
    param.update(hidden)
    return param


def post(url, param):
    while True:
        try:
            r = requests.post(url, param)
            break
        except:
            time.sleep(FAIL_INTERVAL)
    return r


def get_ym_superlotto638(year, month, hidden, url):
    r = post(url, get_ym_param('SuperLotto638', year, month, '1', hidden, '1'))

    d = []
    for k, v in re.findall(r'SuperLotto638Control_history1_dlQuery_DrawTerm_(.*?)">(.*?)<', r.text):
        date = re.findall(r'SuperLotto638Control_history1_dlQuery_Date_' + re.escape(str(k)) + r'">(.*?)<', r.text)[0].split('/')
        date = f'{int(date[0])+1911}-{date[1]}-{date[2]}'
        no = [int(i) for i in re.findall(r'SuperLotto638Control_history1_dlQuery_SNo.*?_' + re.escape(str(k)) + r'">(.*?)<', r.text)]

        d.append((v, date, *no))
    return d

def get_ym_lotto649(year, month, hidden, url):
    r = post(url, get_ym_param('Lotto649', year, month, '2', hidden, ''))

    d = []
    for k, v in re.findall(r'Lotto649Control_history_dlQuery_L649_DrawTerm_(.*?)">(.*?)<', r.text):
        date = re.findall(r'Lotto649Control_history_dlQuery_L649_DDate_' + re.escape(str(k)) + r'">(.*?)<', r.text)[0].split('/')
        date = f'{int(date[0])+1911}-{date[1]}-{date[2]}'
        no = [int(i) for i in re.findall(r'Lotto649Control_history_dlQuery_SNo.*?_' + re.escape(str(k)) + r'">(.*?)<', r.text)]

        d.append((v, date, *no))
    return d

def get_ym_dailycash(year, month, hidden, url):
    r = post(url, get_ym_param('D539', year, month, '5', hidden, '1'))

    d = []
    for k, v in re.findall(r'D539Control_history1_dlQuery_D539_DrawTerm_(.*?)">(.*?)<', r.text):
        date = re.findall(r'D539Control_history1_dlQuery_D539_DDate_' + re.escape(str(k)) + r'">(.*?)<', r.text)[0].split('/')
        date = f'{int(date[0])+1911}-{date[1]}-{date[2]}'
        no = [int(i) for i in re.findall(r'D539Control_history1_dlQuery_SNo.*?_' + re.escape(str(k)) + r'">(.*?)<', r.text)]

        d.append((v, date, *no))
    return d

def get_ym_lotto1224(year, month, hidden, url):
    r = post(url, get_ym_param('Lotto1224', year, month, '12', hidden, ''))

    d = []
    for k, v in re.findall(r'Lotto1224Control_history_dlQuery_Lotto1224_DrawTerm_(.*?)">(.*?)<', r.text):
        date = re.findall(r'Lotto1224Control_history_dlQuery_Lotto1224_DDate_' + re.escape(str(k)) + r'">(.*?)<', r.text)[0].split('/')
        date = f'{int(date[0])+1911}-{date[1]}-{date[2]}'
        no = [int(i) for i in re.findall(r'Lotto1224Control_history_dlQuery_SNo.*?_' + re.escape(str(k)) + r'">(.*?)<', r.text)]

        d.append((v, date, *no))
    return d

def get_ym_d3(year, month, hidden, url):
    r = post(url, get_ym_param('L3D', year, month, '6', hidden, '1'))

    d = []
    for v, date, no_ctx in re.findall(r'</tr><tr><td rowspan=2 class=td_w>(.*?)</td>.*?>開獎<br />(.*?)</p>(.*)', r.text):
        date = date.split('/')
        date = f'{int(date[0])+1911}-{date[1]}-{date[2]}'
        no = [int(i) for i in re.findall(r"font_black14b_center'>(.*?)<", no_ctx)]

        d.append((v, date, *no))
    return d

def get_ym_d4(year, month, hidden, url):
    r = post(url, get_ym_param('L4D', year, month, '7', hidden, '1'))

    d = []
    for v, date, no_ctx in re.findall(r'<td rowspan=2 class=td_w>(.*?)</td>.*?>開獎<br />(.*?)</td>(.*)', r.text):
        date = date.split('/')
        date = f'{int(date[0])+1911}-{date[1]}-{date[2]}'
        no = [int(i) for i in re.findall(r"font_black14b_center>(.*?)<", no_ctx)]

        d.append((v, date, *no))
    return d


def get_hidden(url):
    d = { '__EVENTTARGET': '', '__EVENTARGUMENT': '', '__LASTFOCUS': '' }
    while True:
        try:
            r = requests.get(url)
            break
        except:
            time.sleep(FAIL_INTERVAL)
    for k, v in re.findall(r'type="hidden".*?name="(.*?)".*?value="(.*?)"', r.text):
        d[k] = v
    return d

def get_lotto(lastdate, start_year, start_month, url, get_ym):
    while True:
        try:
            hidden = get_hidden(url)
            break
        except:
            time.sleep(FAIL_INTERVAL)

    year, month = (lastdate.year, lastdate.month) if lastdate else (start_year, start_month)

    now = datetime.date.today()

    data = []
    while True:
        d = get_ym(year, month, hidden, url)
        data = data + d

        if now.year == year and now.month == month:
            break

        month = month + 1
        if month > 12:
            year, month = (year + 1, 1)
    return data


TAB_PREFIX = 'TWN:lottery:'

def last(tab):
    with conn.cursor() as cursor:
        cursor.execute(f'SELECT (date) FROM "{TAB_PREFIX}{tab}" ORDER BY date DESC LIMIT 1')
        row = cursor.fetchone()
        return row[0] if row else None

def count(conn, tab):
    with conn.cursor() as cursor:
        cursor.execute(f'SELECT COUNT(drawing) FROM "{TAB_PREFIX}{tab}"')
        row = cursor.fetchone()
        return row[0] if row else 0

def crawl(conn):
    lotto = [
        ('lotto638', 6+1, (2014, 1, 'https://www.taiwanlottery.com.tw/lotto/superlotto638/history.aspx', get_ym_superlotto638)),
        ('lotto649', 6+1, (2014, 1, 'https://www.taiwanlottery.com.tw/lotto/Lotto649/history.aspx', get_ym_lotto649)),
        ('lotto539', 5, (2014, 1, 'https://www.taiwanlottery.com.tw/Lotto/Dailycash/history.aspx', get_ym_dailycash)),
        ('lotto1224', 12, (2018, 4, 'https://www.taiwanlottery.com.tw/Lotto/Lotto1224/history.aspx', get_ym_lotto1224)),
        ('d3', 3, (2014, 1, 'https://www.taiwanlottery.com.tw/Lotto/3D/history.aspx', get_ym_d3)),
        ('d4', 4, (2014, 1, 'https://www.taiwanlottery.com.tw/Lotto/4D/history.aspx', get_ym_d4)),
    ]
    for tab, num, args in lotto:
        with conn.cursor() as cursor:
            s = f'''
                CREATE TABLE IF NOT EXISTS "{TAB_PREFIX}{tab}" (
                    drawing integer,       -- 期數
                    date    date NOT NULL, -- 日期
                                           -- 獎號
                    {''.join([f'no{i+1} integer NOT NULL,' for i in range(num)])}
                    PRIMARY KEY(drawing))
            '''
            cursor.execute(s)

            c0 = count(conn, tab)

            data = get_lotto(last(tab), *args)
            cursor.executemany(f'''
                INSERT INTO "{TAB_PREFIX}{tab}"
                (drawing,date{''.join([f',no{i+1}' for i in range(num)])})
                VALUES (%s,%s{',%s'*num})
                ON CONFLICT (drawing) DO NOTHING
            ''', data)
            conn.commit()

            c1 = count(conn, tab)
            print(f'{tab:<10}: {c1-c0}/{c1}')

if __name__ == '__main__':
    with psycopg2.connect(sys.argv[1]) as conn:
        crawl(conn)
