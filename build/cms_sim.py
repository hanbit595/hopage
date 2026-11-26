"""
시뮬레이션 페이지(P8, 홍보센터 > 시뮬레이션). build.py 가 불러 쓴다.

- 사례 파일: cms/simulation/<slug>.md (영문 cms/en/simulation/<slug>.md). 앞부분:
  title(현장명, 필수), categories(시공사례 분류 목록 cms_posts.CATEGORIES 중 여러 개), kwp·modules·arrays·parking(선택, 비면 숨김),
  youtube(유튜브 주소, 필수), thumbnail(/uploads/… 선택, 비면 유튜브 썸네일), viewer(/uploads/sim/<slug>.html 선택),
  related(시공사례 주소 /board/media/… 선택), visible(기본 true), order(작은 수 먼저, 기본 0), date. 본문 = 설명 HTML(그대로 출력).
- 설정: 언어별 site.yml 의 simulation_public(true/false, 없으면 false)·simulation_intro(목록 맨 위 소개 문구).
  꺼져 있거나 visible 사례가 0개면 목록·상세·메뉴·sitemap 을 만들지 않는다(쓰는 CSS·JS·업로드도 공개 안 함).
- 출력: 목록 page/simulation.html, 상세 simulation/<slug>.html (영문 en/ 아래 같은 구조).
- 3D 파일 안전 검사(uploads/sim/*.html, 스위치와 상관없이 항상): 25MB 초과, 'reference_photos' 또는 'data:image/jpeg' 포함이면 빌드 실패.
"""
import html
import re
from datetime import date, datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import yaml

import html_safe
from cms_free import split_md
from cms_pages import CmsPageError
from cms_posts import CATEGORIES

FOLDER = {"ko": "cms/simulation", "en": "cms/en/simulation"}
LIST_OUT = {"ko": "page/simulation.html", "en": "en/page/simulation.html"}
ASSETS = ["theme/basic/css/hb_sim.css", "theme/basic/js/hb_sim.js"]
SLUG = re.compile(r"[a-z0-9_-]+")
SIM_MAX = 25 * 1024 * 1024
SIM_BANNED = (b"reference_photos", b"data:image/jpeg")
CAT_EN = {"태양광발전장치": "PV System", "BIPV": "BIPV", "주차장태양광": "Solar Carport", "기타": "Others"}
L = {
    "ko": {"name": "시뮬레이션", "all": "전체", "kwp": ("설비용량", "kWp"), "modules": ("모듈", "장"),
           "arrays": ("어레이", "개"), "parking": ("주차면", "면"), "video": "시뮬레이션 영상", "view3d": "3D 보기",
           "full": "전체 화면", "related": "관련 시공사례 보기", "inquiry": "견적문의", "location": "상담 문의(오시는 길)",
           "note": "기하학적 음영 분석 결과이며 실제 발전량과 다를 수 있습니다.", "list": "목록"},
    "en": {"name": "Simulation", "all": "All", "kwp": ("Capacity", "kWp"), "modules": ("Modules", ""),
           "arrays": ("Arrays", ""), "parking": ("Parking Spaces", ""), "video": "Simulation Video", "view3d": "View 3D",
           "full": "Full Screen", "related": "View Project Case", "inquiry": "Request a Quote", "location": "Contact Us",
           "note": "This is the result of a geometric shading analysis and may differ from actual power generation.",
           "list": "List"},
}


def check_sim_files(uploads: Path):
    """uploads/sim/*.html 안전 검사(원본 사진 유출 방지)."""
    bad = []
    folder = uploads / "sim"
    for f in sorted(folder.rglob("*")) if folder.is_dir() else []:
        if not f.is_file() or f.suffix.lower() not in (".html", ".htm"):
            continue
        name = f.relative_to(uploads.parent).as_posix()
        if f.stat().st_size > SIM_MAX:
            bad.append(f"{name}: 25MB 초과({f.stat().st_size / 1024 / 1024:.1f}MB)")
            continue
        data = f.read_bytes()
        bad += [f"{name}: '{w.decode()}' 가 들어 있음(원본 사진 포함 의심)" for w in SIM_BANNED if w in data]
    if bad:
        raise CmsPageError("3D 시뮬레이션 파일 안전 검사 실패(uploads/sim):\n" + "\n".join("  - " + b for b in bad))


def youtube_id(url: str):
    u = urlparse(url.strip())
    host = (u.hostname or "").lower().removeprefix("www.").removeprefix("m.")
    vid = ""
    if host == "youtu.be":
        vid = u.path.strip("/").split("/")[0]
    elif host in ("youtube.com", "youtube-nocookie.com"):
        if u.path == "/watch":
            vid = (parse_qs(u.query).get("v") or [""])[0]
        else:
            m = re.match(r"/(?:embed|shorts|live|v)/([^/?#]+)", u.path)
            vid = m.group(1) if m else ""
    return vid if re.fullmatch(r"[A-Za-z0-9_-]{6,20}", vid) else None


def _num(v, where, key):
    if v is None or (isinstance(v, str) and not v.strip()):
        return ""
    if isinstance(v, bool) or not isinstance(v, (int, float, str)):
        raise CmsPageError(f"{where}: {key} 형식이 잘못되었습니다 (현재: '{v}')")
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    return f"{v:,}" if isinstance(v, (int, float)) else str(v).strip()


def _upload(v, where, key, site, prefix="/uploads/"):
    s = str(v or "").strip()
    if not s:
        return ""
    if not s.startswith(prefix) or ".." in s:
        raise CmsPageError(f"{where}: {key} 는 {prefix} 로 시작해야 합니다 (현재: '{s}')")
    if not (site / s.lstrip("/")).is_file():
        raise CmsPageError(f"{where}: {key} 파일이 없습니다: {s}")
    return s


def _date(v, where):
    if isinstance(v, datetime):
        return v.date().isoformat()
    if isinstance(v, date):
        return v.isoformat()
    s = str(v or "").strip()
    if not s:
        return ""
    if not re.match(r"\d{4}-\d{2}-\d{2}", s):
        raise CmsPageError(f"{where}: date 는 YYYY-MM-DD 형식이어야 합니다 (현재: '{s}')")
    return s[:10]


def load(site: Path, lang: str, public_on) -> list:
    """노출 사례 목록(정렬됨). public_on 이 False 여도 파일 형식은 검사한다."""
    folder = site / FOLDER[lang]
    rows = []
    for f in sorted(folder.glob("*.md")) if folder.is_dir() else []:
        src = f.relative_to(site).as_posix()
        fm, body = split_md(f.read_text(encoding="utf-8"), src)
        slug = f.stem
        if not SLUG.fullmatch(slug):
            raise CmsPageError(f"{src}: 파일 이름(slug)은 영문 소문자·숫자·_·- 만 쓸 수 있습니다 (현재: '{slug}')")
        title = str(fm.get("title") or "").strip()
        if not title:
            raise CmsPageError(f"{src}: title(현장명)이 비어 있습니다.")
        cats = fm.get("categories") or []
        if isinstance(cats, str):
            cats = [cats]
        if not isinstance(cats, list) or any(c not in CATEGORIES for c in cats):
            raise CmsPageError(f"{src}: categories 는 {', '.join(CATEGORIES)} 중에서 고른 목록이어야 합니다 (현재: '{cats}')")
        vid = youtube_id(str(fm.get("youtube") or ""))
        if not vid:
            raise CmsPageError(f"{src}: youtube 에 유튜브 영상 주소를 넣어야 합니다 (현재: '{fm.get('youtube') or ''}')")
        order = fm.get("order", 0)
        order = 0 if order in (None, "") else order
        if isinstance(order, bool) or not isinstance(order, (int, float)):
            raise CmsPageError(f"{src}: order 는 숫자여야 합니다 (현재: '{order}')")
        visible = fm.get("visible", True)
        if not isinstance(visible, bool):
            raise CmsPageError(f"{src}: visible 은 true 또는 false 여야 합니다 (현재: '{visible}')")
        viewer = _upload(fm.get("viewer"), src, "viewer", site, "/uploads/sim/")
        if viewer and not viewer.lower().endswith(".html"):
            raise CmsPageError(f"{src}: viewer 는 .html 파일이어야 합니다 (현재: '{viewer}')")
        related = str(fm.get("related") or "").strip()
        if related and not re.fullmatch(r"/(en/)?board/media/[\w.-]+\.html", related):
            raise CmsPageError(f"{src}: related 는 시공사례 글 주소(/board/media/<번호>.html)여야 합니다 (현재: '{related}')")
        row = {"src": src, "slug": slug, "title": title, "cats": [c for c in CATEGORIES if c in cats], "vid": vid,
               "thumbnail": _upload(fm.get("thumbnail"), src, "thumbnail", site), "viewer": viewer, "related": related,
               "order": order, "date": _date(fm.get("date"), src), "visible": visible, "body": html_safe.safe(body.strip(), src),
               "out": ("en/" if lang == "en" else "") + f"simulation/{slug}.html"}
        for k in ("kwp", "modules", "arrays", "parking"):
            row[k] = _num(fm.get(k), src, k)
        rows.append(row)
    rows = [r for r in rows if r["visible"]]
    rows.sort(key=lambda r: r["date"], reverse=True)
    rows.sort(key=lambda r: r["order"])
    return rows if public_on else []


def published_sources(site: Path, cases: dict) -> set:
    """업로드 사용 검사에 넣을 사례 파일(노출되는 것만)."""
    return {site / r["src"] for v in cases.values() for r in v}


def _cat_label(c, lang):
    return CAT_EN.get(c, c) if lang == "en" else c


def _thumb(r):
    return ("%%ROOT%%" + r["thumbnail"].lstrip("/")) if r["thumbnail"] else f"https://i.ytimg.com/vi/{r['vid']}/hqdefault.jpg"


def _facts(r, lang):
    out = []
    for k in ("kwp", "modules", "arrays", "parking"):
        if r[k]:
            label, unit = L[lang][k]
            v = html.escape(r[k])
            out.append({"label": label, "value": f"{v} {unit}".strip() if unit and re.fullmatch(r"[\d.,]+", r[k]) else v})
    return out


def _mb(n):
    mb = max(n / 1024 / 1024, 0.1)
    return f"{mb:.1f}" if mb < 10 else f"{round(mb)}"


def render_list(env, lang, cases, intro):
    cats = [c for c in CATEGORIES if any(c in r["cats"] for r in cases)]
    cards = [{"href": "%%ROOT%%" + r["out"], "thumb": _thumb(r), "title": html.escape(r["title"]),
              "cats": " ".join(str(cats.index(c) + 1) for c in r["cats"]),
              "cat_text": html.escape(", ".join(_cat_label(c, lang) for c in r["cats"])),
              "kwp": _facts(r, lang)[0]["value"] if r["kwp"] else ""} for r in cases]
    return env.get_template("sim_list.html").render(
        lang=lang, L=L[lang], intro=html.escape(intro).replace("\n", "<br>\n"),
        categories=[html.escape(_cat_label(c, lang)) for c in cats], cards=cards)


def render_view(env, lang, r, site, inquiry_on):
    size = (site / r["viewer"].lstrip("/")).stat().st_size if r["viewer"] else 0
    contact = ("page/inquiry.html", L[lang]["inquiry"]) if inquiry_on else ("page/location.html", L[lang]["location"])
    return env.get_template("sim_view.html").render(
        lang=lang, L=L[lang], title=html.escape(r["title"]), facts=_facts(r, lang), vid=r["vid"],
        cat_text=html.escape(", ".join(_cat_label(c, lang) for c in r["cats"])),
        viewer=("%%ROOT%%" + r["viewer"].lstrip("/")) if r["viewer"] else "", mb=_mb(size), thumb=_thumb(r),
        body=r["body"], related=("%%ROOT%%" + r["related"].lstrip("/")) if r["related"] else "",
        contact_href="%%ROOT%%" + ("en/" if lang == "en" else "") + contact[0], contact_label=contact[1],
        list_href="%%ROOT%%" + LIST_OUT[lang])


def setting(d: dict, fname: str):
    """site.yml → (simulation_public, simulation_intro)."""
    on = d.get("simulation_public", False)
    if not isinstance(on, bool):
        raise CmsPageError(f"{fname}: simulation_public 은 true 또는 false 여야 합니다 (현재: '{on}')")
    return on, str(d.get("simulation_intro") or "").strip()
