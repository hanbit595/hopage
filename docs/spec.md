# 관리자페이지 1차 명세

## 1. 구조
- 관리자 화면 저장소: hanbit595/hpadmin (D:\hpadmin) → https://admin.hanbitinnotech.com (GitHub Pages, 가비아 CNAME)
- 홈페이지 저장소: hanbit595/hopage (D:\homepage\site) → https://hanbitinnotech.com
- 관리자 화면은 Sveltia CMS(https://unpkg.com/@sveltia/cms/dist/sveltia-cms.js, type="module")를 쓰고,
  GitHub 세분화 토큰(PAT) 로그인으로 hopage 저장소에 직접 커밋한다. 인증 서버는 두지 않는다.
- 저장(커밋) → hopage의 GitHub Actions가 scripts/build.py 실행 → _site 를 Pages로 배포.
  빌드가 실패하면 배포를 중단하고 기존 사이트를 유지한다.
- 토큰·키는 어떤 파일에도 쓰지 않는다.

## 2. hopage 원본 파일 규칙
- cms/notice/*.md   → /board/notice/<파일명>.html   (회사소식)
- cms/media/*.md    → /board/media/<파일명>.html    (시공사례)
- cms/library/*.md  → /board/library/<파일명>.html  (E-Catalog)
- 목록: /board/<게시판>/index.html, 2페이지부터 page-2.html, page-3.html ... (기존 규칙 유지)
- cms/settings/menu.yml, site.yml, popups.yml
- 업로드: uploads/ (기존 data/ 폴더와 겹치지 않게 함), 공개 경로 /uploads
- 기존 글은 기존 글번호를 파일명으로 쓴다(99.md). 새 글은 YYYYMMDD-HHMMSS 형식이다.
- 1차에서는 한국어만 관리한다. /en/ 이하 ENG 페이지는 수정하지 않는다.
- 규정상 비공개 현장 게시물은 cms/에 넣지 않는다(공개 저장소이므로 임시저장도 외부에 보임).

## 3. 필드
- 회사소식: title, date(YYYY-MM-DD), thumbnail(선택), summary(선택), draft(기본 false), body(markdown)
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
- 모든 한글 HTML의 상단 메가메뉴, 모바일 메뉴, 하위 페이지 탭, 하단 푸터(menu.yml, site.yml 기준)
- 게시판 3종의 목록(페이징)과 상세 페이지. 기존 마크업·클래스를 그대로 써서 디자인을 유지한다.
- 메인: 팝업, News(최신 회사소식), Our Project(featured 시공사례 최신순)
- 상세 페이지 <title>: "제목 | HANBIT Innotech", description: summary(없으면 본문 앞 150자)
- 하단 Copyright 연도는 빌드 시 현재 연도로 넣는다.
- 로고 링크 title 속성 "Animotiontech" → "HANBIT Innotech"
- 정적 사이트에서 동작하지 않는 게시판 검색창은 숨긴다.
- sitemap.xml 에 게시판 URL을 반영한다.

## 5. 빌드 실패 조건 (한국어 오류 메시지 출력 후 종료코드 1)
- 필수 필드 누락, 날짜 형식 오류, 파일명(주소) 중복
- menu.yml의 내부 link가 _site 안에 존재하지 않음
- 시공사례 category가 허용 목록에 없음, E-Catalog file 누락

## 6. 기술 조건
- Python 3.12, 외부 패키지는 markdown, pyyaml 만 쓴다.
- 제목·요약·경로는 HTML 이스케이프한다.
- 빌드 산출물 _site 는 git에 올리지 않는다.

## 7. D:\hpadmin 에 만들 파일
- index.html: noindex 메타, 제목 "한빛이노텍 관리자", Sveltia 스크립트만 넣는다.
- config.yml: backend github, repo hanbit595/hopage, branch main, media_folder uploads, public_folder /uploads,
  site_url https://hanbitinnotech.com, collections = 회사소식·시공사례·E-Catalog(folder 컬렉션, 3절 필드, 라벨 한국어,
  새 글 slug "{{year}}{{month}}{{day}}-{{hour}}{{minute}}{{second}}") + "사이트 관리" files 컬렉션(메뉴 관리, 회사정보·기본설정, 메인 팝업)
- CNAME: admin.hanbitinnotech.com
- robots.txt: 모든 크롤러 차단
- .nojekyll (빈 파일)
- CLAUDE.md: "작업 전 docs/spec.md를 읽고 그 기준을 따른다. 명세와 다르게 만들어야 하면 먼저 보고한다."
