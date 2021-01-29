import json
import re
import requests
import time

def get_rom_by_id(id):
    ctx = requests.get(f'https://1link.club/m1.php?id={id}').content.decode("utf-8")
    url = re.findall(r'"(https?://cutdl.xyz/.*?)"', ctx)[0]

    r = requests.get(url)
    ctx = r.content.decode("utf-8")

    _csrfToken = re.findall(r'name="_csrfToken".*?value="(.*?)"', ctx)[0]
    ad_form_data = re.findall(r'name="ad_form_data".*?value="(.*?)"', ctx)[0]
    fields = re.findall(r'name="_Token\[fields\]".*?value="(.*?)"', ctx)[0]
    unlocked = re.findall(r'name="_Token\[unlocked\]".*?value="(.*?)"', ctx)[0]

    cookies = {
        '__cfduid': r.cookies['__cfduid'],
        'AppSession': r.cookies['AppSession'],
        'csrfToken': r.cookies['csrfToken'],
        'app_visitor': r.cookies['app_visitor'],
        'ab': '1',
    }

    time.sleep(4)

    ctx = requests.post('https://cutdl.xyz/links/go',
        data={
            '_method': 'POST',
            '_csrfToken': _csrfToken,
            'ad_form_data': ad_form_data,
            '_Token[fields]': fields,
            '_Token[unlocked]': unlocked,
        },
        cookies=cookies,
        headers={
            'DNT': '1',
            'Host': 'cutdl.xyz',
            'Origin': 'https://cutdl.xyz',
            'Referer': url,
            'Sec-GPC': '1',
            'TE': 'Trailers',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:84.0) Gecko/20100101 Firefox/85.0',
            'X-Requested-With': 'XMLHttpRequest',
        }
        ).content.decode("utf-8")

    return json.loads(ctx)['url']

def get_game_list():
    ctx = requests.get('https://nxbrew.com/list-of-games/').content.decode("utf-8")
    ctx = ctx[ctx.find('columns max-22-columns'):]
    return list(re.findall(r'<a href="(https://nxbrew.com/.*?)">', ctx))

if __name__ == '__main__':
    games = get_game_list()

    n = 0
    for game in games:
        ctx = requests.get(game).content.decode("utf-8")

        name = re.findall(r'<title>(.*?) \|.*?</title>', ctx)[0]

        dl_ctx = ctx[ctx.find('Download Links'):ctx.find('Please report the broken')]

        category = list(re.findall(r'has-medium-font-size"><strong>(.*?)</strong></p>', dl_ctx))

        n = n + 1
        print(f'[{n}/{len(games)}] {name} [ {game} ]')
        for x in range(len(category)):
            if x == len(category)-1:
                c = dl_ctx[dl_ctx.find(category[x]):-1]
            else:
                c = dl_ctx[dl_ctx.find(category[x]):dl_ctx.find(category[x+1])]

            link_id = list(re.findall(r'href="http://1link.club/(.*?)"', c))
            link = []
            for id in link_id:
                link.append(get_rom_by_id(id))

            print(f'    {category[x]}:')

            _1fichier = list(filter(lambda a: a.find('1fichier.com/') >= 0, link))
            _mega = list(filter(lambda a: a.find('mega.nz/') >= 0, link))
            _gd = list(filter(lambda a: a.find('drive.google.com/') >= 0, link))
            if len(_1fichier) > 0:
                for k in _1fichier:
                    print(f'        {k}:')
            elif len(_mega) > 0:
                for k in _mega:
                    print(f'        {k}:')
            elif len(_gd) > 0:
                for k in _gd:
                    print(f'        {k}:')

        print('#'*80, flush=True)
