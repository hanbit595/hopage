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
import sys
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

import boards
import cms_posts
import extras
import uploads
from datetime import date, datetime

SITE = Path(__file__).resolve().parent.parent
TEMPLATES = SITE / "templates"
CONTENT = SITE / "content"
STATIC = SITE / "static"
PUBLIC = SITE / "public"
UPLOADS = SITE / "uploads"   # 관리자 화면 업로드 이미지(원본, 읽기만). 빌드 때 줄여서 public/uploads/ 로
SITE_URL = "https://hanbitinnotech.com/"   # canonical·og:image·sitemap용 최종 도메인
TEMP_BASES = ["/hopage/"]                  # 임시 주소(GitHub Pages 프로젝트 주소)의 시작 경로. 404.html이 이 경로를 떼고 옛 주소를 찾는다
MENU_YML = SITE / "cms" / "settings" / "menu.yml"   # 한글 메뉴 원본(관리자 화면에서 고침)
MENU_SLOT = re.compile(r"%%MENU_KO:(\w+)%%")         # 템플릿·본문 조각의 한글 메뉴 자리표시
MENU_FORMS = {"mega", "mobile", "drop_main", "drop_sub", "subtab"}
SITE_YML = SITE / "cms" / "settings" / "site.yml"       # 회사정보·기본설정(한글 푸터, 게시판 쪽당 글 수, 메인 설명문)
POPUPS_YML = SITE / "cms" / "settings" / "popups.yml"   # 한글 메인 팝업
FOOTER_SLOT = "%%FOOTER_KO%%"                           # _tail_ko.html·메인 본문의 한글 푸터 자리표시
POPUP_DEFAULTS = {"width": 450, "height": 660, "top": 150, "left": 10}


class BuildError(Exception):
    """한국어 메시지로 빌드를 멈춘다(종료코드 1)."""


BUILD_ERRORS = (BuildError, cms_posts.CmsError)


def esc(s) -> str:
    """메뉴 글자·주소 이스케이프. '&' 뒤가 공백이면 그대로 둔다(기존 '제품 & 기술' 표기 유지, 엔티티가 될 수 없음)."""
    s = str(s)
    s = re.sub(r"&(?!\s)", "&amp;", s)
    return s.replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def load_menu():
    """cms/settings/menu.yml → (노출 메뉴 목록, 검사할 내부 주소 목록). 형식이 틀리면 BuildError."""
    try:
        data = yaml.safe_load(MENU_YML.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise BuildError(f"메뉴 파일이 없습니다: {MENU_YML.relative_to(SITE).as_posix()}")
    except yaml.YAMLError as e:
        raise BuildError(f"menu.yml 형식 오류: {e}")
    if not isinstance(data, dict) or not isinstance(data.get("menu"), list):
        raise BuildError("menu.yml 에 menu: 목록이 없습니다.")

    def href(link, where):
        link = str(link or "").strip()
        if link.startswith("/") and not link.startswith("//"):
            return "%%ROOT%%" + link.lstrip("/"), link
        if re.match(r"^https?://", link):
            return link, None
        raise BuildError(f"menu.yml {where}: link 는 / 또는 http 로 시작해야 합니다 (현재: '{link}')")

    menus, internal = [], []
    for i, m in enumerate(data["menu"], 1):
        if not isinstance(m, dict) or not str(m.get("label") or "").strip():
            raise BuildError(f"menu.yml {i}번째 대메뉴: label 이 없습니다.")
        name = f"대메뉴 '{m['label']}'"
        if m.get("visible", True) is False:
            continue
        items = []
        for j, s in enumerate(m.get("items") or [], 1):
            if not isinstance(s, dict) or not str(s.get("label") or "").strip():
                raise BuildError(f"menu.yml {name}의 {j}번째 소메뉴: label 이 없습니다.")
            if s.get("visible", True) is False:
                continue
            where = f"{name} > 소메뉴 '{s['label']}'"
            h, inner = href(s.get("link"), where)
            if inner:
                internal.append((inner, where))
            items.append({"label": str(s["label"]).strip(), "href": h, "new_window": bool(s.get("new_window")),
                          "cls": str(s.get("class") or f"sub_menu_{j:02d}")})
        if str(m.get("link") or "").strip():
            h, inner = href(m["link"], name)
            if inner:
                internal.append((inner, name))
        elif items:
            h = items[0]["href"]   # 비우면 첫 번째 노출 소메뉴로
        else:
            raise BuildError(f"menu.yml {name}: link 가 비어 있고 노출된 소메뉴도 없습니다.")
        menus.append({"label": str(m["label"]).strip(), "href": h, "cls": str(m.get("class") or f"menu_{i:02d}"),
                      "items": items})
    return menus, internal


def read_yml(path: Path, key: str):
    """설정 YAML 을 읽어 최상위 dict 를 돌려준다. 파일 없음·형식 오류는 BuildError."""
    name = path.relative_to(SITE).as_posix()
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise BuildError(f"설정 파일이 없습니다: {name}")
    except yaml.YAMLError as e:
        raise BuildError(f"{path.name} 형식 오류: {e}")
    except ValueError as e:   # YAML 이 날짜로 읽다가 실패(예: 2026-02-30)
        raise BuildError(f"{path.name} 날짜 형식 오류(없는 날짜): {e}")
    if not isinstance(data, dict) or key not in data:
        raise BuildError(f"{path.name} 에 {key}: 항목이 없습니다.")
    return data


def site_link(link, where, required=True):
    """/로 시작 → (%%ROOT%%경로, 검사할 내부 주소), http(s) → (주소, None), 빈 값 → ("", None)."""
    link = str(link or "").strip()
    if not link and not required:
        return "", None
    if link.startswith("/") and not link.startswith("//"):
        return "%%ROOT%%" + link.lstrip("/"), link
    if re.match(r"^https?://", link):
        return esc(link), None
    raise BuildError(f"{where}: 주소는 / 또는 http 로 시작해야 합니다 (현재: '{link}')")


def load_site():
    """cms/settings/site.yml → (푸터 템플릿 변수, 게시판 쪽당 글 수, 메인 설명문, 검사할 내부 주소 목록)."""
    d = read_yml(SITE_YML, "offices")

    def text(k):
        v = d.get(k)
        if not isinstance(v, (str, int)) or not str(v).strip():
            raise BuildError(f"site.yml: {k} 가 비어 있습니다.")
        return str(v).strip()
    if not isinstance(d["offices"], list) or not d["offices"]:
        raise BuildError("site.yml: offices 목록이 비어 있습니다.")
    offices = []
    for i, o in enumerate(d["offices"], 1):
        if not isinstance(o, dict) or not str(o.get("name") or "").strip() or not str(o.get("address") or "").strip():
            raise BuildError(f"site.yml: offices {i}번째 항목에 name·address 가 모두 있어야 합니다.")
        name = str(o["name"]).strip()
        offices.append({"name": esc(name), "address": esc(str(o["address"]).strip()),
                        "comment": name.replace("--", "-").replace(">", "")})
    brochure, inner = site_link(d.get("brochure"), "site.yml brochure")
    per = d.get("per_page")
    if isinstance(per, bool) or not isinstance(per, int) or per < 1:
        raise BuildError(f"site.yml: per_page 는 1 이상의 숫자여야 합니다 (현재: '{per}')")
    footer = {"offices": offices, "tel": esc(text("tel")), "email": esc(text("email")), "brochure": brochure}
    links = [(inner, "site.yml brochure")] if inner else []
    return footer, per, esc(text("seo_description")), links


def load_popups():
    """cms/settings/popups.yml → (HTML 에 넣을 active 팝업 목록, 검사할 내부 주소 목록).
    날짜 형식 오류, start > end, active 팝업의 image 누락은 BuildError. 기간 비교는 브라우저가 한다."""
    d = read_yml(POPUPS_YML, "popups")
    items = d["popups"] or []
    if not isinstance(items, list):
        raise BuildError("popups.yml: popups 는 목록이어야 합니다.")

    def day(v, where):
        if isinstance(v, datetime):
            v = v.date()
        if isinstance(v, date):
            return v
        try:
            if isinstance(v, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", v.strip()):
                return date.fromisoformat(v.strip())
        except ValueError:
            pass
        raise BuildError(f"popups.yml {where}: 날짜 형식 오류 (YYYY-MM-DD 로 적어야 합니다, 현재: '{v}')")

    out, links, ids = [], [], set()
    for i, p in enumerate(items, 1):
        if not isinstance(p, dict):
            raise BuildError(f"popups.yml {i}번째 팝업: 형식이 잘못되었습니다.")
        where = f"{i}번째 팝업 '{p.get('title') or ''}'"
        start, end = day(p.get("start"), where + " start"), day(p.get("end"), where + " end")
        if start > end:
            raise BuildError(f"popups.yml {where}: 시작일(start {start})이 종료일(end {end})보다 늦습니다.")
        pid = p.get("id", i) if p.get("id") not in (None, "") else i
        if isinstance(pid, bool) or not isinstance(pid, int) or pid < 1:
            raise BuildError(f"popups.yml {where}: id 는 1 이상의 숫자여야 합니다 (현재: '{pid}')")
        if pid in ids:
            raise BuildError(f"popups.yml {where}: id {pid} 가 다른 팝업과 겹칩니다.")
        ids.add(pid)
        if p.get("active", True) is False:
            continue   # active: false → HTML 에 넣지 않음
        if not str(p.get("image") or "").strip():
            raise BuildError(f"popups.yml {where}: 노출(active) 팝업에 image 가 없습니다.")
        src, inner = site_link(p["image"], f"popups.yml {where} image")
        if inner:
            links.append((inner, f"popups.yml {where} image"))
        href, inner = site_link(p.get("link"), f"popups.yml {where} link", required=False)
        if inner:
            links.append((inner, f"popups.yml {where} link"))
        size = {}
        for k, dv in POPUP_DEFAULTS.items():
            v = p.get(k, dv) if p.get(k) not in (None, "") else dv
            if isinstance(v, bool) or not isinstance(v, int) or v < 0:
                raise BuildError(f"popups.yml {where}: {k} 는 0 이상의 숫자여야 합니다 (현재: '{v}')")
            size[k] = v
        out.append(dict(size, id=pid, src=src, href=href, name=esc(posixpath.basename(str(p["image"]).strip())),
                        begin=f"{start.isoformat()} 00:00:00", end=f"{end.isoformat()} 23:59:59"))
    return out, links


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
    # 1-1) 관리자 화면 업로드 이미지: 긴 변 1920px 이하로 줄여 public/uploads/ 에(P3-4b). 축소본은 필요할 때 만든다
    up = uploads.Uploads(UPLOADS, PUBLIC / "uploads")
    up.process()
    boards.Site.uploads = up

    # 2) 페이지 렌더링
    env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=False, undefined=StrictUndefined,
                      keep_trailing_newline=True)
    env.filters["esc"] = esc
    menus, menu_links = load_menu()
    footer_vars, per_page_ko, seo_desc_ko, site_links = load_site()
    popups, popup_links = load_popups()
    now = datetime.now(extras.KST)
    # 한글 푸터(P3-3): site.yml 값 + 빌드 시점 연도. 템플릿 끝 줄바꿈은 자리표시 자리에 없던 것이라 뗀다
    footer_ko = env.get_template("_footer_ko.html").render(year=now.year, **footer_vars).rstrip("\n")
    menu_macro = env.get_template("_menu_ko.html").module.menu_set
    menu_cache = {}

    def fill_menu(html, active, out):
        """%%MENU_KO:형태%% → menu.yml 로 그린 한글 메뉴(현재 페이지 active 포함)."""
        def sub(m):
            if m.group(1) not in MENU_FORMS:
                raise BuildError(f"{out}: 알 수 없는 메뉴 형태 %%MENU_KO:{m.group(1)}%%")
            if active not in menu_cache:
                menu_cache[active] = str(menu_macro(menus, active))
            return menu_cache[active]
        return MENU_SLOT.sub(sub, html)
    meta = json.loads((CONTENT / "pages" / "meta.json").read_text(encoding="utf-8"))
    desc = {lang: meta[f"{lang}/index"]["description"] for lang in ("ko", "en")}
    desc["ko"] = seo_desc_ko   # 한글 메인·게시판 설명문은 site.yml seo_description

    rn_file = CONTENT / "renames.json"   # optimize.py가 바꾼 파일 이름(PNG→JPG, MOV→MP4)
    renames = json.loads(rn_file.read_text(encoding="utf-8")) if rn_file.exists() else {}

    def write(out, html, lang, pair, active):
        """공통 후처리: 현재 메뉴 표시, KOR/ENG 주소(D1), 바뀐 파일 이름, 상대경로."""
        ko_out, en_out = (out, pair) if lang == "ko" else (pair, out)
        if lang == "ko":
            html = fill_menu(html, active, out)   # 한글: 메뉴를 menu.yml 로 그리면서 active 표시(P3-2)
            html = html.replace(FOOTER_SLOT, footer_ko)   # 한글: 푸터를 site.yml 로 그림(P3-3)
        else:
            html = apply_active(html, active)     # 영문: 기존 복사본 메뉴에 active 표시
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

    posts = cms_posts.load_posts(SITE)   # 한글 게시판 = cms/*.md, 영문·팝업 = content/posts.json (P3-4a)
    site = boards.Site(STATIC)
    sitemap_urls = []

    # 2-1) 메인·고정 페이지
    tpl = env.get_template("page.html")
    for key, m in meta.items():
        out = m["out"]
        ctx = common(m["lang"], out, m["title"], m["body_class"])
        content_html = (CONTENT / "pages" / m["content"]).read_text(encoding="utf-8")
        if "%%LATEST_NOTICE%%" in content_html:   # D12: 메인 회사소식 = posts.json 최신 글 4건
            content_html = content_html.replace("%%LATEST_NOTICE%%", extras.latest_notice(m["lang"], posts, site))
        if "%%OUR_PROJECT%%" in content_html:   # P3-4b: 메인 Our Project = 시공사례 featured 글
            content_html = content_html.replace("%%OUR_PROJECT%%", extras.our_project(posts, site))
        description = seo_desc_ko if key == "ko/index" else m["description"]
        # 메인 팝업: 한글은 popups.yml(P3-3), 영문은 기존 posts.json 방식 그대로(1차 범위 밖)
        popup = ""
        if m.get("is_main"):
            popup = extras.popup_html(popups) if m["lang"] == "ko" else extras.popup_html_en(posts, site, now)
        ctx.update(description=description, page_css=m.get("page_css", ""), content_html=content_html,
                   popup_html=popup)
        write(out, tpl.render(**ctx), m["lang"], m["pair"], m.get("active"))
        sitemap_urls.append((out, None))
    print(f"  메인·고정 페이지 {len(meta)}개")

    # 2-2) 게시판 목록·글 (한글 cms/*.md, 영문 content/posts.json)
    n_list = n_view = 0
    dates = {f"{b}:{p['id']}": p["datetime"][:10] for b, v in posts["boards"].items() for p in v}
    for out, tname, ctx, pm in boards.build_pages(CONTENT, STATIC, env, posts, per_page_ko):
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
        sitemap_urls.append((out, dates.get(f"{ctx['g5_bo_table']}:{wr}")))   # 글 페이지만 lastmod(목록 쪽은 없음)
    print(f"  게시판 목록 {n_list}쪽, 글 {n_view}건")

    # 3) 옛 주소 이동(404.html + redirects.json), sitemap.xml, robots.txt
    boards_cfg = json.loads((CONTENT / "boards.json").read_text(encoding="utf-8"))
    for cfg in boards_cfg.values():
        if cfg["lang"] == "ko":
            cfg["page_rows"] = per_page_ko   # 옛 주소 page=N 대응도 site.yml per_page 기준
    red = extras.redirects(meta, boards_cfg, posts)
    red_json = json.dumps(red, ensure_ascii=False, indent=0, sort_keys=True)
    (CONTENT / "redirects.json").write_text(red_json, encoding="utf-8", newline="\n")   # 옛 주소 대응표(기록용, 빌드마다 새로 만듦)
    (PUBLIC / "redirects.json").write_text(json.dumps(red, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (PUBLIC / "404.html").write_text(env.get_template("404.html").render(bases=json.dumps(TEMP_BASES)),
                                     encoding="utf-8", newline="\n")
    (PUBLIC / "sitemap.xml").write_text(extras.sitemap(sitemap_urls, SITE_URL), encoding="utf-8", newline="\n")
    (PUBLIC / "robots.txt").write_text(extras.robots(SITE_URL), encoding="utf-8", newline="\n")
    print(f"  옛 주소 대응 {len(red)}건, sitemap {len(sitemap_urls)}개 주소")

    # 4) 메뉴 내부 주소 검사: menu.yml 의 /로 시작하는 link 가 public/ 에 없으면 빌드 실패
    missing = [(link, where) for link, where in menu_links if not (PUBLIC / link.lstrip("/").split("#")[0].split("?")[0]).is_file()]
    if missing:
        raise BuildError("menu.yml 에 사이트에 없는 주소가 있습니다:\n"
                         + "\n".join(f"  - {where}: {link}" for link, where in missing))
    print(f"  메뉴 내부 주소 {len(menu_links)}개 확인")

    # 5) site.yml(회사소개서)·popups.yml(이미지·링크) 내부 주소 검사
    links = site_links + popup_links
    def exists(link):
        p = link.lstrip("/").split("#")[0].split("?")[0]
        return (PUBLIC / renames.get(p, p)).is_file()   # optimize.py 가 이름을 바꾼 파일(PNG→JPG 등)도 인정
    missing = [(link, where) for link, where in links if not exists(link)]
    if missing:
        raise BuildError("설정 파일에 사이트에 없는 주소가 있습니다:\n"
                         + "\n".join(f"  - {where}: {link}" for link, where in missing))
    print(f"  회사정보·팝업 내부 주소 {len(links)}개 확인, 노출 팝업 {len(popups)}개")

    # 6) E-Catalog file 칸: public/ 에 실제 파일이 있어야 한다
    missing = [(p["_src"], p["file"]) for p in posts["boards"]["library"]
               if not exists(p["file"])]
    if missing:
        raise BuildError("E-Catalog 의 file(PDF)이 사이트에 없습니다:\n"
                         + "\n".join(f"  - {src}: {f}" for src, f in missing))
    print(f"  E-Catalog 파일 {len(posts['boards']['library'])}개 확인")

    up.report(PUBLIC)   # 업로드 이미지 용량, public/ 300MB(D13) 넘으면 경고
    files = [f for f in PUBLIC.rglob("*") if f.is_file()]
    size = sum(f.stat().st_size for f in files)
    print(f"완료: public/ 파일 {len(files)}개, {size / 1024 / 1024:.1f}MB")


if __name__ == "__main__":
    try:
        main()
    except BUILD_ERRORS as e:
        print(f"빌드 실패: {e}", file=sys.stderr)
        sys.exit(1)
