from pathlib import Path
from yt_dlp import YoutubeDL

SOURCES = Path('sources.txt')
OUTPUT = Path('youtube.m3u')
POT_SCRIPT = str((Path('pot-provider/server/build/generate_once.js')).resolve())

lines = ['#EXTM3U']

opts = {
    'quiet': True,
    'no_warnings': True,
    'skip_download': True,
    'noplaylist': True,
    'extractor_args': {
        'youtube': {'player_client': ['mweb']},
        'youtubepot-bgutilscript': {'script_path': [POT_SCRIPT]},
    },
    'format': 'best[ext=mp4][acodec!=none][vcodec!=none]/best[acodec!=none][vcodec!=none]',
}

for raw in SOURCES.read_text(encoding='utf-8').splitlines():
    raw = raw.strip()
    if not raw or raw.startswith('#'):
        continue

    if '|' in raw:
        label, url = raw.split('|', 1)
        label, url = label.strip(), url.strip()
    else:
        label, url = '', raw

    try:
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)

        stream_url = info.get('url')
        if not stream_url:
            print(f'No direct stream URL: {url}')
            continue

        title = (label or info.get('title') or 'YouTube').replace('"', "'").replace('\n', ' ')
        thumb = (info.get('thumbnail') or '').replace('"', '%22')
        extinf = f'#EXTINF:-1 group-title="YouTube" tvg-name="{title}"'
        if thumb:
            extinf += f' tvg-logo="{thumb}"'
        extinf += f',{title}'

        lines.append(extinf)
        lines.append('#EXTVLCOPT:http-referrer=https://www.youtube.com/')
        lines.append('#EXTVLCOPT:http-user-agent=Mozilla/5.0')
        lines.append(stream_url)
        print(f'Added: {title}')
    except Exception as exc:
        print(f'Failed: {url} -> {exc}')

OUTPUT.write_text('\n'.join(lines) + '\n', encoding='utf-8')
print(f'Wrote {OUTPUT} with {max(0, len([x for x in lines if x.startswith("#EXTINF")]))} item(s)')
