"""
4-6: 메인 회사소식(D12), 메인 Our Project(P3-4b), 팝업, 옛 주소 이동(404.html + redirects.json), sitemap.xml·robots.txt.
build.py가 불러 쓴다. 저장소 안의 파일만 사용한다. 게시글(posts)은 build.py 가 cms_posts.load_posts() 로 읽어 넘긴다.
"""
import html as html_lib
import json
import re
from datetime import datetime, timezone, timedelta

import boards as B

KST = timezone(timedelta(hours=9))
NEWS_THUMB = (443, 243)
NEWS_TITLE_CUT, NEWS_TEXT_CUT = 15, 45   # 원본 메인 최신글 스킨: 제목 15자 + "…", 본문 45자 + "..."


# ───────── D12 메인 회사소식 4건 (한글: cms/notice 최신 4건, draft 제외) ─────────
def latest_notice(lang: str, posts: dict, site: "B.Site") -> str:
    table = "notice" if lang == "ko" else "notice_en"
    d = ("en/" if lang == "en" else "") + "board/notice/"
    out = ["\n                "]
    for p in posts["boards"][table][:4]:
        w, h = NEWS_THUMB
        t = B.post_thumb_src(p)   # 관리자 화면 thumbnail 칸이 1순위(P3-4b)
        srcs = [t] if t and site.real(t) else [f["stored"] for f in sorted(p["files"], key=lambda f: f["no"]) if f["stored"].lower().endswith(B.IMG_EXT)]
        if not srcs:
            srcs = [s for s in (B.site_path(x) for x in re.findall(r'<img[^>]+src="([^"]+)"', p["content"])) if s]
        thumb = (site.thumb(srcs[0], w, h) or site.real(srcs[0])) if srcs else site.real("theme/basic/images/noimage.jpg")
        title = html_lib.escape(B.cut(html_lib.unescape(p["subject"]), NEWS_TITLE_CUT), quote=False)
        # 요약: summary 칸(있으면, 글자 이스케이프) → 없으면 지금처럼 본문에서 태그를 뺀 앞부분
        text = html_lib.escape(" ".join(p["summary"].split()), quote=False) if p.get("summary") else re.sub(r"<[^>]*>", "", p["content"])
        text = text if len(text) <= NEWS_TEXT_CUT else text[:NEWS_TEXT_CUT] + "..."
        out.append(f"""
    <div class="m_b_ns_box">
        <a href="%%ROOT%%{d}{p['id']}.html" class="m_b_ns_box_a">

            <div class="m_b_ns_thumb">
                <img
                    src="%%ROOT%%{thumb}"
                    alt=""
                    loading="lazy"
                    width="443"
                    height="243"
                >
            </div>

            <div class="m_b_ns_box_in">
                <div class="m_b_ns_title sec_tit2 bold700">
                    {title}                </div>

                <div class="sssgap"></div>

                <div class="m_b_ns_content sec_txt">
                    {text}                </div>
            </div>

        </a>
    </div>""")
    return "".join(out)


# ───────── 메인 Our Project (P3-4b): 시공사례 featured 글 → 카드 ─────────
# 카드 틀은 10칸(5열 2줄, 작은 화면 4·3·2열). 01·02 는 큰 화면에서 소개 글 자리, 06·10 은 디자인상 빈 칸이라 늘 비운다.
# 카드 칸은 6개. 채우는 순서 04 → 07 → 08 → 09 → 03 → 05: 지금 카드 4장이 원래 자리(04·07·08·09)를 지키고,
# 5·6번째 카드는 D17 로 비운 03·05 자리에 들어간다. featured 글이 6건보다 많으면 앞의 6건만 쓴다.
PROJECT_CELLS = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10"]
PROJECT_SLOTS = ["04", "07", "08", "09", "03", "05"]
# 칸 class 에 CSS(layout.css)로 붙어 있는 배경 이미지. 카드 이미지가 이것과 같으면 style 을 쓰지 않는다(기존 마크업 유지)
PROJECT_CSS_BG = {s: f"theme/basic/images/main/mainProject_bg_{s}.jpg" for s in ("04", "07", "08", "09")}
PROJECT_IMG = (900, 600)
PROJECT_TAG = {"태양광발전장치": "PV", "BIPV": "BIPV"}


def featured_projects(posts: dict) -> list:
    """featured 글: featured_order 작은 숫자 먼저, featured_order 없는 글은 그 뒤에 date 최신순."""
    items = [p for p in posts["boards"]["media"] if p.get("featured")]
    with_order = sorted((p for p in items if p["featured_order"] is not None), key=lambda p: p["featured_order"])
    no_order = [p for p in items if p["featured_order"] is None]   # 이미 date 최신순으로 정렬돼 있음
    return with_order + no_order


def project_image(p: dict, site: "B.Site"):
    """카드 이미지: featured_image → thumbnail → 기존 규칙(첨부 이미지 → 본문 첫 이미지). 사이트 루트 기준 경로."""
    for cand in (p.get("featured_image"), p.get("thumbnail")):
        sp = B.site_path(cand) if cand else None
        if sp and site.real(sp):
            if sp.lstrip("/").lower().startswith("theme/"):
                return site.real(sp)   # 디자인 이미지(기존 카드 배경)는 그대로
            return site.thumb(sp, *PROJECT_IMG) or site.thumb(sp, B.VIEW_THUMB_W) or site.real(sp)
        if cand:
            print(f"  주의: {p['_src']} 카드 이미지가 사이트에 없습니다: {cand}")
    srcs = [f["stored"] for f in sorted(p["files"], key=lambda f: f["no"]) if f["stored"].lower().endswith(B.IMG_EXT)]
    srcs = srcs or [s for s in (B.site_path(x) for x in re.findall(r'<img[^>]+src="([^"]+)"', p["content"])) if s]
    if not srcs:
        return None
    return site.thumb(srcs[0], *PROJECT_IMG) or site.thumb(srcs[0], B.VIEW_THUMB_W) or site.real(srcs[0])


def our_project(posts: dict, site: "B.Site") -> str:
    """<ul class="mainProject_list"> 안의 10칸. content/pages/ko/index.html 의 %%OUR_PROJECT%% 자리에 들어간다."""
    cards = featured_projects(posts)
    if len(cards) > len(PROJECT_SLOTS):
        print(f"  주의: 메인 Our Project 는 {len(PROJECT_SLOTS)}칸입니다. featured 글 {len(cards)}건 중 앞의 "
              f"{len(PROJECT_SLOTS)}건만 표시합니다(featured_order 로 순서 조정).")
    by_slot = dict(zip(PROJECT_SLOTS, cards))
    out = []
    for cell in PROJECT_CELLS:
        p = by_slot.get(cell)
        if p is None:
            out.append(f'                <li class="mainProject_item item_{cell}"></li>\n')
            continue
        img = project_image(p, site)
        style = ""
        if img and img.lower() != PROJECT_CSS_BG.get(cell, "").lower():
            style = f' style="background-image:url(&#39;%%ROOT%%{html_lib.escape(img)}&#39;)"'
        # 분류·문구: 기존 글은 featured_label·featured_text(이전 전 카드 글자 그대로), 새 글은 category·title·capacity 로 만듦
        tag = p.get("featured_label") or html_lib.escape("/".join(PROJECT_TAG.get(c, c) for c in p["category"]), quote=False)
        text = p.get("featured_text") or (html_lib.escape(p["title"], quote=False)
                                         + (f" <br>{html_lib.escape(p['capacity'], quote=False)}" if p["capacity"] else ""))
        out.append(f"""                <li class="mainProject_item item_{cell}">
                    <a href="%%ROOT%%board/media/{p['id']}.html" class="mainProject_item_a">
                            <div class="bg"{style}></div>
                        <div class="on">
                            <div class="tit">{tag}</div>
                            <div class="txt">{text}</div>
                        </div>
                    </a>
                </li>\n""")
    return "".join(out)


# ───────── 팝업 ─────────
POPUP_HOURS = 24   # "24시간 동안 다시 열람하지 않습니다"


def popup_html(popups: list) -> str:
    """원본(그누보드 팝업레이어)과 같은 마크업. popups 는 build.py load_popups() 가 검사·정리한 active 팝업 목록.
    게시 기간은 빌드 때 거르지 않고 data-begin/data-end 로 넣어 브라우저가 판단한다(hb/popup.js, 한국 시간 기준).
    '시간 동안 다시 열람하지 않습니다'는 쿠키 대신 localStorage. 팝업이 0개여도 틀과 스크립트는 그대로 둔다(오류 없음)."""
    items = []
    for p in popups:
        img = f'<img src="{p["src"]}" title="{p["name"]}" alt="{p["name"]}" />'
        if p["href"]:
            img = f'<a href="{p["href"]}">{img}</a>'
        content = f'<p>{img}<br style="clear:both;">&nbsp;</p>'
        items.append(f"""
    <div id="hd_pops_{p['id']}" class="hd_pops" style="top:{p['top']}px;left:{p['left']}px" data-begin="{p['begin']}" data-end="{p['end']}">
        <div class="hd_pops_con" style="width:{p['width']}px;height:{p['height']}px">
            {content}        </div>
        <div class="hd_pops_footer">
            <button class="hd_pops_reject hd_pops_{p['id']} {POPUP_HOURS}"><strong>{POPUP_HOURS}</strong>시간 동안 다시 열람하지 않습니다.</button>
            <button class="hd_pops_close hd_pops_{p['id']}">닫기 <i class="fa fa-times" aria-hidden="true"></i></button>
        </div>
    </div>""")
    return popup_wrap(items)


def popup_wrap(items: list) -> str:
    return ("\n\n<!-- 팝업레이어 시작 { -->\n<div id=\"hd_pop\">\n    <h2>팝업레이어 알림</h2>\n\n"
            + "".join(items) + "\n</div>\n\n<script src=\"%%ROOT%%hb/popup.js\"></script>\n<!-- } 팝업레이어 끝 -->")


def popup_html_en(posts: dict, site: "B.Site", build_time: datetime) -> str:
    """영문 메인 팝업: 1차 범위 밖이라 기존 방식 그대로(content/posts.json popups, 빌드 시점에 끝난 팝업 제외)."""
    items = []
    for p in posts.get("popups", []):
        end = datetime.strptime(p["end"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=KST)
        if end < build_time:
            continue
        content = B.render_content(p["content"], site, "%%ROOT%%")
        items.append(f"""
    <div id="hd_pops_{p['id']}" class="hd_pops" style="top:{p['top']}px;left:{p['left']}px" data-begin="{p['begin']}" data-end="{p['end']}">
        <div class="hd_pops_con" style="width:{p['width']}px;height:{p['height']}px">
            {content}        </div>
        <div class="hd_pops_footer">
            <button class="hd_pops_reject hd_pops_{p['id']} {p['disable_hours']}"><strong>{p['disable_hours']}</strong>시간 동안 다시 열람하지 않습니다.</button>
            <button class="hd_pops_close hd_pops_{p['id']}">닫기 <i class="fa fa-times" aria-hidden="true"></i></button>
        </div>
    </div>""")
    return popup_wrap(items)


# ───────── 옛 주소 → 새 주소 ─────────
def redirects(meta: dict, boards_cfg: dict, posts: dict) -> dict:
    """옛 주소(경로?정리된 쿼리) → 새 주소(사이트 루트 기준 상대경로). 404.html이 이 표로 이동한다."""
    r = {}

    def add(path, params, to):
        q = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        r[path + ("?" + q if q else "")] = to

    for lang, loc in (("ko", "ko_KR"), ("en", "en_US")):
        pre = "" if lang == "ko" else "en/"
        for path in ("/", "/index.php"):
            add(path, {"locale": loc}, pre + "index.html")
        for m in meta.values():
            if m["lang"] == lang and "/page/" in "/" + m["out"]:
                name = m["out"].rsplit("/", 1)[1][:-5]
                add(f"/page/{name}.php", {"locale": loc}, m["out"])
                if lang == "ko":
                    add(f"/page/{name}.php", {}, m["out"])
        add("/page/bipv_pdt.php", {"locale": loc}, pre + "index.html")   # D5: 제외된 페이지
    add("/", {}, "index.html")
    add("/index.php", {}, "index.html")
    add("/page/bipv_pdt.php", {}, "index.html")
    for table, cfg in boards_cfg.items():
        items = posts["boards"][table]
        old = [p for p in items if isinstance(p["id"], int)]   # 기존 글번호 글만(새 글 YYYYMMDD-HHMMSS 는 옛 주소가 없음)
        pages = max(1, -(-len(items) // cfg["page_rows"]))
        for loc in (None, "ko_KR", "en_US"):
            extra = {"locale": loc} if loc else {}
            add("/bbs/board.php", {"bo_table": table, **extra}, cfg["dir"] + "index.html")
            for n in range(1, pages + 1):
                add("/bbs/board.php", {"bo_table": table, "page": str(n), **extra}, cfg["dir"] + B.list_page(n))
            for p in old:
                add("/bbs/board.php", {"bo_table": table, "wr_id": str(p["id"]), **extra}, cfg["dir"] + f"{p['id']}.html")
        for p in old:
            for f in p["files"]:
                if not f["stored"].lower().endswith(B.IMG_EXT):
                    ext = f["stored"].rsplit(".", 1)[-1].lower()
                    add("/bbs/download.php", {"bo_table": table, "wr_id": str(p["id"]), "no": str(f["no"])},
                        f"files/{cfg['slug']}/{p['id']}-{f['no']}.{ext}")
    return r


# ───────── sitemap.xml ─────────
def sitemap(urls, site_url: str) -> str:
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for out, lastmod in urls:
        loc = site_url + ("" if out == "index.html" else out)
        lines.append(f"  <url><loc>{html_lib.escape(loc)}</loc>" + (f"<lastmod>{lastmod}</lastmod>" if lastmod else "") + "</url>")
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def robots(site_url: str) -> str:
    return f"User-agent: *\nAllow: /\n\nSitemap: {site_url}sitemap.xml\n"
