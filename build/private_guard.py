"""
비공개 처리(D17)가 extract_pages.py 재실행으로 되살아나지 않게 막는다(내 PC 전용).
비공개 글 목록은 저장소 바깥 D:\\homepage\\private\\posts\\{게시판}\\{글번호}\\ 폴더에서 읽는다(목록을 저장소에 두지 않음).
- check(): private\\ 폴더가 없으면 멈춘다(그대로 추출하면 비공개 글이 되살아남)
- apply(): 추출이 끝난 뒤 비공개 글의 사진(원본·확대본·축소본)과 board_snapshot 항목을 빼고,
           메인 '주요 프로젝트' 카드(private\\main_cards\\item_NN\\ 폴더가 있는 번호)를 빈 칸으로,
           layout.css의 그 카드 배경 규칙과 사진을 지운다
"""
import html
import json
import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
PRIV = SITE.parent / "private"
HOST = re.compile(r"^https?://(?:www\.)?hanbitinnotech\.com/", re.I)


def cards():
    return sorted(d.name[5:] for d in PRIV.glob("main_cards/item_*") if d.is_dir())


def targets():
    return sorted((d.parent.name, d.name) for d in PRIV.glob("posts/*/*") if d.is_dir())


def check():
    if not targets():
        sys.exit(f"[멈춤] {PRIV}\\posts\\ 가 없거나 비어 있음. 비공개 처리(D17) 목록 없이 추출하면 지운 글·사진이 되살아난다.")


def _images(p):
    out = [f["stored"].lstrip("/") for f in p.get("files") or [] if f["stored"].lower().endswith((".jpg", ".jpeg", ".png", ".gif"))]
    out += [HOST.sub("", html.unescape(s)) for s in re.findall(r'<img[^>]+src="([^"]+)"', p.get("content") or "")]
    return out


def apply():
    static, content = SITE / "static", SITE / "content"
    removed = []
    names = set()
    for b, i in targets():
        rec = json.loads((PRIV / "posts" / b / i / "post.json").read_text(encoding="utf-8"))
        for rel in _images(rec):
            d, name = rel.rsplit("/", 1)
            names.add((d.lower(), name.rsplit(".", 1)[0].lower(), name.lower()))
    for f in list(static.rglob("*")):
        if not f.is_file():
            continue
        rel = f.relative_to(static).as_posix()
        d, n = (rel.rsplit("/", 1) + [""])[:2] if "/" in rel else ("", rel)
        dl, nl = d.lower(), n.lower()
        for td, stem, full in names:
            if dl == td and (nl == full or nl.startswith(f"thumb-{stem}_") or nl == f"large-{stem}.jpg"):
                f.unlink(); removed.append(rel)
    for c in cards():
        img = f"theme/basic/images/main/mainProject_bg_{c}.jpg"
        if (static / img).exists():
            (static / img).unlink(); removed.append(img)
    snap_f = content / "board_snapshot.json"
    snap = json.loads(snap_f.read_text(encoding="utf-8"))
    n_snap = sum(snap.pop(f"{b}:{i}", None) is not None for b, i in targets())
    snap_f.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    n_card = 0
    for lang in ("ko", "en"):
        f = content / "pages" / lang / "index.html"
        t = f.read_bytes().decode("utf-8")
        for c in cards():
            t, n = re.subn(rf'([ \t]*)<li class="mainProject_item item_{c}">.*?</li>\n',
                           lambda m: f'{m.group(1)}<li class="mainProject_item item_{c}"></li>\n', t, flags=re.S)
            n_card += n
        f.write_bytes(t.encode("utf-8"))
    css_f = static / "theme/basic/css/layout.css"
    css = css_f.read_bytes().decode("utf-8")
    n_css = 0
    for c in cards():
        rule = f".mainProject_item.item_{c} .bg {{ background-image: url(../images/main/mainProject_bg_{c}.jpg); }}\n"
        n_css += css.count(rule)
        css = css.replace(rule, "")
    css_f.write_bytes(css.encode("utf-8"))
    print(f"비공개 처리(D17) 다시 적용: 글 {len(targets())}건: 사진 {len(removed)}개 삭제, snapshot {n_snap}개 삭제, "
          f"메인 카드 {cards()} {n_card}개 비움, CSS 규칙 {n_css}개 삭제")
