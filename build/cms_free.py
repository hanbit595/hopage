"""
자유 페이지(P6): 고정 페이지 본문 = cms/free/<이름>.md(국문)·cms/en/free/<이름>.md(영문). 관리자 화면 편집기가 고친다.

파일 형식
    ---
    title: "PV | HANBIT Innotech"      # 참고용(화면 제목·<title> 은 content/pages/meta.json)
    path: "/page/pv.html"              # 기존 주소(출력 경로). 파일 이름과 맞아야 한다
    editor_mode: "html"                # html | visual (관리자 편집기 시작 모드)
    ---
    <div class="sec_wrap"> … 본문 HTML …

- 틀: content/pages/{ko,en}/page/<이름>.html 에 상단 제목·왼쪽(상단) 메뉴·감싸는 div·페이지 전용 스크립트가 남고,
  본문 자리에 %%FREE_BODY%% 가 있다. 본문 중간에 있던 스크립트는 틀 맨 아래 <!--%%FREE_SCRIPT:n%%--> … <!--%%END%%--> 블록에
  보관하고, 본문의 <!--hb-script-n--> 자리에 다시 넣는다(자리 표시가 지워지면 본문 끝에 넣는다).
- 본문 주소: /로 시작하는 src·href·poster·data-*·srcset·url() 은 빌드 때 상대경로(%%ROOT%%)로 바꾼다.
- 안전 처리(빌드 때): <script> 제거, on* 속성 제거, javascript: 주소 제거, iframe 은 youtube.com·youtube-nocookie.com 만 허용.
- 빌드 실패(한국어 메시지): 파일 없음, 앞부분 형식 오류, path 불일치, editor_mode 값 오류.
"""
import re
from pathlib import Path

import yaml

from cms_pages import CmsPageError

SLOT = "%%FREE_BODY%%"
MODES = ("html", "visual")
SCRIPT_BLOCK = re.compile(r"\n?<!--%%FREE_SCRIPT:(\d+)%%-->(.*?)<!--%%END%%-->", re.S)
YT_HOSTS = ("www.youtube.com", "youtube.com", "www.youtube-nocookie.com", "youtube-nocookie.com")

ATTR_ROOT = re.compile(r'(\s(?:src|href|poster|data-[\w-]+)=")/(?!/)')
URL_ROOT = re.compile(r"(url\(['\"]?)/(?!/)")
SRCSET = re.compile(r'(\ssrcset=")([^"]*)"')


def md_path(out: str) -> str:
    """출력 경로 → cms 파일 경로. page/pv.html → cms/free/pv.md, en/page/pv.html → cms/en/free/pv.md"""
    name = out.rsplit("/", 1)[1][:-5]
    return ("cms/en/free/" if out.startswith("en/") else "cms/free/") + name + ".md"


# ───────── 주소: 파일에는 /theme/… , 빌드 때 %%ROOT%%theme/… ─────────
def to_root(body: str) -> str:
    body = ATTR_ROOT.sub(r"\1%%ROOT%%", body)
    body = URL_ROOT.sub(r"\1%%ROOT%%", body)
    return SRCSET.sub(lambda m: m.group(1) + re.sub(r"(^|,\s*)/(?!/)", r"\1%%ROOT%%", m.group(2)) + '"', body)


def from_root(body: str) -> str:
    return body.replace("%%ROOT%%", "/")


# ───────── 안전 처리 ─────────
def _iframe_ok(tag: str) -> bool:
    m = re.search(r'\ssrc=["\']?(?:https?:)?//([^/"\'\s>]+)', tag, re.I)
    return bool(m) and m.group(1).lower() in YT_HOSTS


def sanitize(body: str) -> str:
    body = re.sub(r"<script\b.*?</script\s*>", "", body, flags=re.S | re.I)
    body = re.sub(r"<script\b[^>]*>", "", body, flags=re.I)
    body = re.sub(r"""\son[a-z]+\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+)""", "", body, flags=re.I)
    body = re.sub(r"""(\s(?:href|src|action|formaction|xlink:href)\s*=\s*)(["']?)\s*javascript:[^"'>]*\2""",
                  r'\1\2#\2', body, flags=re.I)
    body = re.sub(r"<iframe\b[^>]*>.*?</iframe\s*>",
                  lambda m: m.group(0) if _iframe_ok(m.group(0)) else "", body, flags=re.S | re.I)
    body = re.sub(r"<iframe\b[^>]*>", lambda m: m.group(0) if _iframe_ok(m.group(0)) else "", body, flags=re.I)
    return body


# ───────── 읽기·끼우기 ─────────
def split_md(text: str, name: str):
    m = re.match(r"---\r?\n(.*?)\r?\n---\r?\n", text, re.S)
    if not m:
        raise CmsPageError(f"{name}: 맨 위 --- 사이 앞부분(title·path·editor_mode)이 없습니다.")
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:
        raise CmsPageError(f"{name} 앞부분 형식 오류: {e}")
    if not isinstance(fm, dict):
        raise CmsPageError(f"{name} 앞부분 형식 오류")
    return fm, text[m.end():]


def load(site: Path, out: str) -> str:
    name = md_path(out)
    try:
        text = (site / name).read_text(encoding="utf-8")
    except FileNotFoundError:
        raise CmsPageError(f"자유 페이지 파일이 없습니다: {name}")
    fm, body = split_md(text, name)
    if str(fm.get("path") or "").strip() != "/" + out:
        raise CmsPageError(f"{name}: path 는 '/{out}' 이어야 합니다 (현재: '{fm.get('path')}')")
    if fm.get("editor_mode", "html") not in MODES:
        raise CmsPageError(f"{name}: editor_mode 는 html 또는 visual 이어야 합니다 (현재: '{fm.get('editor_mode')}')")
    return to_root(sanitize(body))


def fill(frame: str, body: str) -> str:
    """틀의 %%FREE_BODY%% 에 본문을 넣고, 보관한 본문 중간 스크립트를 자리 표시에 되돌린다."""
    scripts = {n: s for n, s in SCRIPT_BLOCK.findall(frame)}
    frame = SCRIPT_BLOCK.sub("", frame)
    for n, s in scripts.items():
        mark = f"<!--hb-script-{n}-->"
        body = body.replace(mark, s, 1) if mark in body else body + s
    return frame.replace(SLOT, body, 1)
