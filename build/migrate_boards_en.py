"""
1회용 (P4-EN2): content/posts.json 의 영문 게시판 글(notice_en·media_en·library_en) → cms/en/<게시판>/<글번호>.md

실행 (site/ 폴더에서):
    python build/migrate_boards_en.py              .md 를 쓰고, 다시 읽어 원래 글과 같은지 검사
    python build/migrate_boards_en.py --drop-json  (검증 후) 다시 검사하고 posts.json 에서 영문 배열(boards)을 지움
- 이미 cms/en/<게시판>/ 에 .md 가 있으면 덮어쓰지 않고 멈춘다(--drop-json 은 검사만 다시 한다).
- 승인한 삭제(B4): 시공사례 시험 글 "test" 2건(media_en 1·2번)은 옮기지 않는다.

머리말 칸(국문 cms/ 와 같은 키 이름. 영문은 제목을 나누지 않는다)
- title       : 원래 제목 통째로(예: "[PV] Hanbit Gimhae Factory 168.96kW"). HTML 글자(&amp; 등)는 풀어서 적는다
- date        : 원래 datetime "YYYY-MM-DD HH:MM:SS" 그대로
- thumbnail, summary : 선택 칸. 기존 글은 비워 둔다(목록·메인 썸네일·요약은 기존처럼 첨부·본문에서)
- draft       : 전부 false
- link1, link2, files : 기존 글 전용, 값이 있을 때만(이번 영문 글에는 없음)
- file        : E-Catalog(library) 전용. 영문 E-Catalog 글은 0건이라 이번에는 쓰지 않음
- body_format : html (본문 HTML 그대로 출력)
- 본문        : 원래 content(HTML)를 글자 그대로
"""
import html
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cms_posts as C   # noqa: E402

SITE = Path(__file__).resolve().parent.parent
CMS_EN = SITE / "cms" / "en"
POSTS = SITE / "content" / "posts.json"
SKIP = {"media": {1, 2}}   # B4 승인: 시험용 "test" 글


def front(board: str, p: dict) -> dict:
    fm = {"title": html.unescape(p["subject"]), "date": p["datetime"], "thumbnail": "", "summary": "", "draft": False}
    if board == "library":
        raise SystemExit("library_en 글이 있습니다. E-Catalog file 칸 규칙을 정한 뒤 옮기세요.")
    for k in ("link1", "link2"):
        if p.get(k):
            fm[k] = p[k]
    if p.get("files"):
        fm["files"] = [{"no": f["no"], "source": f["source"], "stored": f["stored"], "size": f["size"]} for f in p["files"]]
    fm["body_format"] = "html"
    return fm


def check(posts) -> list:
    """cms/en/*.md 를 다시 읽어 posts.json 영문 글(B4 제외)과 비교. 문제 목록을 돌려준다."""
    problems = []
    for b in C.EN_BOARDS:
        src = [p for p in posts["boards"][b + "_en"] if p["id"] not in SKIP.get(b, ())]
        got = C.load_board(b, CMS_EN, SITE / "static", lang="en")
        if [q["id"] for q in got] != [p["id"] for p in src]:
            problems.append(f"{b}: 글 목록·순서가 원래와 다름")
        by = {q["id"]: q for q in got}
        for p in src:
            q = by.get(p["id"])
            if q is None:
                problems.append(f"{b} {p['id']}: 다시 읽지 못함")
                continue
            for k in ("datetime", "content", "link1", "link2", "files"):
                if q[k] != p[k]:
                    problems.append(f"{b} {p['id']}: {k} 다름")
            if html.unescape(q["subject"]) != html.unescape(p["subject"]):
                problems.append(f"{b} {p['id']}: 제목 다름")
        print(f"cms/en/{b}/: {len(got)}건 (posts.json {len(posts['boards'][b + '_en'])}건, 제외 {len(SKIP.get(b, ()))}건)")
    return problems


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    text = POSTS.read_text(encoding="utf-8")
    posts = json.loads(text)
    tables = [b + "_en" for b in C.EN_BOARDS]
    if any(t not in posts.get("boards", {}) for t in tables):
        raise SystemExit("posts.json 에 영문 게시판 배열이 없습니다. 이미 이전한 것으로 보고 멈춥니다.")
    drop = "--drop-json" in sys.argv

    if not drop:
        for b in C.EN_BOARDS:
            if (CMS_EN / b).is_dir() and any((CMS_EN / b).glob("*.md")):
                raise SystemExit(f"cms/en/{b}/ 에 이미 .md 가 있습니다. 덮어쓰지 않고 멈춥니다.")
        for b in C.EN_BOARDS:
            (CMS_EN / b).mkdir(parents=True, exist_ok=True)
            keep = CMS_EN / b / ".gitkeep"   # 글이 0건인 폴더(library)도 저장소에 남긴다(관리자 화면 저장 위치)
            if not any(p["id"] not in SKIP.get(b, ()) for p in posts["boards"][b + "_en"]) and not keep.exists():
                keep.write_bytes(b"")
            for p in posts["boards"][b + "_en"]:
                if p["id"] in SKIP.get(b, ()):
                    print(f"  옮기지 않음(B4): {b}_en {p['id']} '{p['subject']}'")
                    continue
                fm = front(b, p)
                body = "---\n" + yaml.safe_dump(fm, allow_unicode=True, sort_keys=False, width=10 ** 6) + "---\n" + p["content"]
                (CMS_EN / b / f"{p['id']}.md").write_bytes(body.encode("utf-8"))

    problems = check(posts)
    if problems:
        print("문제", len(problems), "건:")
        for x in problems:
            print("  -", x)
        sys.exit(1)
    print("검사: 다시 읽은 글이 원래 글과 같음(B4 제외 2건 외)")

    if drop:
        del posts["boards"]   # 영문 배열만 남아 있던 칸. 한글 배열은 P3-4a 에서 이미 지움
        POSTS.write_text(json.dumps(posts, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        print("content/posts.json: boards(notice_en·media_en·library_en) 삭제. 남은 칸:", ", ".join(posts))


if __name__ == "__main__":
    main()
