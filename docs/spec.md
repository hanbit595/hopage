# 관리자페이지 1차 명세 (v2)

v2 변경(2026-11-13): 1절 빌드 경로, 2절 게시판 원본, 4절 메뉴·푸터 생성 방식, 5절 비공개 검사, 6절 기술 조건, 8절 검증 기준·9절 확인 필요 신설.

## 1. 구조
- 관리자 화면 저장소: hanbit595/hpadmin (D:\hpadmin) → https://admin.hanbitinnotech.com (GitHub Pages, 가비아 CNAME)
- 홈페이지 저장소: hanbit595/hopage (D:\homepage\site) → https://hanbitinnotech.com
- 관리자 화면은 Sveltia CMS(https://unpkg.com/@sveltia/cms/dist/sveltia-cms.js, type="module")를 쓰고,
  GitHub 세분화 토큰(PAT) 로그인으로 hopage 저장소에 직접 커밋한다. 인증 서버는 두지 않는다.
- 저장(커밋) → hopage의 기존 GitHub Actions(.github/workflows/deploy.yml)가 기존 build/all.py 실행 → public/ 을 Pages로 배포.
  빌드가 실패하면 배포를 중단하고 기존 사이트를 유지한다.
- 토큰·키는 어떤 파일에도 쓰지 않는다.

## 2. hopage 원본 파일 규칙
- 한글 게시판 글은 cms/<게시판>/<글번호>.md 로 관리한다. 본문(body)은 기존 HTML을 그대로 둔다(markdown 변환하지 않음).
  - cms/notice/*.md   → /board/notice/<파일명>.html   (회사소식)
  - cms/media/*.md    → /board/media/<파일명>.html    (시공사례)
  - cms/library/*.md  → /board/library/<파일명>.html  (E-Catalog)
- ENG 글(notice_en, media_en, library_en)은 content/posts.json 에 그대로 두고 기존 방식으로 빌드한다.
- 목록: /board/<게시판>/index.html, 2페이지부터 page-2.html, page-3.html ... (기존 규칙 유지)
- cms/settings/menu.yml, site.yml, popups.yml
- 업로드: uploads/ (기존 data/ 폴더와 겹치지 않게 함), 공개 경로 /uploads
- 기존 글은 기존 글번호를 파일명으로 쓴다(99.md). 새 글은 YYYYMMDD-HHMMSS 형식이다.
- 1차에서는 한국어만 관리한다. /en/ 이하 ENG 페이지는 수정하지 않는다.
- 규정상 비공개 현장 게시물은 cms/에 넣지 않는다(공개 저장소이므로 임시저장도 외부에 보임).

## 3. 필드
- 회사소식: title, date(YYYY-MM-DD), thumbnail(선택), summary(선택), draft(기본 false), body(HTML)
- 시공사례: title(현장명), category(select: 태양광발전장치/BIPV/주차장태양광/기타), capacity(문자, 선택),
  program(사업구분, 선택), date, thumbnail(선택), gallery(이미지 목록, 선택),
  featured(메인 Our Project 노출, 기본 false), draft, body(선택)
  목록 표시 제목: "[category] title capacity"
- E-Catalog: title, date, thumbnail(선택), file(PDF, 필수), body(선택), draft
- menu.yml: menu[ {label, visible, items[ {label, link, new_window, visible} ]} ]
  대메뉴 클릭 시 첫 번째 노출 소메뉴로 이동한다. link가 /로 시작하면 내부 링크, http로 시작하면 외부 링크다.
- site.yml: offices[{name, address}], tel, email, brochure(PDF), per_page(기본 7), seo_description
- popups.yml: popups[{title, image, link, start, end, active}]
  노출 기간은 브라우저 JS로 오늘 날짜를 비교해 판단한다(빌드 시점에 고정하지 않음). 기존 "24시간 동안 보지 않기" 기능은 유지한다.

## 4. 빌드가 자동 생성·갱신하는 것
- 메뉴(상단 메가메뉴, 모바일 메뉴, 하위 페이지 탭·경로 드롭다운)는 공통 템플릿 조각 하나로 만들고 cms/settings/menu.yml 에서 생성한다.
  템플릿 3곳(_top_ko.html, _board_head_ko.html 등)과 고정 페이지 본문 조각(content/pages/ko/page/*.html)에 복사된 메뉴는
  모두 그 조각을 불러오도록 교체한다(대상 목록은 9절 c).
- 하단 푸터는 cms/settings/site.yml 에서 생성한다.
- 게시판 3종의 목록(페이징)과 상세 페이지. 기존 마크업·클래스를 그대로 써서 디자인을 유지한다.
- 메인: 팝업, News(최신 회사소식), Our Project(featured 시공사례 최신순)
- 상세 페이지 <title>: "제목 | HANBIT Innotech", description: summary(없으면 본문 앞 150자)
- 하단 Copyright 연도는 빌드 시 현재 연도로 넣는다.
- 로고 링크 title 속성 "Animotiontech" → "HANBIT Innotech"
- 정적 사이트에서 동작하지 않는 게시판 검색창은 숨긴다.
- sitemap.xml 에 게시판 URL을 반영한다.

## 5. 빌드 실패 조건 (한국어 오류 메시지 출력 후 종료코드 1)
- 필수 필드 누락, 날짜 형식 오류, 파일명(주소) 중복
- menu.yml의 내부 link가 public/ 안에 존재하지 않음
- 시공사례 category가 허용 목록에 없음, E-Catalog file 누락
- 비공개 검사: build/private_guard.py 와 같은 비공개 검사를 빌드에 포함하고, 비공개 대상이 걸리면 종료코드 1.
  한계: 빌드 실패로 막는 것은 "배포(사이트 노출)"뿐이다. 이미 저장소에 커밋된 글·사진은 GitHub 저장소 화면과 커밋 기록에서 그대로 보인다.
  비공개 대상은 처음부터 관리자 화면에 올리지 않는 것이 원칙이며, 올라간 경우 저장소 기록 정리가 따로 필요하다.

## 6. 기술 조건
- Python 3.12. 의존성은 기존 jinja2, pillow 에 markdown, pyyaml 만 추가 허용한다.
- 제목·요약·경로는 HTML 이스케이프한다.
- 빌드 산출물 public/ 은 git에 올리지 않는다(기존 .gitignore 유지).

## 7. D:\hpadmin 에 만들 파일
- index.html: noindex 메타, 제목 "한빛이노텍 관리자", Sveltia 스크립트만 넣는다.
- config.yml: backend github, repo hanbit595/hopage, branch main, media_folder uploads, public_folder /uploads,
  site_url https://hanbitinnotech.com, collections = 회사소식·시공사례·E-Catalog(folder 컬렉션, 3절 필드, 라벨 한국어,
  새 글 slug "{{year}}{{month}}{{day}}-{{hour}}{{minute}}{{second}}") + "사이트 관리" files 컬렉션(메뉴 관리, 회사정보·기본설정, 메인 팝업)
- CNAME: admin.hanbitinnotech.com
- robots.txt: 모든 크롤러 차단
- .nojekyll (빈 파일)
- CLAUDE.md: "작업 전 docs/spec.md를 읽고 그 기준을 따른다. 명세와 다르게 만들어야 하면 먼저 보고한다."

## 8. 검증 기준
작업 전후 public/ 을 비교한다(작업 전 빌드 결과를 따로 보관해 두고 비교).
- public/en/ 은 완전히 같아야 한다.
- 한글 페이지는 메뉴·푸터·게시판·메인 Our Project/News 영역 외에는 차이가 없어야 한다.
- 기존 게시판 URL(/board/<게시판>/index.html, page-N.html, <글번호>.html) 누락 0건.

## 9. 확인 필요 (2026-11-13 조사 결과, 수정 없음)
a) private_guard.py 의 비공개 판별 목록
- 저장소 안 파일에는 없다. 목록은 저장소 바깥 D:\homepage\private\posts\{게시판}\{글번호}\ 폴더(글 사진은 그 안 post.json)와
  private\main_cards\item_NN\ 폴더 이름에서 읽는다. 저장소(build·content·templates·docs)에서 비공개 현장명 검색 결과 0건,
  content/publish_exclude.json 은 빈 목록([]).
- 따라서 5절 비공개 검사를 GitHub Actions에서 돌리려면 판별 기준을 저장소 안에 두어야 하는데, 공개 저장소에 현장명을 쓰면
  그 자체가 노출된다 → 기준 형식(해시값, 글번호만, GitHub Secrets 등)을 따로 정해야 한다.

b) "용량 여유 약 30MB" 의 기준
- D13 "용량 300MB 이하" 규칙(D:\homepage\CLAUDE.md 결정사항 요약에 있음, 자세한 내용은 저장소 밖 docs/결정사항.md)을 static/ 270.3MB 와 비교한 값이다.
  GitHub 한도가 아니다(GitHub Pages 게시 사이트 1GB, 저장소 권장 1GB, 파일당 100MB).
- 배포본 public/ 은 285.1MB 이므로 300MB 를 public/ 기준으로 보면 여유는 약 15MB 다. D13 이 static/·public/·저장소 중 무엇을 기준으로 하는지 확인 필요.

c) 메뉴가 복사된 파일 (한글, 전체 메뉴 1벌 = menu_05~ 전체 대메뉴·소메뉴 묶음)
- templates/_top_ko.html: 2벌(메가메뉴, 모바일 메뉴)
- templates/_board_head_ko.html: 3벌(경로 드롭다운 p_d_menu 2 + 하위 탭 visual_nav_menu 1)
- content/pages/ko/page/*.html 25개, 모두 60벌:
  - 3벌(경로 드롭다운 2 + 하위 탭 1), 15개: bipv, building, carport, cert, de_system, epc, esg, finance, history, housing, kpso, location, pv, self_energy, solar_village
  - 2벌(경로 드롭다운 2만), 5개: carbon, hanbit, re100, vnm, zeb
  - 1벌(하위 탭만), 5개: combiner, fire_cert, inverter, monitoring, structure
- 합계 한글 27개 파일 65벌. (ENG도 _top_en·_board_head_en·content/pages/en/page/*.html 에 같은 구조로 65벌 있으나 1차 범위 밖)
- 푸터: templates/_tail_ko.html 1벌 + 메인 content/pages/ko/index.html 안에 별도 1벌.
