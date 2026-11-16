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
from pathlib import Path

import yaml

from cms_posts import CmsLoader

# 출력 경로(public/ 기준) → cms/pages/<이름>.yml
PAGES = {
    "page/cert.html": "cert",
}


class CmsPageError(Exception):
    """한국어 메시지로 빌드를 멈춘다(종료코드 1)."""


class Checker:
    """한 yml 파일의 칸 검사 도구. 이미지 존재 여부는 public/ 기준(optimize.py 가 바꾼 이름도 인정)."""

    def __init__(self, name: str, public: Path, renames: dict):
        self.file = f"cms/pages/{name}.yml"
        self.public, self.renames = public, renames

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

    def text(self, d, key, where, required=True):
        v = d.get(key)
        if v is None or (isinstance(v, str) and not v.strip()):
            if required:
                self.fail(where, f"필수 칸 {key} 이(가) 비어 있습니다.")
            return ""
        if isinstance(v, (dict, list, bool)):
            self.fail(where, f"{key} 는 글자여야 합니다 (현재: {v!r}). 글자 그대로 쓰려면 따옴표로 감싸세요.")
        if isinstance(v, (date, datetime)):
            v = v.isoformat()
        return str(v).rstrip("\n")   # 여러 줄 칸(|)의 끝 줄바꿈은 뗀다

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
    """여러 줄 문단: 둘째 줄부터 원래 들여쓰기(indent)를 붙인다. 빈 줄은 들여쓰기 없이."""
    lines = str(v).split("\n")
    return "\n".join([lines[0]] + [indent + s if s else "" for s in lines[1:]])


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


LOADERS = {
    "cert": load_cert,
}


def load(name: str, site: Path, public: Path, renames: dict) -> dict:
    """cms/pages/<name>.yml 을 읽어 검사하고, 본문 조각 렌더링에 넘길 값을 돌려준다."""
    path = site / "cms" / "pages" / f"{name}.yml"
    c = Checker(name, public, renames)
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
