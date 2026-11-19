"""
관리자 화면 업로드 이미지(uploads/) → public/uploads/ (P3-4b). build.py 가 불러 쓴다.

- uploads/ 원본은 읽기만 한다(수정·삭제 안 함). 결과는 매 빌드 public/uploads/ 에 새로 만든다.
- JPEG·PNG: 긴 변 1920px 이하로 줄임(D3 확대본과 같은 기준, docs/spec.md 6절). 원본이 더 작으면 그대로 복사(확대 안 함).
  JPEG 품질 85, PNG 는 PNG 그대로(투명 유지). 축소·인코딩은 optimize.py 의 rgb·encode 를 그대로 쓴다(A4).
  그 밖의 파일(gif·webp·svg·pdf 등)은 그대로 복사.
- 쓰이지 않는 업로드(P3-5c-2): cms/·content/·templates/ 원본 어디에도 /uploads/<이름> 이 없으면 public/ 에 넣지 않고
  빌드 끝에 "쓰이지 않는 업로드: N개(목록)" 로 알린다. 원본 삭제는 하지 않는다.
- 축소본은 필요할 때만 만든다(boards.Site 가 uploads/ 경로를 물으면 여기로 넘김). 이름 규칙은 기존 static/ 축소본과 같다.
  - 글 화면: 폭 1400px 넘는 이미지 → thumb-{이름}_1400x{높이}.{확장자} (확대 보기는 1920px 본)
  - 목록 900x600·420x280, 메인 News 443x243, 메인 Our Project 900x600: 가운데 자르기
"""
import html
import shutil
from pathlib import Path
from urllib.parse import unquote

from PIL import Image, ImageOps

import optimize as O   # 이미지 처리 규칙(rgb·encode)을 기존 최적화와 같이 쓴다

MAX_SIDE = 1920
JPEG_Q = 85
RESIZE_EXT = (".jpg", ".jpeg", ".png")
LIMIT_MB = 300   # D13 용량 규칙


class Uploads:
    def __init__(self, src: Path, out: Path):
        self.src, self.out = src, out
        self.files = {}      # "uploads/a.jpg"(소문자) → "uploads/a.jpg"(실제 이름)
        self.src_bytes = 0
        self.used = None     # find_used 결과(쓰이는 업로드, uploads/ 기준 경로). None 이면 전체를 넣는다
        self.unused = []

    def find_used(self, sources):
        """P3-5c-2: 글·페이지·설정 원본(sources: 파일 목록)에서 /uploads/… 로 쓰인 업로드만 골라 self.used 에 둔다.
        주소는 대소문자 무시, %인코딩(공백·한글)·HTML 엔티티(&amp;)로 적힌 것도 찾는다."""
        blob = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in sources).lower()
        texts = (blob, unquote(blob), html.unescape(blob), unquote(html.unescape(blob)))
        self.used, self.unused = set(), []
        if not self.src.is_dir():
            return
        for f in sorted(self.src.rglob("*")):
            if f.is_file():
                rel = f.relative_to(self.src).as_posix()
                if any(f"uploads/{rel}".lower() in t for t in texts):
                    self.used.add(rel)
                else:
                    self.unused.append(rel)

    def process(self):
        """uploads/ 중 쓰이는 파일만 → public/uploads/ (find_used 를 먼저 부르지 않으면 전체). 원본 합계 바이트 수를 기록한다."""
        if not self.src.is_dir():
            return
        for f in sorted(self.src.rglob("*")):
            if not f.is_file():
                continue
            rel = f.relative_to(self.src).as_posix()
            if self.used is not None and rel not in self.used:
                continue   # 어디에서도 쓰이지 않는 업로드는 배포본에 넣지 않는다(원본은 그대로)
            dst = self.out / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            self.src_bytes += f.stat().st_size
            ext = f.suffix.lower()
            if ext in RESIZE_EXT and not rel.lower().startswith("sim/"):   # P8 3D 파일 폴더(uploads/sim)는 최적화하지 않음
                im = Image.open(f)
                im.load()
                im2 = ImageOps.exif_transpose(im)
                if max(im2.size) > MAX_SIDE:
                    im2.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
                    dst.write_bytes(O.encode(im2, ".png" if ext == ".png" else ".jpg", JPEG_Q))
                else:
                    shutil.copyfile(f, dst)   # 작은 원본은 그대로
            else:
                shutil.copyfile(f, dst)
            self.files[f"uploads/{rel}".lower()] = f"uploads/{rel}"

    def real(self, path: str):
        return self.files.get(path.lstrip("/").lower())

    def thumb(self, path: str, w: int, h: int = None):
        """기존 Site.thumb 와 같은 뜻. h 가 없으면 글 화면 축소본(폭 w 넘을 때만), 있으면 가운데 자르기."""
        real = self.real(path)
        if not real or not real.lower().endswith(RESIZE_EXT):
            return None
        d, name = real.rsplit("/", 1)
        stem, ext = name.rsplit(".", 1)
        ext = "." + ext.lower()
        im = ImageOps.exif_transpose(Image.open(self.src / real[len("uploads/"):]))
        if h is None:
            if im.width <= w:
                return None
            hh = int(w * im.height / im.width + 0.5)
            out_im, rel = im.resize((w, hh), Image.LANCZOS), f"{d}/thumb-{stem}_{w}x{hh}{ext}"
        else:
            out_im, rel = ImageOps.fit(im, (w, h), Image.LANCZOS, centering=(0.5, 0.5)), f"{d}/thumb-{stem}_{w}x{h}{ext}"
        dst = self.out.parent / rel
        if not dst.exists():
            dst.write_bytes(O.encode(out_im, ext, O.THUMB_Q))
        return rel

    def large(self, path: str):
        """확대 보기용: 1920px 이하로 줄인 본."""
        return self.real(path)

    def report(self, public: Path):
        """빌드 끝 용량 보고(C2). public/ 이 300MB 를 넘으면 경고만 한다(실패 아님)."""
        out_bytes = sum(f.stat().st_size for f in self.out.rglob("*") if f.is_file()) if self.out.is_dir() else 0
        total = sum(f.stat().st_size for f in public.rglob("*") if f.is_file())
        mb = lambda n: n / 1048576
        print(f"  업로드 이미지: 원본 합계 {mb(self.src_bytes):.1f}MB → 배포 합계 {mb(out_bytes):.1f}MB, "
              f"public/ 전체 {mb(total):.1f}MB / {LIMIT_MB}MB")
        print(f"  쓰이지 않는 업로드: {len(self.unused)}개" + (f"({', '.join(self.unused)})" if self.unused else "")
              + (" — 배포본에 넣지 않음, uploads/ 원본은 그대로" if self.unused else ""))
        if mb(total) > LIMIT_MB:
            print(f"  경고: public/ 이 {LIMIT_MB}MB(D13 용량 규칙)를 넘었습니다. 업로드 이미지를 줄이거나 정리하세요.")
