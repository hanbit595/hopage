"""
전체 빌드: templates/ + content/ + static/ → public/

- 저장소 안의 파일만 사용한다(crawl/, original/ 불필요). GitHub Actions에서도 그대로 실행된다.
- 모든 링크·이미지는 상대경로로 만든다(임시 주소 /hopage/와 최종 도메인 양쪽에서 동작).

실행:  python build/build.py          (site/ 폴더에서)
미리보기: python -m http.server 8000 -d public
"""
import json
import posixpath
import re
import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

import boards
import extras
from datetime import datetime

SITE = Path(__file__).resolve().parent.parent
TEMPLATES = SITE / "templates"
CONTENT = SITE / "content"
STATIC = SITE / "static"
PUBLIC = SITE / "public"
SITE_URL = "https://hanbitinnotech.com/"   # canonical·og:image·sitemap용 최종 도메인
TEMP_BASES = ["/hopage/"]                  # 임시 주소(GitHub Pages 프로젝트 주소)의 시작 경로. 404.html이 이 경로를 떼고 옛 주소를 찾는다


def root_of(out: str) -> str:
    """public/ 기준 출력 경로 → 사이트 루트까지의 상대경로 ("", "../", "../../")."""
    depth = out.count("/")
    return "../" * depth


def rel(from_out: str, to_out: str) -> str:
    return posixpath.relpath(to_out, posixpath.dirname(from_out) or ".")


def apply_active(html: str, target: str) -> str:
    """상단 메뉴(PC·모바일)에서 target 소메뉴와 그 대메뉴에 원본과 같은 방식으로 active를 붙인다."""
    if not target:
        return html
    start, end = html.find('<div class="header_all_wrap">'), html.find("<!-- } 상단 끝 -->")
    region = html[start:end]
    chunks = re.split(r'(?=<div class="menu menu_\d+ ">)', region)
    # 원본 메뉴에는 '<a ... class="sub_menu_a " >'처럼 > 앞에 공백이 있는 링크도 있다(E-Catalog)
    link = re.escape(f'<a href="{target}" class="sub_menu_a "') + r"(\s*)>"
    for i, c in enumerate(chunks):
        if not re.search(link, c):
            continue
        c = re.sub(r'^<div class="menu (menu_\d+) ">', r'<div class="menu \1 active">', c, count=1)
        c = c.replace('class="menu_a void_link "', 'class="menu_a void_link active"', 1)
        c = re.sub(r'<div class="sub_menu (sub_menu_\d+) ">(\s*)' + link,
                   lambda m: f'<div class="sub_menu {m.group(1)} active">{m.group(2)}<a href="{target}" class="sub_menu_a active"{m.group(3)}>', c)
        chunks[i] = c
    return html[:start] + "".join(chunks) + html[end:]


def main():
    if PUBLIC.exists():
        shutil.rmtree(PUBLIC)
    PUBLIC.mkdir()

    # 1) 정적 파일 복사 (static/ 구조 그대로). 확대본으로 대신하는 새 글 원본(optimize.py가 기록)은 공개하지 않는다
    ex_file = CONTENT / "publish_exclude.json"
    exclude = {e.lower() for e in json.loads(ex_file.read_text(encoding="utf-8"))} if ex_file.exists() else set()

    def ignore(d, names):
        rel = Path(d).relative_to(STATIC).as_posix()
        return [n for n in names if (f"{rel}/{n}" if rel != "." else n).lower() in exclude]
    shutil.copytree(STATIC, PUBLIC, dirs_exist_ok=True, ignore=ignore)

    # 2) 페이지 렌더링
    env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=False, undefined=StrictUndefined,
                      keep_trailing_newline=True)
    meta = json.loads((CONTENT / "pages" / "meta.json").read_text(encoding="utf-8"))
    desc = {lang: meta[f"{lang}/index"]["description"] for lang in ("ko", "en")}

    rn_file = CONTENT / "renames.json"   # optimize.py가 바꾼 파일 이름(PNG→JPG, MOV→MP4)
    renames = json.loads(rn_file.read_text(encoding="utf-8")) if rn_file.exists() else {}

    def write(out, html, lang, pair, active):
        """공통 후처리: 현재 메뉴 표시, KOR/ENG 주소(D1), 바뀐 파일 이름, 상대경로."""
        ko_out, en_out = (out, pair) if lang == "ko" else (pair, out)
        html = apply_active(html, active)
        if out == "index.html":
            # 옛 영문 메인 주소(/?locale=en_US)는 없는 주소가 아니라서 404.html을 거치지 않는다 → 국문 메인에서 바로 영문 메인으로
            html = html.replace("<head>", "<head>\n<script>if(/[?&]locale=en_US(&|$)/.test(location.search))"
                                          "location.replace('en/index.html');</script>", 1)
        for old, new in renames.items():
            html = html.replace("%%ROOT%%" + old, "%%ROOT%%" + new)
        html = (html.replace("%%LANG_KO%%", rel(out, ko_out))
                    .replace("%%LANG_EN%%", rel(out, en_out))
                    .replace("%%ROOT%%", root_of(out)))
        dst = PUBLIC / out
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(html, encoding="utf-8", newline="\n")   # 윈도에서도 LF

    def common(lang, out, title, body_class):
        return dict(lang=lang, html_lang=lang, og_locale="ko_KR" if lang == "ko" else "en_US",
                    title=title, description=desc[lang], body_class=body_class,
                    canonical=SITE_URL + ("" if out == "index.html" else out), site_url=SITE_URL,
                    popup_html="", page_css="", g5_bo_table="", g5_editor="", board_head="", board_close="")

    posts = json.loads((CONTENT / "posts.json").read_text(encoding="utf-8"))
    site = boards.Site(STATIC)
    now = datetime.now(extras.KST)
    sitemap_urls = []

    # 2-1) 메인·고정 페이지
    tpl = env.get_template("page.html")
    for key, m in meta.items():
        out = m["out"]
        ctx = common(m["lang"], out, m["title"], m["body_class"])
        content_html = (CONTENT / "pages" / m["content"]).read_text(encoding="utf-8")
        if "%%LATEST_NOTICE%%" in content_html:   # D12: 메인 회사소식 = posts.json 최신 글 4건
            content_html = content_html.replace("%%LATEST_NOTICE%%", extras.latest_notice(m["lang"], posts, site))
        ctx.update(description=m["description"], page_css=m.get("page_css", ""), content_html=content_html,
                   popup_html=extras.popup_html(posts, site, now) if m.get("is_main") else "")
        write(out, tpl.render(**ctx), m["lang"], m["pair"], m.get("active"))
        sitemap_urls.append((out, None))
    print(f"  메인·고정 페이지 {len(meta)}개")

    # 2-2) 게시판 목록·글 (content/posts.json)
    n_list = n_view = 0
    dates = {f"{b}:{p['id']}": p["datetime"][:10] for b, v in posts["boards"].items() for p in v}
    for out, tname, ctx, pm in boards.build_pages(CONTENT, STATIC, env):
        if tname is None:   # 검색용 목록 JSON
            (PUBLIC / out).parent.mkdir(parents=True, exist_ok=True)
            (PUBLIC / out).write_text(json.dumps(ctx, ensure_ascii=False), encoding="utf-8")
            continue
        full = common(ctx["lang"], out, pm["title"], pm["body_class"])
        full.update(ctx)
        write(out, env.get_template(tname).render(**full), ctx["lang"], ctx["pair"], ctx["active"])
        n_list += tname == "board_list.html"
        n_view += tname == "board_view.html"
        wr = out.rsplit("/", 1)[1][:-5]
        sitemap_urls.append((out, dates.get(f"{ctx['g5_bo_table']}:{wr}") if wr.isdigit() else None))
    print(f"  게시판 목록 {n_list}쪽, 글 {n_view}건")

    # 3) 옛 주소 이동(404.html + redirects.json), sitemap.xml, robots.txt
    boards_cfg = json.loads((CONTENT / "boards.json").read_text(encoding="utf-8"))
    red = extras.redirects(meta, boards_cfg, posts)
    red_json = json.dumps(red, ensure_ascii=False, indent=0, sort_keys=True)
    (CONTENT / "redirects.json").write_text(red_json, encoding="utf-8", newline="\n")   # 옛 주소 대응표(기록용, 빌드마다 새로 만듦)
    (PUBLIC / "redirects.json").write_text(json.dumps(red, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (PUBLIC / "404.html").write_text(env.get_template("404.html").render(bases=json.dumps(TEMP_BASES)),
                                     encoding="utf-8", newline="\n")
    (PUBLIC / "sitemap.xml").write_text(extras.sitemap(sitemap_urls, SITE_URL), encoding="utf-8", newline="\n")
    (PUBLIC / "robots.txt").write_text(extras.robots(SITE_URL), encoding="utf-8", newline="\n")
    print(f"  옛 주소 대응 {len(red)}건, sitemap {len(sitemap_urls)}개 주소")

    files = [f for f in PUBLIC.rglob("*") if f.is_file()]
    size = sum(f.stat().st_size for f in files)
    print(f"완료: public/ 파일 {len(files)}개, {size / 1024 / 1024:.1f}MB")


if __name__ == "__main__":
    main()
