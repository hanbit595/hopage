"""
고정 페이지 데이터(P4): cms/pages/<페이지>.yml → 고정 페이지 본문 조각(content/pages/ko/page/<페이지>.html)

- 본문 조각의 레이아웃·마크업·클래스는 그대로 두고, 내용이 들어갈 자리만 Jinja 칸({{ }}·{% for %})으로 바꿨다.
- build.py 가 한글 고정 페이지를 만들 때 PAGES 에 있는 페이지는 이 모듈로 데이터를 읽고 검사한 뒤 조각을 렌더링한다.
- 빌드 실패(한국어 메시지 + 종료코드 1): 필수 칸 누락, 날짜·월 형식 오류, 이미지 파일이 public/ 에 없음.
- 글자 칸: 제목·명칭은 HTML 이스케이프, 문단·내용 칸은 <br>·<b> 같은 HTML 을 그대로 쓴다.
  여러 줄 문단은 줄마다 원래 들여쓰기를 붙여 출력한다(빈 줄은 들여쓰기 없이).
"""
import re
from datetime import date, datetime
from html.entities import html5
from pathlib import Path

import yaml

from cms_posts import CmsLoader

# 출력 경로(public/ 기준) → cms/pages/<이름>.yml
PAGES = {
    "page/cert.html": "cert",
    "page/history.html": "history",
    "page/hanbit.html": "hanbit",
    "page/esg.html": "esg",
    "page/location.html": "location",
}
# 영문(P4-EN1): 국문과 완전히 분리. 출력 경로 → cms/en/pages/<이름>.yml (이미지 파일은 공유, 데이터는 별도)
PAGES_EN = {
    "en/page/cert.html": "cert",
    "en/page/history.html": "history",
}
ROOT = Path(__file__).resolve().parent.parent
SITE_YML = ROOT / "cms" / "settings" / "site.yml"            # Contact 주소·연락처·메일 원본(국문)
SITE_YML_EN = ROOT / "cms" / "en" / "settings" / "site.yml"  # 영문 전용 회사정보(국문 site.yml 재사용 금지)


def page_of(out: str):
    """출력 경로 → (이름, 언어) 또는 None. 데이터 파일로 만드는 고정 페이지인지 판단한다."""
    if out in PAGES:
        return PAGES[out], "ko"
    if out in PAGES_EN:
        return PAGES_EN[out], "en"
    return None


def data_dir(lang: str) -> str:
    return "cms/pages" if lang == "ko" else "cms/en/pages"


def _is_ref(rest: str) -> bool:
    """'&' 뒤 글자(rest)가 문자 참조(&#…, &amp; 같은 이름)로 읽힐 수 있는가."""
    return rest.startswith("#") or any(rest.startswith(k) for k in html5)


def esc_text(s) -> str:
    """영문 화면 글자 이스케이프: <·> 는 바꾸고, '&' 는 문자 참조로 읽힐 수 있을 때만 &amp; 로 바꾼다.
    (기존 영문 화면의 'R&D' 처럼 글자 그대로 보이는 & 는 원래 표기 그대로 둔다)"""
    s = str(s)
    out = []
    for i, ch in enumerate(s):
        out.append("&amp;" if ch == "&" and _is_ref(s[i + 1:]) else ch)
    return "".join(out).replace("<", "&lt;").replace(">", "&gt;")


class CmsPageError(Exception):
    """한국어 메시지로 빌드를 멈춘다(종료코드 1)."""


class Checker:
    """한 yml 파일의 칸 검사 도구. 이미지 존재 여부는 public/ 기준(optimize.py 가 바꾼 이름도 인정)."""

    def __init__(self, name: str, public: Path, renames: dict, lang: str = "ko"):
        self.file = f"{data_dir(lang)}/{name}.yml"
        self.public, self.renames, self.lang = public, renames, lang

    def fail(self, where, msg):
        raise CmsPageError(f"{self.file} {where}: {msg}" if where else f"{self.file}: {msg}")

    def obj(self, v, where):
        if not isinstance(v, dict):
            self.fail(where, "형식이 잘못되었습니다(칸 이름: 값 형태여야 합니다).")
        return v

    def items(self, d, key, where, required=True):
        v = d.get(key)
        if v in (None, "") and not required:
            return []
        if not isinstance(v, list) or (required and not v):
            self.fail(where, f"필수 칸 {key} 목록이 비어 있습니다.")
        return v

    def text(self, d, key, where, required=True, keep_end=False):
        """keep_end(영문 연혁 내용만): | 로 적은 여러 줄 칸의 끝 줄바꿈 1개를 남긴다(기존 영문 화면의 '…\\n    </td>' 표기 유지)."""
        v = d.get(key)
        if v is None or (isinstance(v, str) and not v.strip()):
            if required:
                self.fail(where, f"필수 칸 {key} 이(가) 비어 있습니다.")
            return ""
        if isinstance(v, (dict, list, bool)):
            self.fail(where, f"{key} 는 글자여야 합니다 (현재: {v!r}). 글자 그대로 쓰려면 따옴표로 감싸세요.")
        if isinstance(v, (date, datetime)):
            v = v.isoformat()
        s = str(v).rstrip("\n")   # 여러 줄 칸(|)의 끝 줄바꿈은 뗀다
        return s + "\n" if keep_end and str(v).endswith("\n") else s

    def flag(self, d, key, where, default=True):
        v = d.get(key)
        if v is None or v == "":
            return default
        if not isinstance(v, bool):
            self.fail(where, f"{key} 는 true 또는 false 여야 합니다 (현재: {v!r})")
        return v

    def number(self, d, key, where, default=0):
        v = d.get(key)
        if v is None or v == "":
            return default
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            self.fail(where, f"{key} 는 숫자여야 합니다 (현재: {v!r})")
        return v

    def image(self, d, key, where, required=True):
        """/로 시작하는 사이트 안 주소. public/ 에 파일이 있어야 한다."""
        p = self.text(d, key, where, required)
        if not p:
            return ""
        p = p.strip()
        if not p.startswith("/") or p.startswith("//"):
            self.fail(where, f"{key} 는 /로 시작하는 사이트 안 주소여야 합니다 (현재: '{p}')")
        rel = p.lstrip("/")
        if not (self.public / self.renames.get(rel, rel)).is_file():
            self.fail(where, f"{key} 이미지 파일이 사이트(public/)에 없습니다: {p}")
        return p

    def day(self, d, key, where, required=False):
        """날짜: YYYY-MM-DD 또는 YYYY-MM (선택 칸이면 비워도 됨)."""
        v = d.get(key)
        if v is None or v == "":
            if required:
                self.fail(where, f"필수 칸 {key} 이(가) 비어 있습니다.")
            return ""
        if isinstance(v, datetime):
            v = v.date()
        if isinstance(v, date):
            return v.isoformat()
        s = str(v).strip()
        try:
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
                return date.fromisoformat(s).isoformat()
            if re.fullmatch(r"\d{4}-\d{2}", s) and 1 <= int(s[5:]) <= 12:
                return s
        except ValueError:
            pass
        self.fail(where, f"{key} 날짜 형식 오류 (YYYY-MM-DD 또는 YYYY-MM, 현재: '{v}')")

    def year(self, d, key, where):
        v = d.get(key)
        s = str(v).strip() if isinstance(v, (int, str)) and not isinstance(v, bool) else ""
        if not re.fullmatch(r"(19|20)\d{2}", s):
            self.fail(where, f"{key} 연도 형식 오류 (4자리 숫자, 예: 2026, 현재: '{v}')")
        return int(s)

    def month(self, d, key, where):
        """월: "01"~"12" (따옴표 권장). 숫자 1~12 도 받는다. 출력은 두 자리."""
        v = d.get(key)
        s = str(v).strip() if isinstance(v, (int, str)) and not isinstance(v, bool) else ""
        if not re.fullmatch(r"\d{1,2}", s) or not 1 <= int(s) <= 12:
            self.fail(where, f"{key} 월 형식 오류 (01~12, 현재: '{v}')")
        return f"{int(s):02d}"


def ml(v, indent: str) -> str:
    """여러 줄 문단: 둘째 줄부터 원래 들여쓰기(indent)를 붙인다. 빈 줄은 들여쓰기 없이.
    끝 줄바꿈이 남은 칸(영문 연혁 keep_end)은 마지막 빈 줄에도 들여쓰기를 붙여 닫는 태그 줄을 맞춘다."""
    lines = str(v).split("\n")
    rest = [indent + s if s else "" for s in lines[1:]]
    if len(lines) > 1 and lines[-1] == "":
        rest[-1] = indent
    return "\n".join([lines[0]] + rest)


def img(path: str) -> str:
    """/theme/... → %%ROOT%%theme/... (build.py 가 상대경로·바뀐 파일 이름으로 바꾼다)."""
    return "%%ROOT%%" + str(path).lstrip("/")


# ---------------------------------------------------------------- 페이지별 읽기
def load_cert(c: Checker, d: dict) -> dict:
    cats = c.items(d, "categories", "")
    titles = []
    for i, t in enumerate(cats, 1):
        t = c.text({"구분": t}, "구분", f"categories {i}번째")
        if t in titles:
            c.fail(f"categories {i}번째", f"구분 '{t}' 이(가) 두 번 있습니다.")
        titles.append(t)
    groups = {t: [] for t in titles}
    for i, it in enumerate(c.items(d, "items", ""), 1):
        it = c.obj(it, f"items {i}번째")
        where = f"items {i}번째 '{it.get('name') or ''}'"
        cat = c.text(it, "category", where)
        if cat not in groups:
            c.fail(where, f"category '{cat}' 이(가) categories 목록({', '.join(titles)})에 없습니다.")
        row = {"name": c.text(it, "name", where), "issuer": c.text(it, "issuer", where, required=False),
               "date": c.day(it, "date", where), "image": c.image(it, "image", where),
               "order": c.number(it, "order", where), "_i": i}
        if c.flag(it, "visible", where):
            groups[cat].append(row)
    out = []
    for n, t in enumerate(titles, 1):
        rows = sorted(groups[t], key=lambda r: (r["order"], r["_i"]))
        if rows:   # 노출 항목이 하나도 없는 구분은 통째로 숨긴다(id 번호는 구분 순서 그대로)
            out.append({"id": f"cert{n:02d}", "title": t, "rows": rows})
    return {"groups": out}


def load_history(c: Checker, d: dict) -> dict:
    out, anchors = [], set()
    for i, p in enumerate(c.items(d, "periods", ""), 1):
        p = c.obj(p, f"periods {i}번째")
        where = f"periods {i}번째 '{p.get('title') or ''}'"
        anchor = c.text(p, "anchor", where, required=False).strip() or f"his-{i}"
        if not re.fullmatch(r"[A-Za-z0-9_-]+", anchor):
            c.fail(where, f"anchor 는 영문·숫자·-·_ 만 쓸 수 있습니다 (현재: '{anchor}')")
        if anchor in anchors:
            c.fail(where, f"anchor '{anchor}' 이(가) 다른 기간과 겹칩니다.")
        anchors.add(anchor)
        years, seen = [], set()
        for j, y in enumerate(c.items(p, "years", where), 1):
            y = c.obj(y, f"{where} years {j}번째")
            yw = f"{where} years {j}번째"
            year = c.year(y, "year", yw)
            if year in seen:
                c.fail(yw, f"연도 {year} 가 같은 기간 안에 두 번 있습니다(한 연도로 합쳐 주세요).")
            seen.add(year)
            yw = f"{where} {year}년"
            months = []
            for k, m in enumerate(c.items(y, "months", yw), 1):
                m = c.obj(m, f"{yw} months {k}번째")
                mw = f"{yw} months {k}번째"
                month = c.month(m, "month", mw)
                rows = [c.text({"내용": t}, "내용", f"{yw} {month}월 items {n}번째", keep_end=c.lang == "en")
                        for n, t in enumerate(c.items(m, "items", f"{yw} {month}월"), 1)]
                months.append({"month": month, "items": rows})
            months.sort(key=lambda m: m["month"], reverse=True)   # 큰 달이 위(같은 달은 적은 순서)
            years.append({"year": year, "months": months})
        years.sort(key=lambda y: y["year"], reverse=True)          # 큰 연도가 위
        out.append({"title": c.text(p, "title", where), "anchor": anchor, "image": c.image(p, "image", where),
                    "years": years})
    return {"periods": out}


def fixed_list(c: Checker, d: dict, key: str, count: int, kind: str):
    """개수가 정해진 목록(화면 움직임 스크립트와 맞물린 칸). 개수가 다르면 빌드 실패."""
    v = c.items(d, key, "")
    if len(v) != count:
        c.fail("", f"{key} 는 꼭 {count}개여야 합니다 (현재 {len(v)}개). 화면 구성이 {kind} {count}개로 고정되어 있습니다.")
    return v


def load_hanbit(c: Checker, d: dict) -> dict:
    hero = c.obj(d.get("hero"), "hero")
    texts = lambda key, n: [c.text({key: t}, key, f"{key} {i}번째") for i, t in enumerate(fixed_list(c, d, key, n, "문단"), 1)]
    return {
        "hero": {"title": c.text(hero, "title", "hero"), "image": c.image(hero, "image", "hero")},
        "intro_texts": texts("intro_texts", 3),
        "photos": [c.image({"photos": p}, "photos", f"photos {i}번째")
                   for i, p in enumerate(fixed_list(c, d, "photos", 6, "사진"), 1)],
        "energy_text": c.text(d, "energy_text", ""),
        "sun_texts": texts("sun_texts", 2),
        "ending_text": c.text(d, "ending_text", ""),
    }


def load_esg(c: Checker, d: dict) -> dict:
    intro = c.obj(d.get("intro"), "intro")
    pillars = []
    for i, p in enumerate(c.items(d, "pillars", ""), 1):
        p = c.obj(p, f"pillars {i}번째")
        where = f"pillars {i}번째 '{p.get('title') or ''}'"
        pillars.append({"title": c.text(p, "title", where), "icon": c.image(p, "icon", where),
                        "text": c.text(p, "text", where)})
    details = []
    for i, b in enumerate(c.items(d, "details", ""), 1):
        b = c.obj(b, f"details {i}번째")
        where = f"details {i}번째 '{b.get('title') or ''}'"
        details.append({"title": c.text(b, "title", where),
                        "items": [c.text({"항목": t}, "항목", f"{where} items {n}번째")
                                  for n, t in enumerate(c.items(b, "items", where), 1)]})
    return {"intro": {"title": c.text(intro, "title", "intro"), "text": c.text(intro, "text", "intro")},
            "flow_text": c.text(d, "flow_text", ""), "pillars": pillars, "details": details}


def domestic_tel(tel: str) -> str:
    """site.yml tel(+82-51-913-0120) → Contact 화면 국내 표기(051-913-0120). 이미 국내 표기면 그대로."""
    return re.sub(r"^\+82[-\s]?(\d)", r"0\1", tel.strip())


def load_location(c: Checker, d: dict) -> dict:
    """Contact: 사업장 이름·지도는 location.yml, 주소·연락처·메일은 site.yml(원본 하나)."""
    sc = Checker("site", c.public, c.renames)
    sc.file = "cms/settings/site.yml"
    site = sc.obj(yaml.load(SITE_YML.read_text(encoding="utf-8"), Loader=CmsLoader), "")
    offices = {}
    for i, o in enumerate(sc.items(site, "offices", ""), 1):
        o = sc.obj(o, f"offices {i}번째")
        offices[sc.text(o, "name", f"offices {i}번째").strip()] = sc.text(o, "address", f"offices {i}번째").strip()
    tel, email = domestic_tel(sc.text(site, "tel", "")), sc.text(site, "email", "").strip()
    out = []
    for i, L in enumerate(c.items(d, "locations", ""), 1):
        L = c.obj(L, f"locations {i}번째")
        where = f"locations {i}번째 '{L.get('title') or ''}'"
        office = c.text(L, "office", where).strip()
        if office not in offices:
            c.fail(where, f"office '{office}' 이(가) site.yml offices 이름({', '.join(offices)})에 없습니다.")
        m = c.text(L, "map", where).strip()
        if not m.startswith("https://www.google.com/maps/embed"):
            c.fail(where, f"map 은 https://www.google.com/maps/embed 로 시작하는 구글 지도 삽입 주소여야 합니다 (현재: '{m[:60]}')")
        ind = c.number(L, "map_indent", where)
        if not isinstance(ind, int) or not 0 <= ind <= 40:
            c.fail(where, f"map_indent 는 0~40 숫자여야 합니다 (현재: {ind!r})")
        out.append({"label": c.text(L, "label", where), "title": c.text(L, "title", where), "map": m,
                    "indent": " " * ind, "address": offices[office]})
    return {"locations": out, "tel": tel, "email": email}


LOADERS = {
    "cert": load_cert,
    "history": load_history,
    "hanbit": load_hanbit,
    "esg": load_esg,
    "location": load_location,
}


def load(name: str, site: Path, public: Path, renames: dict, lang: str = "ko") -> dict:
    """cms/pages/<name>.yml(영문은 cms/en/pages/<name>.yml)을 읽어 검사하고, 본문 조각 렌더링에 넘길 값을 돌려준다."""
    path = site / data_dir(lang) / f"{name}.yml"
    c = Checker(name, public, renames, lang)
    try:
        d = yaml.load(path.read_text(encoding="utf-8"), Loader=CmsLoader)
    except FileNotFoundError:
        raise CmsPageError(f"고정 페이지 데이터 파일이 없습니다: {c.file}")
    except yaml.YAMLError as e:
        raise CmsPageError(f"{c.file} 형식 오류: {e}")
    except ValueError as e:   # YAML 이 날짜로 읽다가 실패(예: 2026-02-30)
        raise CmsPageError(f"{c.file} 날짜 형식 오류(없는 날짜): {e}")
    return LOADERS[name](c, c.obj(d, ""))


def render(env, content_html: str, ctx: dict) -> str:
    """본문 조각을 Jinja 로 렌더링한다(조각 안의 %%ROOT%%·%%MENU_KO%% 자리표시는 그대로 남아 build.py 가 채운다)."""
    return env.from_string(content_html).render(**ctx)
