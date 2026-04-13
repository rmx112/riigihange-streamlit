import re
from urllib.request import urlopen
import xml.etree.ElementTree as ET
import streamlit as st

RSS_URL = "https://riigihanked.riik.ee/rhr/api/public/v1/rss"


def normalize_text(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.lower()).strip()


def normalize_cpv(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"[^0-9]", "", text)


@st.cache_data(ttl=300)
def parse_rss(url: str):
    with urlopen(url) as response:
        xml_data = response.read()

    root = ET.fromstring(xml_data)
    items = []

    for item in root.findall(".//item"):
        title = item.findtext("title", default="").strip()
        link = item.findtext("link", default="").strip()
        description = item.findtext("description", default="").strip()
        pub_date = item.findtext("pubDate", default="").strip()

        items.append({
            "title": title,
            "link": link,
            "description": description,
            "pub_date": pub_date,
        })

    return items


def extract_possible_cpv_codes(text: str):
    if not text:
        return []

    # otsib kujusid nagu 72000000-5 või ka lihtsalt 72000000
    matches = re.findall(r"\b\d{8}(?:-\d)?\b", text)
    return matches


def filter_items(items, keyword: str, cpv_prefix: str):
    keyword_norm = normalize_text(keyword)
    cpv_prefix_norm = normalize_cpv(cpv_prefix)

    results = []

    for item in items:
        title_text = normalize_text(item["title"])
        description_text = normalize_text(item["description"])
        full_text = f"{title_text} {description_text}"

        keyword_ok = True
        cpv_ok = True

        if keyword_norm:
            keyword_ok = keyword_norm in full_text

        found_cpvs = extract_possible_cpv_codes(
            f"{item['title']} {item['description']}"
        )

        if cpv_prefix_norm:
            cpv_ok = any(
                normalize_cpv(code).startswith(cpv_prefix_norm)
                for code in found_cpvs
            )

        if keyword_ok and cpv_ok:
            new_item = item.copy()
            new_item["found_cpvs"] = found_cpvs
            results.append(new_item)

    seen = set()
    unique_items = []

    for item in results:
        if item["link"] not in seen:
            seen.add(item["link"])
            unique_items.append(item)

    return unique_items


st.set_page_config(page_title="riigihangete otsing", layout="wide")
st.title("Riigihangete registri märksõnaotsing")
st.write("Sisesta märksõna ja soovi korral CPV algus. Näiteks 72000000.")

keyword = st.text_input("märksõna", placeholder="näiteks: litsents")
cpv_prefix = st.text_input("cpv algus", placeholder="näiteks: 72000000")

if st.button("otsi"):
    if not keyword.strip() and not cpv_prefix.strip():
        st.warning("sisesta vähemalt märksõna või cpv algus")
    else:
        items = parse_rss(RSS_URL)
        results = filter_items(items, keyword, cpv_prefix)

        st.write(f"leitud: {len(results)}")

        if not results:
            st.info("sobivaid hankeid ei leitud")
        else:
            for item in results:
                st.subheader(item["title"])
                st.write(f"kuupäev: {item['pub_date']}")

                if item["found_cpvs"]:
                    st.write("leitud cpv koodid: " + ", ".join(item["found_cpvs"]))

                st.markdown(f"[ava hange]({item['link']})")
                st.divider()
