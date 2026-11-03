"""
이미지·동영상 최적화 (설계서 4장). build/all.py가 build.py 앞에서 실행한다. 몇 번을 다시 실행해도 결과가 같다.

없는 것만 만든다(새 글을 posts.json에 넣고 이미지를 static/data/... 에 넣은 뒤 all.py만 실행하면 된다)
0) 새 글의 축소본(원본 그누보드와 같은 규칙)
   - 글 화면: 폭 1400px 넘는 이미지 → thumb-{이름}_1400x{높이}.{확장자} (비율 유지, 품질 90)
   - 목록: 첫 이미지(이미지 첨부 → 없으면 본문 첫 이미지) → _900x600(좌측)·_420x280(우측), 가운데 자르기
   - 메인 회사소식(notice·notice_en): _443x243, 가운데 자르기
1) 확대본(D3): 글 화면에서 축소본으로 보여 주는 원본 → large-{이름}.jpg (긴 변 1920px, 품질 82)
   - 수집 원본(original/www)에서 온 원본은 static/에서 지움(다시 만들 수 있음)
   - 새로 올린 원본은 static/에 남기되 공개(public/)에서는 뺌 → content/publish_exclude.json
2) 페이지에서 쓰는 1MB 초과 이미지: 긴 변 2560px, 품질 82 (JPEG 같은 이름 / 투명 PNG는 PNG 최적화 / 불투명 PNG는 .jpg로 이름 변경, D13)
   - 한 번 처리한 결과는 content/optimize_manifest.json에 기록해 두고 다시 압축하지 않는다
3) 동영상 .mov → MP4 H.264, 폭 1920 이하 (D8)
4) 글꼴: @font-face에 woff2가 있으면 예비 형식 제거 (D13)
5) 바뀐 파일 이름은 content/renames.json에 누적 → build.py가 HTML 주소를, 여기서 CSS·JS 주소를 바꾼다

실행: python build/optimize.py [--report]   (site/ 폴더에서. --report면 ../docs/최적화결과.md 표를 새로 씀)
"""
import hashlib
import io
import json
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageOps

SITE = Path(__file__).resolve().parent.parent
HOME = SITE.parent
WWW = HOME / "original" / "www"          # 내 PC에만 있음(Actions에는 없음)
STATIC, CONTENT, TEMPLATES = SITE / "static", SITE / "content", SITE / "templates"
REPORT = HOME / "docs" / "최적화결과.md"
RENAMES, MANIFEST, EXCLUDE = CONTENT / "renames.json", CONTENT / "optimize_manifest.json", CONTENT / "publish_exclude.json"

LARGE_MAX, LARGE_Q = 1920, 82
PAGE_MAX, PAGE_Q = 2560, 82
THUMB_Q = 90                              # 원본 그누보드 축소본 품질
NEWS_THUMB = (443, 243)
BIG = 1024 * 1024
IMG_EXT = (".jpg", ".jpeg", ".png")

sys.path.insert(0, str(Path(__file__).resolve().parent))
import boards as B   # noqa: E402  (축소본 찾기 규칙을 빌드와 같이 쓴다)


def load(p, default):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


def save(p, data):
    p.write_text(json.dumps(data, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8", newline="\n")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:20]


def source(rel: str):
    """최적화 원본: original/www의 같은 경로 → 없으면 static/의 파일 → 없으면 None."""
    for base in (WWW, STATIC):
        p = base / rel
        if p.is_file():
            return p
    return None


def has_alpha(im: Image.Image) -> bool:
    if im.mode in ("RGBA", "LA"):
        return im.getchannel("A").getextrema()[0] < 255
    return im.mode == "P" and "transparency" in im.info


def rgb(im: Image.Image) -> Image.Image:
    im = ImageOps.exif_transpose(im)   # 휴대폰 사진의 회전 정보를 실제 픽셀에 반영
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGB", im.size, "white")
        bg.paste(im, mask=im.getchannel("A"))
        return bg
    return im if im.mode == "RGB" else im.convert("RGB")


def encode(im: Image.Image, ext: str, q: int) -> bytes:
    buf = io.BytesIO()
    if ext == ".png":
        im.save(buf, "PNG", optimize=True)
    else:
        rgb(im).save(buf, "JPEG", quality=q, optimize=True, progressive=q != THUMB_Q)
    return buf.getvalue()


def to_jpeg(im: Image.Image, max_side: int, q: int) -> bytes:
    im = rgb(im)
    if max(im.size) > max_side:
        im.thumbnail((max_side, max_side), Image.LANCZOS)
    return encode(im, ".jpg", q)


def post_images(p):
    """글의 이미지: (본문 이미지 경로들, 목록 썸네일 원본)."""
    content = [s for s in (B.site_path(x) for x in re.findall(r'<img[^>]+src="([^"]+)"', p["content"])) if s]
    files = [f["stored"] for f in sorted(p["files"], key=lambda f: f["no"]) if f["stored"].lower().endswith(B.IMG_EXT)]
    first = (files or content or [None])[0]
    return content + files, first


def main(report=False):
    posts = json.loads((CONTENT / "posts.json").read_text(encoding="utf-8"))
    renames, manifest = load(RENAMES, {}), load(MANIFEST, {})
    exclude = {e for e in load(EXCLUDE, []) if (STATIC / e).exists()}   # 지워진 파일은 목록에서도 뺌
    stats, warn = {}, []

    def stat(k, b0, b1):
        s = stats.setdefault(k, [0, 0, 0]); s[0] += 1; s[1] += b0; s[2] += b1

    site = B.Site(STATIC)

    # 0) 새 글의 축소본: 지금 화면 배치에 필요한 것만(원본처럼 목록 각 쪽 첫 글은 900x600, 나머지는 420x280, 메인은 최신 4건)
    boards_cfg = load(CONTENT / "boards.json", {})
    generated = set(manifest.get("_generated", []))   # 이 스크립트가 만든 축소본(더 이상 안 쓰이면 지움)
    needed = set()
    for table, items in posts["boards"].items():
        per = boards_cfg.get(table, {}).get("page_rows", 7)
        for i, p in enumerate(items):
            imgs, first = post_images(p)
            jobs = []
            for s in imgs:
                real = site.real(s) or s.lstrip("/")
                th = site.thumb(real, B.VIEW_THUMB_W)
                if th:
                    needed.add(th)
                else:
                    jobs.append((real, "view", None))
            if first:
                real = site.real(first) or first.lstrip("/")
                sizes = [B.LIST_THUMB["left"] if i % per == 0 else B.LIST_THUMB["right"]]
                if table in ("notice", "notice_en") and i < 4:
                    sizes.append(NEWS_THUMB)
                for w, h in sizes:
                    th = site.thumb(real, w, h)
                    if th:
                        needed.add(th)
                    else:
                        jobs.append((real, "crop", (w, h)))
            for real, kind, size in jobs:
                src = source(real)
                if src is None:
                    warn.append(f"{table} {p['id']}: 이미지 파일 없음 {real}")
                    continue
                im = Image.open(src)
                d, name = real.rsplit("/", 1)
                stem, ext = name.rsplit(".", 1)
                ext = "." + ext.lower()
                if kind == "view":
                    if im.width <= B.VIEW_THUMB_W:
                        continue   # 원본처럼 작은 이미지는 축소본 없이 원본을 그대로 보여 준다
                    h = int(B.VIEW_THUMB_W * im.height / im.width + 0.5)
                    out = ImageOps.exif_transpose(im).resize((B.VIEW_THUMB_W, h), Image.LANCZOS)
                    dst = STATIC / d / f"thumb-{stem}_{B.VIEW_THUMB_W}x{h}{ext}"
                else:
                    out = ImageOps.fit(ImageOps.exif_transpose(im), size, Image.LANCZOS, centering=(0.5, 0.5))
                    dst = STATIC / d / f"thumb-{stem}_{size[0]}x{size[1]}{ext}"
                dst.parent.mkdir(parents=True, exist_ok=True)
                data = encode(out if ext == ".png" else out, ext, THUMB_Q)
                dst.write_bytes(data)
                rel_dst = dst.relative_to(STATIC).as_posix()
                site.files[rel_dst.lower()] = rel_dst
                generated.add(rel_dst)
                needed.add(rel_dst)
                stat("새 글 축소본 생성(원본 규칙: 글 1400px 비율 유지, 목록 900x600·420x280, 메인 443x243 가운데 자르기)",
                     src.stat().st_size, len(data))
    # 이 스크립트가 만들었지만 이제 쓰이지 않는 축소본(글 순서가 밀려 크기가 바뀐 경우 등)은 지운다. 수집 원본의 축소본은 건드리지 않음
    for rel in sorted(generated - needed):
        if (STATIC / rel).exists():
            stat("쓰이지 않게 된 생성 축소본 삭제", (STATIC / rel).stat().st_size, 0)
            (STATIC / rel).unlink()
        generated.discard(rel)
    manifest["_generated"] = sorted(generated)

    # 1) 확대본 large-*.jpg (없는 것만)
    corpus = "\n".join(f.read_text(encoding="utf-8", errors="ignore").lower()
                       for f in list((CONTENT / "pages").rglob("*.html")) + list(TEMPLATES.glob("*.html"))
                       + [x for x in STATIC.rglob("*") if x.suffix.lower() in (".css", ".js") and "hb" not in x.parts])
    targets = set()
    for items in posts["boards"].values():
        for p in items:
            for s in post_images(p)[0]:
                real = site.real(s) or s.lstrip("/")
                if site.thumb(real, B.VIEW_THUMB_W):
                    targets.add(real)
    for rel in sorted(targets):
        d, name = rel.rsplit("/", 1)
        out = STATIC / d / f"large-{name.rsplit('.', 1)[0]}.jpg"
        if not out.exists():
            src = source(rel)
            if src is None:
                warn.append(f"확대본 원본 없음 {rel}")
                continue
            data = to_jpeg(Image.open(src), LARGE_MAX, LARGE_Q)
            out.write_bytes(data)
            stat("확대본 large-*.jpg 생성 (D3, 1920px·q82)", src.stat().st_size, len(data))
        orig = STATIC / rel
        if orig.exists() and rel.lower() not in corpus:
            if (WWW / rel).exists():
                orig.unlink()                 # 수집 원본은 original/www에 있으므로 static/에서 뺀다
            else:
                exclude.add(rel)              # 새로 올린 원본: 저장소에는 남기고 공개에서만 뺀다

    # 2) 페이지에서 쓰는 1MB 초과 이미지 (한 번 처리한 결과는 다시 압축하지 않음)
    kinds = {"jpg": "1MB 초과 JPEG 재압축(2560px·q82, 같은 이름)", "png_alpha": "1MB 초과 투명 PNG 최적화(PNG 유지)",
             "png_to_jpg": "1MB 초과 불투명 PNG → JPEG(2560px·q82, 이름 .jpg로 변경)", "kept": "1MB 초과지만 줄지 않아 원본 유지"}
    for f in sorted(STATIC.rglob("*")):
        rel = f.relative_to(STATIC).as_posix()
        if (not f.is_file() or f.suffix.lower() not in IMG_EXT or f.name.startswith("large-")
                or rel.startswith(("hb/", "vendor/")) or rel in exclude):
            continue
        if manifest.get(rel) == sha(f):
            continue   # 이미 처리한 결과
        src = source(rel)
        if src.stat().st_size <= BIG:
            continue
        im = Image.open(src)
        size0 = src.stat().st_size
        if f.suffix.lower() in (".jpg", ".jpeg"):
            data, kind, out = to_jpeg(im, PAGE_MAX, PAGE_Q), "jpg", f
        elif has_alpha(im):
            im2 = ImageOps.exif_transpose(im)
            if max(im2.size) > PAGE_MAX:
                im2.thumbnail((PAGE_MAX, PAGE_MAX), Image.LANCZOS)
            data, kind, out = encode(im2, ".png", 0), "png_alpha", f
        else:
            out = f.with_suffix(".jpg")
            if out.exists() and out != f:
                out = f.with_name(f.stem + "_png.jpg")
            data, kind = to_jpeg(im, PAGE_MAX, PAGE_Q), "png_to_jpg"
        if len(data) >= size0:
            kind, data, out = "kept", src.read_bytes(), f
        out.write_bytes(data)
        if out != f:
            f.unlink()
            renames[rel] = out.relative_to(STATIC).as_posix()
            if rel in generated:   # 방금 만든 축소본이 PNG→JPG로 바뀐 경우
                generated.discard(rel)
                generated.add(out.relative_to(STATIC).as_posix())
                manifest["_generated"] = sorted(generated)
        manifest[out.relative_to(STATIC).as_posix()] = sha(out)
        stat(kinds[kind], size0, len(data))

    # 3) 동영상 .mov → .mp4 (D8)
    movs = sorted(STATIC.rglob("*.mov"))
    if movs:
        import imageio_ffmpeg
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        for f in movs:
            rel = f.relative_to(STATIC).as_posix()
            src = source(rel)
            out = f.with_suffix(".mp4")
            # 화면 전체 배경 영상: 폭 1920 이하로(원본 4K), 소리가 있으면 AAC
            subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", str(src), "-map", "0:v:0", "-map", "0:a?",
                            "-vf", "scale='min(1920,iw)':-2", "-c:v", "libx264", "-preset", "slow", "-crf", "23",
                            "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-c:a", "aac", "-b:a", "128k", str(out)], check=True)
            renames[rel] = out.relative_to(STATIC).as_posix()
            stat(f"동영상 .mov → MP4 H.264 (D8): {rel}", src.stat().st_size, out.stat().st_size)
            f.unlink()

    # 4) 글꼴 예비 형식 (D13)
    used = set()
    for f in STATIC.rglob("*.css"):
        if "hb" in f.parts or "vendor" in f.parts:
            continue
        t = f.read_bytes().decode("utf-8", errors="surrogateescape")

        def face(m):
            block = m.group(0)
            src = re.search(r"src\s*:([^;}]*)", block)
            if not src or "woff2" not in src.group(1):
                return block
            keep = [s.strip() for s in re.split(r",(?![^(]*\))", src.group(1)) if "woff2" in s]
            return block.replace(src.group(0), "src: " + ", ".join(keep))
        t2 = re.sub(r"@font-face\s*\{[^}]*\}", face, t)
        if t2 != t:
            f.write_bytes(t2.encode("utf-8", errors="surrogateescape"))
        used |= {(f.parent / u).resolve() for u in re.findall(r"""url\(\s*['"]?([^'")?#]+)""", t2)}
    for x in list(STATIC.rglob("*")):
        if x.suffix.lower() in (".otf", ".ttf", ".woff", ".eot") and x.resolve() not in used:
            stat("글꼴 예비 형식(otf·woff 등) 제거 (D13, woff2만 사용)", x.stat().st_size, 0)
            x.unlink()

    # 5) 바뀐 이름을 static/의 CSS·JS에 반영(상대 주소라 파일 이름으로, 같은 이름이 여러 폴더에 있으면 건너뜀)
    names = {}
    for x in list(STATIC.rglob("*")) + [STATIC / o for o in renames]:
        names.setdefault(x.name.lower(), set()).add(x.parent.as_posix())
    for f in STATIC.rglob("*"):
        if f.suffix.lower() in (".css", ".js") and "hb" not in f.parts and "vendor" not in f.parts:
            t = f.read_bytes().decode("utf-8", errors="surrogateescape")
            t2 = t
            for old, new in renames.items():
                on, nn = old.rsplit("/", 1)[-1], new.rsplit("/", 1)[-1]
                pat = re.compile(rf"(?<![\w.\-]){re.escape(on)}(?![\w\-])")
                if pat.search(t2):
                    if len(names.get(on.lower(), ())) > 1:
                        warn.append(f"{f.name}: 같은 이름 {on}이 여러 폴더에 있어 바꾸지 않음")
                        continue
                    t2 = pat.sub(nn, t2)
            if t2 != t:
                f.write_bytes(t2.encode("utf-8", errors="surrogateescape"))

    save(RENAMES, renames)
    save(MANIFEST, manifest)
    save(EXCLUDE, sorted(exclude))

    total = sum(x.stat().st_size for x in STATIC.rglob("*") if x.is_file())
    for k, (n, b0, b1) in stats.items():
        print(f"{k}: {n}개 {b0 / 1048576:,.1f}MB → {b1 / 1048576:,.1f}MB")
    if not stats:
        print("최적화: 새로 처리할 파일 없음")
    for w in warn:
        print("주의:", w)
    print(f"static/ 전체 {total / 1048576:,.1f}MB, 이름 변경 누적 {len(renames)}개, 공개 제외 {len(exclude)}개")
    if report:
        lines = ["# 최적화 결과", "", "`python build/optimize.py --report` 실행 결과(이번 실행에서 처리한 것).", "",
                 "| 처리 | 파일 수 | 원본 | 결과 |", "|---|---|---|---|"]
        lines += [f"| {k} | {n} | {b0 / 1048576:,.1f}MB | {b1 / 1048576:,.1f}MB |" for k, (n, b0, b1) in stats.items()]
        lines += ["", f"- static/ 전체: {total / 1048576:,.1f}MB", f"- 이름이 바뀐 파일 {len(renames)}개: `site/content/renames.json`", ""]
        lines += [f"  - {o} → {n}" for o, n in renames.items()]
        REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return stats, warn


if __name__ == "__main__":
    main(report="--report" in sys.argv)
