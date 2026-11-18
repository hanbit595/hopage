"""
P6 1회용(2026-11-18 실행 완료, 다시 돌리지 않음): 고정 페이지 21개(국·영 42개) 본문을 content/pages/{ko,en}/page/<이름>.html → cms/free/<이름>.md·cms/en/free/<이름>.md 로 옮긴다.
틀(상단 제목·메뉴 자리·감싸는 div·스크립트)은 content/pages 쪽에 남기고 본문 자리에 %%FREE_BODY%% 를 둔다.
ESG 는 cms/pages/esg.yml·cms/en/pages/esg.yml 로 렌더링한 결과를 옮긴다(yml 은 남김).
옮긴 뒤 build/cms_free.py 로 다시 합친 결과가 원래 조각과 글자 하나까지 같은지 검사하고, 다르면 아무것도 쓰지 않는다.
    python build/migrate_free.py [--write]
"""
import json
import re
import sys
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import cms_free  # noqa: E402
import cms_pages  # noqa: E402

SITE = HERE.parent
CONTENT = SITE / "content" / "pages"
NAMES = ("epc pv bipv carport solar_village kpso de_system structure combiner fire_cert monitoring inverter "
         "re100 zeb vnm carbon housing building self_energy finance esg").split()
VISUAL = {"solar_village", "zeb", "vnm", "structure", "combiner", "fire_cert", "monitoring"}   # 위험 '하'
def trail_start(s, pos):
    """s[pos:] 끝에서부터 공백·</div>·</section>·<script>…</script>·<!--…--> 만 이어지는 구간의 시작 위치."""
    end = len(s)
    while end > pos:
        t = s[pos:end]
        if t[-1].isspace():
            end -= 1
        elif t.endswith("</div>") or t.endswith("</section>"):
            end = pos + t.rfind("</")
        elif t.endswith("</script>"):
            end = pos + t.rfind("<script")
        elif t.endswith("-->"):
            end = pos + t.rfind("<!--")
        else:
            break
    return end
SCRIPT = re.compile(r"<script\b.*?</script>|<!--(?:(?!-->).)*<script\b.*?-->", re.S)


def esg_rendered(lang, frag):
    def esc(s):
        s = re.sub(r"&(?!\s)", "&amp;", str(s))
        return s.replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    env = Environment(loader=FileSystemLoader(SITE / "templates"), autoescape=False, undefined=StrictUndefined,
                      keep_trailing_newline=True)
    env.filters.update(esc=esc, ml=cms_pages.ml, img=cms_pages.img, esc_text=cms_pages.esc_text)
    rn = SITE / "content" / "renames.json"
    renames = json.loads(rn.read_text(encoding="utf-8")) if rn.exists() else {}
    data = cms_pages.load("esg", SITE, SITE / "public", renames, lang)
    return cms_pages.render(env, frag, data)


def split(s):
    i = s.find('class="visual_nav_box"')   # 사업분야·제품·정부지원·ESG: 상단 제목 + 메뉴 상자까지가 틀
    if i < 0:   # 탄소중립 4개: 메뉴·제목(h1)·소개 문구(<p class="info sec_txt2">, 있으면)까지가 틀
        i = s.find('class="info sec_txt2"')
        pos = s.index("</p>", i) + 4 if i >= 0 else s.index("</h1>") + 5
    else:
        st = s.rfind("<div", 0, i)
        d, pos = 0, None
        for m in re.finditer(r"<div\b|</div>", s[st:]):
            d += 1 if m.group() == "<div" else -1
            if d == 0:
                pos = st + m.end()
                break
    while (m := re.match(r"\s*</div>", s[pos:])):   # 바로 뒤에 상단 상자를 닫는 태그가 오면 틀에 포함
        pos += m.end()
    end = trail_start(s, pos)   # 끝의 닫는 태그·스크립트·주석·공백은 틀(꼬리)에 둔다
    # 단, 본문 안에서 연 div·section 을 닫는 태그는 본문으로 되돌린다(본문 태그 균형)
    while True:
        b = s[pos:end]
        m = re.match(r"\s*</(div|section)>", s[end:])
        if not m:
            break
        t = m.group(1)
        if len(re.findall(rf"<{t}\b", b)) - len(re.findall(rf"</{t}>", b)) <= 0:
            break
        end += m.end()
    head, body, tail = s[:pos], s[pos:end], s[end:]
    scripts = []

    def keep(m):
        scripts.append(m.group(0))
        return f"<!--hb-script-{len(scripts)}-->"
    body = SCRIPT.sub(keep, body)
    frame = head + cms_free.SLOT + tail + "".join(
        f"\n<!--%%FREE_SCRIPT:{n}%%-->{x}<!--%%END%%-->" for n, x in enumerate(scripts, 1))
    return frame, body, scripts


def main(write):
    meta = json.loads((CONTENT / "meta.json").read_text(encoding="utf-8"))
    plan, bad = [], []
    for lang in ("ko", "en"):
        for n in NAMES:
            m = meta[f"{lang}/page/{n}"]
            src = CONTENT / m["content"]
            orig = src.read_text(encoding="utf-8")
            frag = esg_rendered(lang, orig) if n == "esg" else orig
            frame, body, scripts = split(frag)
            md_body = cms_free.from_root(body)
            if cms_free.sanitize(body) != body:
                bad.append(f"{lang}/{n}: 안전 처리로 본문이 바뀜")
            if cms_free.fill(frame, cms_free.to_root(cms_free.sanitize(md_body))) != frag:
                bad.append(f"{lang}/{n}: 다시 합친 결과가 원래와 다름")
            bal = len(re.findall(r"<div\b", body)) - len(re.findall(r"</div>", body))
            fm = {"title": m["title"], "path": "/" + m["out"], "editor_mode": "visual" if n in VISUAL else "html"}
            md = "---\n" + yaml.safe_dump(fm, allow_unicode=True, sort_keys=False, default_style='"') + "---\n" + md_body
            plan.append((src, frame, SITE / cms_free.md_path(m["out"]), md))
            print(f"{lang}/{n}: 본문 {len(body)}자, 본문 div 균형 {bal:+d}, 틀로 옮긴 본문 중간 스크립트 {len(scripts)}개, {fm['editor_mode']}")
    if bad:
        print("중단:\n  " + "\n  ".join(bad))
        sys.exit(1)
    if write:
        for src, frame, dst, md in plan:
            src.write_text(frame, encoding="utf-8", newline="\n")
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(md, encoding="utf-8", newline="\n")
        print(f"썼음: 틀 {len(plan)}개, 본문 {len(plan)}개")


if __name__ == "__main__":
    main("--write" in sys.argv)
