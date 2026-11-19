"""
자유 페이지(P6): 고정 페이지 본문 = cms/free/<이름>.md(국문)·cms/en/free/<이름>.md(영문). 관리자 화면 편집기가 고친다.

파일 형식
    ---
    title: "PV | HANBIT Innotech"      # 참고용(화면 제목·<title> 은 content/pages/meta.json)
    path: "/page/pv.html"              # 기존 주소(출력 경로). 파일 이름과 맞아야 한다
    editor_mode: "html"                # html | visual (관리자 편집기 시작 모드)
    ---
    <div class="sec_wrap"> … 본문 HTML …

- 틀: content/pages/{ko,en}/page/<이름>.html 에 상단 제목·왼쪽(상단) 메뉴·감싸는 div·페이지 전용 스크립트가 남고,
  본문 자리에 %%FREE_BODY%% 가 있다. 본문 중간에 있던 스크립트는 틀 맨 아래 <!--%%FREE_SCRIPT:n%%--> … <!--%%END%%--> 블록에
  보관하고, 본문의 <!--hb-script-n--> 자리에 다시 넣는다(자리 표시가 지워지면 본문 끝에 넣는다).
- 본문 주소: /로 시작하는 src·href·poster·data-*·srcset·url() 은 빌드 때 상대경로(%%ROOT%%)로 바꾼다.
- 안전 처리(빌드 때): <script> 제거, on* 속성 제거, javascript: 주소 제거, iframe 은 youtube.com·youtube-nocookie.com 만 허용.
- 빌드 실패(한국어 메시지): 파일 없음, 앞부분 형식 오류, path 불일치, editor_mode 값 오류.
"""
import re
from pathlib import Path

import yaml

from cms_pages import CmsPageError

SLOT = "%%FREE_BODY%%"
MODES = ("html", "visual")
SCRIPT_BLOCK = re.compile(r"\n?<!--%%FREE_SCRIPT:(\d+)%%-->(.*?)<!--%%END%%-->", re.S)
YT_HOSTS = ("www.youtube.com", "youtube.com", "www.youtube-nocookie.com", "youtube-nocookie.com")

ATTR_ROOT = re.compile(r'(\s(?:src|href|poster|data-[\w-]+)=")/(?!/)')
URL_ROOT = re.compile(r"(url\(['\"]?)/(?!/)")
SRCSET = re.compile(r'(\ssrcset=")([^"]*)"')


def md_path(out: str) -> str:
    """출력 경로 → cms 파일 경로. page/pv.html → cms/free/pv.md, en/page/pv.html → cms/en/free/pv.md"""
    name = out.rsplit("/", 1)[1][:-5]
    return ("cms/en/free/" if out.startswith("en/") else "cms/free/") + name + ".md"


# ───────── 주소: 파일에는 /theme/… , 빌드 때 %%ROOT%%theme/… ─────────
def to_root(body: str) -> str:
    body = ATTR_ROOT.sub(r"\1%%ROOT%%", body)
    body = URL_ROOT.sub(r"\1%%ROOT%%", body)
    return SRCSET.sub(lambda m: m.group(1) + re.sub(r"(^|,\s*)/(?!/)", r"\1%%ROOT%%", m.group(2)) + '"', body)


def from_root(body: str) -> str:
    return body.replace("%%ROOT%%", "/")


# ───────── 안전 처리 ─────────
def _iframe_ok(tag: str) -> bool:
    m = re.search(r'\ssrc=["\']?(?:https?:)?//([^/"\'\s>]+)', tag, re.I)
    return bool(m) and m.group(1).lower() in YT_HOSTS


def sanitize(body: str) -> str:
    body = re.sub(r"<script\b.*?</script\s*>", "", body, flags=re.S | re.I)
    body = re.sub(r"<script\b[^>]*>", "", body, flags=re.I)
    body = re.sub(r"""\son[a-z]+\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+)""", "", body, flags=re.I)
    body = re.sub(r"""(\s(?:href|src|action|formaction|xlink:href)\s*=\s*)(["']?)\s*javascript:[^"'>]*\2""",
                  r'\1\2#\2', body, flags=re.I)
    body = re.sub(r"<iframe\b[^>]*>.*?</iframe\s*>",
                  lambda m: m.group(0) if _iframe_ok(m.group(0)) else "", body, flags=re.S | re.I)
    body = re.sub(r"<iframe\b[^>]*>", lambda m: m.group(0) if _iframe_ok(m.group(0)) else "", body, flags=re.I)
    return body


# ───────── 읽기·끼우기 ─────────
def split_md(text: str, name: str):
    m = re.match(r"---\r?\n(.*?)\r?\n---\r?\n", text, re.S)
    if not m:
        raise CmsPageError(f"{name}: 맨 위 --- 사이 앞부분(title·path·editor_mode)이 없습니다.")
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:
        raise CmsPageError(f"{name} 앞부분 형식 오류: {e}")
    if not isinstance(fm, dict):
        raise CmsPageError(f"{name} 앞부분 형식 오류")
    return fm, text[m.end():]


def load(site: Path, out: str) -> str:
    name = md_path(out)
    try:
        text = (site / name).read_text(encoding="utf-8")
    except FileNotFoundError:
        raise CmsPageError(f"자유 페이지 파일이 없습니다: {name}")
    fm, body = split_md(text, name)
    if str(fm.get("path") or "").strip() != "/" + out:
        raise CmsPageError(f"{name}: path 는 '/{out}' 이어야 합니다 (현재: '{fm.get('path')}')")
    if fm.get("editor_mode", "html") not in MODES:
        raise CmsPageError(f"{name}: editor_mode 는 html 또는 visual 이어야 합니다 (현재: '{fm.get('editor_mode')}')")
    return to_root(sanitize(body))


def fill(frame: str, body: str) -> str:
    """틀의 %%FREE_BODY%% 에 본문을 넣고, 보관한 본문 중간 스크립트를 자리 표시에 되돌린다."""
    scripts = {n: s for n, s in SCRIPT_BLOCK.findall(frame)}
    frame = SCRIPT_BLOCK.sub("", frame)
    for n, s in scripts.items():
        mark = f"<!--hb-script-{n}-->"
        body = body.replace(mark, s, 1) if mark in body else body + s
    return frame.replace(SLOT, body, 1)


# ───────── 숨김(기존 페이지 포함): menu.yml 에서 그 주소를 가리키는 소메뉴가 모두 숨김이면 만들지 않음 ─────────
def menu_visibility(menu_file: Path) -> tuple:
    """menu.yml → (가리키는 주소 전체, 노출로 가리키는 주소). 소메뉴는 대메뉴도 노출일 때만 노출(P7 과 같음).
    대메뉴 link 는 그 주소를 가리키는 소메뉴가 없을 때만 셈(있으면 소메뉴 기준)."""
    menu = (yaml.safe_load(menu_file.read_text(encoding="utf-8")) or {}).get("menu") or []
    linked, shown, parents = set(), set(), []
    for m in menu:
        if not isinstance(m, dict):
            continue
        on = m.get("visible", True) is not False
        for s in m.get("items") or []:
            if isinstance(s, dict):
                link = str(s.get("link") or "").strip()
                linked.add(link)
                if on and s.get("visible", True) is not False:
                    shown.add(link)
        parents.append((str(m.get("link") or "").strip(), on))
    for link, on in parents:
        if link and link not in linked:
            linked.add(link)
            if on:
                shown.add(link)
    linked.discard("")
    return linked, shown


def hidden_pages(site: Path, lang: str, menu_file: Path) -> tuple:
    """기존 자유 페이지(created 아님) 중 숨길 출력 경로 set, 메뉴에 아예 연결 안 된 파일 목록(규칙 적용 안 함, 보고용)."""
    folder = site / ("cms/en/free" if lang == "en" else "cms/free")
    prefix = "en/page/" if lang == "en" else "page/"
    linked, shown = menu_visibility(menu_file)
    hidden, unlinked = set(), []
    for f in sorted(folder.glob("*.md")) if folder.is_dir() else []:
        src = f.relative_to(site).as_posix()
        fm, _ = split_md(f.read_text(encoding="utf-8"), src)
        if fm.get("created") is True:
            continue   # 새 페이지는 created_pages 가 같은 기준으로 처리
        out = prefix + f.stem + ".html"
        if "/" + out not in linked:
            unlinked.append(src)
        elif "/" + out not in shown:
            hidden.add(out)
    return hidden, unlinked


# ───────── 새 페이지(created: true): 관리자 화면에서 만든 페이지 ─────────
# 파일 cms/free/<slug>.md(영문 cms/en/free/<slug>.md), 앞부분 title·path·editor_mode·created: true·hero_title·hero_desc·hero_image(선택).
# 틀 templates/free_page.html. menu.yml 에 visible: true 소메뉴로 연결된 것만 만든다(대메뉴도 visible). 옛 주소 대응표에는 넣지 않는다.
SLUG = re.compile(r"[a-z0-9_]+")
# 대메뉴 class → 기본 대표 이미지(기존 화면 CSS 의 대메뉴 이미지). 없는 대메뉴는 hero_image 가 없으면 사진 배경 없이 제목만
DEFAULT_HERO = {"menu_01": "theme/basic/images/sub/sub_01.jpg", "menu_04": "theme/basic/images/sub/sub_04.jpg",
                "menu_05": "theme/basic/images/sub/sub_05.jpg"}
# 사진 배경이 없을 때의 모양(기존 페이지와 같게): 제품·기술=제목+하위 탭, 탄소중립=경로 드롭다운+제목, 홍보센터=게시판 머리
PLAIN_SHAPE = {"menu_02": "title_tab", "menu_03": "title_drop", "menu_06": "board"}


def _text(v) -> str:
    """hero_title·hero_desc: 이스케이프, 줄바꿈 → <br>"""
    s = str(v or "").strip()
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    return "<br>\n".join(x.strip() for x in s.splitlines())


def created_pages(site: Path, lang: str, menu_file: Path, existing_outs: set) -> list:
    """새 페이지 목록 → [{out, slug, front, menu_cls, item_cls, src}]. 메뉴에 노출 연결이 없는 파일은 뺀다(만들지 않음)."""
    folder = site / ("cms/en/free" if lang == "en" else "cms/free")
    prefix = "en/page/" if lang == "en" else "page/"
    menu = yaml.safe_load(menu_file.read_text(encoding="utf-8")) or {}
    links = {}   # path → (대메뉴 class, 소메뉴 class), 노출된 것만
    for i, m in enumerate(menu.get("menu") or [], 1):
        if not isinstance(m, dict) or m.get("visible", True) is False:
            continue
        for j, s in enumerate(m.get("items") or [], 1):
            if isinstance(s, dict) and s.get("visible", True) is not False:
                links.setdefault(str(s.get("link") or "").strip(),
                                 (str(m.get("class") or f"menu_{i:02d}"), str(s.get("class") or f"sub_menu_{j:02d}")))
    pages = []
    for f in sorted(folder.glob("*.md")) if folder.is_dir() else []:
        src = f.relative_to(site).as_posix()
        fm, _ = split_md(f.read_text(encoding="utf-8"), src)
        if fm.get("created") is not True:
            continue
        slug, out = f.stem, prefix + f.stem + ".html"
        if not SLUG.fullmatch(slug):
            raise CmsPageError(f"{src}: 새 페이지 파일 이름(slug)은 영문 소문자·숫자·_ 만 쓸 수 있습니다 (현재: '{slug}')")
        if out in existing_outs or (site / "static" / prefix / slug).exists() or (site / "static" / out).exists():
            raise CmsPageError(f"{src}: '{slug}' 는 기존 페이지·폴더 이름과 겹칩니다. 다른 이름을 쓰세요.")
        if not str(fm.get("title") or "").strip():
            raise CmsPageError(f"{src}: title(페이지 제목)이 비어 있습니다.")
        if "/" + out not in links:
            continue   # 메뉴에 노출 연결이 없으면 만들지 않음(숨김 상태)
        menu_cls, item_cls = links["/" + out]
        pages.append({"out": out, "slug": slug, "front": fm, "menu_cls": menu_cls, "item_cls": item_cls, "src": src})
    return pages


def render_created(env, p: dict, lang: str, site: Path, public: Path, renames: dict) -> tuple:
    """새 페이지 하나 → (본문 HTML, body class, <title>)."""
    fm, src = p["front"], p["src"]
    hero = str(fm.get("hero_image") or "").strip()
    if hero:
        if not hero.startswith("/") or hero.startswith("//"):
            raise CmsPageError(f"{src}: hero_image 는 / 로 시작하는 사이트 안 주소여야 합니다 (현재: '{hero}')")
        rp = hero.lstrip("/").split("?")[0]
        if not (public / renames.get(rp, rp)).is_file():
            raise CmsPageError(f"{src}: hero_image 파일이 사이트에 없습니다: {hero}")
        hero = rp
    else:
        hero = DEFAULT_HERO.get(p["menu_cls"], "")
    shape = "photo" if hero else PLAIN_SHAPE.get(p["menu_cls"], "title_drop")
    title = _text(fm["title"]).replace("<br>\n", " ")
    body = env.get_template("free_page.html").render(
        lang=lang, shape=shape, title=title, hero_title=_text(fm.get("hero_title")), hero_desc=_text(fm.get("hero_desc")),
        hero_image="%%ROOT%%" + hero.replace("'", "%27"), body=load(site, p["out"]))
    n = re.sub(r"\D", "", p["menu_cls"])[-2:].zfill(2)
    k = re.sub(r"\D", "", p["item_cls"])[-2:].zfill(2)
    body_class = (f" pc sub sub_{n} sub_{n}_{k} sub file_{p['slug']} page "
                  f"lang_{'ko_KR' if lang == 'ko' else 'en_US'} b_tp")
    head = str(fm["title"]).strip()
    return body, body_class, (head if head.endswith("HANBIT Innotech") else f"{head} | HANBIT Innotech")
