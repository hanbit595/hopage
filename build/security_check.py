"""
빌드 보안 검사(build.py 가 불러 쓴다). 실패하면 한국어 메시지로 빌드를 멈춘다 → GitHub Actions 는 배포하지 않고 기존 사이트 유지.

1) check_uploads(uploads): 관리자 화면 업로드(uploads/)의 파일 종류 제한
   - 허용: 사진(jpg·jpeg·png·gif·webp), 문서 첨부(pdf·hwp·hwpx·docx·xlsx·zip — 관리자 서버 UPLOAD_RE 와 맞춤),
     동영상(mp4·webm), 3D 시뮬레이션 uploads/sim/*.html
   - 막는 이유: .svg·.html·.js 등은 홈페이지와 같은 주소(hanbitinnotech.com)에서 열리므로
     파일 안의 스크립트가 홈페이지 권한으로 실행된다(업로드를 통한 XSS·피싱 페이지 호스팅).
2) check_public(public): 배포본(public/)에 올라가면 안 되는 파일 차단
   - 숨김 파일·폴더(.git, .env 등), 소스·설정·백업(.py .php .sql .bak .log .yml .md …), 허용 목록 밖 확장자
   - svg 는 디자인 폴더(theme/, js/)에 있는 기존 아이콘만 허용
"""
from pathlib import Path


class SecurityCheckError(Exception):
    """한국어 메시지로 빌드를 멈춘다(종료코드 1)."""


DOC_EXT = {".pdf", ".hwp", ".hwpx", ".docx", ".xlsx", ".zip"}   # 다운로드 첨부(브라우저에서 실행되지 않음)
UPLOAD_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".mp4", ".webm"} | DOC_EXT
UPLOAD_SIM_EXT = {".html"}   # uploads/sim/ 안에서만
PUBLIC_EXT = {".html", ".jpg", ".jpeg", ".png", ".gif", ".webp", ".ico", ".js", ".css", ".woff", ".woff2", ".eot",
              ".ttf", ".otf", ".json", ".xml", ".txt", ".mp4", ".webm", ".svg"} | DOC_EXT
SVG_DIRS = ("theme/", "js/")
TXT_ALLOWED = {"robots.txt"}


def check_uploads(uploads: Path):
    bad = []
    for f in sorted(uploads.rglob("*")) if uploads.is_dir() else []:
        rel = f.relative_to(uploads).as_posix()
        if any(part.startswith(".") for part in Path(rel).parts):
            if f.is_file() and f.name != ".gitkeep":
                bad.append(f"uploads/{rel}: 숨김 파일")
            continue
        if not f.is_file():
            continue
        ext = f.suffix.lower()
        if ext in UPLOAD_EXT or (rel.lower().startswith("sim/") and ext in UPLOAD_SIM_EXT):
            continue
        bad.append(f"uploads/{rel}: 올릴 수 없는 파일 종류({ext or '확장자 없음'})")
    if bad:
        raise SecurityCheckError("업로드 파일 보안 검사 실패 — 사진(jpg·png·gif·webp)·문서(pdf·hwp·hwpx·docx·xlsx·zip)·mp4 만 올릴 수 있습니다. "
                                 "관리자 화면에서 해당 파일을 지우세요:\n" + "\n".join("  - " + b for b in bad))
    return True


def check_public(public: Path):
    bad = []
    for f in sorted(public.rglob("*")):
        rel = f.relative_to(public).as_posix()
        if any(part.startswith(".") for part in Path(rel).parts):
            bad.append(f"{rel}: 숨김 파일·폴더는 배포하지 않습니다")
            continue
        if not f.is_file():
            continue
        ext = f.suffix.lower()
        if ext not in PUBLIC_EXT:
            bad.append(f"{rel}: 배포 허용 목록에 없는 파일 종류({ext or '확장자 없음'})")
        elif ext == ".svg" and not rel.startswith(SVG_DIRS):
            bad.append(f"{rel}: svg 는 디자인 폴더(theme/·js/) 밖에 둘 수 없습니다")
        elif ext == ".txt" and rel not in TXT_ALLOWED:
            bad.append(f"{rel}: txt 파일은 robots.txt 만 배포합니다")
    if bad:
        raise SecurityCheckError("배포본(public/) 보안 검사 실패:\n" + "\n".join("  - " + b for b in bad[:50])
                                 + (f"\n  … 외 {len(bad) - 50}개" if len(bad) > 50 else ""))
    return True
