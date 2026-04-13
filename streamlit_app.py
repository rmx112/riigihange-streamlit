import re
from urllib.request import urlopen
import xml.etree.ElementTree as ET
import streamlit as st

RSS_URL = "https://riigihanked.riik.ee/rhr/api/public/v1/rss"


def normalize_text(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.lower()).strip()


@st.cache_data(ttl=300)
def parse_rss(url: str):
    with urlopen(url) as response:
        xml_data = response.read()

    root = ET.fromstring(xml_data)
    items = []

    for item in root.findall(".//item"):
        items.append({
            "title": item.findtext("title", default="").strip(),
            "link": item.findtext("link", default="").strip(),
            "description": item.findtext("description", default="").strip(),
            "pub_date": item.findtext("pubDate", default="").strip(),
        })

    return items


def filter_items(items, keyword: str):
    keyword_norm = normalize_text(keyword)
    results = []

    for item in items:
        full_text = normalize_text(item["title"] + " " + item["description"])
        if keyword_norm in full_text:
            results.append(item)

    seen = set()
    unique = []
    for item in results:
        if item["link"] not in seen:
            seen.add(item["link"])
            unique.append(item)

    return unique


st.set_page_config(page_title="Riigihangete registri otsing", layout="wide")
st.title("riigihangete märksõnaotsing")
st.write("Sisesta märksõna ja rakendus otsib selle järgi riigihangete RSS voost sobivad hanked.")

keyword = st.text_input("sisesta märksõna", placeholder="näiteks: server")

if st.button("otsi"):
    if not keyword.strip():
        st.warning("sisesta märksõna")
    else:
        items = parse_rss(RSS_URL)
        results = filter_items(items, keyword)

        st.write(f"leitud: {len(results)}")

        if not results:
            st.info("sobivaid hankeid ei leitud")
        else:
            for item in results:
                st.subheader(item["title"])
                st.write(f"kuupäev: {item['pub_date']}")
                st.markdown(f"[ava hange]({item['link']})")
                st.divider()
