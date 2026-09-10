from pathlib import Path
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET
import re

HANDLE = "mukhtalif_career"
CHANNEL_NAME = "إذاعة مختلف"
OUTPUT = Path("mukhtalif.m3u")
STREAM_BASE = "https://yewtu.be/latest_version"
MAX_ITEMS = 15
UA = "Mozilla/5.0"


def get(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": UA, "Accept-Language": "ar,en;q=0.8"})
    with urlopen(req, timeout=30) as response:
        return response.read()


def clean(text: str) -> str:
    return " ".join((text or "").replace('"', "'").split())


# Resolve the @handle to its current YouTube channel ID.
html = get(f"https://www.youtube.com/@{HANDLE}").decode("utf-8", errors="ignore")
patterns = [
    r'"channelId":"(UC[0-9A-Za-z_-]{22})"',
    r'"externalId":"(UC[0-9A-Za-z_-]{22})"',
    r'youtube\.com/channel/(UC[0-9A-Za-z_-]{22})',
]
channel_id = None
for pattern in patterns:
    match = re.search(pattern, html)
    if match:
        channel_id = match.group(1)
        break

if not channel_id:
    raise RuntimeError("Could not resolve YouTube channel ID from handle")

feed = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
root = ET.fromstring(get(feed))
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
    # Invidious resolves this stable URL to an MP4 stream when CarTV requests it.
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
print(f"Resolved channel: {channel_id}")
print(f"Wrote {OUTPUT} with {count} video(s)")
