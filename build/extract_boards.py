"""
게시판(4-4) 1회 추출: extract_pages.py가 불러서 실행한다 (내 PC 전용, crawl/·original/은 읽기만).

만드는 것
- templates/_board_head_{ko,en}.html : 게시판 공통 머리(게시판 제목·하위 메뉴). 원본에서 상단 끝 표시 바로 앞에 들어감
- content/boards.json                : 게시판별 설정(언어, 주소, 제목, body class, 스킨 CSS, 현재 메뉴)
- content/board_snapshot.json        : 원본 화면에 찍혀 있던 숫자(조회수, 첨부 다운로드 수·날짜, 관련링크 연결 수). 정적 사이트에서는 고정값
- static/ : 게시판 화면이 쓰는 이미지(축소본·확대용 원본), 첨부(라이브러리 PDF는 files/library/{글번호}-{순번}.pdf)

글 내용(제목·본문·날짜·첨부 정보)은 cms_posts.load_posts()(한글 cms/*.md, 영문 content/posts.json)를 그대로 쓴다.
"""
import json
import re
import shutil
from pathlib import Path

# 게시판 → (언어, 새 주소의 게시판 이름, 수집본 폴더)
BOARDS = {
    "notice": ("ko", "notice"), "media": ("ko", "media"), "library": ("ko", "library"),
    "notice_en": ("en", "notice"), "media_en": ("en", "media"), "library_en": ("en", "library"),
}
IMG_EXT = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp")


def board_dir(table):
    lang, slug = BOARDS[table]
    return ("en/" if lang == "en" else "") + f"board/{slug}/"


def extract_boards(E):
    """E: extract_pages 모듈(공용 함수와 자산 목록을 같이 쓴다)."""
    import cms_posts
    posts = cms_posts.load_posts(E.CONTENT.parent)
    problems, head_blocks, close_blocks = [], {}, {}
    boards_cfg, snapshot = {}, {}

    main_tops = {lang: E.split_page((E.CRAWL / lang / "index.html").read_text(encoding="utf-8")) for lang in ("ko", "en")}

    def crawled(lang, table, wr_id=None, page=None):
        name = f"board__bo_table-{table}" + (f"__wr_id-{wr_id}" if wr_id else "") + (f"__page-{page}" if page else "") + ".html"
        return E.CRAWL / lang / "bbs" / name

    for table, (lang, slug) in BOARDS.items():
        mh, _, _, mtop, _, mtail = main_tops[lang]
        mtop_r = E.strip_active(E.rewrite(mtop, "m", lang)).replace("{{ popup_html }}", "")
        mtail_r = E.rewrite(mtail, "m", lang)
        marker = "<!-- } 상단 끝 -->"
        prefix = mtop_r[: mtop_r.rindex(marker)]

        pages = [crawled(lang, table)] + [crawled(lang, table, page=n) for n in range(2, 40) if crawled(lang, table, page=n).exists()]
        views = [crawled(lang, table, wr_id=p["id"]) for p in posts["boards"][table]]
        cfg = None
        for f in pages + views:
            if not f.exists():
                problems.append(f"{table}: 수집본 없음 {f.name}")
                continue
            head, body_class, popup, top, body, tail = E.split_page(f.read_text(encoding="utf-8"))
            where = f"{table} {f.stem}"
            top_r, tail_r, head_r = E.rewrite(top, where, lang), E.rewrite(tail, where, lang), E.rewrite(head, where, lang)
            # 원본 게시판의 KOR/ENG는 상대 언어 게시판 목록(?locale=..&bo_table=..)으로 연결 → 빌드 때 D1 주소로 채울 자리 표시로 통일
            top_r = re.sub(r'<a href="[^"]*"( class="active")?>KOR</a>', rf'<a href="{E.LANG_KO}"\1>KOR</a>', top_r)
            top_r = re.sub(r'<a href="[^"]*"( class="active")?>ENG</a>', rf'<a href="{E.LANG_EN}"\1>ENG</a>', top_r)
            E.rewrite(body, where, lang)   # 본문이 쓰는 이미지(축소본 등)를 자산 목록에 올린다
            st = E.strip_active(top_r)
            if not st.startswith(prefix):
                problems.append(f"{where}: 공통 상단과 다름")
                continue
            block = st[len(prefix): st.rindex(marker)]
            head_blocks.setdefault(lang, block)
            if block != head_blocks[lang]:
                problems.append(f"{where}: 게시판 머리가 다른 게시판과 다름")
            mk = "<!-- 하단 시작 { -->\n"
            rest = mtail_r[len(mk):]
            if not (tail_r.startswith(mk) and tail_r.endswith(rest)):
                problems.append(f"{where}: 하단 형태가 다름")
            else:
                close = tail_r[len(mk): len(tail_r) - len(rest)]
                close_blocks.setdefault(lang, close)
                if close != close_blocks[lang]:
                    problems.append(f"{where}: 게시판 닫는 태그가 다름")
            is_view = "__wr_id-" in f.name
            if cfg is None and not is_view:
                skin = re.search(r'<link rel="stylesheet" href="%%ROOT%%theme/basic/skin/board/[^"]+">', head_r).group(0)
                title = re.search(r"<title>([^<]*)</title>", head_r).group(1)
                cfg = {
                    "table": table, "lang": lang, "slug": slug, "dir": board_dir(table),
                    "subject": next(m["subject"] for m in posts["boards_meta"] if m["bo_table"] == table),
                    "page_rows": next(m["page_rows"] for m in posts["boards_meta"] if m["bo_table"] == table),
                    "list_title": title, "skin_css": skin,
                    "editor": re.search(r'var g5_editor\s*= "([^"]*)";', head_r).group(1),
                    "body_class_list": body_class, "active": E.active_target(top_r),
                    "pair_dir": board_dir(table[:-3] if table.endswith("_en") else table + "_en"),   # D1
                }
            if is_view and "body_class_view" not in (cfg or {}):
                cfg["body_class_view"] = body_class
                cfg["view_title_suffix"] = re.search(r"<title>[^<]*?( &gt; [^<]*| > [^<]*)</title>", head_r).group(1)
            # 원본 화면에 찍혀 있던 숫자
            if is_view:
                wr = int(f.stem.rsplit("-", 1)[1])
                hit = re.search(r'board_view_info_hit">\s*<b>.*?</b><span>([^<]*)</span>', body, re.S)
                files = re.findall(r'<span class="bo_v_file_cnt">([^<]*?) \| DATE : ([^<]*)</span>', body)
                links = re.findall(r'<span class="bo_v_link_cnt">([^<]*)</span>', body)
                snapshot[f"{table}:{wr}"] = {"hit": hit.group(1) if hit else "",
                                            "files": [{"download": d, "date": t} for d, t in files],
                                            "links": links}
        if cfg is None:
            problems.append(f"{table}: 목록 수집본을 읽지 못함")
            continue
        cfg.setdefault("body_class_view", cfg["body_class_list"].replace("b_list", "b_view"))
        cfg.setdefault("view_title_suffix", f" > {cfg['subject']} | HANBIT Innotech")
        boards_cfg[table] = cfg

        # 확대 보기(라이트박스)용 원본 이미지, 첨부파일
        for p in posts["boards"][table]:
            for src in re.findall(r'<img[^>]+src="([^"]+)"', p["content"]):
                if re.match(r"^(https?:)?//(www\.)?hanbitinnotech\.com/", src) or src.startswith("/"):
                    E.map_asset(src, f"{table} {p['id']} 본문 원본")
            for fl in p["files"]:
                stored = fl["stored"]
                if stored.lower().endswith(IMG_EXT):
                    E.map_asset(stored, f"{table} {p['id']} 첨부 이미지")
                else:
                    real = E.real_path(stored)
                    ext = Path(stored).suffix.lower()
                    dst = E.STATIC / "files" / slug / f"{p['id']}-{fl['no']}{ext}"
                    if real is None:
                        problems.append(f"{table} {p['id']}: 첨부 원본 없음 {stored}")
                    else:
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(E.WWW / real.lstrip("/"), dst)

    for lang, block in head_blocks.items():
        (E.TEMPLATES / f"_board_head_{lang}.html").write_text(block, encoding="utf-8", newline=E.LF)
    for cfg in boards_cfg.values():
        cfg["close"] = close_blocks[cfg["lang"]]
    (E.CONTENT / "boards.json").write_text(json.dumps(boards_cfg, ensure_ascii=False, indent=2), encoding="utf-8", newline=E.LF)
    (E.CONTENT / "board_snapshot.json").write_text(json.dumps(snapshot, ensure_ascii=False, indent=1), encoding="utf-8", newline=E.LF)

    print(f"게시판 추출: {len(boards_cfg)}개 게시판, 숫자 기록 {len(snapshot)}건, 게시판 머리 {list(head_blocks)}")
    print("게시판 점검:", f"문제 {len(problems)}건" if problems else "문제 없음")
    for p in problems[:15]:
        print("  -", p)
    return problems
