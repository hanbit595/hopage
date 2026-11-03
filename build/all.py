"""
전체 빌드 한 번에: optimize.py(이미지·동영상 최적화, 새 글 축소본·확대본) → build.py(페이지 생성 → public/)

- 글을 고치거나 새 글을 넣었을 때는 이것만 실행하면 된다. GitHub Actions(.github/workflows/deploy.yml)도 이것을 실행한다.
    python build/all.py          (site/ 폴더에서)
    미리보기: python -m http.server 8000 -d public
- 새 글 넣는 법: content/posts.json의 게시판 목록 맨 앞에 글을 추가하고, 본문·첨부 이미지는 static/data/editor/… 등
  본문에 적은 경로에 넣는다. 축소본·확대본은 이 스크립트가 없는 것만 만든다.

※ extract_pages.py(수집본 crawl/·FTP 원본 original/에서 틀·본문·자산을 다시 뽑기)는 여기에 넣지 않는다.
  그 폴더들은 내 PC에만 있고 저장소에는 없기 때문이다. 다시 뽑아야 할 때만 내 PC에서 수동으로:
    python build/extract_pages.py   →   python build/all.py
  (extract_pages.py는 static/을 원본으로 다시 채우므로 반드시 all.py를 이어서 실행)
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
for step in ("optimize.py", "build.py"):
    print(f"===== {step} =====", flush=True)
    subprocess.run([sys.executable, str(HERE / step)], check=True, cwd=HERE.parent)
print("===== 완료 =====")
