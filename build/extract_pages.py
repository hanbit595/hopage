"""
수집본(crawl/)에서 공통 틀과 페이지 본문 조각을 1회 추출하고, 필요한 자산을 original/www에서 static/으로 복사한다.

- 이 스크립트는 내 PC에서만 실행한다(crawl/, original/는 저장소에 없음). 결과물(templates/, content/, static/)만 저장소에 올린다.
- crawl/, original/는 읽기만 한다.
- 4-1 범위: 국문 메인(base.html + content/pages/ko/index.html)

실행:  python build/extract_pages.py          (site/ 폴더에서)
"""
import hashlib
import html as html_lib
import json
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import urlparse, parse_qsl, unquote, urljoin

import requests

SITE = Path(__file__).resolve().parent.parent          # D:\homepage\site
HOME = SITE.parent                                      # D:\homepage
CRAWL = HOME / "crawl" / "pages"
WWW = HOME / "original" / "www"
TEMPLATES = SITE / "templates"
CONTENT = SITE / "content"
STATIC = SITE / "static"

LF = "\n"                   # 윈도에서도 줄바꿈을 LF로 저장
ROOT = "%%ROOT%%"           # 빌드 때 상대경로("", "../" 등)로 바뀜
LANG_KO = "%%LANG_KO%%"     # 빌드 때 국문판 주소로 바뀜
LANG_EN = "%%LANG_EN%%"     # 빌드 때 영문판 주소로 바뀜

# D4: 외부 GSAP 베타 파일은 사이트 안에 보관, 쓰지 않는 Swiper·MotionPathPlugin은 제거
GSAP_BETA_URL = "https://s3-us-west-2.amazonaws.com/s.cdpn.io/16327/gsap-latest-beta.min.js"
GSAP_BETA_LOCAL = "vendor/gsap-latest-beta.min.js"
REMOVE_SCRIPTS = (
    "https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/gsap/3.2.6/MotionPathPlugin.min.js",
)

HOST_RE = r"(?:https?:)?//(?:www\.)?hanbitinnotech\.com"
ASSET_EXT = r"png|jpe?g|gif|svg|webp|ico|mp4|mov|webm|pdf|css|js|woff2?|ttf|eot|otf|json|txt"
ASSET_RE = re.compile(
    rf"""(?P<q>["'(])\s*(?P<url>(?:{HOST_RE})?/(?!/)[^"'()\s<>]+?\.(?:{ASSET_EXT})(?:\?[^"'()\s<>]*)?)\s*(?=["')])""",
    re.I)
HREF_RE = re.compile(r"""(?P<attr>\bhref)=(?P<q>["'])(?P<url>[^"']*)(?P=q)""", re.I)

# original/www 파일의 실제 대소문자 (GitHub Pages는 대소문자를 구분한다)
REAL_CASE = {}
for _f in WWW.rglob("*"):
    if _f.is_file():
        REAL_CASE["/" + _f.relative_to(WWW).as_posix().lower()] = "/" + _f.relative_to(WWW).as_posix()

SENSITIVE = re.compile(r"^/data/(member|session|log|tmp|cache)/|dbconfig\.php$|\.php$|\.sql$|\.dump$", re.I)

assets_needed = set()     # 실제 경로(대소문자 보정)
assets_missing = {}       # 경로 -> 처음 발견 위치
report = {"removed_tags": [], "page_links": {}, "unmapped_links": set(), "css_fixes": []}


def real_path(path: str):
    return REAL_CASE.get(unquote(path).lower())


def map_asset(url: str, where: str):
    """자산 주소 → %%ROOT%% 상대경로. 원본에 없으면 None."""
    path = urlparse(url).path
    rp = real_path(path)
    if rp is None or SENSITIVE.search(rp):
        assets_missing.setdefault(unquote(path), where)
        return None
    assets_needed.add(rp)
    return ROOT + rp.lstrip("/")


def map_page(url: str, lang: str = "ko"):
    """페이지 링크 → 새 주소. 매핑 대상이 아니면 원래 값, 관리자 링크는 None."""
    if url.startswith(("#", "javascript:", "mailto:", "tel:")) or not url:
        return url
    url = html_lib.unescape(url)   # &amp; → &
    if url in ("?locale=ko_KR",):
        return LANG_KO
    if url in ("?locale=en_US",):
        return LANG_EN
    m = re.match(rf"^(?:{HOST_RE})?(/[^?#]*)?(\?[^#]*)?(#.*)?$", url, re.I)
    if not m or (url.startswith("http") and not re.match(HOST_RE, url, re.I)):
        return url  # 외부 링크
    path, query = m.group(1) or "/", dict(parse_qsl((m.group(2) or "")[1:]))
    # 원본은 언어를 세션으로 유지하므로 locale이 없으면 현재 페이지의 언어를 따른다
    en = query.get("locale", "en_US" if lang == "en" else "ko_KR") == "en_US"
    prefix = ROOT + ("en/" if en else "")
    if path.lower().startswith("/adm"):
        return None
    if path == "/" or path.lower() == "/index.php":
        return prefix + "index.html"
    pm = re.match(r"^/page/([\w-]+)\.php$", path, re.I)
    if pm:
        return prefix + f"page/{pm.group(1)}.html"
    if path.lower() == "/bbs/board.php" and "bo_table" in query:
        b = query["bo_table"]
        lang_prefix = ROOT + ("en/" if b.endswith("_en") else "")
        b = b[:-3] if b.endswith("_en") else b
        if "wr_id" in query:
            return lang_prefix + f"board/{b}/{query['wr_id']}.html"
        page = query.get("page", "1")
        return lang_prefix + f"board/{b}/" + ("index.html" if page == "1" else f"{page}.html")
    report["unmapped_links"].add(url)
    return url


def rewrite(html: str, where: str, lang: str = "ko") -> str:
    # 1) D4 외부 스크립트
    for src in REMOVE_SCRIPTS:
        html, n = re.subn(rf'\s*<script src="{re.escape(src)}"></script>', "", html)
        if n:
            report["removed_tags"].append(f"{where}: <script src=\"{src}\"> 제거 (D4, 사용 안 함)")
    html = html.replace(GSAP_BETA_URL, ROOT + GSAP_BETA_LOCAL)

    # 2) 원본에 없는 파일을 부르는 link/script/img 태그 제거 (D6)
    def drop_missing(m):
        tag = m.group(0)
        u = re.search(r'(?:href|src)="([^"]+)"', tag).group(1)
        if re.match(HOST_RE, u, re.I) or (u.startswith("/") and not u.startswith("//")):
            path = urlparse(u).path
            if real_path(path) is None:
                assets_missing.setdefault(unquote(path), where)
                report["removed_tags"].append(f"{where}: {tag.strip()} 제거 (D6, 원본 서버에도 없음)")
                return ""
        return tag
    html = re.sub(r'[ \t]*<link rel="stylesheet" href="[^"]+">\n?', drop_missing, html)
    html = re.sub(r'[ \t]*<script src="[^"]+"></script>\n?', drop_missing, html)

    # 3) 자산 주소 → 상대경로
    def asset_sub(m):
        new = map_asset(m.group("url"), where)
        return m.group("q") + (new if new else m.group("url"))
    html = ASSET_RE.sub(asset_sub, html)

    # 4) 페이지 링크 → 새 주소
    def href_sub(m):
        url = m.group("url")
        if url.startswith(ROOT):
            return m.group(0)
        new = map_page(url, lang)
        if new is None:
            report["page_links"][url] = "(관리자 링크 제거)"
            return ""  # href 속성 자체를 없앰
        if new != url:
            report["page_links"][url] = new
        return f'{m.group("attr")}={m.group("q")}{new}{m.group("q")}'
    html = HREF_RE.sub(href_sub, html)

    # 5) 남은 사이트 절대주소(전역 변수 등)
    html = re.sub(rf'var g5_url\s*= "{HOST_RE}";', 'var g5_url       = "";', html)
    html = re.sub(rf'"{HOST_RE}/bbs"', '"bbs"', html)
    html = re.sub(rf'"{HOST_RE}/theme/basic/shop"', '""', html)
    html = re.sub(rf'"{HOST_RE}/shop"', '""', html)
    return html


def split_page(html: str):
    """수집본 HTML → (head 안쪽, body class, 팝업, 상단, 본문, 하단 이후)."""
    head = html[html.index("<head>") + 6: html.index("</head>")]
    body_class = re.search(r'<body\s+class="([^"]*)"', html).group(1)
    top_s, top_e = html.index("<!-- 상단 시작 { -->"), html.index("<!-- } 상단 끝 -->") + len("<!-- } 상단 끝 -->")
    foot_s = html.index("<!-- 하단 시작 { -->")
    top = html[top_s:top_e]
    popup = ""
    p_s, p_e = top.find("<!-- 팝업레이어 시작 { -->"), top.find("<!-- } 팝업레이어 끝 -->")
    if p_s >= 0:
        p_e += len("<!-- } 팝업레이어 끝 -->")
        if top[p_s - 1] == "\n":   # 팝업이 있는 메인에만 있는 빈 줄도 팝업 조각에 포함
            p_s -= 1
        popup, top = top[p_s:p_e], top[:p_s] + "{{ popup_html }}" + top[p_e:]
    body = html[top_e:foot_s]
    tail = html[foot_s: html.rindex("</body>")]
    return head, body_class, popup, top, body, tail


BASE_HTML = (
    "<!doctype html>\n<html lang=\"{{ html_lang }}\" class=\"sok\">\n"
    "<head>{% include \"_head_\" ~ lang ~ \".html\" %}</head>\n"
    "<body  class=\"{{ body_class }}\">\n\n<div id=\"wrap\">\n"
    "{% include \"_top_\" ~ lang ~ \".html\" %}\n"
    "{% block content %}{% endblock %}\n"
    "{% include \"_tail_\" ~ lang ~ \".html\" %}{% block body_end %}{% endblock %}\n</body>\n</html>\n")


def make_partials(head: str, top: str, tail: str):
    """언어별 공통 틀 조각(_head, _top, _tail). base.html이 언어에 맞는 조각을 불러온다."""
    # 페이지마다 바뀌는 메타 정보를 변수로
    head = re.sub(r'<link rel="canonical" href="[^"]*">', '<link rel="canonical" href="{{ canonical }}">', head)
    head = re.sub(r'<meta property="og:url" content="[^"]*">', '<meta property="og:url" content="{{ canonical }}">', head)
    head = re.sub(r'<meta property="og:locale" content="[^"]*">', '<meta property="og:locale" content="{{ og_locale }}">', head)
    head = re.sub(r'<title>[^<]*</title>', '<title>{{ title }}</title>', head)
    head = re.sub(r'(<meta (?:name="title" itemprop="name"|property="og:title") content=")[^"]*(">)', r'\1{{ title }}\2', head)
    head = re.sub(r'(<meta (?:name="description" itemprop="description"|property="og:description") content=")[^"]*(">)',
                  r'\1{{ description }}\2', head)
    # og:image는 절대주소여야 하므로 최종 도메인 기준으로
    head = re.sub(r'(<meta property="og:image" content=")%%ROOT%%([^"]*")', r'\1{{ site_url }}\2', head)
    # 페이지별 CSS 자리: 메인은 main_news/style.css, 게시판은 스킨 style.css가 원본에서 같은 위치에 들어간다
    head = re.sub(r"\{% if is_main %\}(.*?)\{% endif %\}", "{{ page_css }}", head)
    # 게시판에서만 값이 있는 전역 변수
    head = head.replace('var g5_bo_table  = "";', 'var g5_bo_table  = "{{ g5_bo_table }}";')
    head = head.replace('var g5_editor    = "";', 'var g5_editor    = "{{ g5_editor }}";')
    # 게시판 머리(게시판 제목·하위 메뉴)는 상단 끝 표시 바로 앞, 게시판을 감싸는 닫는 태그는 하단 시작 바로 뒤
    i = top.rindex("<!-- } 상단 끝 -->")
    top = top[:i] + "{{ board_head }}" + top[i:]
    tail = tail.replace("<!-- 하단 시작 { -->\n", "<!-- 하단 시작 { -->\n{{ board_close }}", 1)
    # KOR/ENG 표시(active)는 언어별 상단 조각에 원본 그대로 들어 있다. 링크 주소만 빌드 때 상대 언어판으로 바뀐다
    return head, top, tail


def fetch_gsap_beta():
    dst = STATIC / GSAP_BETA_LOCAL
    if dst.exists():
        return hashlib.sha256(dst.read_bytes()).hexdigest()
    r = requests.get(GSAP_BETA_URL, timeout=30)
    r.raise_for_status()
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(r.content)
    return hashlib.sha256(r.content).hexdigest()


CSS_URL = re.compile(r"""url\(\s*['"]?([^'")]+?)['"]?\s*\)""", re.I)
CSS_IMPORT = re.compile(r"""@import\s+(?:url\()?['"]([^'"]+)['"]""", re.I)
JS_PATH = re.compile(rf"""["']((?:{HOST_RE})?/?(?:theme|data|img|js|css)/[^"'\s]+?\.(?:{ASSET_EXT}))["']""", re.I)


def copy_assets():
    """필요한 자산을 static/으로 복사. CSS 안의 url()과 JS 안의 경로도 따라간다."""
    done, copied, size = set(), [], 0
    queue = sorted(assets_needed)
    while queue:
        rp = queue.pop()
        if rp in done:
            continue
        done.add(rp)
        src, dst = WWW / rp.lstrip("/"), STATIC / rp.lstrip("/")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied.append(rp)
        size += src.stat().st_size
        ext = src.suffix.lower()
        if ext not in (".css", ".js"):
            continue
        text = src.read_bytes().decode("utf-8", errors="ignore")   # 줄바꿈 그대로
        refs = (CSS_URL.findall(text) + CSS_IMPORT.findall(text)) if ext == ".css" else []
        refs += [m for m in JS_PATH.findall(text)]
        if ext == ".css":
            # D6: 원본 서버에도 없는 이미지를 부르는 url()은 none으로 (글꼴은 다른 형식이 있으면 그쪽을 쓰므로 그대로 둠)
            def drop(m):
                ref = m.group(1).strip()
                if (ref.startswith(("data:", "http", "//")) or re.search(r"\.(woff2?|ttf|eot|otf)(\?|#|$)", ref, re.I)
                        or re.search(r"\.svg(\?[^#]*)?#", ref, re.I)):   # SVG 글꼴(@font-face)
                    return m.group(0)
                if real_path(urlparse(urljoin("http://x" + rp, ref)).path) is None:
                    report["css_fixes"].append(f"{rp}: url({ref}) → none (D6)")
                    return "none"
                return m.group(0)
            patched = CSS_URL.sub(drop, text)
            if patched != text:
                dst.write_text(patched, encoding="utf-8", newline="")   # 원본 줄바꿈 유지
        for ref in refs:
            ref = ref.strip()
            if ref.startswith(("data:", "#", "about:")) or (ref.startswith("http") and not re.match(HOST_RE, ref, re.I)):
                continue
            base = "http://x" + rp if ext == ".css" else "http://x/"   # CSS는 파일 위치 기준, JS는 사이트 루트 기준
            path = urlparse(urljoin(base, re.sub(HOST_RE, "", ref, flags=re.I))).path
            real = real_path(path)
            if real is None:
                assets_missing.setdefault(unquote(path), f"{rp} 안의 참조")
            elif not SENSITIVE.search(real) and real not in done:
                queue.append(real)
    return copied, size


# D2: 메인 '주요 프로젝트' 카드(원본에서 삭제된 시공사례 글 번호를 가리킴) → 새 연결
D2_LINKS = {
    "ko": {"board/media/2.html": "board/media/62.html",      # 구포초
           "board/media/5.html": "board/media/48.html",      # 경산정수장
           "board/media/3.html": "board/media/52.html",      # 대전둔곡초
           "board/media/1.html": "board/media/index.html",   # 에코유치원 → 시공사례 목록
           "board/media/7.html": "board/media/index.html"},  # 경기도청 → 시공사례 목록
    # 영문 메인 카드도 국문 media 글을 가리킴 → D1과 같은 원칙으로 영문 시공사례 목록
    "en": {f"board/media/{n}.html": "en/board/media/index.html" for n in (1, 2, 3, 5, 7)},
}

VAR_HEAD = re.compile(r'<link rel="canonical"|<meta property="og:url"')
EXCLUDED_PAGES = {"bipv_pdt"}   # D5: 메뉴에 없는 페이지 제외


def strip_active(s: str) -> str:
    """상단 메뉴의 현재 페이지 표시(active)를 지운 형태. 공통 틀 비교용."""
    return re.sub(r'class="((?:menu|sub_menu)[^"]*?) ?active"', lambda m: f'class="{m.group(1)} "', s)


def active_target(top: str):
    """수집본 상단에서 현재 페이지로 표시된 소메뉴 링크(변환 후 주소)."""
    m = re.search(r'<a href="([^"]+)" class="sub_menu_a active"', top)
    return m.group(1) if m else None


def head_lines(head: str):
    return [l for l in head.splitlines() if l.strip()]


STATIC_KEEP = {"hb", "vendor"}   # static/ 안에서 직접 만든 파일(자체 JS·CSS, D4 보관 파일). 나머지는 매번 원본에서 다시 복사


def clean_static():
    """static/을 비우고 다시 채운다(직접 만든 hb/, vendor/는 남김). 이후 optimize.py를 다시 실행해야 한다."""
    if STATIC.exists():
        for p in STATIC.iterdir():
            if p.name in STATIC_KEEP:
                continue
            shutil.rmtree(p) if p.is_dir() else p.unlink()


def main():
    clean_static()
    TEMPLATES.mkdir(parents=True, exist_ok=True)
    (TEMPLATES / "base.html").write_text(BASE_HTML, encoding="utf-8", newline=LF)
    (TEMPLATES / "page.html").write_text(
        "{% extends \"base.html\" %}\n"
        "{% block content %}{{ content_html }}{% endblock %}\n", encoding="utf-8", newline=LF)
    meta_file = CONTENT / "pages" / "meta.json"
    meta = json.loads(meta_file.read_text(encoding="utf-8")) if meta_file.exists() else {}
    common_problems, extracted = [], []

    for lang, lang_name in (("ko", "국문"), ("en", "영문")):
        # 대상: 메인 + 고정 페이지(D5 제외). 출력: 국문 /, 영문 /en/
        pre = "" if lang == "ko" else "en/"
        sources = [(f"{lang}/index", CRAWL / lang / "index.html", pre + "index.html")]
        for f in sorted((CRAWL / lang / "page").glob("*.html")):
            if f.stem not in EXCLUDED_PAGES:
                sources.append((f"{lang}/page/{f.stem}", f, f"{pre}page/{f.stem}.html"))

        parsed = {}
        for key, src, out in sources:
            head, body_class, popup, top, body, tail = split_page(src.read_text(encoding="utf-8"))
            where = f"{lang_name} " + ("메인" if key.endswith("/index") else out)
            parsed[key] = dict(out=out, body_class=body_class,
                               head=rewrite(head, f"{where} head", lang), top=rewrite(top, f"{where} 상단", lang),
                               tail=rewrite(tail, f"{where} 하단", lang), body=rewrite(body, f"{where} 본문", lang),
                               popup=rewrite(popup, f"{where} 팝업", lang) if popup else "")

        # 공통 틀: 그 언어의 메인 기준. 고정 페이지 상단·하단이 메인과 같은지(active 제외) 확인
        main_p = parsed[f"{lang}/index"]
        for key, p in parsed.items():
            if strip_active(p["top"]).replace("{{ popup_html }}", "") != strip_active(main_p["top"]).replace("{{ popup_html }}", ""):
                common_problems.append(f"{key}: 상단이 메인과 다름")
            if p["tail"] != main_p["tail"]:
                common_problems.append(f"{key}: 하단이 메인과 다름")

        # head: 메인에만 있는 줄(main_news/style.css 등)은 제자리에 조건부로 둔다
        sub_heads = [set(head_lines(p["head"])) for k, p in parsed.items() if k != f"{lang}/index"]
        sub_common = set.intersection(*sub_heads) if sub_heads else set()
        base_head, main_only = [], []
        for l in main_p["head"].splitlines():
            if l.strip() and not VAR_HEAD.match(l.strip()) and sub_heads and l not in sub_common:
                base_head.append("{% if is_main %}" + l + "{% endif %}")   # make_partials에서 {{ page_css }}로 바뀜
                main_only.append(l)
            else:
                base_head.append(l)
        if len(main_only) != 1:
            common_problems.append(f"{lang}: 메인에만 있는 head 줄이 {len(main_only)}개(1개여야 page_css 자리로 처리 가능)")

        # D2: 메인 '주요 프로젝트' 카드의 깨진 링크
        for old, new in D2_LINKS[lang].items():
            main_p["body"] = main_p["body"].replace(f'href="{ROOT}{old}"', f'href="{ROOT}{new}"')
        # D12: 메인 회사소식 4건은 빌드 때 posts.json 최신 글로 만든다 → 자리 표시만 남김
        m = re.search(r'(<section[^>]*id="section_05"[\s\S]*?<div class="NewsList">)([\s\S]*?)(\n            </div>\n        </div>\n    </section>)',
                      main_p["body"])
        if m:
            main_p["body"] = main_p["body"][:m.start(2)] + "%%LATEST_NOTICE%%" + main_p["body"][m.end(2):]
        else:
            common_problems.append(f"{lang}: 메인 회사소식 영역을 찾지 못함(D12)")
        # 4-6: 팝업은 빌드 때 posts.json(팝업 데이터)으로 만든다
        main_p["popup"] = ""
        for key, p in parsed.items():
            extra = [l for l in head_lines(p["head"]) if l not in main_p["head"].splitlines() and not VAR_HEAD.match(l.strip())]
            if extra:
                common_problems.append(f"{key}: head에 메인에 없는 줄 {len(extra)}개 → {extra[:2]}")

        head_text = "\n".join(base_head) + ("\n" if main_p["head"].endswith("\n") else "")   # </head> 앞 줄바꿈 유지
        head_t, top_t, tail_t = make_partials(head_text, strip_active(main_p["top"]), main_p["tail"])
        for part, text in (("_head", head_t), ("_top", top_t), ("_tail", tail_t)):
            (TEMPLATES / f"{part}_{lang}.html").write_text(text, encoding="utf-8", newline=LF)

        for key, p in parsed.items():
            rel_content = key + ".html"
            dst = CONTENT / "pages" / rel_content
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(p["body"].strip("\n") + "\n", encoding="utf-8", newline=LF)
            popup_rel = None
            if p["popup"]:
                popup_rel = key.rsplit("/", 1)[0] + "/_popup.html"
                (CONTENT / "pages" / popup_rel).write_text(p["popup"], encoding="utf-8", newline=LF)   # 원본처럼 뒤 줄바꿈 없음
            title = re.search(r"<title>([^<]*)</title>", p["head"]).group(1)
            desc = re.search(r'<meta name="description" itemprop="description" content="([^"]*)">', p["head"]).group(1)
            plain = p["out"][3:] if lang == "en" else p["out"]
            meta[key] = {
                "lang": lang, "out": p["out"], "content": rel_content, "popup": popup_rel,
                "title": title, "description": desc, "body_class": p["body_class"],
                "is_main": key.endswith("/index"),
                "page_css": main_only[0] if key.endswith("/index") and main_only else "",
                "active": active_target(p["top"]),          # 상단 메뉴에서 현재 페이지로 표시할 소메뉴 링크
                "pair": ("en/" + plain) if lang == "ko" else plain,   # D1: 같은 페이지의 상대 언어판
            }
        extracted += [p["out"] for p in parsed.values()]
    meta_file.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8", newline=LF)

    # 게시판(4-4): 게시판 머리·설정·숫자 기록, 게시판 화면이 쓰는 이미지·첨부를 자산 목록에 올림
    from extract_boards import extract_boards
    common_problems += extract_boards(sys.modules[__name__])

    sha = fetch_gsap_beta()
    copied, size = copy_assets()

    # 결과 보고
    print(f"공통 틀: base.html + _head/_top/_tail_(ko|en).html")
    print(f"페이지 {len(extracted)}개 추출")
    print("공통 틀 점검:", "문제 없음(상단은 active 표시만, 하단은 동일)" if not common_problems else "")
    for c in common_problems:
        print("  -", c)
    print("현재 페이지 표시 없는 고정 페이지:", [k for k, m in meta.items() if "/page/" in k and not m["active"]] or "없음")
    print(f"D4: {GSAP_BETA_URL} → static/{GSAP_BETA_LOCAL} (sha256 {sha[:16]}…)")
    print(f"자산 복사: {len(copied)}개, {size / 1024 / 1024:.1f}MB → static/")
    print(f"제거한 태그 {len(report['removed_tags'])}개:")
    for t in report["removed_tags"]:
        print("  -", t)
    print(f"CSS 안의 없는 파일 참조 정리 {len(report['css_fixes'])}개:")
    for t in report["css_fixes"]:
        print("  -", t)
    print(f"원본에 없는 참조 {len(assets_missing)}개:")
    for p, w in sorted(assets_missing.items()):
        print(f"  - {p}  ({w})")
    print(f"바뀐 페이지 링크 {len(report['page_links'])}개:")
    for a, b in sorted(report["page_links"].items()):
        print(f"  - {a} → {b}")
    if report["unmapped_links"]:
        print("매핑하지 않은 링크:", *sorted(report["unmapped_links"]), sep="\n  - ")
    leftovers = set()
    for f in [TEMPLATES / "base.html"] + list((CONTENT / "pages").rglob("*.html")):
        leftovers |= set(re.findall(rf"{HOST_RE}[^\"'\s<>)]*", f.read_text(encoding="utf-8"), re.I))
    print("남은 사이트 절대주소:", sorted(leftovers) or "없음")


if __name__ == "__main__":
    sys.exit(main())
