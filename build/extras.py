"""
4-6: 메인 회사소식(D12), 팝업, 옛 주소 이동(404.html + redirects.json), sitemap.xml·robots.txt.
build.py가 불러 쓴다. 저장소 안의 파일(content/, static/)만 사용한다.
"""
import html as html_lib
import json
import re
from datetime import datetime, timezone, timedelta

import boards as B

KST = timezone(timedelta(hours=9))
NEWS_THUMB = (443, 243)
NEWS_TITLE_CUT, NEWS_TEXT_CUT = 15, 45   # 원본 메인 최신글 스킨: 제목 15자 + "…", 본문 45자 + "..."


# ───────── D12 메인 회사소식 4건 ─────────
def latest_notice(lang: str, posts: dict, site: "B.Site") -> str:
    table = "notice" if lang == "ko" else "notice_en"
    d = ("en/" if lang == "en" else "") + "board/notice/"
    out = ["\n                "]
    for p in posts["boards"][table][:4]:
        w, h = NEWS_THUMB
        srcs = [f["stored"] for f in sorted(p["files"], key=lambda f: f["no"]) if f["stored"].lower().endswith(B.IMG_EXT)]
        if not srcs:
            srcs = [s for s in (B.site_path(x) for x in re.findall(r'<img[^>]+src="([^"]+)"', p["content"])) if s]
        thumb = (site.thumb(srcs[0], w, h) or site.real(srcs[0])) if srcs else site.real("theme/basic/images/noimage.jpg")
        title = html_lib.escape(B.cut(html_lib.unescape(p["subject"]), NEWS_TITLE_CUT), quote=False)
        text = re.sub(r"<[^>]*>", "", p["content"])
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
        pages = max(1, -(-len(items) // cfg["page_rows"]))
        for loc in (None, "ko_KR", "en_US"):
            extra = {"locale": loc} if loc else {}
            add("/bbs/board.php", {"bo_table": table, **extra}, cfg["dir"] + "index.html")
            for n in range(1, pages + 1):
                add("/bbs/board.php", {"bo_table": table, "page": str(n), **extra}, cfg["dir"] + B.list_page(n))
            for p in items:
                add("/bbs/board.php", {"bo_table": table, "wr_id": str(p["id"]), **extra}, cfg["dir"] + f"{p['id']}.html")
        for p in items:
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
