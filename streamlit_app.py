import re
from urllib.request import urlopen
import xml.etree.ElementTree as ET
import streamlit as st

RSS_URL = "https://riigihanked.riik.ee/rhr/api/public/v1/rss"

CPV_GROUPS = {
    "": "kõik cpv grupid",
    "03000000": "03000000-1 põllumajandussaadused, loomakasvatus-, kalandus-, metsandus- ja seonduvad tooted",
    "09000000": "09000000-3 naftatooted, kütused, elekter ja muud energiaallikad",
    "14000000": "14000000-1 kaevandustooted, mitteväärismetallid ja seonduvad tooted",
    "15000000": "15000000-8 toiduained, joogid ja tubakas ja seonduvad tooted",
    "16000000": "16000000-5 põllutöömasinad",
    "18000000": "18000000-9 rõivad, jalatsid, reisitarbed ja manused",
    "19000000": "19000000-6 nahk ja tekstiilriie, plast- ja kummimaterjalid",
    "22000000": "22000000-0 trükised ja seonduvad tooted",
    "24000000": "24000000-4 keemiatooted",
    "30000000": "30000000-9 kontorimasinad ja arvutid, nende seadmed ja tarvikud, v.a mööbel ja tarkvarapaketid",
    "31000000": "31000000-6 elektrimasinad, -aparaadid, -seadmed ja -tarvikud; valgustus",
    "32000000": "32000000-3 raadio-, televisiooni-, kommunikatsiooni-, teleside- ja sellega seotud seadmed",
    "33000000": "33000000-0 meditsiiniseadmed, farmaatsiatooted ja isikuhooldustooted",
    "34000000": "34000000-7 transpordivahendid ja seonduvad lisatooted",
    "35000000": "35000000-4 turva-, tuletõrje-, politsei- ja kaitseseadmed",
    "37000000": "37000000-8 muusikariistad, spordikaubad, mängud, mänguasjad, käsitöö- ja kunstitarbed ning -tarvikud",
    "38000000": "38000000-5 laboriseadmed, optika- ja täppisinstrumendid (v.a klaasid)",
    "39000000": "39000000-2 mööbel (sh kontorimööbel), sisustus, kodumasinad (v.a valgustus) ja puhastusvahendid",
    "41000000": "41000000-9 kogutud ja puhastatud vesi",
    "42000000": "42000000-6 tööstusmasinad",
    "43000000": "43000000-3 kaevandus-, karjääri- ja ehitusmasinad",
    "44000000": "44000000-0 ehituskonstruktsioonid ja -materjalid; ehituse abimaterjalid (v.a elektriseadmed)",
    "45000000": "45000000-7 ehitustööd",
    "48000000": "48000000-8 tarkvarapaketid ja infosüsteemid",
    "50000000": "50000000-5 remondi-, hooldus- ja paigaldusteenused",
    "51000000": "51000000-9 paigaldusteenused (v.a tarkvara)",
    "55000000": "55000000-0 hotelli-, restorani- ja jaemüügiteenused",
    "60000000": "60000000-8 transporditeenused (v.a jäätmetransport)",
    "63000000": "63000000-9 tugi- ja abiveoteenused; reisibürooteenused",
    "64000000": "64000000-6 posti- ja telekommunikatsiooniteenused",
    "65000000": "65000000-3 kommunaalteenused",
    "66000000": "66000000-0 finantsvahendus- ja kindlustusteenused",
    "70000000": "70000000-1 kinnisvarateenused",
    "71000000": "71000000-8 arhitektuuri-, ehitus-, inseneri- ja ehitusjärelevalveteenused",
    "72000000": "72000000-5 it-teenused: nõuande-, tarkvaraarendus-, interneti- ja tugiteenused",
    "73000000": "73000000-2 uurimis- ja arendusteenused ja seonduvad nõustamisteenused",
    "75000000": "75000000-6 riigihaldus-, kaitse- ja sotsiaalkindlustusteenused",
    "76000000": "76000000-3 nafta- ja gaasitööstusega seotud teenused",
    "77000000": "77000000-0 põllumajandus-, metsandus-, aiandus-, vesiviljelus- ja mesindusteenused",
    "79000000": "79000000-4 õigus-, turundus-, nõustamis-, värbamis-, trüki- ja turvaalased kommertsteenused",
    "80000000": "80000000-4 haridus- ja koolitusteenused",
    "85000000": "85000000-9 tervishoiu ja sotsiaaltöö teenused",
    "90000000": "90000000-7 reovee- ja jäätmekõrvaldusteenused, puhastus- ja keskkonnateenused",
    "92000000": "92000000-1 vabaaja-, kultuuri- ja sporditeenused",
    "98000000": "98000000-3 muud ühiskondlikud, sotsiaal- ja isikuteenused",
}


def normalize_text(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.lower()).strip()


def normalize_cpv(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"[^0-9]", "", text)


def extract_cpv_codes(text: str):
    if not text:
        return []

    matches = re.findall(r"\b\d{8}-\d\b", text)
    unique = []
    seen = set()

    for m in matches:
        if m not in seen:
            seen.add(m)
            unique.append(m)

    return unique


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
        item_xml = ET.tostring(item, encoding="unicode")

        items.append({
            "title": title,
            "link": link,
            "description": description,
            "pub_date": pub_date,
            "item_xml": item_xml,
        })

    return items


def filter_items(items, keyword: str, cpv_prefix: str):
    keyword_norm = normalize_text(keyword)
    cpv_prefix_norm = normalize_cpv(cpv_prefix)

    results = []

    for item in items:
        title_text = normalize_text(item["title"])
        description_text = normalize_text(item["description"])
        full_text = f"{title_text} {description_text}"

        found_cpvs = extract_cpv_codes(item["item_xml"])

        keyword_ok = True
        cpv_ok = True

        if keyword_norm:
            keyword_ok = keyword_norm in full_text

        if cpv_prefix_norm:
            cpv_ok = any(
                normalize_cpv(code).startswith(cpv_prefix_norm)
                for code in found_cpvs
            )

        if keyword_ok and cpv_ok:
            new_item = item.copy()
            new_item["found_cpvs"] = found_cpvs
            results.append(new_item)

    unique_results = []
    seen_links = set()

    for item in results:
        if item["link"] not in seen_links:
            seen_links.add(item["link"])
            unique_results.append(item)

    return unique_results


st.set_page_config(page_title="riigihangete otsing", layout="wide")
st.title("riigihangete märksõnaotsing")
st.write("Sisesta märksõna ja soovi korral vali CPV põhirühm.")

keyword = st.text_input("märksõna", placeholder="näiteks: litsents või server")

selected_cpv = st.selectbox(
    "cpv põhirühm",
    options=list(CPV_GROUPS.keys()),
    format_func=lambda x: CPV_GROUPS[x],
)

if st.button("otsi"):
    if not keyword.strip() and not selected_cpv.strip():
        st.warning("sisesta märksõna või vali cpv põhirühm")
    else:
        items = parse_rss(RSS_URL)
        results = filter_items(items, keyword, selected_cpv)

        st.write(f"leitud: {len(results)}")

        if not results:
            st.info("sobivaid hankeid ei leitud")

            with st.expander("miks nii võib juhtuda"):
                st.write(
                    "Kui cpv kood ei tule rss itemi sees kaasa, siis ainult rss põhjal filtreerimine ei leia seda."
                )
        else:
            for item in results:
                st.subheader(item["title"])
                st.write(f"kuupäev: {item['pub_date']}")

                if item["found_cpvs"]:
                    st.write("leitud cpv koodid: " + ", ".join(item["found_cpvs"]))

                st.markdown(f"[ava hange]({item['link']})")
                st.divider()
