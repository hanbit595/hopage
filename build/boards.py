"""
게시판 빌드 (build.py가 불러 씀). 저장소 안의 파일만 사용한다.

입력
- content/posts.json           : 게시글(DB 추출). 글을 고치거나 더할 때는 이 파일만 고치면 된다
- content/boards.json          : 게시판 설정(extract_boards.py가 만듦)
- content/board_snapshot.json  : 원본 화면에 찍혀 있던 조회수·다운로드 수·연결 수(고정값). 없는 글은 0으로 표시
- static/                      : 이미지(축소본 thumb-*·원본)와 첨부

원본(그누보드5)이 화면에 낼 때 하던 처리를 똑같이 한다
- 본문 정리(HTML Purifier와 같은 규칙): id·data-*·contenteditable 속성 삭제, button 태그 삭제(글자는 남김),
  허용되지 않는 CSS 속성 삭제, !important 삭제, 잘못된 주소의 링크는 href 삭제
- 본문 이미지: 축소본(thumb-*_1400x*)이 있으면 축소본을 보여 주고 확대 보기 링크(view_image)를 건다. 없으면 원본 그대로
- 목록 썸네일: 첫 번째 이미지 첨부 → 없으면 본문 첫 이미지의 축소본(좌측 900x600, 우측 420x280)
"""
import html as html_lib
import json
import posixpath
import re
from pathlib import Path

LABELS = {
    "ko": {"writer": "작성자", "date": "작성일", "views": "조회수", "search_placeholder": "검색어를 입력해주세요",
           "link_cnt": "{}회 연결", "list_label": "회사소식"},
    "en": {"writer": "Writer", "date": "Date", "views": "Views", "search_placeholder": "Please enter",
           "link_cnt": "{}회 연결", "list_label": "Notice"},
}
CUT_VIEW_SUBJECT = 70   # 글 화면 머리의 제목은 70자에서 자르고 … (원본 스킨 그대로)
CUT_LIST_SUBJECT = 60   # 목록 제목은 60자


def cut(text: str, n: int) -> str:
    return text if len(text) <= n else text[:n] + "…"


def list_page(n: int) -> str:
    """목록 쪽 파일 이름. 2쪽부터 page-2.html (글 번호 파일 2.html과 겹치지 않게)."""
    return "index.html" if n == 1 else f"page-{n}.html"
IMG_EXT = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp")
VIEW_THUMB_W = 1400
LIST_THUMB = {"left": (900, 600), "right": (420, 280)}
WRITE_PAGES = 10   # 페이지 번호를 한 번에 몇 개 보일지(원본 설정)

# HTML Purifier 기본 CSS 허용 목록(원본 화면에서 남은 속성 15개 포함)
ALLOWED_CSS = {
    "background", "background-color", "background-image", "background-repeat", "background-attachment", "background-position",
    "border", "border-collapse", "border-spacing", "border-color", "border-style", "border-width",
    "border-top", "border-right", "border-bottom", "border-left",
    *(f"border-{s}-{p}" for s in ("top", "right", "bottom", "left") for p in ("color", "style", "width")),
    "caption-side", "clear", "color", "empty-cells", "float", "font", "font-family", "font-size", "font-style",
    "font-variant", "font-weight", "height", "letter-spacing", "line-height", "list-style", "list-style-image",
    "list-style-position", "list-style-type", "margin", "margin-top", "margin-right", "margin-bottom", "margin-left",
    "padding", "padding-top", "padding-right", "padding-bottom", "padding-left", "table-layout", "text-align",
    "text-decoration", "text-indent", "text-transform", "vertical-align", "width", "word-spacing",
}
HOST = re.compile(r"^(?:https?:)?//(?:www\.)?hanbitinnotech\.com", re.I)
TAG = re.compile(r"<(/?)([a-zA-Z][a-zA-Z0-9]*)(\s[^<>]*?)?(/?)>", re.S)
ATTR = re.compile(r"""([^\s=/>]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+)))?""")


# ───────── 본문 정리 ─────────
def clean_css(style: str) -> str:
    out = []
    for decl in re.split(r";(?![^(]*\))", style):
        if ":" not in decl:
            continue
        prop, val = decl.split(":", 1)
        prop = prop.strip().lower()
        if prop not in ALLOWED_CSS:
            continue
        val = re.sub(r"\s*!\s*important\s*$", "", val.strip(), flags=re.I)
        if prop == "font-family":
            val = ", ".join(f.strip() for f in val.split(",") if "\\" not in f)
        if val:
            out.append(f"{prop}:{val};")
    return "".join(out)


def valid_url(u: str) -> bool:
    m = re.match(r"^(https?)://([^/?#]*)", u, re.I)
    if not m:
        return True   # 상대주소·mailto 등은 그대로
    return bool(re.fullmatch(r"[A-Za-z0-9.\-]+(:\d+)?", m.group(2)))


def purify(content: str) -> str:
    def tag_sub(m):
        close, name, attrs, selfc = m.group(1), m.group(2).lower(), m.group(3) or "", m.group(4)
        if name == "button":
            return ""
        if close or not attrs.strip():
            return m.group(0)
        kept, changed = [], False
        pairs = [(a.group(1), next((g for g in a.groups()[1:] if g is not None), None)) for a in ATTR.finditer(attrs)]
        for k, v in pairs:
            kl = k.lower()
            if kl in ("id", "contenteditable", "draggable") or kl.startswith(("data-", "on")):
                changed = True
                continue
            if kl == "style" and v is not None:
                nv = clean_css(html_lib.unescape(v))
                if nv != v:
                    changed = True
                if not nv:
                    continue
                v = html_lib.escape(nv, quote=True)
            if name == "a" and kl == "href" and v is not None and not valid_url(html_lib.unescape(v)):
                changed = True   # 잘못된 주소는 href만 지움(target은 남음)
                continue
            if name == "a" and kl == "target" and (v or "").lower() != "_blank":
                changed = True   # 허용된 target은 _blank뿐
                continue
            if name == "a" and kl == "rel":
                changed = True   # rel은 아래에서 원본 규칙대로 다시 붙임
                continue
            kept.append((k, v))
        if name == "a":
            rel = []
            href = next((v for k, v in kept if k.lower() == "href"), None)
            if href and re.match(r"^(https?:)?//", html_lib.unescape(href)) and not HOST.match(html_lib.unescape(href)):
                rel.append("nofollow")   # 외부 링크(HTML.Nofollow)
            if any(k.lower() == "target" and (v or "").lower() == "_blank" for k, v in kept):
                rel += ["noreferrer", "noopener"]   # 새 창 링크
            if rel:
                kept.append(("rel", " ".join(rel)))
                changed = True
        if not changed:
            return m.group(0)
        body = "".join(f' {k}="{v}"' if v is not None else f" {k}" for k, v in kept)
        return f"<{name}{body}{' /' if selfc else ''}>"
    return TAG.sub(tag_sub, content)


# ───────── 주소·이미지 ─────────
class Site:
    def __init__(self, static: Path):
        self.files = {}
        for f in static.rglob("*"):
            if f.is_file():
                rel = f.relative_to(static).as_posix()
                self.files[rel.lower()] = rel
        rn = static.parent / "content" / "renames.json"   # optimize.py가 바꾼 파일 이름(PNG→JPG, MOV→MP4)
        self.renames = {k.lower(): v for k, v in json.loads(rn.read_text(encoding="utf-8")).items()} if rn.exists() else {}

    def real(self, path: str):
        key = path.lstrip("/").lower()
        key = self.renames.get(key, key).lower()
        return self.files.get(key)

    def large(self, path: str):
        """확대 보기용 확대본(optimize.py가 만든 large-{이름}.jpg). 없으면 원본."""
        d, name = posixpath.split(path.lstrip("/"))
        return self.files.get(f"{d}/large-{name.rsplit('.', 1)[0]}.jpg".lower()) or self.real(path)

    def thumb(self, path: str, w: int, h: int = None):
        """원본 경로 → 같은 폴더의 thumb-{이름}_{w}x{h}.* (있으면 실제 경로)."""
        d, name = posixpath.split(path.lstrip("/"))
        stem = name.rsplit(".", 1)[0]
        pat = re.compile(re.escape(f"{d}/thumb-{stem}_{w}x").lower() + (str(h) if h else r"\d+") + r"\.\w+$")
        for k, v in self.files.items():
            if pat.match(k):
                return v
        return None


def site_path(u: str):
    """사이트 안 주소면 경로(/data/...) 반환."""
    u = html_lib.unescape(u)
    if HOST.match(u):
        return re.sub(HOST, "", u) or "/"
    if u.startswith("/") and not u.startswith("//"):
        return u
    return None


def map_link(u: str, root: str) -> str:
    """본문 안의 사이트 링크 → 새 주소(설계서 3장)."""
    p = site_path(u)
    if p is None:
        return u
    m = re.match(r"^/page/([\w-]+)\.php", p)
    if m:
        return f"{root}page/{m.group(1)}.html"
    m = re.match(r"^/bbs/board\.php\?(.*)$", p)
    if m:
        q = dict(x.split("=", 1) for x in m.group(1).split("&") if "=" in x)
        b = q.get("bo_table", "")
        pre = "en/" if b.endswith("_en") else ""
        b = b[:-3] if b.endswith("_en") else b
        return f"{root}{pre}board/{b}/" + (f"{q['wr_id']}.html" if "wr_id" in q else "index.html")
    if p == "/":
        return f"{root}index.html"
    return root + p.lstrip("/")


def render_content(content: str, site: Site, root: str) -> str:
    content = purify(content)

    def img_sub(m):
        tag = m.group(0)
        src = re.search(r'\ssrc\s*=\s*"([^"]*)"', tag)
        if not src:
            return tag
        p = site_path(src.group(1))
        if p is None:
            return tag
        name = posixpath.basename(p)
        th = site.thumb(p, VIEW_THUMB_W)
        real = site.real(p) or (site.large(p) if th else None)
        if th:
            return (f'<a href="{root}{site.large(p)}" target="_blank" class="view_image">'
                    f'<img src="{root}{th}" alt="{html_lib.escape(name)}"/></a>')
        tag = tag.replace(src.group(0), f' src="{root}{real or p.lstrip("/")}"')
        if not re.search(r"\salt\s*=", tag):
            tag = re.sub(r"\s*/?>$", f' alt="{html_lib.escape(name)}" />', tag)
        return tag
    content = re.sub(r"<img\b[^>]*>", img_sub, content, flags=re.I)
    # 남은 사이트 절대주소(링크 등) → 상대경로
    content = re.sub(r'(\shref\s*=\s*")([^"]*)(")', lambda m: m.group(1) + map_link(m.group(2), root) + m.group(3), content)
    return content


def file_size(n: int) -> str:
    if n >= 1048576:
        return f"{n / 1048576:,.1f}M"
    if n >= 1024:
        return f"{n / 1024:,.1f}K"
    return f"{n:,}byte"


def youtube_embed(link: str):
    m = re.search(r"(?:youtu\.be/|youtube\.com/(?:watch\?v=|embed/|shorts/))([\w-]{6,})", link)
    if not m:
        return None
    return (f"https://www.youtube.com/embed/{m.group(1)}?theme=light&amp;iv_load_policy=3&amp;controls=1&amp;rel=0"
            "&amp;modestbranding=1&amp;fs=1&amp;showinfo=0&amp;autohide=0")


def paging(cur: int, total: int) -> str:
    """원본(get_paging)과 같은 페이지 번호 마크업. 쪽 주소: 1쪽 index.html, 2쪽부터 n.html."""
    if total <= 1:
        return ""
    href = list_page
    s = []
    if cur > 1:
        s.append(f'<a href="{href(1)}" class="pg_page pg_start">처음</a>\n')
    start = (cur - 1) // WRITE_PAGES * WRITE_PAGES + 1
    end = min(start + WRITE_PAGES - 1, total)
    if start > 1:
        s.append(f'<a href="{href(start - 1)}" class="pg_page pg_prev">이전</a>\n')
    for k in range(start, end + 1):
        if k == cur:
            s.append(f'<span class="sound_only">열린</span><strong class="pg_current">{k}</strong><span class="sound_only">페이지</span>\n')
        else:
            s.append(f'<a href="{href(k)}" class="pg_page">{k}<span class="sound_only">페이지</span></a>\n')
    if total > end:
        s.append(f'<a href="{href(end + 1)}" class="pg_page pg_next">다음</a>\n')
    if cur < total:
        s.append(f'<a href="{href(total)}" class="pg_page pg_end">맨끝</a>\n')
    return '<nav class="pg_wrap"><span class="pg">' + "".join(s) + "</span></nav>"


def list_thumb(post, table, site: Site, which: str):
    w, h = LIST_THUMB[which]
    srcs = [f["stored"] for f in sorted(post["files"], key=lambda f: f["no"]) if f["stored"].lower().endswith(IMG_EXT)]
    if not srcs:
        srcs = [site_path(s) for s in re.findall(r'<img[^>]+src="([^"]+)"', post["content"])]
        srcs = [s for s in srcs if s]
    if not srcs:
        return site.real("theme/basic/images/noimage.jpg")   # 이미지 없는 글: 원본 스킨의 대체 이미지
    th = site.thumb(srcs[0], w, h)
    return th or site.real(srcs[0])


# ───────── 페이지 만들기 ─────────
def build_pages(content_dir: Path, static_dir: Path, templates):
    """게시판 목록·글 페이지 정보 목록을 돌려준다: (출력 경로, 템플릿 이름, 템플릿 변수, 페이지 정보)."""
    posts = json.loads((content_dir / "posts.json").read_text(encoding="utf-8"))
    boards = json.loads((content_dir / "boards.json").read_text(encoding="utf-8"))
    snap = json.loads((content_dir / "board_snapshot.json").read_text(encoding="utf-8"))
    site = Site(static_dir)
    out = []
    for table, cfg in boards.items():
        lang, d = cfg["lang"], cfg["dir"]
        labels = LABELS[lang]
        head = templates.loader.get_source(templates, f"_board_head_{lang}.html")[0]
        items = posts["boards"][table]
        common = dict(lang=lang, page_css=cfg["skin_css"], g5_bo_table=table, g5_editor=cfg["editor"],
                      board_head=head, board_close=cfg["close"], active=cfg["active"], pair=cfg["pair_dir"] + "index.html",
                      board=cfg, labels=labels)
        root = "../" * d.count("/")   # 게시판 폴더 깊이(board/x/ → ../../)

        # 목록 쪽
        per = cfg["page_rows"]
        total = max(1, -(-len(items) // per))
        index = []
        for p in items:
            index.append({"id": p["id"], "subject": html_lib.unescape(p["subject"]), "date": p["datetime"][:10],
                          "href": f"{p['id']}.html",
                          "thumb_left": (lambda t: t and root + t)(list_thumb(p, table, site, "left")),
                          "thumb_right": (lambda t: t and root + t)(list_thumb(p, table, site, "right"))})
        for n in range(1, total + 1):
            chunk = index[(n - 1) * per: n * per]
            mk = lambda it, side: {"href": it["href"], "subject": html_lib.escape(cut(it["subject"], CUT_LIST_SUBJECT), quote=False),
                                   "date": it["date"], "thumb": it[f"thumb_{side}"].replace(root, "%%ROOT%%", 1) if it[f"thumb_{side}"] else None}
            left = mk(chunk[0], "left") if chunk else None
            right = [mk(it, "right") for it in chunk[1:]]
            o = d + list_page(n)
            out.append((o, "board_list.html", dict(common, page=n, left=left, right=right, paging=paging(n, total)),
                        dict(title=cfg["list_title"], body_class=cfg["body_class_list"])))
        # 검색용 목록(JS 제목 검색)
        out.append((d + "search.json", None,
                    [{"href": i["href"], "subject": i["subject"], "date": i["date"],
                      "left": i["thumb_left"], "right": i["thumb_right"]} for i in index], None))   # 썸네일은 게시판 폴더 기준 상대경로

        # 글
        for i, p in enumerate(items):
            s = snap.get(f"{table}:{p['id']}", {})
            dt = p["datetime"]
            nav = lambda q: q and {"href": f"{q['id']}.html", "subject": html_lib.escape(html_lib.unescape(q["subject"]), quote=False),
                                   "date": f"{q['datetime'][2:4]}.{q['datetime'][5:7]}.{q['datetime'][8:10]}"}
            file_images, downloads = [], []
            snap_files = iter(s.get("files", []))
            for f in sorted(p["files"], key=lambda f: f["no"]):
                stored = f["stored"]
                if stored.lower().endswith(IMG_EXT):
                    large = site.large(stored) or stored.lstrip("/")
                    th = site.thumb(stored, VIEW_THUMB_W) or large
                    file_images.append({"large": "%%ROOT%%" + large, "thumb": "%%ROOT%%" + th})
                else:
                    sf = next(snap_files, {})
                    ext = posixpath.splitext(stored)[1].lower()
                    downloads.append({"href": f"%%ROOT%%files/{cfg['slug']}/{p['id']}-{f['no']}{ext}",
                                      "name": html_lib.escape(f["source"]), "size": file_size(f["size"]),
                                      "count": sf.get("download", "0"), "date": sf.get("date", dt)})
            links = []
            snap_links = iter(s.get("links", []))
            for lk in (p.get("link1"), p.get("link2")):
                if lk:
                    links.append({"href": html_lib.escape(lk), "text": html_lib.escape(lk),
                                  "count": next(snap_links, labels["link_cnt"].format(0))})
            embed = next((youtube_embed(lk) for lk in (p.get("link1"), p.get("link2")) if lk and youtube_embed(lk)), None)
            post = {
                "subject": html_lib.escape(cut(html_lib.unescape(p["subject"]), CUT_VIEW_SUBJECT), quote=False),
                "view_date": f"{dt[2:4]}-{dt[5:7]}-{dt[8:10]} {dt[11:16]}",
                "hit": s.get("hit", "0"),
                "content_html": render_content(p["content"], site, "%%ROOT%%"),
                "file_images": file_images, "downloads": downloads, "links": links, "embed": embed,
                "prev": nav(items[i - 1] if i > 0 else None), "next": nav(items[i + 1] if i + 1 < len(items) else None),
            }
            title = html_lib.unescape(p["subject"]) + html_lib.unescape(cfg["view_title_suffix"])
            out.append((d + f"{p['id']}.html", "board_view.html", dict(common, post=post),
                        dict(title=html_lib.escape(title, quote=True), body_class=cfg["body_class_view"])))
    return out
