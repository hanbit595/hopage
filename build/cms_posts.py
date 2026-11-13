"""
한글 게시판 글 원본 읽기 (P3-4a). build.py·optimize.py·extract_boards.py 가 불러 쓴다.

- 한글 글: cms/notice|media|library/<파일명>.md (머리말 YAML + 본문)
  본문 형식(P3-4b): 머리말 body_format: html 인 글(이전한 기존 글)은 본문 HTML 을 그대로 쓴다.
  그 칸이 없는 글(관리자 화면으로 쓴 새 글)은 markdown → HTML 로 바꾼다(표·줄바꿈 지원, 원문 HTML 은 그대로 통과).
- 영문 글(notice_en·media_en·library_en)과 팝업 등: content/posts.json 그대로
- 돌려주는 값은 posts.json 과 같은 모양이다. 글 = {id, subject, datetime, content, link1, link2, files}
  (기존 게시판·메인 News·sitemap·옛 주소·이미지 최적화 코드를 그대로 쓰기 위해)

파일명: 기존 글은 글번호(99.md), 새 글은 YYYYMMDD-HHMMSS.md → 주소 /board/<게시판>/<파일명>.html
순서: date 최신순, 같은 date 는 파일명 역순(새 형식 파일명 > 글번호, 글번호는 숫자 크기로 비교)
draft: true 인 글은 여기서 빼므로 목록·상세·메인·sitemap·옛 주소 어디에도 나오지 않는다(검사는 똑같이 한다).

머리말 칸(docs/spec.md 3절)
- 공통: title(필수), date(필수, "YYYY-MM-DD HH:MM:SS" 또는 "YYYY-MM-DD" → 시각 00:00:00), draft(기본 false),
        thumbnail(선택, 목록·메인 썸네일 1순위), summary(선택, 메인 News 요약·상세 meta description 1순위),
        body_format(선택, html 이면 본문 HTML 그대로, 없으면 markdown)
- 시공사례: category(필수, 목록, 허용값 CATEGORIES, 표시는 선택 순서대로 쉼표로 이음), capacity·program(선택),
           gallery(선택, 이미지 목록, 상세 본문 아래), featured(기본 false, 메인 Our Project 카드)
           featured_order(선택, 숫자, 카드 순서 작은 숫자 먼저), featured_image(선택, 카드 이미지 1순위)
           featured_label·featured_text(기존 글 전용, 선택: 이전 전 메인 카드에 손으로 적혀 있던 분류·문구를 글자 그대로)
           목록·상세 표시 제목 = "[category] title capacity" + program 이 있으면 " ㅣ program"
- E-Catalog: file(필수, 사이트 주소 /… 의 PDF. public/ 에 있는지는 build.py 가 확인)
- 기존 글 전용(선택, 없으면 기본값): link1·link2(관련 링크, 기본 ""), files(첨부 목록 [{no, source, stored, size}], 기본 [])
  E-Catalog 에서 files 가 없으면 file 로 첨부 1개를 만든다(이름 = 파일 이름, 크기 = 실제 파일 크기)
"""
import html
import json
import posixpath
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import markdown
import yaml

KO_BOARDS = ("notice", "media", "library")
BOARD_NAMES = {"notice": "회사소식", "media": "시공사례", "library": "E-Catalog"}
CATEGORIES = ("태양광발전장치", "BIPV", "주차장태양광", "기타")
DEFAULT_TIME = "00:00:00"   # date 에 시각이 없을 때
NAME_RE = re.compile(r"[1-9]\d*|\d{8}-\d{6}")   # 기존 글번호 또는 새 글 YYYYMMDD-HHMMSS
FRONT = re.compile(r"\A---\r?\n(.*?)\r?\n?---\r?\n?(.*)\Z", re.S)
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})(?:[ T](\d{2}:\d{2})(?::(\d{2}))?(?:\.\d+)?(Z|[+-]\d{2}:?\d{2})?)?")
KST = timezone(timedelta(hours=9))


MD_EXTENSIONS = ["tables", "nl2br", "sane_lists"]   # 표·줄바꿈(엔터 한 번 = <br>)·목록


def md_to_html(text: str) -> str:
    """관리자 화면(markdown) 본문 → HTML. 원문 HTML 은 그대로 통과."""
    return markdown.markdown(text, extensions=MD_EXTENSIONS, output_format="html")


def _image_list(fm, key, where):
    """gallery: ["/uploads/a.jpg", ...] 또는 [{image: "/uploads/a.jpg"}, ...] → 주소 목록."""
    v = fm.get(key)
    if v in (None, ""):
        return []
    if not isinstance(v, list):
        raise CmsError(f"{where}: {key} 는 목록이어야 합니다.")
    out = []
    for i, g in enumerate(v):
        if isinstance(g, dict):
            g = g.get("image") or g.get("src")
        if not isinstance(g, str):
            raise CmsError(f"{where}: {key} {i + 1}번째 항목이 이미지 주소가 아닙니다.")
        if g.strip():
            out.append(g.strip())
    return out


class CmsError(Exception):
    """한국어 메시지로 빌드를 멈춘다(종료코드 1)."""


def compose_media_title(category, title, capacity="", program=""):
    """시공사례 표시 제목: [category] title capacity + (program 있으면) ' ㅣ program'."""
    s = f"[{','.join(category)}] {title}"
    if capacity:
        s += f" {capacity}"
    if program:
        s += f" ㅣ {program}"
    return s


def parse_date(v, where):
    """date 값 → 'YYYY-MM-DD HH:MM:SS'. YAML 이 날짜로 읽은 값(date·datetime)도 받는다."""
    if isinstance(v, datetime):
        if v.tzinfo:
            v = v.astimezone(KST)
        return v.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(v, date):
        return f"{v.isoformat()} {DEFAULT_TIME}"
    if isinstance(v, str):
        m = DATE_RE.fullmatch(v.strip())
        if m:
            d, hm, ss, tz = m.groups()
            try:
                if tz:
                    return parse_date(datetime.fromisoformat(v.strip().replace("Z", "+00:00")), where)
                s = f"{d} {hm}:{ss or '00'}" if hm else f"{d} {DEFAULT_TIME}"
                datetime.strptime(s, "%Y-%m-%d %H:%M:%S")   # 없는 날짜·시각 거름
                return s
            except ValueError:
                pass
    raise CmsError(f"{where}: date 형식 오류 (YYYY-MM-DD 또는 YYYY-MM-DD HH:MM:SS, 현재: '{v}')")


def _text(fm, key, where, required=False):
    v = fm.get(key)
    if v is None or (isinstance(v, str) and not v.strip()):
        if required:
            raise CmsError(f"{where}: 필수 칸 {key} 이(가) 비어 있습니다.")
        return ""
    if isinstance(v, (dict, list, bool)):
        raise CmsError(f"{where}: {key} 는 글자여야 합니다 (현재: {v!r})")
    return str(v)


def _flag(fm, key, where):
    v = fm.get(key)
    if v is None or v == "":
        return False
    if not isinstance(v, bool):
        raise CmsError(f"{where}: {key} 는 true 또는 false 여야 합니다 (현재: {v!r})")
    return v


def _files(fm, where):
    v = fm.get("files")
    if v in (None, ""):
        return []
    if not isinstance(v, list):
        raise CmsError(f"{where}: files 는 목록이어야 합니다.")
    out = []
    for i, f in enumerate(v):
        if not isinstance(f, dict) or not str(f.get("stored") or "").strip():
            raise CmsError(f"{where}: files {i + 1}번째 항목에 stored 가 없습니다.")
        stored = str(f["stored"]).strip()
        no, size = f.get("no", i), f.get("size", 0)
        if isinstance(no, bool) or not isinstance(no, int) or isinstance(size, bool) or not isinstance(size, int):
            raise CmsError(f"{where}: files {i + 1}번째 항목의 no·size 는 숫자여야 합니다.")
        out.append({"no": no, "source": str(f.get("source") or posixpath.basename(stored)), "stored": stored, "size": size})
    return out


def read_md(path: Path, where: str = None):
    """md 파일 → (머리말 dict, 본문 문자열). 본문은 닫는 --- 다음 줄부터 글자 그대로."""
    where = where or path.as_posix()
    text = path.read_bytes().decode("utf-8-sig")
    m = FRONT.match(text)
    if not m:
        raise CmsError(f"{where}: 머리말(--- 로 시작·끝)이 없습니다.")
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except ValueError as e:   # YAML 이 날짜로 읽다가 실패(예: 2026-02-30)
        raise CmsError(f"{where}: date 형식 오류(없는 날짜): {e}")
    except yaml.YAMLError as e:
        raise CmsError(f"{where}: 머리말 형식 오류: {e}")
    if not isinstance(fm, dict):
        raise CmsError(f"{where}: 머리말 형식 오류(칸: 값 형태가 아님)")
    return fm, m.group(2)


def load_board(board: str, cms_dir: Path, static_dir: Path = None, include_draft=False):
    """cms/<board>/*.md → posts.json 모양의 글 목록(정렬됨)."""
    folder = cms_dir / board
    if not folder.is_dir():
        raise CmsError(f"게시판 폴더가 없습니다: cms/{board}/")
    seen, items = {}, []
    for path in sorted(folder.iterdir()):
        if not path.is_file() or path.suffix.lower() != ".md":
            continue
        where = f"cms/{board}/{path.name}"
        name = path.stem
        if not NAME_RE.fullmatch(name):
            raise CmsError(f"{where}: 파일명은 글번호(예: 99.md) 또는 YYYYMMDD-HHMMSS.md 형식이어야 합니다.")
        if name.lower() in seen:
            raise CmsError(f"{where}: 파일명(주소)이 {seen[name.lower()]} 와 겹칩니다.")
        seen[name.lower()] = where
        fm, body = read_md(path, where)

        title = _text(fm, "title", where, required=True)
        if "date" not in fm or fm["date"] in (None, ""):
            raise CmsError(f"{where}: 필수 칸 date 이(가) 비어 있습니다.")
        dt = parse_date(fm["date"], where)
        draft = _flag(fm, "draft", where)
        fmt = _text(fm, "body_format", where).strip().lower()
        if fmt not in ("", "html", "markdown"):
            raise CmsError(f"{where}: body_format 은 html 또는 markdown 이어야 합니다 (현재: '{fmt}')")
        if fmt != "html":
            body = md_to_html(body)
        post = {"id": int(name) if name.isdigit() else name, "datetime": dt, "content": body,
                "link1": _text(fm, "link1", where), "link2": _text(fm, "link2", where), "files": _files(fm, where),
                "thumbnail": _text(fm, "thumbnail", where).strip(), "summary": _text(fm, "summary", where).strip()}

        if board == "media":
            cats = fm.get("category")
            if isinstance(cats, str):
                cats = [cats]
            if not cats:
                raise CmsError(f"{where}: 필수 칸 category 이(가) 비어 있습니다.")
            if not isinstance(cats, list):
                raise CmsError(f"{where}: category 는 목록이어야 합니다.")
            for c in cats:
                if c not in CATEGORIES:
                    raise CmsError(f"{where}: category '{c}' 는 허용 목록({', '.join(CATEGORIES)})에 없습니다.")
            capacity = _text(fm, "capacity", where)
            subject = compose_media_title(cats, title, capacity, _text(fm, "program", where))
            order = fm.get("featured_order")
            if order in ("", None):
                order = None
            elif isinstance(order, bool) or not isinstance(order, int):
                raise CmsError(f"{where}: featured_order 는 숫자여야 합니다 (현재: {order!r})")
            post.update(title=title, category=cats, capacity=capacity, gallery=_image_list(fm, "gallery", where),
                        featured=_flag(fm, "featured", where), featured_order=order,
                        featured_image=_text(fm, "featured_image", where).strip(),
                        featured_label=_text(fm, "featured_label", where), featured_text=_text(fm, "featured_text", where))
        else:
            subject = title
        if board == "library":
            file = _text(fm, "file", where)
            if not file.strip():
                raise CmsError(f"{where}: 필수 칸 file(E-Catalog PDF) 이(가) 비어 있습니다.")
            file = file.strip()
            if not file.startswith("/") or file.startswith("//"):
                raise CmsError(f"{where}: file 은 / 로 시작하는 사이트 주소여야 합니다 (현재: '{file}')")
            post["file"] = file
            if not post["files"]:
                real = static_dir / file.lstrip("/") if static_dir else None
                post["files"] = [{"no": 0, "source": posixpath.basename(file), "stored": file,
                                  "size": real.stat().st_size if real and real.is_file() else 0}]
        post["subject"] = html.escape(subject, quote=False)   # posts.json 처럼 HTML 글자로 둔다(빌드가 풀어서 다시 이스케이프)
        post["_src"] = where
        if draft and not include_draft:
            continue
        items.append(post)

    def key(p):
        i = p["id"]
        return (p["datetime"], (1, i) if isinstance(i, str) else (0, i))
    items.sort(key=key, reverse=True)
    return items


def load_posts(site_dir: Path):
    """content/posts.json(영문·팝업 등) + cms/ 한글 게시판 → posts.json 모양 전체."""
    posts = json.loads((site_dir / "content" / "posts.json").read_text(encoding="utf-8"))
    left = [b for b in KO_BOARDS if b in posts.get("boards", {})]
    if left:
        raise CmsError(f"content/posts.json 에 한글 게시판 배열({', '.join(left)})이 남아 있습니다. "
                       "한글 글의 원본은 cms/ 하나뿐이어야 합니다.")
    for b in KO_BOARDS:
        posts["boards"][b] = load_board(b, site_dir / "cms", site_dir / "static")
    return posts
