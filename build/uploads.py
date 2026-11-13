"""
관리자 화면 업로드 이미지(uploads/) → public/uploads/ (P3-4b). build.py 가 불러 쓴다.

- uploads/ 원본은 읽기만 한다(수정·삭제 안 함). 결과는 매 빌드 public/uploads/ 에 새로 만든다.
- JPEG·PNG: 긴 변 1920px 이하로 줄임(D3 확대본과 같은 기준, docs/spec.md 6절). 원본이 더 작으면 그대로 복사(확대 안 함).
  JPEG 품질 85, PNG 는 PNG 그대로(투명 유지). 축소·인코딩은 optimize.py 의 rgb·encode 를 그대로 쓴다(A4).
  그 밖의 파일(gif·webp·svg·pdf 등)은 그대로 복사.
- 축소본은 필요할 때만 만든다(boards.Site 가 uploads/ 경로를 물으면 여기로 넘김). 이름 규칙은 기존 static/ 축소본과 같다.
  - 글 화면: 폭 1400px 넘는 이미지 → thumb-{이름}_1400x{높이}.{확장자} (확대 보기는 1920px 본)
  - 목록 900x600·420x280, 메인 News 443x243, 메인 Our Project 900x600: 가운데 자르기
"""
import shutil
from pathlib import Path

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

    def process(self):
        """uploads/ 전체 → public/uploads/. 원본 합계 바이트 수를 기록한다."""
        if not self.src.is_dir():
            return
        for f in sorted(self.src.rglob("*")):
            if not f.is_file():
                continue
            rel = f.relative_to(self.src).as_posix()
            dst = self.out / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            self.src_bytes += f.stat().st_size
            ext = f.suffix.lower()
            if ext in RESIZE_EXT:
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
        if mb(total) > LIMIT_MB:
            print(f"  경고: public/ 이 {LIMIT_MB}MB(D13 용량 규칙)를 넘었습니다. 업로드 이미지를 줄이거나 정리하세요.")
