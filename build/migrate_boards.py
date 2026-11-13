"""
1회용 (P3-4a): content/posts.json 의 한글 게시판 글(notice·media·library) → cms/<게시판>/<글번호>.md

실행:  python build/migrate_boards.py          (site/ 폴더에서)
- 이미 cms/<게시판>/ 에 .md 가 있으면 덮어쓰지 않고 멈춘다.
- 쓴 뒤 cms_posts.py 로 다시 읽어 원래 글과 필드가 모두 같은지 검사한다(다르면 종료코드 1).
- posts.json 에서 한글 배열을 지우는 일(B3)은 이 스크립트가 하지 않는다(검증 후 따로).

머리말에 쓰는 칸과 이유
- title     : (명세 3절) 회사소식·E-Catalog 는 원래 제목 그대로. 시공사례는 제목을 나눈 현장명
- date      : (명세 3절) 원래 datetime "YYYY-MM-DD HH:MM:SS" 그대로. 목록 순서·상세 화면 시각·sitemap lastmod 에 쓰임
- category  : (시공사례) 원래 [..] 안의 분류를 쉼표로 나눈 목록. [태양광발전설비] 는 결정에 따라 [태양광발전장치] 로 통일(50번)
- capacity  : (시공사례) 제목 끝의 용량 부분 글자 그대로. 깔끔히 나눌 수 없으면(앞쪽에도 용량이 남는 경우) 비우고 title 에 둠
- program   : (시공사례) 제목의 " ㅣ " 뒤(예: 건물지원사업)
- thumbnail, summary, gallery : (명세 3절) 선택 칸. 기존 글은 비워 둔다(목록 썸네일은 기존처럼 첨부·본문 첫 이미지)
- featured  : (시공사례) 전부 false. 메인 Our Project 는 P3-4b 에서 다룬다
- draft     : 전부 false
- file      : (E-Catalog, 필수) 기존 다운로드 주소 /files/library/<글번호>-<순번>.pdf (static/ 에 있는 파일)
- link1, link2 : (기존 글 전용, 값이 있을 때만) 상세 화면 관련 링크·YouTube 임베드. 회사소식 17번만 있음
- files     : (기존 글 전용, 값이 있을 때만) 첨부 목록. 이미지 첨부는 상세 상단 이미지·목록·메인 News 썸네일 1순위,
              PDF 는 다운로드 이름(source)·크기(size)·옛 주소 download.php 대응(no·stored 확장자)에 쓰임
- 본문      : 원래 content(HTML)를 글자 그대로(닫는 --- 다음부터 파일 끝까지, 끝 줄바꿈도 더하지 않음)
"""
import html
import json
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cms_posts as C   # noqa: E402

SITE = Path(__file__).resolve().parent.parent
CMS = SITE / "cms"
CATEGORY_FIX = {"태양광발전설비": "태양광발전장치"}   # 50번 (결정 가)
ONE_CAP = r"(?:(?:PV|BIPV)\s+)?\d[\d.]*\s*k[Ww]"
CAP = re.compile(rf"(.+?) ({ONE_CAP}(?:,?\s+{ONE_CAP})*)")
HAS_CAP = re.compile(r"\d\s*k[Ww]\b")


def split_media(subject: str):
    m = re.fullmatch(r"\[([^\]]+)\] (.*)", subject, re.S)
    if not m:
        raise SystemExit(f"시공사례 제목을 나눌 수 없음: {subject}")
    cats = [CATEGORY_FIX.get(c, c) for c in m.group(1).split(",")]
    rest, program = m.group(2), ""
    if " ㅣ " in rest:
        rest, program = rest.split(" ㅣ ", 1)
    title, capacity = rest, ""
    mm = CAP.fullmatch(rest)
    if mm and not HAS_CAP.search(mm.group(1)):
        title, capacity = mm.group(1), mm.group(2)
    return {"title": title, "category": cats, "capacity": capacity, "program": program}


def front(board: str, p: dict) -> dict:
    subject = html.unescape(p["subject"])
    fm = {}
    if board == "media":
        d = split_media(subject)
        fm.update(title=d["title"], category=d["category"], capacity=d["capacity"], program=d["program"],
                  date=p["datetime"], thumbnail="", gallery=[], featured=False, draft=False)
    elif board == "library":
        pdf = [f for f in p["files"] if not f["stored"].lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"))]
        if len(pdf) != 1:
            raise SystemExit(f"library {p['id']}: PDF 첨부가 1개가 아님")
        ext = pdf[0]["stored"].rsplit(".", 1)[1].lower()
        fm.update(title=subject, date=p["datetime"], thumbnail="", file=f"/files/library/{p['id']}-{pdf[0]['no']}.{ext}", draft=False)
    else:
        fm.update(title=subject, date=p["datetime"], thumbnail="", summary="", draft=False)
    for k in ("link1", "link2"):
        if p.get(k):
            fm[k] = p[k]
    if p.get("files"):
        fm["files"] = [{"no": f["no"], "source": f["source"], "stored": f["stored"], "size": f["size"]} for f in p["files"]]
    return fm


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    posts = json.loads((SITE / "content" / "posts.json").read_text(encoding="utf-8"))
    missing = [b for b in C.KO_BOARDS if b not in posts["boards"]]
    if missing:
        raise SystemExit(f"posts.json 에 한글 게시판 배열이 없습니다({', '.join(missing)}). 이미 이전한 것으로 보고 멈춥니다.")
    for b in C.KO_BOARDS:
        if (CMS / b).is_dir() and any((CMS / b).glob("*.md")):
            raise SystemExit(f"cms/{b}/ 에 이미 .md 가 있습니다. 덮어쓰지 않고 멈춥니다.")

    problems, changed = [], []
    for b in C.KO_BOARDS:
        (CMS / b).mkdir(parents=True, exist_ok=True)
        for p in posts["boards"][b]:
            fm = front(b, p)
            text = "---\n" + yaml.safe_dump(fm, allow_unicode=True, sort_keys=False, width=10 ** 6) + "---\n" + p["content"]
            (CMS / b / f"{p['id']}.md").write_bytes(text.encode("utf-8"))
        # 다시 읽어 원래 글과 비교
        got = {q["id"]: q for q in C.load_board(b, CMS, SITE / "static")}
        if [q["id"] for q in C.load_board(b, CMS, SITE / "static")] != [p["id"] for p in posts["boards"][b]]:
            problems.append(f"{b}: 글 순서가 원래와 다름")
        for p in posts["boards"][b]:
            q = got.get(p["id"])
            if q is None:
                problems.append(f"{b} {p['id']}: 다시 읽지 못함")
                continue
            for k in ("datetime", "content", "link1", "link2", "files"):
                if q[k] != p[k]:
                    problems.append(f"{b} {p['id']}: {k} 다름")
            if html.unescape(q["subject"]) != html.unescape(p["subject"]):
                fixed = html.unescape(p["subject"])
                for old, new in CATEGORY_FIX.items():
                    fixed = fixed.replace(f"[{old}]", f"[{new}]", 1)
                (changed if html.unescape(q["subject"]) == fixed else problems).append(
                    f"{b} {p['id']}: 제목 '{html.unescape(p['subject'])}' → '{html.unescape(q['subject'])}'")
        print(f"cms/{b}/: {len(posts['boards'][b])}건")
    for c in changed:
        print("  결정(가)에 따른 제목 변경:", c)
    if problems:
        print("문제", len(problems), "건:")
        for x in problems:
            print("  -", x)
        sys.exit(1)
    print("검사: 다시 읽은 글이 원래 글과 같음(위 결정 변경 제외)")


if __name__ == "__main__":
    main()
