from pathlib import Path
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

CHANNEL_ID = "UC8vdjzu_0QMQlG9qNT5D_AQ"
CHANNEL_NAME = "إذاعة مختلف"
OUTPUT = Path("mukhtalif.m3u")
FEED = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
STREAM_BASE = "https://yewtu.be/latest_version"
MAX_ITEMS = 15


def clean(text: str) -> str:
    return " ".join((text or "").replace('"', "'").split())


req = Request(FEED, headers={"User-Agent": "Mozilla/5.0"})
with urlopen(req, timeout=30) as response:
    xml = response.read()

root = ET.fromstring(xml)
ns = {
    "atom": "http://www.w3.org/2005/Atom",
    "yt": "http://www.youtube.com/xml/schemas/2015",
}

lines = ["#EXTM3U"]
count = 0
for entry in root.findall("atom:entry", ns)[:MAX_ITEMS]:
    video_id = entry.findtext("yt:videoId", default="", namespaces=ns).strip()
    title = clean(entry.findtext("atom:title", default="YouTube", namespaces=ns))
    if not video_id:
        continue

    thumb = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
    stream = f"{STREAM_BASE}?id={video_id}&itag=18&local=true"
    lines.append(
        f'#EXTINF:-1 group-title="{CHANNEL_NAME}" tvg-name="{title}" tvg-logo="{thumb}",{title}'
    )
    lines.append("#EXTVLCOPT:http-user-agent=Mozilla/5.0")
    lines.append(stream)
    count += 1

if count == 0:
    raise RuntimeError("YouTube feed returned no videos; refusing to overwrite playlist")

OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"Wrote {OUTPUT} with {count} video(s)")
