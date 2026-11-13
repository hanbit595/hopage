"""
빌드 결과 비교 (읽기 전용, 아무 파일도 쓰지 않는다)

사용법 (site/ 폴더에서):
    python build/compare_public.py D:\\hanbit_work\\baseline_public public
    python build/compare_public.py D:\\hanbit_work\\baseline_public public --diff board/media/index.html

출력
- 추가·삭제·변경 파일 수, public/en/ 변경 여부(있으면 맨 위에 "❌ ENG 변경 발생")
- 변경된 한글 HTML 목록(en/ 밖의 .html), 변경 파일별 변경 줄 수
- --diff <경로>: 해당 파일의 차이를 짧게(unified diff, 최대 80줄)
"""
import argparse
import difflib
import hashlib
import re
import sys
from pathlib import Path

TEXT_EXT = {".html", ".htm", ".css", ".js", ".json", ".xml", ".txt", ".svg", ".md"}
DIFF_MAX_LINES = 80


def files_of(root: Path) -> dict:
    return {f.relative_to(root).as_posix(): f for f in root.rglob("*") if f.is_file()}


def digest(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fp:
        for block in iter(lambda: fp.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def lines_of(p: Path) -> list:
    return p.read_bytes().decode("utf-8", errors="replace").splitlines()


def changed_lines(a: Path, b: Path) -> int:
    """바뀐 줄 수(삭제 줄 + 추가 줄)."""
    n = 0
    for line in difflib.unified_diff(lines_of(a), lines_of(b), lineterm="", n=0):
        if line.startswith(("+++", "---")):
            continue
        if line.startswith(("+", "-")):
            n += 1
    return n


def is_en(rel: str) -> bool:
    return rel.startswith("en/")


WS = re.compile(r"\s+")


def ws_only(a: Path, b: Path) -> bool:
    """공백·줄바꿈만 다른가(모든 공백 문자를 지우면 같은가). 표시용일 뿐 집계에서 빼지 않는다."""
    if Path(a).suffix.lower() not in TEXT_EXT:
        return False
    ta, tb = (p.read_bytes().decode("utf-8", errors="replace") for p in (a, b))
    return WS.sub("", ta) == WS.sub("", tb)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="public/ 빌드 결과 비교(읽기 전용)")
    ap.add_argument("base", help="기준 폴더(수정 전 public/ 복사본)")
    ap.add_argument("new", help="비교할 폴더(현재 public/)")
    ap.add_argument("--diff", metavar="경로", help="이 파일의 차이를 짧게 출력 (예: board/media/index.html)")
    args = ap.parse_args()

    base, new = Path(args.base), Path(args.new)
    for p in (base, new):
        if not p.is_dir():
            print(f"폴더가 없습니다: {p}")
            return 2

    if args.diff:
        rel = args.diff.replace("\\", "/").lstrip("/")
        a, b = base / rel, new / rel
        if not a.is_file() and not b.is_file():
            print(f"양쪽 모두 없는 파일: {rel}")
            return 2
        if not a.is_file() or not b.is_file():
            print(f"{'추가된' if b.is_file() else '삭제된'} 파일: {rel}")
            return 0
        if Path(rel).suffix.lower() not in TEXT_EXT:
            print(f"이진 파일: {rel} — {'같음' if digest(a) == digest(b) else '다름'}")
            return 0
        diff = list(difflib.unified_diff(lines_of(a), lines_of(b), f"기준/{rel}", f"현재/{rel}", lineterm="", n=1))
        if not diff:
            print(f"차이 없음: {rel}")
        for line in diff[:DIFF_MAX_LINES]:
            print(line[:200])
        if len(diff) > DIFF_MAX_LINES:
            print(f"... (생략 {len(diff) - DIFF_MAX_LINES}줄)")
        return 0

    fa, fb = files_of(base), files_of(new)
    added = sorted(set(fb) - set(fa))
    removed = sorted(set(fa) - set(fb))
    changed = sorted(r for r in set(fa) & set(fb)
                     if fa[r].stat().st_size != fb[r].stat().st_size or digest(fa[r]) != digest(fb[r]))

    en_changes = [r for r in added + removed + changed if is_en(r)]
    if en_changes:
        print(f"❌ ENG 변경 발생 ({len(en_changes)}개)")
    print(f"기준: {base}  ({len(fa)}개)")
    print(f"현재: {new}  ({len(fb)}개)")
    print(f"추가 {len(added)} / 삭제 {len(removed)} / 변경 {len(changed)}")
    print(f"public/en/ 변경: {'있음 ' + str(len(en_changes)) + '개' if en_changes else '없음'}")

    if added:
        print("\n[추가]")
        for r in added:
            print("  +", r)
    if removed:
        print("\n[삭제]")
        for r in removed:
            print("  -", r)

    wso = {r for r in changed if ws_only(fa[r], fb[r])}   # 표시용(위 집계·ENG 경고에는 그대로 포함)
    print(f"  (변경 {len(changed)}개 중 공백·줄바꿈만 다름 {len(wso)} / 실질 변경 {len(changed) - len(wso)})")

    ko_html = [r for r in changed if not is_en(r) and r.lower().endswith((".html", ".htm"))]
    print(f"\n[변경된 한글 HTML] {len(ko_html)}개")
    for r in ko_html:
        print("  ", r, "(공백만)" if r in wso else "")

    if changed:
        print("\n[파일별 변경 줄 수]")
        for r in changed:
            if Path(r).suffix.lower() in TEXT_EXT:
                print(f"  {changed_lines(fa[r], fb[r]):>6}줄  {r}" + ("  (공백만)" if r in wso else ""))
            else:
                print(f"  {'(이진)':>6}    {r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
