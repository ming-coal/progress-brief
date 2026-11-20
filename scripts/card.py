#!/usr/bin/env python3
"""Render a one-page status card (1080x1350 PNG) from a small JSON.

Usage:
  python3 card.py data.json [--html out.html] [--png out.png]

JSON:
  {
    "title": "EP.002 · 一个人把产品做到上线",
    "kicker": "VIDEO PRODUCTION",
    "status": "制作中 · 5/7 镜头",
    "stats": [{"k": "镜头", "v": "5 / 7"}, {"k": "规格", "v": "1080×1920"}],
    "done": ["文档", "GitHub", "产品录屏"],
    "next": ["九步地图", "小结", "口播"],
    "foot": "episodes/002-invoice2sheet"
  }
"""

import json
import os
import shutil
import subprocess
import sys

# 按平台找浏览器：Chrome / Chromium / Edge / Brave，找不到就只出 HTML
CHROME_NAMES = [
    'google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser',
    'microsoft-edge', 'microsoft-edge-stable', 'brave-browser', 'chrome',
]
CHROME_PATHS = {
    'darwin': [
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        '/Applications/Chromium.app/Contents/MacOS/Chromium',
        '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
        '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser',
    ],
    'win32': [
        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
        r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
        r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
    ],
    'linux': [
        '/usr/bin/google-chrome', '/usr/bin/google-chrome-stable',
        '/usr/bin/chromium', '/usr/bin/chromium-browser',
        '/snap/bin/chromium', '/usr/bin/microsoft-edge',
    ],
}


def find_chrome():
    env = os.environ.get('PROGRESS_BRIEF_CHROME')
    if env and os.path.exists(env):
        return env
    for p in (CHROME_PATHS.get(sys.platform) or CHROME_PATHS.get('linux') or []):
        if os.path.exists(p):
            return p
    for name in CHROME_NAMES:
        p = shutil.which(name)
        if p:
            return p
    return ''

HTML = """<!doctype html><html><head><meta charset="utf-8"><style>
*{box-sizing:border-box;margin:0;padding:0}
body{width:1080px;height:1350px;background:#141517;color:#F2F2EF;
  font-family:"PingFang SC","Helvetica Neue",sans-serif;position:relative;overflow:hidden}
.grid{position:absolute;inset:0;background-image:
  linear-gradient(rgba(155,229,100,.09) 1px,transparent 1px),
  linear-gradient(90deg,rgba(155,229,100,.09) 1px,transparent 1px);
  background-size:54px 54px}
.glow{position:absolute;inset:0;background:radial-gradient(60% 40% at 30% 4%,rgba(124,255,79,.16),transparent 70%)}
.wrap{position:relative;padding:110px 96px}
.kicker{font:500 20px/1 "SF Mono",Menlo,monospace;letter-spacing:.22em;color:rgba(242,242,239,.42)}
h1{font-size:74px;line-height:1.12;letter-spacing:-.03em;font-weight:900;margin-top:34px}
h1 em{font-style:normal;color:#7CFF4F}
.status{display:inline-block;margin-top:30px;font:500 22px/1 "SF Mono",Menlo,monospace;
  color:#7CFF4F;border:2px solid rgba(124,255,79,.45);border-radius:999px;padding:12px 22px}
.stats{display:flex;gap:56px;margin-top:64px;border-top:1px solid rgba(242,242,239,.14);padding-top:36px}
.stat .k{font:400 16px/1 "SF Mono",Menlo,monospace;letter-spacing:.18em;color:rgba(242,242,239,.38)}
.stat .v{font-size:44px;font-weight:800;margin-top:14px;letter-spacing:-.02em}
.cols{display:flex;gap:64px;margin-top:60px}
.col{flex:1}
.col .h{font:400 16px/1 "SF Mono",Menlo,monospace;letter-spacing:.18em;color:rgba(242,242,239,.38);margin-bottom:20px}
.item{display:flex;align-items:center;gap:14px;padding:13px 0;border-bottom:1px solid rgba(242,242,239,.1);font-size:26px}
.dot{width:10px;height:10px;border-radius:5px;background:#7CFF4F;flex:none}
.dot.off{background:rgba(242,242,239,.22)}
.foot{position:absolute;left:96px;bottom:72px;font:400 18px/1 "SF Mono",Menlo,monospace;
  letter-spacing:.12em;color:rgba(242,242,239,.38)}
.mark{position:absolute;right:96px;bottom:64px;font:800 30px/1 "SF Mono",Menlo,monospace;
  color:#7CFF4F;border:4px solid rgba(124,255,79,.5);padding:10px 20px;border-radius:6px;transform:rotate(-6deg)}
</style></head><body>
<div class="grid"></div><div class="glow"></div>
<div class="wrap">
  <div class="kicker">__KICKER__</div>
  <h1 style="font-size:__FS__px">__TITLE__</h1>
  __STATUS__
  __STATS__
  <div class="cols">
    <div class="col"><div class="h">DONE</div>__DONE__</div>
    <div class="col"><div class="h">NEXT</div>__NEXT__</div>
  </div>
</div>
<div class="foot">__FOOT__</div>
<div class="mark">__MARK__</div>
</body></html>"""


def esc(s):
    return (str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


def rows(items, on=True):
    cls = 'dot' if on else 'dot off'
    return ''.join(f'<div class="item"><span class="{cls}"></span>{esc(i)}</div>' for i in items)


def build(data):
    stats = ''.join(
        f'<div class="stat"><div class="k">{esc(s.get("k", ""))}</div>'
        f'<div class="v">{esc(s.get("v", ""))}</div></div>'
        for s in data.get('stats', [])
    )
    stats = f'<div class="stats">{stats}</div>' if stats else ''
    status = esc(data.get('status', ''))
    status = f'<div class="status">{status}</div>' if status else ''
    title = esc(data.get('title', ''))
    # 按字宽估算自动缩字号（中文 1em / 英文 0.55em），避免卡片里折行
    raw = data.get('title', '')
    w = sum(1.0 if ord(c) > 0x2E80 else 0.55 for c in raw)
    fs = max(36, min(74, int(860 / max(w, 1))))
    for word in data.get('highlight', []):
        title = title.replace(esc(word), f'<em>{esc(word)}</em>', 1)
    return (HTML
            .replace('__KICKER__', esc(data.get('kicker', 'PROJECT STATUS')))
            .replace('__TITLE__', title)
            .replace('__FS__', str(fs))
            .replace('__STATUS__', status)
            .replace('__STATS__', stats)
            .replace('__DONE__', rows(data.get('done', []), True))
            .replace('__NEXT__', rows(data.get('next', []), False))
            .replace('__FOOT__', esc(data.get('foot', '')))
            .replace('__MARK__', esc(data.get('mark', 'WIP'))))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    src = sys.argv[1]
    try:
        with open(src) as fh:
            data = json.load(fh)
    except FileNotFoundError:
        sys.exit(f'找不到 {src}')
    except ValueError as e:
        sys.exit(f'{src} 不是合法 JSON：{e}')
    html = build(data)
    html_path = src.rsplit('.', 1)[0] + '.html'
    png_path = src.rsplit('.', 1)[0] + '.png'
    if '--html' in sys.argv:
        html_path = sys.argv[sys.argv.index('--html') + 1]
    if '--png' in sys.argv:
        png_path = sys.argv[sys.argv.index('--png') + 1]
    open(html_path, 'w').write(html)
    print('html', html_path)

    chrome = find_chrome()
    if chrome:
        subprocess.run([
            chrome, '--headless=new', '--disable-gpu', '--hide-scrollbars',
            '--force-device-scale-factor=1', '--window-size=1080,1350',
            f'--screenshot={png_path}', 'file://' + os.path.abspath(html_path),
        ], capture_output=True)
        if os.path.exists(png_path):
            print('png ', png_path)
        else:
            print('screenshot failed, open the html manually:', html_path)
    else:
        print('no chrome/chromium/edge found, open the html manually:', html_path)
        print('tip: PROGRESS_BRIEF_CHROME=/path/to/chrome python3 card.py data.json')


if __name__ == '__main__':
    main()
