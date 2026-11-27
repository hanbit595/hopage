# 관리자페이지 1차 명세 (v2)

v2 변경(2026-11-13): 1절 빌드 경로, 2절 게시판 원본, 4절 메뉴·푸터 생성 방식, 5절 비공개 검사, 6절 기술 조건, 8절 검증 기준·9절 확인 필요 신설.
v2.1 변경(2026-11-13, P3-4a): 3절 date 형식, 시공사례 category 다중 선택·표시 제목에 program, 기존 글 전용 칸. 2절 한글 글은 posts.json 에서 제거.
v2.2 변경(2026-11-13, P3-4b): 2절 본문 형식(body_format), 3절 thumbnail·summary·gallery 출력과 featured_* 칸, 4절 Our Project 칸 배치, 6절 업로드 처리.
v2.3 변경(2026-11-16, P4): 8-1절 고정 페이지 데이터(cms/pages/*.yml) 신설. Contact 는 결정 (나)로 site.yml 재사용 연결.
v2.4 변경(2026-11-16, P4-EN1): 8-2절 영문 완전 분리 원칙(cms/en/)·영문 페이지 칸 목록 신설, 2절 ENG 수정 규칙 변경, 8-1절 Contact 표 정리.
v2.5 변경(2026-11-16, P4-EN2): 영문 게시판 3종을 cms/en/<게시판>/*.md 로 이전. 2절 ENG 글 규칙 변경, 8-3절 영문 게시판 칸 목록 신설.
v2.6 변경(2026-11-16, P4-EN3): 영문 메뉴·푸터·메인 팝업을 cms/en/settings/menu.yml·site.yml·popups.yml 로 생성. 8-4절 신설, 2절·8-2절·9절 c 정리.

## 1. 구조
- 관리자 화면 저장소: hanbit595/hpadmin (D:\hpadmin) → https://admin.hanbitinnotech.com (GitHub Pages, 가비아 CNAME)
- 홈페이지 저장소: hanbit595/hopage (D:\homepage\site) → https://hanbitinnotech.com
- 관리자 화면은 Sveltia CMS(https://unpkg.com/@sveltia/cms/dist/sveltia-cms.js, type="module")를 쓰고,
  GitHub 세분화 토큰(PAT) 로그인으로 hopage 저장소에 직접 커밋한다. 인증 서버는 두지 않는다.
- 저장(커밋) → hopage의 기존 GitHub Actions(.github/workflows/deploy.yml)가 기존 build/all.py 실행 → public/ 을 Pages로 배포.
  빌드가 실패하면 배포를 중단하고 기존 사이트를 유지한다.
- 토큰·키는 어떤 파일에도 쓰지 않는다.

## 2. hopage 원본 파일 규칙
- 한글 게시판 글은 cms/<게시판>/<글번호>.md 로 관리한다. 이전한 기존 글은 머리말 body_format: html 로 본문 HTML을 그대로 출력한다.
  body_format 이 없는 글(관리자 화면으로 쓴 새 글)은 본문을 markdown → HTML 로 바꾼다(표·줄바꿈 지원, 원문 HTML 은 통과하되 13절 보안 정화를 거친다).
  - cms/notice/*.md   → /board/notice/<파일명>.html   (회사소식)
  - cms/media/*.md    → /board/media/<파일명>.html    (시공사례)
  - cms/library/*.md  → /board/library/<파일명>.html  (E-Catalog)
- ENG 글(notice_en, media_en, library_en)은 cms/en/<게시판>/<파일명>.md 로 관리한다(P4-EN2, 8-3절). 주소 /en/board/<게시판>/<파일명>.html.
  posts.json 의 게시판 글 배열(boards)은 한글·영문 모두 지웠다. 다시 생기면 빌드 실패.
  posts.json 에는 boards_meta·contents 만 남는다(extract_boards.py 가 읽음). 영문 메인 팝업(popups)은 P4-EN3 에서
  cms/en/settings/popups.yml 로 옮기고 지웠다. popups 가 다시 생기면 빌드 실패.
- 목록: /board/<게시판>/index.html, 2페이지부터 page-2.html, page-3.html ... (기존 규칙 유지)
- cms/settings/menu.yml, site.yml, popups.yml
- 업로드: uploads/ (기존 data/ 폴더와 겹치지 않게 함), 공개 경로 /uploads
- 기존 글은 기존 글번호를 파일명으로 쓴다(99.md). 새 글은 YYYYMMDD-HHMMSS 형식이다.
- ENG 는 cms/en/ 데이터로 전환된 페이지만, 비교 검증을 거쳐 수정한다(8-2절).
- 규정상 비공개 현장 게시물은 cms/에 넣지 않는다(공개 저장소이므로 임시저장도 외부에 보임).

## 3. 필드
- date: "YYYY-MM-DD HH:MM:SS"(기존 글은 원래 작성 시각). "YYYY-MM-DD" 만 있으면 시각 00:00:00 으로 본다.
  목록 순서: date 최신순, 같은 date 는 파일명 역순(새 형식 YYYYMMDD-HHMMSS 가 기존 글번호보다 앞, 글번호는 숫자 크기로 비교).
- 회사소식: title, date, thumbnail(선택), summary(선택), draft(기본 false), body(HTML)
- 시공사례: title(현장명), category(다중 선택 목록, 허용값: 태양광발전장치/BIPV/주차장태양광/기타, 1개 이상 필수),
  capacity(문자, 선택. 원래 제목의 용량 부분을 글자 그대로. 깔끔히 나눌 수 없는 기존 글은 title 에 두고 비움),
  program(사업구분, 선택), date, thumbnail(선택), gallery(이미지 목록, 선택),
  featured(메인 Our Project 노출, 기본 false), draft, body(선택)
  목록·상세 표시 제목: "[category] title capacity" + program 이 있으면 " ㅣ {program}".
  category 는 선택 순서대로 쉼표로 잇는다(예: [태양광발전장치,BIPV]). 빈 capacity 는 앞 공백 없이 생략.
  (기존 50번 [태양광발전설비] 는 [태양광발전장치] 로 통일, 2026-11-13 결정)
- E-Catalog: title, date, thumbnail(선택), file(PDF, 필수, /로 시작하는 사이트 주소, public/ 에 있어야 함), body(선택), draft
- 기존 글 전용 칸(선택, 관리자 화면에 없어도 됨): link1·link2(관련 링크·YouTube, 기본 ""), files(첨부 목록 [{no, source, stored, size}], 기본 [])
  E-Catalog 에 files 가 없으면 file 로 첨부 1개를 만든다(다운로드 이름 = 파일 이름, 크기 = 실제 파일 크기).
  조회수·다운로드 수·연결 수(content/board_snapshot.json)가 없는 새 글은 0, 첨부 날짜는 글 date.
- thumbnail: 목록·메인 News·Our Project 썸네일 1순위(없으면 첨부 이미지 → 본문 첫 이미지).
  summary: 메인 News 요약·상세 meta description 1순위(없으면 본문 앞부분 / site.yml seo_description).
  gallery: 상세 본문 아래, 기존 상세 사진과 같은 마크업(a.view_image > img, 1400px 축소본 + 1920px 확대 보기).
- 시공사례 메인 카드 칸(선택): featured_order(숫자, 작은 숫자 먼저, 없으면 date 최신순), featured_image(카드 이미지 1순위 → thumbnail → 기존 규칙).
  기존 글 전용: featured_label·featured_text(이전 전 메인 카드에 손으로 적혀 있던 분류·문구, HTML 그대로).
  없으면 분류 = category(태양광발전장치→PV), 문구 = "title <br>capacity".
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
- 메인: 팝업, News(최신 회사소식), Our Project(featured 시공사례, 3절 순서)
  Our Project 틀은 10칸(item_01~10). 01·02(소개 글 자리)·06·10 은 디자인상 늘 빈 칸. 카드 칸 6개를 04→07→08→09→03→05 순서로 채우고
  남는 칸은 빈 <li>. featured 글이 6건을 넘으면 앞의 6건만 표시(빌드 주의 메시지).
- 상세 페이지 <title>: "제목 | HANBIT Innotech", description: summary(없으면 본문 앞 150자)
- 하단 Copyright 연도는 빌드 시 현재 연도로 넣는다.
- 로고 링크 title 속성 "Animotiontech" → "HANBIT Innotech"
- 정적 사이트에서 동작하지 않는 게시판 검색창은 숨긴다.
- sitemap.xml 에 게시판 URL을 반영한다.

## 5. 빌드 실패 조건 (한국어 오류 메시지 출력 후 종료코드 1)
- 필수 필드 누락, 날짜 형식 오류, 파일명(주소) 중복
- menu.yml의 내부 link가 public/ 안에 존재하지 않음
- 시공사례 category가 허용 목록에 없음, E-Catalog file 누락
- 비공개 검사: 1차에서는 자동 배포 빌드에 비공개 검사를 넣지 않는다. 판별 목록이 저장소 밖에 있어 Actions 에서
  읽을 수 없기 때문이다. 비공개 현장은 관리자 화면에 올리지 않는 원칙으로 막고, 관리자 화면 입력칸 안내문에 이 원칙을 표시한다.
- 보안 검사(13절): 정화 후에도 본문에 위험 코드가 남음, uploads/ 에 허용 밖 파일 종류, public/ 에 숨김·소스·허용 밖 파일

## 6. 기술 조건
- Python 3.12. 의존성은 기존 jinja2, pillow 에 markdown, pyyaml 만 추가 허용한다. 버전은 build/requirements.txt 에 고정한다(13절).
- 제목·요약·경로는 HTML 이스케이프한다.
- 빌드 산출물 public/ 은 git에 올리지 않는다(기존 .gitignore 유지).
- 관리자 화면 업로드 이미지(uploads/)는 빌드 시 pillow 로 긴 변 1920px 이하(기존 확대본 D3 기준과 동일)로 줄여 public/ 에 넣는다.
  원본이 더 작으면 그대로 둔다(확대 안 함). JPEG 품질 85, PNG 는 PNG 유지. uploads/ 원본은 수정·삭제하지 않는다.
  쓰이지 않는 업로드(P3-5c-2): cms/·content/·templates/ 의 글·페이지·설정 어디에도 /uploads/<이름>(대소문자 무시, %인코딩·HTML 엔티티 포함)이
  없으면 public/ 에 넣지 않고 빌드 끝에 "쓰이지 않는 업로드: N개(목록)" 를 출력한다. 원본은 삭제하지 않는다.
  배포본 용량 규칙(D13, 300MB)을 지키기 위함이다. 빌드 끝에 업로드 원본·배포 합계와 public/ 전체 용량을 출력하고 300MB 를 넘으면 경고(실패 아님).

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
- public/en/ 은 완전히 같아야 한다(cms/en/ 로 전환하는 영문 페이지는 8-2절의 승인한 차이만 허용).
- 한글 페이지는 메뉴·푸터·게시판·메인 Our Project/News 영역 외에는 차이가 없어야 한다.
- 기존 게시판 URL(/board/<게시판>/index.html, page-N.html, <글번호>.html) 누락 0건.

## 8-1. 고정 페이지 데이터(cms/pages/*.yml) (P4, 2026-11-16)
- 한글 고정 페이지 일부의 내용을 cms/pages/<페이지>.yml 에서 읽어 만든다. 레이아웃·마크업·클래스는 그대로 두고,
  본문 조각(content/pages/ko/page/<페이지>.html)의 내용 자리만 Jinja 칸({{ }}·{% for %})으로 바꿨다.
- 읽기·검사: build/cms_pages.py (PAGES 표에 있는 페이지만). build.py 가 고정 페이지를 만들 때 불러 쓴다. 영문은 8-2절.
- 빌드 실패(한국어 메시지 + 종료코드 1): 필수 칸 누락, 날짜·연도·월 형식 오류, 이미지 파일이 public/ 에 없음(optimize.py 가 바꾼 이름 인정),
  그 밖에 없는 구분, 같은 연도 중복, 고정 개수 칸의 개수 불일치.
- 글자 칸: 제목·명칭은 HTML 이스케이프. 문단·내용 칸은 <br>·<b> 등 HTML 그대로. 여러 줄 문단은 줄마다 원래 들여쓰기를 붙여 출력.
- 이미지 칸: /로 시작하는 사이트 안 주소.

| 페이지 | 파일 | 칸 |
|---|---|---|
| 인증 및 수상 /page/cert.html | cms/pages/cert.yml | categories[구분 이름, 표시 순서], items[{category 구분, name 명칭, issuer 발급기관(선택·기록용), date 날짜(선택·기록용, YYYY-MM-DD 또는 YYYY-MM), image 인증서 이미지, visible 노출(기본 true), order 순서(구분 안에서 작은 수 먼저)}]. 노출 항목이 없는 구분은 숨김 |
| 연혁 /page/history.html | cms/pages/history.yml | periods[{title 기간 제목, anchor 주소 이름표(선택, 기본 his-N), image 사진, years[{year 4자리, months[{month "01"~"12", items[내용, 한 달 2칸 가능]}]}]}]. 연도·월은 큰 값이 위로 자동 정렬, 기간은 홀수째 사진 왼쪽·짝수째 오른쪽 |
| 회사소개 /page/hanbit.html | cms/pages/hanbit.yml | hero{title, image}, intro_texts[3], photos[6], energy_text, sun_texts[2], ending_text. 개수는 애니메이션 스크립트와 맞물려 고정. 숫자 표시 영역은 페이지에 없음, 배경 사진 2곳은 CSS 고정 |
| ESG 경영 /page/esg.html | cms/pages/esg.yml | intro{title, text}, flow_text, pillars[{title, icon, text}], details[{title, items[]}] |
| Contact /page/location.html | cms/pages/location.yml + cms/settings/site.yml | locations[{office 사업장 이름(site.yml offices 의 name 과 연결), label 작은 제목(HTML 그대로), title 사업장 이름, map 구글 지도 embed 주소 전체, map_indent(선택·기록용 들여쓰기)}]. 주소·연락처·메일은 site.yml 재사용(결정 나) |

- Contact(2026-11-16 결정 (나)): site.yml 주소 표기를 Contact 화면 표기로 맞춤(부산시 해운대구…, 김해시 상동면…, 680 , 706).
  그 결과 바뀐 것은 한글 모든 페이지 하단 푸터 주소 3줄뿐(승인된 차이). 주소·연락처·메일의 원본은 site.yml 하나.
  연락처는 site.yml tel(+82-51-…)을 국내 표기(051-…)로 바꿔 쓴다.
  지도는 embed 주소 안에 좌표(!2d경도!3d위도)와 주소 글자(base64)가 함께 들어 있어 주소 전체를 map 한 칸으로 뺐다.

## 8-2. 영문 완전 분리 원칙(cms/en/) (P4-EN1, 2026-11-16)
- 영문은 국문과 완전히 분리해 관리한다. 데이터 파일·관리 메뉴 모두 별도이고, 국문 데이터(cms/pages/*.yml, cms/settings/*.yml)를 영문이 읽지 않는다.
- 구조: cms/en/pages/<페이지>.yml(영문 고정 페이지), cms/en/settings/site.yml(영문 회사정보). 국문 cms/ 와 같은 이름·같은 칸 구조를 쓴다.
- 이미지·동영상·PDF 파일은 공유한다(같은 /theme/…, /uploads/… 주소를 양쪽 데이터에 적어도 된다). 글자·목록·순서·노출은 언어별 데이터에 따로 둔다.
- 영문 본문 조각(content/pages/en/page/<페이지>.html)은 레이아웃·마크업·클래스·영문 원래 공백을 그대로 두고 내용 자리만 Jinja 칸으로 바꿨다.
  읽기·검사는 국문과 같은 build/cms_pages.py(PAGES_EN 표). 빌드 실패 조건도 국문(8-1절)과 같다.
- 영문 글자 칸은 esc_text 로 이스케이프한다: <·> 는 바꾸고, & 는 문자 참조로 읽힐 수 있을 때만 &amp; 로 바꾼다(기존 'R&D' 표기 유지).
- 검증: 전환 전 빌드 결과와 비교해 국문 차이 0, 영문은 승인한 차이 외 0 이어야 커밋한다.
  P4-EN1 승인 차이 1건: 영문 Credit Rating Certificate 이미지를 국문과 같은 /uploads/신용등급확인서.png 로 교체.
- 영문 하단 푸터·메뉴·메인 팝업은 P4-EN3 에서 cms/en/settings/ 로 연결했다(8-4절). 푸터 주소는 Contact 화면 표기로 통일.

| 페이지 | 파일 | 칸 (국문과 다른 점) |
|---|---|---|
| Certification /en/page/cert.html | cms/en/pages/cert.yml | categories[구분 이름(Awards·Certifications·Patents)], items[{category, name, issuer, date, image, visible, order}] (국문과 같음) |
| History /en/page/history.html | cms/en/pages/history.yml | periods[{title, anchor, image, years[{year, months[{month, items[]}]}]}] (국문과 같음. `\|` 로 적은 내용은 끝 줄바꿈을 남김) |
| About /en/page/hanbit.html | cms/en/pages/hanbit.yml | hero{title, video}, intro_texts[3], photos[6], energy_text, sun_texts[2], ending_text (영문 맨 위 화면은 동영상이라 hero.image 대신 hero.video) |
| ESG /en/page/esg.html | cms/en/pages/esg.yml | intro{title, text}, flow_text, pillars[{title, icon, text}], details[{title, items[]}] (항목 앞 '-' 는 틀이 붙임) |
| Contact /en/page/location.html | cms/en/pages/location.yml + cms/en/settings/site.yml | locations[{office, label, title, map}] (map_indent 없음) + site.yml offices[{name, address}], tel, email |

## 8-3. 영문 게시판(cms/en/<게시판>/*.md) (P4-EN2, 2026-11-16)
- 원본: cms/en/notice/*.md(Notice) → /en/board/notice/, cms/en/media/*.md(Project Cases) → /en/board/media/,
  cms/en/library/*.md(E-Catalog) → /en/board/library/. 국문 cms/notice|media|library 와 완전히 따로 둔다.
- 읽기·검사·정렬·draft·파일명·본문 형식(body_format)·thumbnail·summary·업로드 1920px 처리는 국문과 같은 코드
  (build/cms_posts.py load_board(lang="en"), boards.py, uploads.py)를 쓴다. 빌드 실패 조건도 5절과 같다
  (필수 칸 누락, 날짜 형식, 파일명 중복, E-Catalog file 누락·사이트에 없는 파일).
- 영문 메인 News 4건 = cms/en/notice 최신 4건(draft 제외). 영문 메인 Our Project 는 지금처럼 고정 마크업(글과 연결 안 함).
- 기존 글은 기존 글번호(예: 73.md), 새 글은 YYYYMMDD-HHMMSS.md. 기존 글 본문은 body_format: html 로 HTML 그대로.
- 이전 결과: Notice 7건, Project Cases 65건, E-Catalog 0건(빈 폴더는 .gitkeep). 시험용 "test" 글 2건(media 1·2번)은 승인에 따라 이전하지 않음
  (그 결과 /en/board/media/1.html·2.html, 목록 10쪽의 2건, sitemap 2건, 옛 주소 wr_id=1·2 대응 6건, 3번 글의 Next 링크가 빠짐).

| 게시판 | 폴더 | 칸 (국문과 같은 키 이름) |
|---|---|---|
| Notice | cms/en/notice/ | title(필수, 제목 통째로), date(필수, YYYY-MM-DD HH:MM:SS), body, body_format(기존 글 html), thumbnail·summary(선택), draft(기본 false), link1·link2·files(기존 글 전용, 선택) |
| Project Cases | cms/en/media/ | 위와 같음. title 은 "[PV] 현장명 용량" 처럼 통째로 쓰고 나누지 않는다(category·capacity·program·gallery·featured 칸 없음) |
| E-Catalog | cms/en/library/ | 위와 같음 + file(필수, /로 시작하는 PDF 주소, public/ 에 있어야 함). files 가 없으면 file 로 첨부 1개 |

## 8-4. 영문 메뉴·푸터·메인 팝업(cms/en/settings/) (P4-EN3, 2026-11-16)
- 국문 P3-2·P3-3 과 같은 방식. 국문 파일(cms/settings/*, _menu_ko·_footer_ko 등)과 따로 두며 서로 읽지 않는다.
- 메뉴: cms/en/settings/menu.yml → templates/_menu_en.html(국문과 같은 마크업의 영문 전용 조각).
  영문 메뉴 복사본 65벌(_top_en 2, _board_head_en 3, content/pages/en/page/*.html 25개 60벌, 분포는 9절 c 의 국문과 같음)을
  %%MENU_EN:형태%%(mega·mobile·drop_main·drop_sub·subtab) 자리표시로 바꿨다. 현재 페이지 active 는 국문과 같은 규칙(기존 apply_active 는 삭제).
- 푸터: cms/en/settings/site.yml(offices·tel·email, brochure 선택) → templates/_footer_en.html.
  _tail_en.html 과 영문 메인 본문(content/pages/en/index.html)의 %%FOOTER_EN%% 자리. Copyright 연도는 빌드 시점.
  brochure 를 비우면 Company Profile 은 기존처럼 href="#" 새 창 링크. 같은 site.yml 을 영문 Contact 도 쓴다(주소·연락처 원본 하나).
- 메인 팝업: cms/en/settings/popups.yml → 국문과 같은 extras.popup_html(같은 칸·같은 검사·data-begin/data-end 브라우저 판단·24시간 보지 않기).
  기존처럼 빌드 시점에 끝난 팝업을 거르지 않는다(끝난 팝업은 active: false 로 둠).
- 빌드 실패: 국문과 같다(메뉴 내부 link 가 public/ 에 없음, 팝업 날짜 형식·start>end·active 팝업 image 누락, 설정의 내부 주소가 public/ 에 없음).
  오류 메시지에 파일 경로(cms/en/settings/…)를 붙인다.
- 승인 차이(2026-11-16): ① 영문 푸터 주소를 영문 Contact 표기로 통일 ② 메뉴 복사본 안의 주석 처리된 깨진 링크
  "BIPV Wall & Window System"(없는 bipv_pdt.html) 제거 ③ Copyright 연도 자동(2025 → 빌드 연도) ④ 영문 로고 title "HANBIT Innotech"
  ⑤ 공통화로 빠지는 HTML 주석·공백. 그리고 사용자 확인으로 영문 팝업 종료를 날짜만 쓰는 규칙에 맞춰
  data-end "2026-12-31 00:00:00" → "2026-12-30 23:59:59"(1초 차이, en/index.html 1개).

| 화면 | 파일 | 칸 |
|---|---|---|
| 영문 메뉴(상단·모바일·경로 드롭다운·하위 탭) | cms/en/settings/menu.yml | menu[{label, link, visible, class, items[{label, link, new_window, visible, class}]}] (국문 3절 menu.yml 과 같음, 링크는 /en/…) |
| 영문 푸터·Contact | cms/en/settings/site.yml | offices[{name, address}], tel, email, brochure(선택) |
| 영문 메인 팝업 | cms/en/settings/popups.yml | popups[{title, image, link, start, end, active, id, width, height, top, left}] (국문과 같음) |

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
- 합계 한글 27개 파일 65벌. (ENG도 _top_en·_board_head_en·content/pages/en/page/*.html 에 같은 구조로 65벌 → P4-EN3 에서 공통화, 8-4절)
- 푸터: templates/_tail_ko.html 1벌 + 메인 content/pages/ko/index.html 안에 별도 1벌.

## 10. 관리자 화면 새 페이지(created: true) (P7, 2026-11-19)
- 파일 cms/free/<slug>.md(영문 cms/en/free/<slug>.md). 앞부분 title·path(/page/<slug>.html, 영문 /en/page/<slug>.html)·editor_mode·created: true·hero_title·hero_desc·hero_image(선택).
  slug 는 영문 소문자·숫자·_, 기존 페이지·static 폴더 이름과 겹치면 빌드 실패.
- 틀 templates/free_page.html(국·영 공통, build/cms_free.py created_pages·render_created). h1·<title> = title, 사진 위 문구 .tit = hero_title, 설명 .txt = hero_desc(이스케이프, 줄바꿈 → <br>).
- 모양은 소속 대메뉴의 기존 페이지와 같다: 사업분야·정부지원·회사소개 = 사진 배경(hero_image, 비면 sub_01·sub_04·sub_05.jpg),
  제품·기술 = 제목+하위 탭, 탄소중립 = 경로 드롭다운+제목, 홍보센터 = 게시판 머리(_page_head). 이 셋도 hero_image 가 있으면 사진 배경.
- body class 는 sub_<대메뉴 번호> sub_<대메뉴>_<소메뉴 class 번호>. menu.yml 에 visible: true 소메뉴(대메뉴도 노출)로 연결된 것만 만들고 sitemap 에 넣는다. 옛 주소 대응표에는 넣지 않는다.
- KOR/ENG: 짝 언어 새 페이지가 있으면 그 페이지, 없으면 상대 언어 메인(사용자 결정 2026-11-19).
- 빌드 실패: 노출 메뉴 link(/page/…·/en/page/…)가 가리키는 페이지가 없으면 필요한 파일 이름을 붙여 실패. hero_image 가 사이트에 없으면 실패.

## 11. 시뮬레이션 페이지(P8, 2026-11-19)
- 사례 cms/simulation/<slug>.md(영문 cms/en/simulation/). 앞부분 title·categories(시공사례 분류, 여러 개)·kwp·modules·arrays·parking(선택, 비면 숨김)·youtube(필수)·thumbnail(/uploads/…, 비면 유튜브 썸네일)·viewer(/uploads/sim/<slug>.html)·related(/board/media/<번호>.html)·visible·order·date. 본문 = 설명 HTML. 정렬 order 오름차순 → date 최신순.
- 설정: 언어별 site.yml simulation_public(기본 false)·simulation_intro. 꺼짐 또는 노출 사례 0개 → 메뉴(홍보센터 > 시뮬레이션, 시공사례 다음)·페이지·sitemap·hb_sim.css·js·사례 업로드 모두 없음.
- 목록 /page/simulation.html: 소개 → 분류 탭(전체 + 사례 있는 분류, 영문 All·PV System·BIPV·Solar Carport·Others) → 카드(썸네일·분류·현장명·용량).
- 상세 /simulation/<slug>.html: 수치 → 유튜브(youtube-nocookie) → 3D(PC 화면에 보이면 iframe, 768px 미만은 썸네일 + "3D 보기 (약 N MB)" 버튼, 전체 화면 버튼·안 되면 새 탭) → 설명 → 관련 시공사례·상담(inquiry_public 이면 견적문의, 아니면 오시는 길)·목록 → 안내문.
- KOR/ENG: 상대 언어 시뮬레이션 목록(꺼져 있으면 상대 언어 메인).
- 빌드 실패: uploads/sim/*.html 이 25MB 초과이거나 reference_photos·data:image/jpeg 포함(스위치와 무관, 항상), title·youtube 누락, 허용 밖 분류, viewer·thumbnail 파일 없음, related 글 없음. uploads/sim 은 이미지 최적화 안 함.

## 12. 메뉴 숨김 페이지(P9, 2026-11-19)
- 기존 자유 페이지(cms/free·cms/en/free, created 아님)도 menu.yml 에서 그 path 를 가리키는 소메뉴가 모두 숨김(소메뉴 visible: false 또는 대메뉴 visible: false)이면 페이지·sitemap·옛 .php 주소 이동에서 뺀다(build/cms_free.py hidden_pages). 대메뉴 link 는 같은 주소의 소메뉴가 없을 때만 셈.
- 대메뉴 link 가 숨긴 페이지면 첫 노출 소메뉴로 바꾸고 경고. 짝 언어 페이지가 숨겨졌으면 KOR/ENG 는 상대 언어 메인.
- 숨긴 페이지를 가리키는 본문 링크(메인 버튼 등)는 빌드 경고(실패 아님). 메뉴에 아예 연결 안 된 자유 페이지는 규칙 적용 없이 경고로 보고.

## 13. 보안(S1, 2026-11-26)
- 본문 정화(build/html_safe.py): 게시판 본문(이전 글 포함)·자유 페이지·FAQ 답변·회사 페이지(cms/pages) 글 칸·시뮬레이션 설명에 적용.
  - 내용째 삭제: script·object·embed·applet·svg·math·noembed·noframes·template / 태그만 삭제: base·meta·link·frame·frameset·form·input·textarea·select·button·option
  - iframe 은 유튜브(youtube·youtube-nocookie)·구글 지도(www.google.com/maps)만 허용, 그 밖은 삭제
  - on… 이벤트 속성 삭제. 주소 속성(href·src 등)은 http·https·mailto·tel·상대주소만(img 의 data:image/png·jpeg·gif·webp 허용). 문자 참조·공백을 풀어서 판단
  - style 속성에 expression(·javascript:·behavior:·-moz-binding·@import 가 있으면 속성 삭제
  - 위험 요소가 없는 태그는 원문 글자 그대로 둔다(기존 글 출력 변화 없음). 정화 후 표준 HTML 파서로 다시 검사해 남은 것이 있으면 빌드 실패.
- 업로드 종류(build/security_check.py): uploads/ 는 jpg·jpeg·png·gif·webp·mp4·webm + 문서 첨부 pdf·hwp·hwpx·docx·xlsx·zip(관리자 서버 업로드 허용 목록과 동일),
  uploads/sim/ 은 html 추가 허용. svg·html·js 등은 빌드 실패. 관리자 서버 허용 종류를 늘리면 이 목록도 함께 늘린다.
- 배포본 검사: public/ 에 숨김 파일·폴더, 허용 목록 밖 확장자, theme/·js/ 밖의 svg, robots.txt 외 txt 가 있으면 빌드 실패.
- 보안 정책(templates/_security_meta.html): 모든 페이지 <head> 맨 앞에 CSP·referrer meta. 스크립트·스타일은 이 사이트(+구글 폰트), iframe 은 유튜브·구글 지도,
  전송은 admin.hanbitinnotech.com 만. 새 외부 서비스를 붙이면 이 파일에 주소를 추가한다. (GitHub Pages 는 응답 헤더를 못 바꿔 frame-ancestors·HSTS 는 미적용)
- 배포(deploy.yml): checkout persist-credentials: false. 패키지는 build/requirements.txt 고정 버전으로 설치(올릴 때는 내 PC 빌드로 확인 후 변경).
