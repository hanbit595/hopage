"""
FAQ·견적문의·개인정보처리방침 페이지(새 페이지, 옛 .php 주소 없음)

- FAQ: cms/faq.yml(국문)·cms/en/faq.yml(영문) → content/pages/{ko,en}/page/faq.html 조각을 Jinja 로 렌더링.
  items[{category 분류, question 질문, answer 답변(HTML 그대로), order 순서(작은 수 먼저, 기본 0), visible 노출(기본 true)}]
  분류 탭은 노출 항목의 분류를 순서대로(처음 나온 순서) 모은다. 분류를 비우면 '기타'(영문 'General').
- 견적문의(inquiry)·개인정보처리방침(privacy)도 같은 방식으로 조각을 렌더링한다(privacy 는 site.yml 연락처·메일).
- 공개 스위치(P5-2): FAQ 는 faq.yml 의 public(true/false, 없으면 false) + 노출 질문 1개 이상, 견적문의는 언어별 site.yml 의
  inquiry_public(없으면 false). 꺼진 페이지는 만들지 않고 메뉴·sitemap 에서도 빠진다. 개인정보처리방침(국문뿐)은
  국문·영문 견적문의 중 하나라도 켜져 있으면 만든다(영문 견적문의·푸터도 국문 방침으로 연결). 아무도 안 쓰는 hb_* CSS·JS 는 public/ 에서 지운다.
- 빌드 실패(한국어 메시지 + 종료코드 1): 파일 없음·형식 오류, question·answer 누락, order 가 숫자가 아님.
"""
import html
from pathlib import Path

import yaml

from cms_pages import CmsPageError

# 출력 경로 → (종류, 언어)
NEW_PAGES = {
    "page/faq.html": ("faq", "ko"),
    "en/page/faq.html": ("faq", "en"),
    "page/inquiry.html": ("inquiry", "ko"),
    "en/page/inquiry.html": ("inquiry", "en"),
    "page/privacy.html": ("privacy", "ko"),
}
FAQ_YML = {"ko": "cms/faq.yml", "en": "cms/en/faq.yml"}
DEFAULT_CAT = {"ko": "기타", "en": "General"}
ASSETS = {"faq": ["theme/basic/js/hb_faq.js"], "inquiry": ["theme/basic/js/hb_inquiry.js"], "privacy": []}
COMMON_ASSETS = ["theme/basic/css/hb_pages.css"]   # 새 페이지 공통


def faq_public(site: Path, lang: str) -> bool:
    data = yaml.safe_load((site / FAQ_YML[lang]).read_text(encoding="utf-8")) or {}
    v = data.get("public", False)
    if not isinstance(v, bool):
        raise CmsPageError(f"{FAQ_YML[lang]}: public 은 true 또는 false 여야 합니다 (현재: '{v}')")
    return v


def switches(site: Path, inquiry_public: dict) -> dict:
    """{언어: {"faq": 켬, "inquiry": 켬}}. inquiry_public 은 언어별 site.yml 값."""
    return {lang: {"faq": faq_public(site, lang) and bool(load_faq(site, lang)["items"]),
                   "inquiry": inquiry_public[lang]} for lang in FAQ_YML}


def is_on(out: str, sw: dict) -> bool:
    kind, lang = NEW_PAGES[out]
    if kind == "privacy":
        return any(s["inquiry"] for s in sw.values())
    return sw[lang][kind]


def off_pages(sw: dict) -> set:
    """만들지 않을 출력 경로."""
    return {out for out in NEW_PAGES if not is_on(out, sw)}


def unused_assets(sw: dict) -> list:
    on = {NEW_PAGES[o][0] for o in NEW_PAGES if is_on(o, sw)}
    return [a for k, v in ASSETS.items() if k not in on for a in v] + ([] if on else COMMON_ASSETS)


def page_of(out: str):
    return NEW_PAGES.get(out)


def load_faq(site: Path, lang: str) -> dict:
    name = FAQ_YML[lang]
    try:
        data = yaml.safe_load((site / name).read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise CmsPageError(f"FAQ 파일이 없습니다: {name}")
    except yaml.YAMLError as e:
        raise CmsPageError(f"{name} 형식 오류: {e}")
    if not isinstance(data, dict) or not isinstance(data.get("items", []) or [], list):
        raise CmsPageError(f"{name} 에 items: 목록이 없습니다.")
    rows = []
    for i, it in enumerate(data.get("items") or [], 1):
        if not isinstance(it, dict):
            raise CmsPageError(f"{name} {i}번째 항목: 형식이 잘못되었습니다.")
        q, a = str(it.get("question") or "").strip(), str(it.get("answer") or "").strip()
        if not q or not a:
            raise CmsPageError(f"{name} {i}번째 항목: question(질문)과 answer(답변)이 모두 있어야 합니다.")
        order = it.get("order", 0)
        order = 0 if order in (None, "") else order
        if isinstance(order, bool) or not isinstance(order, (int, float)):
            raise CmsPageError(f"{name} {i}번째 항목 '{q}': order 는 숫자여야 합니다 (현재: '{order}')")
        if it.get("visible", True) is False:
            continue
        cat = str(it.get("category") or "").strip() or DEFAULT_CAT[lang]
        rows.append((order, i, cat, q, a))
    rows.sort(key=lambda r: (r[0], r[1]))
    cats, items = [], []
    for _, _, cat, q, a in rows:
        if cat not in cats:
            cats.append(cat)
        items.append({"cat": cats.index(cat) + 1, "category": html.escape(cat), "question": html.escape(q), "answer": a})
    return {"categories": [html.escape(c) for c in cats], "items": items}


def context(kind: str, lang: str, site: Path, footer: dict, sw: dict) -> dict:
    """조각 렌더링 변수. footer 는 build.py 의 국문 푸터 변수(tel·email 은 이미 이스케이프됨), sw 는 switches() 결과."""
    if kind == "faq":
        return dict(load_faq(site, lang), inquiry=sw[lang]["inquiry"])
    if kind == "privacy":
        from cms_pages import domestic_tel
        return {"tel": domestic_tel(footer["tel"]), "email": footer["email"]}
    return {}
