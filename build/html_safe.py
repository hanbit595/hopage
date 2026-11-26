"""
관리자 화면에서 들어온 HTML(게시판 본문·자유 페이지·FAQ 답변·회사 페이지 글 칸·시뮬레이션 설명)의 안전 처리.

왜 필요한가
- 관리자 화면(Sveltia)은 저장소에 바로 커밋하고, 빌드는 본문 HTML 을 그대로 페이지에 넣는다.
  관리자 토큰이 새거나 다른 곳에서 복사한 HTML 을 붙여 넣으면 <script>·onerror=·javascript: 주소가
  공개 홈페이지에 그대로 실린다(저장형 XSS: 방문자 브라우저에서 피싱 이동·가짜 문의폼·악성 스크립트 실행).
- 기존 boards.purify·cms_free.sanitize 는 정규식 기반이라 <script> 를 남기거나(boards.purify),
  java&#115;cript: 처럼 문자 참조를 쓰거나 <svg/onload=…> 처럼 공백 대신 / 를 쓰면 통과됐다.

동작(의존성 없음: 표준 라이브러리만)
1) clean(html): 위험한 것만 고치고 나머지 글자는 한 글자도 바꾸지 않는다(기존 글 출력이 그대로 유지되도록).
   - 내용째 삭제: script, object, embed, applet, svg, math, noembed, noframes, template
   - 태그만 삭제(안 글자는 남김): base, meta, link, frame, frameset, form, input, textarea, select, button
   - 허용 외 iframe 삭제(유튜브·구글 지도만 허용)
   - on… 이벤트 속성 삭제, 주소 속성(href·src·action 등)은 http·https·mailto·tel·상대주소만 허용
     (img 의 data:image/png|jpeg|gif|webp 는 허용), 문자 참조·공백·제어문자를 풀어서 판단한다.
   - style 속성에 expression( · javascript: · behavior: · -moz-binding 이 있으면 속성 삭제
2) check(html): 표준 HTML 파서로 결과를 다시 읽어 위험 요소가 남았으면 목록을 돌려준다.
   정규식과 브라우저의 해석 차이(주석·따옴표 속 > 등)를 노린 우회를 잡기 위한 2차 검사다.
3) safe(html, where): clean → check, 남은 것이 있으면 UnsafeHtml(한국어 메시지)로 빌드를 멈춘다.
   빌드가 멈추면 GitHub Actions 는 배포하지 않으므로 기존 사이트가 그대로 유지된다.
"""
import html as html_lib
import re
from html.parser import HTMLParser
from urllib.parse import urlsplit


class UnsafeHtml(Exception):
    """한국어 메시지로 빌드를 멈춘다(종료코드 1)."""


DROP_WITH_CONTENT = ("script", "object", "embed", "applet", "svg", "math", "noembed", "noframes", "template")
DROP_TAG_ONLY = ("base", "meta", "link", "frame", "frameset", "form", "input", "textarea", "select", "button",
                 "option", "isindex", "keygen")
IFRAME_HOSTS = ("www.youtube.com", "youtube.com", "www.youtube-nocookie.com", "youtube-nocookie.com",
                "www.google.com", "maps.google.com")
IFRAME_PATH_PREFIX = {"www.google.com": "/maps/", "maps.google.com": "/maps"}
URL_ATTRS = ("href", "src", "action", "formaction", "xlink:href", "data", "poster", "background", "cite",
             "longdesc", "lowsrc", "dynsrc", "ping", "codebase", "manifest", "usemap", "icon", "profile")
SAFE_SCHEMES = ("http", "https", "mailto", "tel")
DATA_IMAGE = re.compile(r"^data:image/(?:png|jpe?g|gif|webp);", re.I)
BAD_STYLE = re.compile(r"expression\s*\(|javascript\s*:|vbscript\s*:|behavior\s*:|-moz-binding|@import", re.I)
CTRL = re.compile(r"[\x00-\x20\x7f-\x9f]+")

# 태그 하나: 따옴표 안의 > 는 태그 끝으로 보지 않는다. 이름 뒤 구분자는 공백 또는 / (브라우저와 같음)
TAG = re.compile(r"""<(/?)([a-zA-Z][^\s/>]*)((?:"[^"]*"|'[^']*'|[^'">])*)>""", re.S)
ATTR = re.compile(r"""([^\s"'<>/=]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'=<>`]+)))?""")


def _norm_url(v: str) -> str:
    """브라우저가 주소를 읽는 방식에 가깝게: 문자 참조 풀기(두 번) → 제어문자·공백 제거 → 소문자."""
    v = html_lib.unescape(html_lib.unescape(v or ""))
    return CTRL.sub("", v).lower()


def url_ok(v: str, tag: str = "", attr: str = "") -> bool:
    u = _norm_url(v)
    if tag == "img" and attr == "src" and DATA_IMAGE.match(u):
        return True
    m = re.match(r"^([a-z][a-z0-9+.\-]*):", u)
    if not m:
        return True   # 상대주소·#·?·// (스킴 없음)
    return m.group(1) in SAFE_SCHEMES


def srcset_ok(v: str) -> bool:
    return all(url_ok(part.strip().split(" ")[0]) for part in html_lib.unescape(v).split(",") if part.strip())


def iframe_ok(src: str) -> bool:
    u = html_lib.unescape(src or "").strip()
    if u.startswith("//"):
        u = "https:" + u
    try:
        p = urlsplit(u)
    except ValueError:
        return False
    host = (p.hostname or "").lower()
    if p.scheme not in ("http", "https") or host not in IFRAME_HOSTS:
        return False
    pre = IFRAME_PATH_PREFIX.get(host)
    return not pre or p.path.startswith(pre)


def _attrs(raw: str):
    return [(a.group(1), next((g for g in a.groups()[1:] if g is not None), None)) for a in ATTR.finditer(raw)]


def _attr_bad(tag: str, k: str, v) -> bool:
    kl = k.lower()
    if kl.startswith("on"):
        return True
    if v is None:
        return False
    if kl in URL_ATTRS and not url_ok(v, tag, kl):
        return True
    if kl in ("srcset", "imagesrcset") and not srcset_ok(v):
        return True
    if kl == "style" and BAD_STYLE.search(html_lib.unescape(v)):
        return True
    if kl in ("formaction", "srcdoc"):
        return True
    return False


def clean(body: str) -> str:
    """위험한 태그·속성만 고친다. 고칠 것이 없는 태그는 원문 글자 그대로 둔다."""
    if not body or "<" not in body:
        return body
    # 1) 내용째 지울 요소(여는 태그 ~ 닫는 태그, 닫는 태그가 없으면 끝까지)
    for name in DROP_WITH_CONTENT:
        body = re.sub(rf"<{name}\b(?:\"[^\"]*\"|'[^']*'|[^'\">])*>.*?(?:</{name}\s*>|$)", "", body, flags=re.S | re.I)
        body = re.sub(rf"</?{name}\b[^>]*>", "", body, flags=re.I)
    # 2) 허용 외 iframe(내용째)
    def iframe_sub(m):
        src = next((v for k, v in _attrs(m.group(1)) if k.lower() == "src"), None)
        return m.group(0) if iframe_ok(src) else ""
    body = re.sub(r"<iframe\b((?:\"[^\"]*\"|'[^']*'|[^'\">])*)>.*?(?:</iframe\s*>|$)", iframe_sub, body,
                  flags=re.S | re.I)

    # 3) 태그 하나씩: 위험 태그는 태그만 지우고, 위험 속성만 뺀다
    def tag_sub(m):
        close, name, raw = m.group(1), m.group(2).lower(), m.group(3) or ""
        if name in DROP_TAG_ONLY:
            return ""
        if close or not raw.strip(" \t\r\n/"):
            return m.group(0)
        pairs = _attrs(raw)
        if not any(_attr_bad(name, k, v) for k, v in pairs) and not raw.lstrip().startswith("/"):
            return m.group(0)
        kept = [(k, v) for k, v in pairs if not _attr_bad(name, k, v)]
        selfc = raw.rstrip().endswith("/")
        out = "".join(f' {k}="{html_lib.escape(html_lib.unescape(v), quote=True)}"' if v is not None else f" {k}"
                      for k, v in kept)
        return f"<{m.group(2)}{out}{' /' if selfc else ''}>"
    return TAG.sub(tag_sub, body)


class _Checker(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.problems = []

    def _tag(self, tag, attrs):
        t = tag.lower()
        if t in DROP_WITH_CONTENT or t in DROP_TAG_ONLY:
            self.problems.append(f"<{t}> 태그")
        if t == "iframe" and not iframe_ok(dict(attrs).get("src")):
            self.problems.append(f"허용되지 않은 iframe({dict(attrs).get('src')})")
        for k, v in attrs:
            # HTMLParser 는 값의 문자 참조를 이미 풀어 준다 → 다시 이스케이프해서 같은 판단 함수 사용
            if _attr_bad(t, k, html_lib.escape(v) if v is not None else None):
                self.problems.append(f"<{t} {k}=\"{(v or '')[:60]}\">")

    def handle_starttag(self, tag, attrs):
        self._tag(tag, attrs)

    def handle_startendtag(self, tag, attrs):
        self._tag(tag, attrs)


def check(body: str) -> list:
    c = _Checker()
    c.feed(body or "")
    c.close()
    return c.problems


def safe(body: str, where: str) -> str:
    """clean 후 표준 파서로 다시 검사. 위험 요소가 남으면 빌드를 멈춘다."""
    out = clean(body)
    left = check(out)
    if left:
        raise UnsafeHtml(f"{where}: 본문에 허용되지 않는 코드가 있어 빌드를 멈춥니다(보안). 해당 부분을 지우고 다시 저장하세요.\n"
                         + "\n".join(f"  - {p}" for p in dict.fromkeys(left)))
    return out
