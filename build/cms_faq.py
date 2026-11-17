"""
FAQ·견적문의·개인정보처리방침 페이지(새 페이지, 옛 .php 주소 없음)

- FAQ: cms/faq.yml(국문)·cms/en/faq.yml(영문) → content/pages/{ko,en}/page/faq.html 조각을 Jinja 로 렌더링.
  items[{category 분류, question 질문, answer 답변(HTML 그대로), order 순서(작은 수 먼저, 기본 0), visible 노출(기본 true)}]
  분류 탭은 노출 항목의 분류를 순서대로(처음 나온 순서) 모은다. 분류를 비우면 '기타'(영문 'General').
- 견적문의(inquiry)·개인정보처리방침(privacy)도 같은 방식으로 조각을 렌더링한다(privacy 는 site.yml 연락처·메일).
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


def context(kind: str, lang: str, site: Path, footer: dict) -> dict:
    """조각 렌더링 변수. footer 는 build.py 의 국문 푸터 변수(tel·email 은 이미 이스케이프됨)."""
    if kind == "faq":
        return load_faq(site, lang)
    if kind == "privacy":
        from cms_pages import domestic_tel
        return {"tel": domestic_tel(footer["tel"]), "email": footer["email"]}
    return {}
