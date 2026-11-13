# 사이트 현황 점검 (site-audit)

작성: docs/_audit_tmp.py (읽기 전용 분석). 기준: D:\homepage\site 작업본과 GitHub 조회 결과.

## 1) 원격 저장소·브랜치·배포
- 원격: https://github.com/hanbit595/hopage.git
- 현재 브랜치: main
- GitHub 기본 브랜치: (실행 실패: [WinError 2] 지정된 파일을 찾을 수 없습니다) / 공개여부: ?
- 최근 커밋 5개:
```
d1d2bed 시공사례 비공개 대상 4건 삭제, 메인 프로젝트 카드 1개 추가로 비움 (D17)
3a0eaee 시공사례 비공개 대상 10건 삭제, 메인 프로젝트 카드 1개 비움 (D17)
69ac9da 글꼴 CSS에서 없는 파일 참조 정리 (D6·D13)
7f05d08 한빛이노텍 홈페이지 정적 사이트 첫 커밋
```
- Pages 설정(gh api repos/…/pages):
```json
{
 "_error": "(실행 실패: [WinError 2] 지정된 파일을 찾을 수 없습니다)"
}
```
- 등록 워크플로: (gh 미설치로 조회 못 함 — 이 PC에 GitHub CLI가 없음)
- 저장소 안 CNAME 파일: 없음
- **판단**: Pages 배포 방식은 **GitHub Actions**(아래 deploy.yml: push → build/all.py → public/ 업로드 → deploy-pages). gh-pages 브랜치 방식이 아님.
- **CNAME 없이 도메인이 유지되는 이유**: Actions 배포에서는 커스텀 도메인(hanbitinnotech.com)이 산출물의 CNAME 파일이 아니라
  저장소 Settings > Pages 의 Custom domain 값(GitHub 서버 쪽 설정)으로 유지된다. 그래서 public/에 CNAME이 없어도 배포마다 도메인이 풀리지 않는다.
  (gh 설치 후 `gh api repos/hanbit595/hopage/pages` 의 build_type=workflow, cname 값으로 재확인 권장)
- 워크플로 원문 .github/workflows/deploy.yml:
```yaml
# push하면 사이트를 다시 만들어 GitHub Pages에 배포한다.
# 저장소 설정 > Pages > Source 를 "GitHub Actions"로 한 번 바꿔 두어야 한다.
# 빌드: build/all.py (optimize.py → build.py) → public/ 을 Pages에 올림
# extract_pages.py는 수집본(crawl/)·FTP 원본(original/)이 필요해서 여기서는 돌리지 않는다(내 PC에서만).
name: 배포 (GitHub Pages)

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: 패키지 설치
        # pillow: 이미지 최적화·새 글 축소본, jinja2: 페이지 틀
        # .mov 동영상을 새로 넣는 경우에만 imageio-ffmpeg가 필요하다(그때 아래 줄 끝에 imageio-ffmpeg 추가)
        run: python -m pip install pillow jinja2

      - name: 사이트 빌드
        env:
          PYTHONIOENCODING: utf-8
        run: python build/all.py

      - uses: actions/configure-pages@v5

      - uses: actions/upload-pages-artifact@v3
        with:
          path: public

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
```

## 2) 폴더 구조(2단계)·HTML 수·용량
```
.gitattributes  (173B)
.github/  (1개, 0.0MB)
  workflows/  (1개, 0.0MB)
.gitignore  (157B)
build/  (14개, 0.2MB)
  __pycache__/  (6개, 0.1MB)
  (파일 8개: all.py, boards.py, build.py, extract_boards.py, extract_pages.py, extras.py, optimize.py, private_guard.py)
CLAUDE.md  (255B)
content/  (60개, 1.9MB)
  pages/  (53개, 1.5MB)
  (파일 7개: board_snapshot.json, boards.json, optimize_manifest.json, posts.json, publish_exclude.json, redirects.json, renames.json)
docs/  (2개, 0.0MB)
  (파일 2개: _audit_tmp.py, spec.md)
public/  (1013개, 285.1MB)
  board/  (95개, 5.9MB)
  data/  (477개, 143.0MB)
  en/  (115개, 7.2MB)
  files/  (2개, 4.9MB)
  hb/  (4개, 0.0MB)
  img/  (1개, 0.0MB)
  js/  (11개, 0.8MB)
  page/  (25개, 1.6MB)
  theme/  (277개, 121.4MB)
  vendor/  (1개, 0.1MB)
  (파일 5개: 404.html, index.html, redirects.json, robots.txt, sitemap.xml)
static/  (773개, 270.3MB)
  data/  (477개, 143.0MB)
  files/  (2개, 4.9MB)
  hb/  (4개, 0.0MB)
  img/  (1개, 0.0MB)
  js/  (11개, 0.8MB)
  theme/  (277개, 121.4MB)
  vendor/  (1개, 0.1MB)
templates/  (13개, 0.1MB)
  (파일 13개: 404.html, _board_head_en.html, _board_head_ko.html, _head_en.html, _head_ko.html, _tail_en.html, _tail_ko.html, _top_en.html, _top_ko.html, base.html, board_list.html, board_view.html …)
```
- public/(빌드 결과, git 제외) HTML: 전체 231 / 한글 119 / ENG(en/) 112
- git 추적 파일 857개, 그중 .html 65개(템플릿·본문 조각)
- 전체 용량(.git 제외): 557.6MB / public 제외: 272.6MB / .git: 0.0MB

## 3) 메가메뉴·모바일 메뉴·하위 탭·푸터
- 템플릿 목록: templates/404.html, templates/_board_head_en.html, templates/_board_head_ko.html, templates/_head_en.html, templates/_head_ko.html, templates/_tail_en.html, templates/_tail_ko.html, templates/_top_en.html, templates/_top_ko.html, templates/base.html, templates/board_list.html, templates/board_view.html, templates/page.html
  - templates/404.html: extends=[] include=[] blocks=[]
  - templates/_board_head_en.html: extends=[] include=[] blocks=[]
  - templates/_board_head_ko.html: extends=[] include=[] blocks=[]
  - templates/_head_en.html: extends=[] include=[] blocks=[]
  - templates/_head_ko.html: extends=[] include=[] blocks=[]
  - templates/_tail_en.html: extends=[] include=[] blocks=[]
  - templates/_tail_ko.html: extends=[] include=[] blocks=[]
  - templates/_top_en.html: extends=[] include=[] blocks=[]
  - templates/_top_ko.html: extends=[] include=[] blocks=[]
  - templates/base.html: extends=[] include=['{% include "_head_" ~ lang ~ ".html" %}', '{% include "_top_" ~ lang ~ ".html" %}', '{% include "_tail_" ~ lang ~ ".html" %}'] blocks=['content', 'body_end']
  - templates/board_list.html: extends=['{% extends "base.html" %}'] include=[] blocks=['content']
  - templates/board_view.html: extends=['{% extends "base.html" %}'] include=[] blocks=['content']
  - templates/page.html: extends=['{% extends "base.html" %}'] include=[] blocks=['content']
- 빌드된 HTML 231개 중 포함 수: header 0, footer 230, mega/gnb 0, mobile 230, subtab 0
- templates/ 밖의 추적 HTML 중 header/footer를 직접 가진 파일: 2개 ['content/pages/en/index.html', 'content/pages/ko/index.html']
- 공통 틀 원문(templates/base.html):
```html
<!doctype html>
<html lang="{{ html_lang }}" class="sok">
<head>{% include "_head_" ~ lang ~ ".html" %}</head>
<body  class="{{ body_class }}">

<div id="wrap">
{% include "_top_" ~ lang ~ ".html" %}
{% block content %}{% endblock %}
{% include "_tail_" ~ lang ~ ".html" %}{% block body_end %}{% endblock %}
</body>
</html>
```
- page.html 원문(하위 탭 포함 여부 확인용):
```html
{% extends "base.html" %}
{% block content %}{{ content_html }}{% endblock %}
```

## 4) 게시판 3종
- content/posts.json 최상위 구조: dict ['source', 'note', 'boards_meta', 'boards', 'popups', 'contents']
  - 키 boards_meta: 6건, 첫 항목 키 ['bo_table', 'subject', 'skin', 'page_rows', 'mobile_page_rows']
  - 키 boards.notice: 10
  - 키 boards.notice_en: 7
  - 키 boards.media: 67
  - 키 boards.media_en: 67
  - 키 boards.library: 2
  - 키 boards.library_en: 0
  - 키 popups: 2건, 첫 항목 키 ['id', 'subject', 'begin', 'end', 'width', 'height', 'left', 'top', 'disable_hours', 'content']
  - 키 contents: 3건, 첫 항목 키 ['id', 'subject', 'content']
- public/board/notice: HTML 12개, 목록 파일 ['index.html', 'page-2.html']…['page-2.html'], 상세 예 ['10.html', '11.html', '12.html']
- public/data/file/notice: HTML 0개, 목록 파일 []…, 상세 예 []
- public/en/board/notice: HTML 8개, 목록 파일 ['index.html']…['index.html'], 상세 예 ['2.html', '3.html', '4.html']
- public/theme/basic/skin/board/notice: HTML 0개, 목록 파일 []…, 상세 예 []
- public/board/media: HTML 77개, 목록 파일 ['index.html', 'page-10.html', 'page-2.html']…['page-9.html'], 상세 예 ['24.html', '25.html', '26.html']
- public/en/board/media: HTML 77개, 목록 파일 ['index.html', 'page-10.html', 'page-2.html']…['page-9.html'], 상세 예 ['1.html', '10.html', '11.html']
- public/board/library: HTML 3개, 목록 파일 ['index.html']…['index.html'], 상세 예 ['1.html', '2.html']
- public/files/library: HTML 0개, 목록 파일 []…, 상세 예 []
- public/en/board/library: HTML 1개, 목록 파일 ['index.html']…['index.html'], 상세 예 []
- 템플릿 원문 board_list.html:
```html
{#- 게시판 목록 (원본 theme/basic/skin/board/notice·reference 목록 화면을 그대로 옮김, 웹진형: 좌측 1건 + 우측 6건)
    - 관리용 목록 폼(board_list_update.php)은 정적 사이트에서 쓸 수 없어 action을 없앰
    - 검색: 원본처럼 검색창은 숨겨져 있고, 열리면 JS 제목 검색(board_search.js)으로 동작. 주소 ?stx=검색어 로도 검색 -#}
{% extends "base.html" %}
{% block content %}

<!-- 게시판 목록 시작 { -->
<div id="bo_list" style="width:100%">

    <!-- 게시판 카테고리 시작 { -->
        <!-- } 게시판 카테고리 끝 -->

    <form name="fboardlist" id="fboardlist" action="#" onsubmit="return false;" method="post">

        <input type="hidden" name="bo_table" value="{{ board.table }}">
        <input type="hidden" name="sfl" value="">
        <input type="hidden" name="stx" value="">
        <input type="hidden" name="spt" value="">
        <input type="hidden" name="sca" value="">
        <input type="hidden" name="sst" value="wr_num, wr_reply">
        <input type="hidden" name="sod" value="">
        <input type="hidden" name="page" value="{{ page }}">
        <input type="hidden" name="sw" value="">

        <!-- 게시판 페이지 정보 및 버튼 시작 { -->
        <div id="bo_btn_top">

            <ul class="btn_bo_user">
                                                                            </ul>
        </div>
        <!-- } 게시판 페이지 정보 및 버튼 끝 -->



            <div class="webzine_layout">

                <!-- 좌측 : 최신글 1건 -->
                {% if left %}                <div class="webzine_left">
                                    <a href="{{ left.href }}" >
{%- if left.thumb %}
                        <div class="left_thumb">
                        <img src="{{ left.thumb }}" alt="">
                        </div>
{%- endif %}

                    <div class="left_txt">
                        <span class="label">
                                                    {{ labels.list_label }}
                                                </span>
                        <h2>{{ left.subject }}</h2>
                        <p class="date">{{ left.date }}</p>
                    </div>
                    </a>
                </div>
                {% endif %}
                <!-- 우측 : 다음 6건 -->
                <div class="webzine_right">
                    {% for it in right %}                    <div class="right_item">
                                            <a href="{{ it.href }}">
{%- if it.thumb %}
                            <div class="thumb">
                                <img src="{{ it.thumb }}" alt="">
                            </div>
{%- endif %}
                            <div class="txt">
                                <p class="tit">{{ it.subject }}</p>
                                <span class="date">{{ it.date }}</span>
                            </div>
                        </a>
                    </div>
                    {% endfor %}                </div>

            </div>

        <!-- 페이지 -->
        {{ paging }}
        <!-- 페이지 -->

            </form>

    <!-- 게시판 검색 시작 { -->
    <div class="bo_sch_wrap">
        <fieldset class="bo_sch">
            <h3>검색</h3>
            <form name="fsearch" method="get" data-board-index="search.json">
                <input type="hidden" name="bo_table" value="{{ board.table }}">
                <input type="hidden" name="sca" value="">
                <input type="hidden" name="sop" value="and">
                <label for="sfl" class="sound_only">검색대상</label>
                <select name="sfl" id="sfl">
                    <option value="wr_subject" >제목</option><option value="wr_content" >내용</option><option value="wr_subject||wr_content" >제목+내용</option><option value="wr_name,1" >글쓴이</option><option value="wr_name,0" >글쓴이(코)</option>                </select>
                <label for="stx" class="sound_only">검색어<strong class="sound_only"> 필수</strong></label>
                <div class="sch_bar">
                    <input type="text" name="stx" value="" required id="stx" class="sch_input" size="25" maxlength="20" placeholder="{{ labels.search_placeholder }}">
                    <button type="submit" value="검색" class="sch_btn"><i class="fa fa-search" aria-hidden="true"></i><span class="sound_only">검색</span></button>
                </div>
                <button type="button" class="bo_sch_cls" title="닫기"><i class="fa fa-times" aria-hidden="true"></i><span class="sound_only">닫기</span></button>
            </form>
        </fieldset>
        <div class="bo_sch_bg"></div>
    </div>
    <script>
        jQuery(function ($) {
            // 게시판 검색
            $(".btn_bo_sch").on("click", function () {
                $(".bo_sch_wrap").toggle();
            })
            $('.bo_sch_bg, .bo_sch_cls').click(function () {
                $('.bo_sch_wrap').hide();
            });
        });

    </script>
    <script src="%%ROOT%%hb/board_search.js"></script>
    <!-- } 게시판 검색 끝 -->
</div>


<!-- } 게시판 목록 끝 -->





{% endblock %}
```
- 템플릿 원문 board_view.html:
```html
{#- 게시글 보기 (원본 스킨의 글 화면을 그대로 옮김)
    - 조회수·다운로드 수·연결 수: 원본 화면에 찍혀 있던 값(content/board_snapshot.json)을 고정 표시
    - 이미지 확대 보기: 원본은 view_image.php 새 창 → 정적판은 라이트박스(lightbox.js)
    - 첨부: download.php 대신 파일 직접 링크(download 속성에 원본 파일명), 관련링크: link.php 대신 직접 링크 -#}
{% extends "base.html" %}
{% block content %}

<script src="%%ROOT%%js/viewimageresize.js"></script>

<!-- 게시물 읽기 시작 { -->

<article id="bo_v" style="width:100%">
	<div class="board_view_top">
		<div class="board_view_label">
			<div class="main_board_line">
				<div class="main_board_line_in">
					 {{ post.subject }}				</div>
			</div>
		</div>
		<div class="board_view_info">
			<div class="board_view_info_left">
				<div class="board_view_info_div board_view_info_name">
					<b>
													{{ labels.writer }}
											</b><span><span class="sv_member">Hanbit</span></span>
				</div>
			</div>
			<div class="board_view_info_right">
				<div class="board_view_info_div board_view_info_date">
					<b>
													{{ labels.date }}
											</b><span>{{ post.view_date }}</span>
				</div>
				<div class="board_view_info_div board_view_info_hit">
					<b>
													{{ labels.views }}
											</b><span>{{ post.hit }}</span>
				</div>
			</div>
		</div>
	</div>
	<section id="bo_v_info">
		<!-- 게시물 상단 버튼 시작 { -->
		<div id="bo_v_top">

			<ul class="btn_bo_user bo_v_com">
				<li><a href="index.html" class="btn_b01 btn" title="목록"><i class="fa fa-list" aria-hidden="true"></i><span class="sound_only">목록</span></a></li>
															</ul>
			<script>

			jQuery(function($){
				// 게시판 보기 버튼 옵션
				$(".btn_more_opt.is_view_btn").on("click", function(e) {
					e.stopPropagation();
					$(".more_opt.is_view_btn").toggle();
				})
;
				$(document).on("click", function (e) {
					if(!$(e.target).closest('.is_view_btn').length) {
						$(".more_opt.is_view_btn").hide();
					}
				});
			});
			</script>
					</div>
		<!-- } 게시물 상단 버튼 끝 -->
	</section>

	<section id="bo_v_atc">
		<h2 id="bo_v_atc_title">본문</h2>
		<div id="bo_v_img">
{% for im in post.file_images %}<a href="{{ im.large }}" target="_blank" class="view_image"><img src="{{ im.thumb }}" alt=""/></a>{% endfor %}</div>

		<!-- 본문 내용 시작 { -->
		<div id="bo_v_con">{{ post.content_html }}</div>
				<!-- } 본문 내용 끝 -->

{% if post.embed %}
                    <!-- 관련링크 시작 { -->
            <div class="pt_view_con_wrap">
                                        <div class="pt_view_con">
                                                        <div style="position: relative; padding-bottom: 56.25%; height: 0px;">
                                <iframe type="text/html" allowtransparency="true" frameborder="0" width="100%" height="100%" src="{{ post.embed }}" allowfullscreen="true" style="position: absolute; top: 0px; left: 0px;"></iframe>
                            </div>
                        </div>

                                    </div>
            <!-- } 관련링크 끝 -->
{% endif %}




		<!--  추천 비추천 시작 { -->
				<!-- }  추천 비추천 끝 -->
	</section>


{% if post.downloads %}
		<!-- 첨부파일 시작 { -->
	<section id="bo_v_file">
		<h2>첨부파일</h2>
		<ul>
		{% for f in post.downloads %}
			<li>
				<i class="fa fa-folder-open" aria-hidden="true"></i>
				<a href="{{ f.href }}" class="view_file_download" download="{{ f.name }}">
					<strong>{{ f.name }}</strong>  ({{ f.size }})
				</a>
				<br>
				<span class="bo_v_file_cnt">{{ f.count }} | DATE : {{ f.date }}</span>
			</li>
		{% endfor %}
		</ul>
	</section>
	<!-- } 첨부파일 끝 -->
{% endif %}

{% if post.links %}
		<!-- 관련링크 시작 { -->
	<section id="bo_v_link">
		<h2>관련링크</h2>
		<ul>
		{% for l in post.links %}
			<li>
				<i class="fa fa-link" aria-hidden="true"></i>
				<a href="{{ l.href }}" target="_blank">
					<strong>{{ l.text }}</strong>
				</a>
				<br>
				<span class="bo_v_link_cnt">{{ l.count }}</span>
			</li>
		{% endfor %}
		</ul>
	</section>
	<!-- } 관련링크 끝 -->
{% endif %}

		<ul class="bo_v_nb">
{% if post.prev %}		<li class="btn_prv"><span class="nb_tit"><i class="fa fa-chevron-up" aria-hidden="true"></i> Prev</span><a href="{{ post.prev.href }}">{{ post.prev.subject }}</a> <span class="nb_date">{{ post.prev.date }}</span></li>{% endif %}
{% if post.next %}		<li class="btn_next"><span class="nb_tit"><i class="fa fa-chevron-down" aria-hidden="true"></i> Next</span><a href="{{ post.next.href }}">{{ post.next.subject }}</a>  <span class="nb_date">{{ post.next.date }}</span></li>{% endif %}
	</ul>


</article>
<!-- } 게시판 읽기 끝 -->

<script>

function board_move(href)
{
	window.open(href, "boardmove", "left=50, top=50, width=500, height=550, scrollbars=1");
}
</script>

<link rel="stylesheet" href="%%ROOT%%hb/lightbox.css">
<script src="%%ROOT%%hb/lightbox.js"></script>
<script>
$(function() {
	// 이미지 확대 보기: 원본의 새 창(view_image.php) 대신 라이트박스
	$("a.view_image").click(function() {
		hanbitLightbox.open(this.href, $(this).find("img").attr("alt") || "");
		return false;
	});

	// 이미지 리사이즈
	$("#bo_v_atc").viewimageresize();
});
</script>
<!-- } 게시글 읽기 끝 -->





{% endblock %}
```
- 빌드된 목록 원문 일부(public/board/notice/index.html):
```html
--- 818행 ---
	<div class="notice_wrap_in sec_in">
		<div class="notice_tit_wrap animate" data-animate="fadeIn" data-duration="1.0s" data-delay="0.3s">
			<div class="board_top_label">
                <div class="visual_nav_label">
                    <div class="sub_visual_nav_wrap animate" data-animate="fadeIn" data-duration="1.0s" data-delay="0.3s">
    <div class="sub_visual_nav">
        <a href="../../index.html">
                    홈
                </a>
        <span class="deco"></span>
        <div class="p_d_menu">
            <div class="p_d_menu_label mainmenu">
            <div class="menu menu_05 ">
    <a href="../../page/hanbit.html" class="menu_a void_link ">
		<span>
                    회사소개
        		</span>
    </a>
    <div class="sub_menu_wrap">
        <div class="sub_menu sub_menu_01 ">
            <a href="../../page/hanbit.html" class="sub_menu_a ">
				<span>
				                    한빛이노텍
                				</span>
            </a>
        </div>
        <div class="sub_menu sub_menu_02 ">
            <a href="../../page/history.html" class="sub_menu_a ">
				<span>
					                    연혁
                    				</span>
            </a>
        </div>
        <div class="sub_menu sub_menu_03 ">
            <a href="../../page/cert.html" class="sub_menu_a ">
				<span>
					                        인증 및 수상
                    				</span>
            </a>
        </div>
        <div class="sub_menu sub_menu_03 ">
            <a href="../../page/esg.html" class="sub_menu_a ">
				<span>
					                        ESG 경영 
                    				</span>
            </a>
        </div>
        <div class="sub_menu sub_menu_03 ">
            <a href="../../page/location.html" class="sub_menu_a ">
				<span>
                Contact
				</span>
            </a>
        </div>
    </div>
</div>
<div class="menu menu_01 ">
    <a href="../../page/pv.html" class="menu_a void_link ">
		<span>
                    사업분야
        		</span>
    </a>
```
- 빌드된 상세 원문 일부(public/board/notice/10.html):
```html
--- 1662행 ---
<!-- 게시물 읽기 시작 { -->

<article id="bo_v" style="width:100%">
	<div class="board_view_top">
		<div class="board_view_label">
			<div class="main_board_line">
				<div class="main_board_line_in">
					 [NEWS] 한빛이노텍 지능형 인버터 상용화박차, 탄소중립 대응 본격화				</div>
			</div>
		</div>
		<div class="board_view_info">
			<div class="board_view_info_left">
				<div class="board_view_info_div board_view_info_name">
					<b>
													작성자
											</b><span><span class="sv_member">Hanbit</span></span>
				</div>
			</div>
			<div class="board_view_info_right">
				<div class="board_view_info_div board_view_info_date">
					<b>
													작성일
											</b><span>26-02-26 16:09</span>
				</div>
				<div class="board_view_info_div board_view_info_hit">
					<b>
													조회수
											</b><span>238</span>
				</div>
			</div>
		</div>
	</div>
	<section id="bo_v_info">
		<!-- 게시물 상단 버튼 시작 { -->
		<div id="bo_v_top">

			<ul class="btn_bo_user bo_v_com">
				<li><a href="index.html" class="btn_b01 btn" title="목록"><i class="fa fa-list" aria-hidden="true"></i><span class="sound_only">목록</span></a></li>
															</ul>
			<script>

			jQuery(function($){
				// 게시판 보기 버튼 옵션
				$(".btn_more_opt.is_view_btn").on("click", function(e) {
					e.stopPropagation();
					$(".more_opt.is_view_btn").toggle();
				})
;
				$(document).on("click", function (e) {
					if(!$(e.target).closest('.is_view_btn').length) {
						$(".more_opt.is_view_btn").hide();
					}
				});
			});
			</script>
					</div>
		<!-- } 게시물 상단 버튼 끝 -->
	</section>

	<section id="bo_v_atc">
		<h2 id="bo_v_atc_title">본문</h2>
		<div id="bo_v_img">
```
- 게시판 HTML 이미지 경로(폴더별 상위 8): [('data/editor/2603/', 265), ('data/file/notice/', 12), ('data/editor/2606/', 10), ('data/editor/2605/', 8), ('data/editor/2607/', 8), ('data/editor/2608/', 3), ('data/editor/2609/', 2), ('data/editor/2602/', 2)]
- 게시판 HTML 첨부 경로(폴더별 상위 8): [('theme/basic/images/', 92), ('files/library/', 2)]
- 요약: 글 수(posts.json) notice 10 / media 67 / library 2 (ENG: notice_en 7 / media_en 67 / library_en 0). 페이지당 7건(D7, 좌측 1 + 우측 6).
  페이징 파일명 index.html, page-2.html … (media는 page-10.html까지). 상세는 /board/<게시판>/<글번호>.html.
  이미지: 본문은 data/editor/YYMM/, 첨부 이미지는 data/file/<게시판>/ (썸네일은 optimize.py가 만든 축소본). 첨부 PDF: files/library/.
- **"회사소식" 라벨이 잘못 붙는 원인**: build/boards.py 22~27행 `LABELS["ko"]["list_label"] = "회사소식"` 이 게시판 구분 없이 한 값이라,
  board_list.html 의 `<span class="label">{{ labels.list_label }}</span>`(좌측 최신글 카드)에 시공사례·E-Catalog 목록에서도 "회사소식"이 찍힌다.
  (ENG도 같은 구조로 모든 게시판에 "Notice") → 게시판별 라벨(boards_meta.subject 등)로 바꿔야 함.
- '회사소식' 문자열 출처(templates·build·content/pages 검색, 메뉴 문구 포함):
```
templates/_board_head_ko.html:254: 회사소식
templates/_board_head_ko.html:526: 회사소식
templates/_board_head_ko.html:805: 회사소식
templates/_top_ko.html:278: 회사소식
templates/_top_ko.html:579: 회사소식
build/boards.py:24: "link_cnt": "{}회 연결", "list_label": "회사소식"},
build/build.py:118: if "%%LATEST_NOTICE%%" in content_html:   # D12: 메인 회사소식 = posts.json 최신 글 4건
build/extract_pages.py:375: # D12: 메인 회사소식 4건은 빌드 때 posts.json 최신 글로 만든다 → 자리 표시만 남김
build/extract_pages.py:381: common_problems.append(f"{lang}: 메인 회사소식 영역을 찾지 못함(D12)")
build/extras.py:2: 4-6: 메인 회사소식(D12), 팝업, 옛 주소 이동(404.html + redirects.json), sitemap.xml·robots.txt.
build/extras.py:17: # ───────── D12 메인 회사소식 4건 ─────────
build/optimize.py:8: - 메인 회사소식(notice·notice_en): _443x243, 가운데 자르기
content/pages/ko/index.html:256: <li class="news_btn"><a href="%%ROOT%%board/notice/index.html" class="news_btn_a">회사소식 </a></li>
content/pages/ko/page/bipv.html:254: 회사소식
content/pages/ko/page/bipv.html:526: 회사소식
content/pages/ko/page/bipv.html:826: 회사소식
content/pages/ko/page/building.html:254: 회사소식
content/pages/ko/page/building.html:526: 회사소식
content/pages/ko/page/building.html:825: 회사소식
content/pages/ko/page/carbon.html:254: 회사소식
content/pages/ko/page/carbon.html:526: 회사소식
content/pages/ko/page/carport.html:253: 회사소식
content/pages/ko/page/carport.html:525: 회사소식
content/pages/ko/page/carport.html:816: 회사소식
content/pages/ko/page/cert.html:254: 회사소식
content/pages/ko/page/cert.html:526: 회사소식
content/pages/ko/page/cert.html:826: 회사소식
content/pages/ko/page/combiner.html:253: 회사소식
content/pages/ko/page/de_system.html:254: 회사소식
content/pages/ko/page/de_system.html:526: 회사소식
content/pages/ko/page/de_system.html:826: 회사소식
content/pages/ko/page/epc.html:254: 회사소식
content/pages/ko/page/epc.html:526: 회사소식
content/pages/ko/page/epc.html:818: 회사소식
content/pages/ko/page/esg.html:254: 회사소식
content/pages/ko/page/esg.html:526: 회사소식
content/pages/ko/page/esg.html:826: 회사소식
content/pages/ko/page/finance.html:254: 회사소식
content/pages/ko/page/finance.html:526: 회사소식
content/pages/ko/page/finance.html:825: 회사소식
content/pages/ko/page/fire_cert.html:253: 회사소식
content/pages/ko/page/hanbit.html:258: 회사소식
content/pages/ko/page/hanbit.html:530: 회사소식
content/pages/ko/page/history.html:254: 회사소식
content/pages/ko/page/history.html:526: 회사소식
content/pages/ko/page/history.html:826: 회사소식
content/pages/ko/page/housing.html:254: 회사소식
content/pages/ko/page/housing.html:526: 회사소식
content/pages/ko/page/housing.html:825: 회사소식
content/pages/ko/page/inverter.html:253: 회사소식
content/pages/ko/page/kpso.html:254: 회사소식
content/pages/ko/page/kpso.html:526: 회사소식
content/pages/ko/page/kpso.html:825: 회사소식
content/pages/ko/page/location.html:254: 회사소식
content/pages/ko/page/location.html:526: 회사소식
content/pages/ko/page/location.html:826: 회사소식
content/pages/ko/page/monitoring.html:253: 회사소식
content/pages/ko/page/pv.html:254: 회사소식
content/pages/ko/page/pv.html:526: 회사소식
content/pages/ko/page/pv.html:828: 회사소식
```
- public/board/media/index.html 안 '회사소식' 등장 6회, 줄:
```
--- 371행 ---
        <div class="sub_menu sub_menu_01 ">
            <a href="../../board/notice/index.html" class="sub_menu_a ">
				<span>
					                        회사소식
                    				</span>
            </a>
        </div>
--- 672행 ---
        <div class="sub_menu sub_menu_01 ">
            <a href="../../board/notice/index.html" class="sub_menu_a ">
				<span>
					                        회사소식
                    				</span>
            </a>
        </div>
--- 1068행 ---
        <div class="sub_menu sub_menu_01 ">
            <a href="../../board/notice/index.html" class="sub_menu_a ">
				<span>
					                        회사소식
                    				</span>
            </a>
        </div>
--- 1340행 ---
        <div class="sub_menu sub_menu_01 ">
            <a href="../../board/notice/index.html" class="sub_menu_a ">
				<span>
					                        회사소식
                    				</span>
            </a>
        </div>
--- 1619행 ---
        <div class="sub_menu sub_menu_01 ">
            <a href="../../board/notice/index.html" class="sub_menu_a ">
				<span>
					                        회사소식
                    				</span>
            </a>
        </div>
```
- public/board/library/index.html 안 '회사소식' 등장 6회, 줄:
```
--- 371행 ---
        <div class="sub_menu sub_menu_01 ">
            <a href="../../board/notice/index.html" class="sub_menu_a ">
				<span>
					                        회사소식
                    				</span>
            </a>
        </div>
--- 672행 ---
        <div class="sub_menu sub_menu_01 ">
            <a href="../../board/notice/index.html" class="sub_menu_a ">
				<span>
					                        회사소식
                    				</span>
            </a>
        </div>
--- 1068행 ---
        <div class="sub_menu sub_menu_01 ">
            <a href="../../board/notice/index.html" class="sub_menu_a ">
				<span>
					                        회사소식
                    				</span>
            </a>
        </div>
--- 1340행 ---
        <div class="sub_menu sub_menu_01 ">
            <a href="../../board/notice/index.html" class="sub_menu_a ">
				<span>
					                        회사소식
                    				</span>
            </a>
        </div>
--- 1619행 ---
        <div class="sub_menu sub_menu_01 ">
            <a href="../../board/notice/index.html" class="sub_menu_a ">
				<span>
					                        회사소식
                    				</span>
            </a>
        </div>
```

## 5) 메인 index.html
- 메인 원본 후보: ['content/pages/en/index.html', 'content/pages/ko/index.html']
- 팝업 마크업(public/index.html):
```html
--- 103행 ---


    <div id="hd_pops_3" class="hd_pops" style="top:150px;left:10px" data-begin="2026-05-06 00:00:00" data-end="2026-12-31 00:00:00">
        <div class="hd_pops_con" style="width:450px;height:660px">
            <p><img src="data/editor/2605/8ff05b45953783ab60f04bdda10a57c4_1778041614_95.jpg" title="8ff05b45953783ab60f04bdda10a57c4_1778041614_95.jpg" alt="8ff05b45953783ab60f04bdda10a57c4_1778041614_95.jpg" /><br style="clear:both;">&nbsp;</p>        </div>
        <div class="hd_pops_footer">
            <button class="hd_pops_reject hd_pops_3 24"><strong>24</strong>시간 동안 다시 열람하지 않습니다.</button>
            <button class="hd_pops_close hd_pops_3">닫기 <i class="fa fa-times" aria-hidden="true"></i></button>
        </div>
    </div>
</div>

<script src="hb/popup.js"></script>
<!-- } 팝업레이어 끝 --><div class="header_all_wrap">
    <div class="header_wrap">
        <div class="header_mid_wrap">
            <div class="header_mid">
                <div class="logo_wrap">
                    <a href="index.html" class="logo" alt="Animotiontech" title="Animotiontech">
                        <span class="logo_off"><svg id="_레이어_2" data-name="레이어 2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 127.26 28.44">
<g>
    <path class="st1" d="M100.88,19.98c1.05.61,1.73,1.73,1.73,3.7,0,3.93-2.65,4.76-6.37,4.76h-10.27V12.04h10.27c3.45,0,6.06.81,6.06,4.53,0,1.7-.54,2.76-1.41,3.41M90.25,18.71h6.08c1.19,0,1.82-.45,1.82-1.61,0-1.3-.81-1.68-1.86-1.68h-6.03v3.3ZM90.25,21.44v3.45h6.1c1.1,0,1.93-.36,1.93-1.75s-.72-1.71-1.86-1.71h-6.17Z"/>
    <rect class="st1" x="105" y="12.05" width="4.4" height="16.4"/>
    <polygon class="st1" points="117.06 15.59 111.25 15.59 111.25 12.04 127.26 12.04 127.26 15.59 121.45 15.59 121.45 28.44 117.06 28.44 117.06 15.59"/>
    <polygon class="st1" points="47.54 28.44 42.96 28.44 50.99 12.04 55.75 12.04 63.78 28.44 59.33 28.44 53.41 15.95 47.54 28.44"/>
    <path class="st1" d="M36.83,22.05v-10h4.4v16.4h-4.4v-6.39ZM29.01,28.44h-4.4V12.05h4.4v16.4Z"/>
    <rect class="st1" x="27.66" y="18.71" width="11.23" height="3.06"/>
    <path class="st1" d="M65.81,12.73v15.71h4.08v-12.42c-1.29-1.19-2.65-2.29-4.08-3.29"/>
    <path class="st1" d="M82.91,26.09v-14.04h-4.06l.04,6.81c1.55,2.27,2.9,4.69,4.02,7.23"/>
    <path class="st0" d="M7.61,28.44C13.71,14.56,27.58,4.87,43.72,4.87s30.01,9.69,36.12,23.57h3.07C76.5,11.8,60.36,0,41.46,0S6.42,11.8,0,28.44h7.61Z"/>
  </g>
</svg></span>
                        <span class="logo_on"><svg id="_레이어_2" data-name="레이어 2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 127.26 28.44">
<g>
    <path class="st1" d="M100.88,19.98c1.05.61,1.73,1.73,1.73,3.7,0,3.93-2.65,4.76-6.37,4.76h-10.27V12.04h10.27c3.45,0,6.06.81,6.06,4.53,0,1.7-.54,2.76-1.41,3.41M90.25,18.71h6.08c1.19,0,1.82-.45,1.82-1.61,0-1.3-.81-1.68-1.86-1.68h-6.03v3.3ZM90.25,21.44v3.45h6.1c1.1,0,1.93-.36,1.93-1.75s-.72-1.71-1.86-1.71h-6.17Z"/>
    <rect class="st1" x="105" y="12.05" width="4.4" height="16.4"/>
    <polygon class="st1" points="117.06 15.59 111.25 15.59 111.25 12.04 127.26 12.04 127.26 15.59 121.45 15.59 121.45 28.44 117.06 28.44 117.06 15.59"/>
    <polygon class="st1" points="47.54 28.44 42.96 28.44 50.99 12.04 55.75 12.04 63.78 28.44 59.33 28.44 53.41 15.95 47.54 28.44"/>
    <path class="st1" d="M36.83,22.05v-10h4.4v16.4h-4.4v-6.39ZM29.01,28.44h-4.4V12.05h4.4v16.4Z"/>
    <rect class="st1" x="27.66" y="18.71" width="11.23" height="3.06"/>
    <path class="st1" d="M65.81,12.73v15.71h4.08v-12.42c-1.29-1.19-2.65-2.29-4.08-3.29"/>
    <path class="st1" d="M82.91,26.09v-14.04h-4.06l.04,6.81c1.55,2.27,2.9,4.69,4.02,7.23"/>
    <path class="st0" d="M7.61,28.44C13.71,14.56,27.58,4.87,43.72,4.87s30.01,9.69,36.12,23.57h3.07C76.5,11.8,60.36,0,41.46,0S6.42,11.8,0,28.44h7.61Z"/>
  </g>
</svg></span>
                    </a>
                </div>
```
- Our Project 마크업(public/index.html):
```html
--- 996행 ---
        <div class="main_sec_wrap main_visual_wrap main_sec_in">
            <div class="main_sec_03_text_wrap animate" data-animate="fadeIn" data-duration="1.0s" data-delay="0.3s">
                <h2 class="sec_tit8 bold600">Our Project</h2>
                <div class="ssgap"></div>
                <p class="sec_txt2"> 
                설계부터 시공, 제조, 감리, 유지보수까지 <br>
                끊김없는 에너지 솔루션을 제공합니다.
                </p>
                <div class="ssgap"></div>
                <div class="view_more_btn">
                    <a href="board/media/index.html">View Project <i class="xi-angle-right-min"></i> </a>
                </div>
            </div>
            <ul class="mainProject_list">
                <li class="mainProject_item item_01"></li>
                <li class="mainProject_item item_02"></li>
                <li class="mainProject_item item_03"></li>
                <li class="mainProject_item item_04">
                    <a href="" class="mainProject_item_a">
                            <div class="bg"></div>
                        <div class="on">
                            <div class="tit">BIPV</div>
                            <div class="txt">일광도서관 <br>BIPV24.09kW, <br>태양광발전장치 <br>39.6kW </div>
                        </div>
                    </a>
                </li>
                <li class="mainProject_item item_05"></li>
                <li class="mainProject_item item_06"></li>
                <li class="mainProject_item item_07">
                    <a href="board/media/index.html" class="mainProject_item_a">
                            <div class="bg"></div>
                        <div class="on">
                            <div class="tit">PV</div>
                            <div class="txt">경기도청 신청사 <br>태양광발전장치 <br>984.6kW</div>
                        </div>
                    </a>
                </li>
                <li class="mainProject_item item_08">
                    <a href="board/media/48.html" class="mainProject_item_a">
                            <div class="bg"></div>
                        <div class="on">
                            <div class="tit">PV</div>
                            <div class="txt">경산정수장 <br>태양광발전장치<br>810kW</div>
                        </div>
                    </a>
                </li>
                <li class="mainProject_item item_09">
```
- News 마크업 원본(content/pages/ko/index.html 248~264행, `%%LATEST_NOTICE%%` 자리에 build/extras.py latest_notice()가 notice 최신 4건을 넣음):
```html
    <section class="News main_sec_all_wrap main_visual_all_wrap section" id="section_05">
        <div class="NewsIn main_visual_wrap sec_in">
            <div class="NewsTit">
                <div class="NewsTit_in">
                    <h2 class="sec_tit9 bold600">News</h2>
                    <p class="sec_txt2">한빛이노텍의 새로운 소식과 <br>혁신을 전해드립니다.</p>
                </div>
                <ul>
                    <li class="news_btn"><a href="%%ROOT%%board/notice/index.html" class="news_btn_a">회사소식 </a></li>
                    <li class="news_btn"><a href="%%ROOT%%board/media/index.html" class="news_btn_a">시공사례 </a></li>
                    <li class="news_btn"><a href="https://blog.naver.com/hkele" class="news_btn_a">블로그</a></li>
                </ul>
            </div>
            <div class="NewsList">%%LATEST_NOTICE%%
            </div>
        </div>
    </section>
```
- News 1건 마크업(extras.py가 생성):
```html
    <div class="m_b_ns_box">
        <a href="%%ROOT%%board/notice/{id}.html" class="m_b_ns_box_a">
            <div class="m_b_ns_thumb"><img src="%%ROOT%%{thumb 443x243}" alt="" loading="lazy" width="443" height="243"></div>
            <div class="m_b_ns_box_in">
                <div class="m_b_ns_title sec_tit2 bold700">{title}</div>
                <div class="sssgap"></div>
                <div class="m_b_ns_content sec_txt">{본문 앞부분}...</div>
            </div>
        </a>
    </div>
```
- Our Project: content/pages/ko/index.html 안에 9칸(item_01~09)이 **손으로 쓴 고정 마크업**(제목·용량·링크 직접 기재). 3·5번 등 비공개 칸은 빈 `<li>`. posts.json과 연결되지 않음.
- 팝업: posts.json `popups`(begin/end/disable_hours/content) → 빌드 때 `.hd_pops` 마크업(data-begin/data-end) 생성, static/hb/popup.js가 브라우저 시각(KST)과 비교해 표시, "24시간" 닫기는 localStorage 만료 시각 저장.
- (참고) 아래 스크립트의 News 자동 추출은 CSS 줄을 잘못 잡았음:
```html
--- 41행 ---
<link rel="stylesheet" href="theme/basic/css/owl.carousel.min.css">
<link rel="stylesheet" href="js/font-awesome/css/font-awesome.min.css">
<link rel="stylesheet" href="theme/basic/skin/latest/main_news/style.css">
<link rel="stylesheet" href="theme/basic/css/owl.theme.default.min.css">
<link rel="stylesheet" href="theme/basic/css/animate.min.css">
<link rel="stylesheet" href="theme/basic/css/jquery.fullpage.css">
<link rel="stylesheet" href="theme/basic/css/base.css">
<link rel="stylesheet" href="theme/basic/css/slick-theme.min.css">
<link rel="stylesheet" href="theme/basic/css/slick.min.css">
<link rel="stylesheet" href="theme/basic/css/xeicon.min.css">
<link rel="stylesheet" href="theme/basic/css/xeicon.css">
<link rel="stylesheet" href="theme/basic/css/layout.css">
<link rel="stylesheet" href="theme/basic/css/board.css">
<link rel="stylesheet" href="theme/basic/css/res.css">


<!--[if lte IE 8]>
<script src="js/html5.js"></script>
<![endif]-->
<script>
// 자바스크립트에서 사용하는 전역변수 선언
var g5_url       = "";
var g5_bbs_url   = "bbs";
var g5_is_member = "";
var g5_is_admin  = "";
var g5_is_mobile = "";
var g5_bo_table  = "";
var g5_sca       = "";
var g5_editor    = "";
var g5_cookie_domain = "";
var g5_theme_shop_url = "";
var g5_shop_url = "";
</script>

<script src="js/jquery-1.12.4.min.js"></script>
<script src="js/jquery-migrate-1.4.1.min.js"></script>
<script src="js/common.js"></script>
<script src="js/wrest.js"></script>
<script src="theme/basic/js/jquery.fullpage.js"></script>
<script src="theme/basic/js/plugins.js"></script>
<script src="theme/basic/js/vanilla-tilt.js"></script>
<script src="theme/basic/js/jquery.placeholder.js"></script>
<script src="theme/basic/js/jquery_sly.js"></script>
<script src="theme/basic/js/scrolla.jquery.min.js"></script>
<script src="theme/basic/js/owl.carousel.min.js"></script>
<script src="theme/basic/js/slick.min.js"></script>
<script src="theme/basic/js/gsap.min.js"></script>
```
- 팝업 JS:
  - static/hb/popup.js
```js
--- 3행 ---
/* 메인 팝업 (원본 그누보드 팝업레이어를 정적 사이트용으로 옮김)
   - 게시 기간: 각 팝업의 data-begin ~ data-end (한국 시간)를 방문자 브라우저의 현재 시각과 비교해 자동으로 보이거나 숨김
   - "24시간 동안 다시 열람하지 않습니다": 원본의 쿠키 대신 localStorage에 만료 시각 저장
   - 이 스크립트는 팝업 마크업 바로 뒤에서 읽혀서, 화면이 그려지기 전에 숨길 팝업을 숨긴다 */
(function () {
  function kst(s) { return s ? new Date(s.replace(" ", "T") + "+09:00").getTime() : NaN; }
  function load(key) { try { return parseInt(window.localStorage.getItem(key) || "0", 10) || 0; } catch (e) { return 0; } }
  function save(key, v) { try { window.localStorage.setItem(key, String(v)); } catch (e) { /* 저장 불가(사생활 보호 모드 등): 이번 화면에서만 닫힘 */ } }

  var now = Date.now();
  var pops = document.querySelectorAll(".hd_pops");
  for (var i = 0; i < pops.length; i++) {
    var el = pops[i];
    var b = kst(el.getAttribute("data-begin")), e = kst(el.getAttribute("data-end"));
    var hidden = (!isNaN(b) && now < b) || (!isNaN(e) && now > e) || load(el.id) > now;
    if (hidden) el.style.display = "none";
  }

  function onClick(cls, fn) {
    var btns = document.querySelectorAll("." + cls);
    for (var j = 0; j < btns.length; j++) btns[j].addEventListener("click", fn);
  }
  // 원본과 같은 방식: 버튼 class의 두 번째 값이 팝업 id, 세 번째 값이 다시 안 볼 시간
  onClick("hd_pops_reject", function () {
    var c = this.className.split(" ");
    var box = document.getElementById(c[1]);
    if (box) box.style.display = "none";
    save(c[1], Date.now() + (parseInt(c[2], 10) || 24) * 3600 * 1000);
  });
  onClick("hd_pops_close", function () {
    var box = document.getElementById(this.className.split(" ")[1]);
    if (box) box.style.display = "none";
  });
  if (window.jQuery) jQuery(function ($) { $("#hd").css("z-index", 1000); });
})();
--- 7행 ---
   - 이 스크립트는 팝업 마크업 바로 뒤에서 읽혀서, 화면이 그려지기 전에 숨길 팝업을 숨긴다 */
(function () {
  function kst(s) { return s ? new Date(s.replace(" ", "T") + "+09:00").getTime() : NaN; }
  function load(key) { try { return parseInt(window.localStorage.getItem(key) || "0", 10) || 0; } catch (e) { return 0; } }
  function save(key, v) { try { window.localStorage.setItem(key, String(v)); } catch (e) { /* 저장 불가(사생활 보호 모드 등): 이번 화면에서만 닫힘 */ } }

  var now = Date.now();
  var pops = document.querySelectorAll(".hd_pops");
  for (var i = 0; i < pops.length; i++) {
    var el = pops[i];
    var b = kst(el.getAttribute("data-begin")), e = kst(el.getAttribute("data-end"));
    var hidden = (!isNaN(b) && now < b) || (!isNaN(e) && now > e) || load(el.id) > now;
    if (hidden) el.style.display = "none";
  }

  function onClick(cls, fn) {
    var btns = document.querySelectorAll("." + cls);
    for (var j = 0; j < btns.length; j++) btns[j].addEventListener("click", fn);
  }
  // 원본과 같은 방식: 버튼 class의 두 번째 값이 팝업 id, 세 번째 값이 다시 안 볼 시간
  onClick("hd_pops_reject", function () {
    var c = this.className.split(" ");
    var box = document.getElementById(c[1]);
    if (box) box.style.display = "none";
    save(c[1], Date.now() + (parseInt(c[2], 10) || 24) * 3600 * 1000);
  });
  onClick("hd_pops_close", function () {
    var box = document.getElementById(this.className.split(" ")[1]);
    if (box) box.style.display = "none";
  });
  if (window.jQuery) jQuery(function ($) { $("#hd").css("z-index", 1000); });
})();
```
  - static/js/common.js
```js
--- 105행 ---
}

// 새 창
function popup_window(url, winname, opt)
{
    window.open(url, winname, opt);
}


// 폼메일 창
function popup_formmail(url)
{
    opt = 'scrollbars=yes,width=417,height=385,top=10,left=20';
    popup_window(url, "wformmail", opt);
}

// , 를 없앤다.
function no_comma(data)
{
    var tmp = '';
    var comma = ',';
    var i;

    for (i=0; i<data.length; i++)
    {
        if (data.charAt(i) != comma)
            tmp += data.charAt(i);
    }
    return tmp;
}

// 삭제 검사 확인
function del(href)
{
    if(confirm("한번 삭제한 자료는 복구할 방법이 없습니다.\n\n정말 삭제하시겠습니까?")) {
        document.location.href = href;
    }
}

// 쿠키 입력
function set_cookie(name, value, expirehours, domain)
{
    var today = new Date();
--- 112행 ---


// 폼메일 창
function popup_formmail(url)
{
    opt = 'scrollbars=yes,width=417,height=385,top=10,left=20';
    popup_window(url, "wformmail", opt);
}

// , 를 없앤다.
function no_comma(data)
{
    var tmp = '';
    var comma = ',';
    var i;

    for (i=0; i<data.length; i++)
    {
        if (data.charAt(i) != comma)
            tmp += data.charAt(i);
    }
    return tmp;
}

// 삭제 검사 확인
function del(href)
{
    if(confirm("한번 삭제한 자료는 복구할 방법이 없습니다.\n\n정말 삭제하시겠습니까?")) {
        document.location.href = href;
    }
}

// 쿠키 입력
function set_cookie(name, value, expirehours, domain)
{
    var today = new Date();
    today.setTime(today.getTime() + (60*60*1000*expirehours));
    document.cookie = name + "=" + escape( value ) + "; path=/; expires=" + today.toGMTString() + ";";
    if (domain) {
        document.cookie += "domain=" + domain + ";";
    }
}
```
  - static/theme/basic/js/owl.carousel.min.js
```js
--- 6행 ---
 * Copyright 2013-2018 David Deutsch
 * Licensed under: SEE LICENSE IN https://github.com/OwlCarousel2/OwlCarousel2/blob/master/LICENSE
 */
!function(a,b,c,d){function e(b,c){this.settings=null,this.options=a.extend({},e.Defaults,c),this.$element=a(b),this._handlers={},this._plugins={},this._supress={},this._current=null,this._speed=null,this._coordinates=[],this._breakpoint=null,this._width=null,this._items=[],this._clones=[],this._mergers=[],this._widths=[],this._invalidated={},this._pipe=[],this._drag={time:null,target:null,pointer:null,stage:{start:null,current:null},direction:null},this._states={current:{},tags:{initializing:["busy"],animating:["busy"],dragging:["interacting"]}},a.each(["onResize","onThrottledResize"],a.proxy(function(b,c){this._handlers[c]=a.proxy(this[c],this)},this)),a.each(e.Plugins,a.proxy(function(a,b){this._plugins[a.charAt(0).toLowerCase()+a.slice(1)]=new b(this)},this)),a.each(e.Workers,a.proxy(function(b,c){this._pipe.push({filter:c.filter,run:a.proxy(c.run,this)})},this)),this.setup(),this.initialize()}e.Defaults={items:3,loop:!1,center:!1,rewind:!1,checkVisibility:!0,mouseDrag:!0,touchDrag:!0,pullDrag:!0,freeDrag:!1,margin:0,stagePadding:0,merge:!1,mergeFit:!0,autoWidth:!1,startPosition:0,rtl:!1,smartSpeed:250,fluidSpeed:!1,dragEndSpeed:!1,responsive:{},responsiveRefreshRate:200,responsiveBaseElement:b,fallbackEasing:"swing",slideTransition:"",info:!1,nestedItemSelector:!1,itemElement:"div",stageElement:"div",refreshClass:"owl-refresh",loadedClass:"owl-loaded",loadingClass:"owl-loading",rtlClass:"owl-rtl",responsiveClass:"owl-responsive",dragClass:"owl-drag",itemClass:"owl-item",stageClass:"owl-stage",stageOuterClass:"owl-stage-outer",grabClass:"owl-grab"},e.Width={Default:"default",Inner:"inner",Outer:"outer"},e.Type={Event:"event",State:"state"},e.Plugins={},e.Workers=[{filter:["width","settings"],run:function(){this._width=this.$element.width()}},{filter:["width","items","settings"],run:function(a){a.current=this._items&&this._items[this.relative(this._current)]}},{filter:["items","settings"],run:function(){this.$stage.children(".cloned").remove()}},{filter:["width","items","settings"],run:function(a){var b=this.settings.margin||"",c=!this.settings.autoWidth,d=this.settings.rtl,e={width:"auto","margin-left":d?b:"","margin-right":d?"":b};!c&&this.$stage.children().css(e),a.css=e}},{filter:["width","items","settings"],run:function(a){var b=(this.width()/this.settings.items).toFixed(3)-this.settings.margin,c=null,d=this._items.length,e=!this.settings.autoWidth,f=[];for(a.items={merge:!1,width:b};d--;)c=this._mergers[d],c=this.settings.mergeFit&&Math.min(c,this.settings.items)||c,a.items.merge=c>1||a.items.merge,f[d]=e?b*c:this._items[d].width();this._widths=f}},{filter:["items","settings"],run:function(){var b=[],c=this._items,d=this.settings,e=Math.max(2*d.items,4),f=2*Math.ceil(c.length/2),g=d.loop&&c.length?d.rewind?e:Math.max(e,f):0,h="",i="";for(g/=2;g>0;)b.push(this.normalize(b.length/2,!0)),h+=c[b[b.length-1]][0].outerHTML,b.push(this.normalize(c.length-1-(b.length-1)/2,!0)),i=c[b[b.length-1]][0].outerHTML+i,g-=1;this._clones=b,a(h).addClass("cloned").appendTo(this.$stage),a(i).addClass("cloned").prependTo(this.$stage)}},{filter:["width","items","settings"],run:function(){for(var a=this.settings.rtl?1:-1,b=this._clones.length+this._items.length,c=-1,d=0,e=0,f=[];++c<b;)d=f[c-1]||0,e=this._widths[this.relative(c)]+this.settings.margin,f.push(d+e*a);this._coordinates=f}},{filter:["width","items","settings"],run:function(){var a=this.settings.stagePadding,b=this._coordinates,c={width:Math.ceil(Math.abs(b[b.length-1]))+2*a,"padding-left":a||"","padding-right":a||""};this.$stage.css(c)}},{filter:["width","items","settings"],run:function(a){var b=this._coordinates.length,c=!this.settings.autoWidth,d=this.$stage.children();if(c&&a.items.merge)for(;b--;)a.css.width=this._widths[this.relative(b)],d.eq(b).css(a.css);else c&&(a.css.width=a.items.width,d.css(a.css))}},{filter:["items"],run:function(){this._coordinates.length<1&&this.$stage.removeAttr("style")}},{filter:["width","items","settings"],run:function(a){a.current=a.current?this.$stage.children().index(a.current):0,a.current=Math.max(this.minimum(),Math.min(this.maximum(),a.current)),this.reset(a.current)}},{filter:["position"],run:function(){this.animate(this.coordinates(this._current))}},{filter:["width","position","items","settings"],run:function(){var a,b,c,d,e=this.settings.rtl?1:-1,f=2*this.settings.stagePadding,g=this.coordinates(this.current())+f,h=g+this.width()*e,i=[];for(c=0,d=this._coordinates.length;c<d;c++)a=this._coordinates[c-1]||0,b=Math.abs(this._coordinates[c])+f*e,(this.op(a,"<=",g)&&this.op(a,">",h)||this.op(b,"<",g)&&this.op(b,">",h))&&i.push(c);this.$stage.children(".active").removeClass("active"),this.$stage.children(":eq("+i.join("), :eq(")+")").addClass("active"),this.$stage.children(".center").removeClass("center"),this.settings.center&&this.$stage.children().eq(this.current()).addClass("center")}}],e.prototype.initializeStage=function(){this.$stage=this.$element.find("."+this.settings.stageClass),this.$stage.length||(this.$element.addClass(this.options.loadingClass),this.$stage=a("<"+this.settings.stageElement+">",{class:this.settings.stageClass}).wrap(a("<div/>",{class:this.settings.stageOuterClass})),this.$element.append(this.$stage.parent()))},e.prototype.initializeItems=function(){var b=this.$element.find(".owl-item");if(b.length)return this._items=b.get().map(function(b){return a(b)}),this._mergers=this._items.map(function(){return 1}),void this.refresh();this.replace(this.$element.children().not(this.$stage.parent())),this.isVisible()?this.refresh():this.invalidate("width"),this.$element.removeClass(this.options.loadingClass).addClass(this.options.loadedClass)},e.prototype.initialize=function(){if(this.enter("initializing"),this.trigger("initialize"),this.$element.toggleClass(this.settings.rtlClass,this.settings.rtl),this.settings.autoWidth&&!this.is("pre-loading")){var a,b,c;a=this.$element.find("img"),b=this.settings.nestedItemSelector?"."+this.settings.nestedItemSelector:d,c=this.$element.children(b).width(),a.length&&c<=0&&this.preloadAutoWidthImages(a)}this.initializeStage(),this.initializeItems(),this.registerEventHandlers(),this.leave("initializing"),this.trigger("initialized")},e.prototype.isVisible=function(){return!this.settings.checkVisibility||this.$element.is(":visible")},e.prototype.setup=function(){var b=this.viewport(),c=this.options.responsive,d=-1,e=null;c?(a.each(c,function(a){a<=b&&a>d&&(d=Number(a))}),e=a.extend({},this.options,c[d]),"function"==typeof e.stagePadding&&(e.stagePadding=e.stagePadding()),delete e.responsive,e.responsiveClass&&this.$element.attr("class",this.$element.attr("class").replace(new RegExp("("+this.options.responsiveClass+"-)\\S+\\s","g"),"$1"+d))):e=a.extend({},this.options),this.trigger("change",{property:{name:"settings",value:e}}),this._breakpoint=d,this.settings=e,this.invalidate("settings"),this.trigger("changed",{property:{name:"settings",value:this.settings}})},e.prototype.optionsLogic=function(){this.settings.autoWidth&&(this.settings.stagePadding=!1,this.settings.merge=!1)},e.prototype.prepare=function(b){var c=this.trigger("prepare",{content:b});return c.data||(c.data=a("<"+this.settings.itemElement+"/>").addClass(this.options.itemClass).append(b)),this.trigger("prepared",{content:c.data}),c.data},e.prototype.update=function(){for(var b=0,c=this._pipe.length,d=a.proxy(function(a){return this[a]},this._invalidated),e={};b<c;)(this._invalidated.all||a.grep(this._pipe[b].filter,d).length>0)&&this._pipe[b].run(e),b++;this._invalidated={},!this.is("valid")&&this.enter("valid")},e.prototype.width=function(a){switch(a=a||e.Width.Default){case e.Width.Inner:case e.Width.Outer:return this._width;default:return this._width-2*this.settings.stagePadding+this.settings.margin}},e.prototype.refresh=function(){this.enter("refreshing"),this.trigger("refresh"),this.setup(),this.optionsLogic(),this.$element.addClass(this.options.refreshClass),this.update(),this.$element.removeClass(this.options.refreshClass),this.leave("refreshing"),this.trigger("refreshed")},e.prototype.onThrottledResize=function(){b.clearTimeout(this.resizeTimer),this.resizeTimer=b.setTimeout(this._handlers.onResize,this.settings.responsiveRefreshRate)},e.prototype.onResize=function(){return!!this._items.length&&(this._width!==this.$element.width()&&(!!this.isVisible()&&(this.enter("resizing"),this.trigger("resize").isDefaultPrevented()?(this.leave("resizing"),!1):(this.invalidate("width"),this.refresh(),this.leave("resizing"),void this.trigger("resized")))))},e.prototype.registerEventHandlers=function(){a.support.transition&&this.$stage.on(a.support.transition.end+".owl.core",a.proxy(this.onTransitionEnd,this)),!1!==this.settings.responsive&&this.on(b,"resize",this._handlers.onThrottledResize),this.settings.mouseDrag&&(this.$element.addClass(this.options.dragClass),this.$stage.on("mousedown.owl.core",a.proxy(this.onDragStart,this)),this.$stage.on("dragstart.owl.core selectstart.owl.core",function(){return!1})),this.settings.touchDrag&&(this.$stage.on("touchstart.owl.core",a.proxy(this.onDragStart,this)),this.$stage.on("touchcancel.owl.core",a.proxy(this.onDragEnd,this)))},e.prototype.onDragStart=function(b){var d=null;3!==b.which&&(a.support.transform?(d=this.$stage.css("transform").replace(/.*\(|\)| /g,"").split(","),d={x:d[16===d.length?12:4],y:d[16===d.length?13:5]}):(d=this.$stage.position(),d={x:this.settings.rtl?d.left+this.$stage.width()-this.width()+this.settings.margin:d.left,y:d.top}),this.is("animating")&&(a.support.transform?this.animate(d.x):this.$stage.stop(),this.invalidate("position")),this.$element.toggleClass(this.options.grabClass,"mousedown"===b.type),this.speed(0),this._drag.time=(new Date).getTime(),this._drag.target=a(b.target),this._drag.stage.start=d,this._drag.stage.current=d,this._drag.pointer=this.pointer(b),a(c).on("mouseup.owl.core touchend.owl.core",a.proxy(this.onDragEnd,this)),a(c).one("mousemove.owl.core touchmove.owl.core",a.proxy(function(b){var d=this.difference(this._drag.pointer,this.pointer(b));a(c).on("mousemove.owl.core touchmove.owl.core",a.proxy(this.onDragMove,this)),Math.abs(d.x)<Math.abs(d.y)&&this.is("valid")||(b.preventDefault(),this.enter("dragging"),this.trigger("drag"))},this)))},e.prototype.onDragMove=function(a){var b=null,c=null,d=null,e=this.difference(this._drag.pointer,this.pointer(a)),f=this.difference(this._drag.stage.start,e);this.is("dragging")&&(a.preventDefault(),this.settings.loop?(b=this.coordinates(this.minimum()),c=this.coordinates(this.maximum()+1)-b,f.x=((f.x-b)%c+c)%c+b):(b=this.settings.rtl?this.coordinates(this.maximum()):this.coordinates(this.minimum()),c=this.settings.rtl?this.coordinates(this.minimum()):this.coordinates(this.maximum()),d=this.settings.pullDrag?-1*e.x/5:0,f.x=Math.max(Math.min(f.x,b+d),c+d)),this._drag.stage.current=f,this.animate(f.x))},e.prototype.onDragEnd=function(b){var d=this.difference(this._drag.pointer,this.pointer(b)),e=this._drag.stage.current,f=d.x>0^this.settings.rtl?"left":"right";a(c).off(".owl.core"),this.$element.removeClass(this.options.grabClass),(0!==d.x&&this.is("dragging")||!this.is("valid"))&&(this.speed(this.settings.dragEndSpeed||this.settings.smartSpeed),this.current(this.closest(e.x,0!==d.x?f:this._drag.direction)),this.invalidate("position"),this.update(),this._drag.direction=f,(Math.abs(d.x)>3||(new Date).getTime()-this._drag.time>300)&&this._drag.target.one("click.owl.core",function(){return!1})),this.is("dragging")&&(this.leave("dragging"),this.trigger("dragged"))},e.prototype.closest=function(b,c){var e=-1,f=30,g=this.width(),h=this.coordinates();return this.settings.freeDrag||a.each(h,a.proxy(function(a,i){return"left"===c&&b>i-f&&b<i+f?e=a:"right"===c&&b>i-g-f&&b<i-g+f?e=a+1:this.op(b,"<",i)&&this.op(b,">",h[a+1]!==d?h[a+1]:i-g)&&(e="left"===c?a+1:a),-1===e},this)),this.settings.loop||(this.op(b,">",h[this.minimum()])?e=b=this.minimum():this.op(b,"<",h[this.maximum()])&&(e=b=this.maximum())),e},e.prototype.animate=function(b){var c=this.speed()>0;this.is("animating")&&this.onTransitionEnd(),c&&(this.enter("animating"),this.trigger("translate")),a.support.transform3d&&a.support.transition?this.$stage.css({transform:"translate3d("+b+"px,0px,0px)",transition:this.speed()/1e3+"s"+(this.settings.slideTransition?" "+this.settings.slideTransition:"")}):c?this.$stage.animate({left:b+"px"},this.speed(),this.settings.fallbackEasing,a.proxy(this.onTransitionEnd,this)):this.$stage.css({left:b+"px"})},e.prototype.is=function(a){return this._states.current[a]&&this._states.current[a]>0},e.prototype.current=function(a){if(a===d)return this._current;if(0===this._items.length)return d;if(a=this.normalize(a),this._current!==a){var b=this.trigger("change",{property:{name:"position",value:a}});b.data!==d&&(a=this.normalize(b.data)),this._current=a,this.invalidate("position"),this.trigger("changed",{property:{name:"position",value:this._current}})}return this._current},e.prototype.invalidate=function(b){return"string"===a.type(b)&&(this._invalidated[b]=!0,this.is("valid")&&this.leave("valid")),a.map(this._invalidated,function(a,b){return b})},e.prototype.reset=function(a){(a=this.normalize(a))!==d&&(this._speed=0,this._current=a,this.suppress(["translate","translated"]),this.animate(this.coordinates(a)),this.release(["translate","translated"]))},e.prototype.normalize=function(a,b){var c=this._items.length,e=b?0:this._clones.length;return!this.isNumeric(a)||c<1?a=d:(a<0||a>=c+e)&&(a=((a-e/2)%c+c)%c+e/2),a},e.prototype.relative=function(a){return a-=this._clones.length/2,this.normalize(a,!0)},e.prototype.maximum=function(a){var b,c,d,e=this.settings,f=this._coordinates.length;if(e.loop)f=this._clones.length/2+this._items.length-1;else if(e.autoWidth||e.merge){if(b=this._items.length)for(c=this._items[--b].width(),d=this.$element.width();b--&&!((c+=this._items[b].width()+this.settings.margin)>d););f=b+1}else f=e.center?this._items.length-1:this._items.length-e.items;return a&&(f-=this._clones.length/2),Math.max(f,0)},e.prototype.minimum=function(a){return a?0:this._clones.length/2},e.prototype.items=function(a){return a===d?this._items.slice():(a=this.normalize(a,!0),this._items[a])},e.prototype.mergers=function(a){return a===d?this._mergers.slice():(a=this.normalize(a,!0),this._mergers[a])},e.prototype.clones=function(b){var c=this._clones.length/2,e=c+this._items.length,f=function(a){return a%2==0?e+a/2:c-(a+1)/2};return b===d?a.map(this._clones,function(a,b){return f(b)}):a.map(this._clones,function(a,c){return a===b?f(c):null})},e.prototype.speed=function(a){return a!==d&&(this._speed=a),this._speed},e.prototype.coordinates=function(b){var c,e=1,f=b-1;return b===d?a.map(this._coordinates,a.proxy(function(a,b){return this.coordinates(b)},this)):(this.settings.center?(this.settings.rtl&&(e=-1,f=b+1),c=this._coordinates[b],c+=(this.width()-c+(this._coordinates[f]||0))/2*e):c=this._coordinates[f]||0,c=Math.ceil(c))},e.prototype.duration=function(a,b,c){return 0===c?0:Math.min(Math.max(Math.abs(b-a),1),6)*Math.abs(c||this.settings.smartSpeed)},e.prototype.to=function(a,b){var c=this.current(),d=null,e=a-this.relative(c),f=(e>0)-(e<0),g=this._items.length,h=this.minimum(),i=this.maximum();this.settings.loop?(!this.settings.rewind&&Math.abs(e)>g/2&&(e+=-1*f*g),a=c+e,(d=((a-h)%g+g)%g+h)!==a&&d-e<=i&&d-e>0&&(c=d-e,a=d,this.reset(c))):this.settings.rewind?(i+=1,a=(a%i+i)%i):a=Math.max(h,Math.min(i,a)),this.speed(this.duration(c,a,b)),this.current(a),this.isVisible()&&this.update()},e.prototype.next=function(a){a=a||!1,this.to(this.relative(this.current())+1,a)},e.prototype.prev=function(a){a=a||!1,this.to(this.relative(this.current())-1,a)},e.prototype.onTransitionEnd=function(a){if(a!==d&&(a.stopPropagation(),(a.target||a.srcElement||a.originalTarget)!==this.$stage.get(0)))return!1;this.leave("animating"),this.trigger("translated")},e.prototype.viewport=function(){var d;return this.options.responsiveBaseElement!==b?d=a(this.options.responsiveBaseElement).width():b.innerWidth?d=b.innerWidth:c.documentElement&&c.documentElement.clientWidth?d=c.documentElement.clientWidth:console.warn("Can not detect viewport width."),d},e.prototype.replace=function(b){this.$stage.empty(),this._items=[],b&&(b=b instanceof jQuery?b:a(b)),this.settings.nestedItemSelector&&(b=b.find("."+this.settings.nestedItemSelector)),b.filter(function(){return 1===this.nodeType}).each(a.proxy(function(a,b){b=this.prepare(b),this.$stage.append(b),this._items.push(b),this._mergers.push(1*b.find("[data-merge]").addBack("[data-merge]").attr("data-merge")||1)},this)),this.reset(this.isNumeric(this.settings.startPosition)?this.settings.startPosition:0),this.invalidate("items")},e.prototype.add=function(b,c){var e=this.relative(this._current);c=c===d?this._items.length:this.normalize(c,!0),b=b instanceof jQuery?b:a(b),this.trigger("add",{content:b,position:c}),b=this.prepare(b),0===this._items.length||c===this._items.length?(0===this._items.length&&this.$stage.append(b),0!==this._items.length&&this._items[c-1].after(b),this._items.push(b),this._mergers.push(1*b.find("[data-merge]").addBack("[data-merge]").attr("data-merge")||1)):(this._items[c].before(b),this._items.splice(c,0,b),this._mergers.splice(c,0,1*b.find("[data-merge]").addBack("[data-merge]").attr("data-merge")||1)),this._items[e]&&this.reset(this._items[e].index()),this.invalidate("items"),this.trigger("added",{content:b,position:c})},e.prototype.remove=function(a){(a=this.normalize(a,!0))!==d&&(this.trigger("remove",{content:this._items[a],position:a}),this._items[a].remove(),this._items.splice(a,1),this._mergers.splice(a,1),this.invalidate("items"),this.trigger("removed",{content:null,position:a}))},e.prototype.preloadAutoWidthImages=function(b){b.each(a.proxy(function(b,c){this.enter("pre-loading"),c=a(c),a(new Image).one("load",a.proxy(function(a){c.attr("src",a.target.src),c.css("opacity",1),this.leave("pre-loading"),!this.is("pre-loading")&&!this.is("initializing")&&this.refresh()},this)).attr("src",c.attr("src")||c.attr("data-src")||c.attr("data-src-retina"))},this))},e.prototype.destroy=function(){this.$element.off(".owl.core"),this.$stage.off(".owl.core"),a(c).off(".owl.core"),!1!==this.settings.responsive&&(b.clearTimeout(this.resizeTimer),this.off(b,"resize",this._handlers.onThrottledResize));for(var d in this._plugins)this._plugins[d].destroy();this.$stage.children(".cloned").remove(),this.$stage.unwrap(),this.$stage.children().contents().unwrap(),this.$stage.children().unwrap(),this.$stage.remove(),this.$element.removeClass(this.options.refreshClass).removeClass(this.options.loadingClass).removeClass(this.options.loadedClass).removeClass(this.options.rtlClass).removeClass(this.options.dragClass).removeClass(this.options.grabClass).attr("class",this.$element.attr("class").replace(new RegExp(this.options.responsiveClass+"-\\S+\\s","g"),"")).removeData("owl.carousel")},e.prototype.op=function(a,b,c){var d=this.settings.rtl;switch(b){case"<":return d?a>c:a<c;case">":return d?a<c:a>c;case">=":return d?a<=c:a>=c;case"<=":return d?a>=c:a<=c}},e.prototype.on=function(a,b,c,d){a.addEventListener?a.addEventListener(b,c,d):a.attachEvent&&a.attachEvent("on"+b,c)},e.prototype.off=function(a,b,c,d){a.removeEventListener?a.removeEventListener(b,c,d):a.detachEvent&&a.detachEvent("on"+b,c)},e.prototype.trigger=function(b,c,d,f,g){var h={item:{count:this._items.length,index:this.current()}},i=a.camelCase(a.grep(["on",b,d],function(a){return a}).join("-").toLowerCase()),j=a.Event([b,"owl",d||"carousel"].join(".").toLowerCase(),a.extend({relatedTarget:this},h,c));return this._supress[b]||(a.each(this._plugins,function(a,b){b.onTrigger&&b.onTrigger(j)}),this.register({type:e.Type.Event,name:b}),this.$element.trigger(j),this.settings&&"function"==typeof this.settings[i]&&this.settings[i].call(this,j)),j},e.prototype.enter=function(b){a.each([b].concat(this._states.tags[b]||[]),a.proxy(function(a,b){this._states.current[b]===d&&(this._states.current[b]=0),this._states.current[b]++},this))},e.prototype.leave=function(b){a.each([b].concat(this._states.tags[b]||[]),a.proxy(function(a,b){this._states.current[b]--},this))},e.prototype.register=function(b){if(b.type===e.Type.Event){if(a.event.special[b.name]||(a.event.special[b.name]={}),!a.event.special[b.name].owl){var c=a.event.special[b.name]._default;a.event.special[b.name]._default=function(a){return!c||!c.apply||a.namespace&&-1!==a.namespace.indexOf("owl")?a.namespace&&a.namespace.indexOf("owl")>-1:c.apply(this,arguments)},a.event.special[b.name].owl=!0}}else b.type===e.Type.State&&(this._states.tags[b.name]?this._states.tags[b.name]=this._states.tags[b.name].concat(b.tags):this._states.tags[b.name]=b.tags,this._states.tags[b.name]=a.grep(this._states.tags[b.name],a.proxy(function(c,d){return a.inArray(c,this._states.tags[b.name])===d},this)))},e.prototype.suppress=function(b){a.each(b,a.proxy(function(a,b){this._supress[b]=!0},this))},e.prototype.release=function(b){a.each(b,a.proxy(function(a,b){delete this._supress[b]},this))},e.prototype.pointer=function(a){var c={x:null,y:null};return a=a.originalEvent||a||b.event,a=a.touches&&a.touches.length?a.touches[0]:a.changedTouches&&a.changedTouches.length?a.changedTouches[0]:a,a.pageX?(c.x=a.pageX,c.y=a.pageY):(c.x=a.clientX,c.y=a.clientY),c},e.prototype.isNumeric=function(a){return!isNaN(parseFloat(a))},e.prototype.difference=function(a,b){return{x:a.x-b.x,y:a.y-b.y}},a.fn.owlCarousel=function(b){var c=Array.prototype.slice.call(arguments,1);return this.each(function(){var d=a(this),f=d.data("owl.carousel");f||(f=new e(this,"object"==typeof b&&b),d.data("owl.carousel",f),a.each(["next","prev","to","destroy","refresh","replace","add","remove"],function(b,c){f.register({type:e.Type.Event,name:c}),f.$element.on(c+".owl.carousel.core",a.proxy(function(a){a.namespace&&a.relatedTarget!==this&&(this.suppress([c]),f[c].apply(this,[].slice.call(arguments,1)),this.release([c]))},f))})),"string"==typeof b&&"_"!==b.charAt(0)&&f[b].apply(f,c)})},a.fn.owlCarousel.Constructor=e}(window.Zepto||window.jQuery,window,document),function(a,b,c,d){var e=function(b){this._core=b,this._interval=null,this._visible=null,this._handlers={"initialized.owl.carousel":a.proxy(function(a){a.namespace&&this._core.settings.autoRefresh&&this.watch()},this)},this._core.options=a.extend({},e.Defaults,this._core.options),this._core.$element.on(this._handlers)};e.Defaults={autoRefresh:!0,autoRefreshInterval:500},e.prototype.watch=function(){this._interval||(this._visible=this._core.isVisible(),this._interval=b.setInterval(a.proxy(this.refresh,this),this._core.settings.autoRefreshInterval))},e.prototype.refresh=function(){this._core.isVisible()!==this._visible&&(this._visible=!this._visible,this._core.$element.toggleClass("owl-hidden",!this._visible),this._visible&&this._core.invalidate("width")&&this._core.refresh())},e.prototype.destroy=function(){var a,c;b.clearInterval(this._interval);for(a in this._handlers)this._core.$element.off(a,this._handlers[a]);for(c in Object.getOwnPropertyNames(this))"function"!=typeof this[c]&&(this[c]=null)},a.fn.owlCarousel.Constructor.Plugins.AutoRefresh=e}(window.Zepto||window.jQuery,window,document),function(a,b,c,d){var e=function(b){this._core=b,this._loaded=[],this._handlers={"initialized.owl.carousel change.owl.carousel resized.owl.carousel":a.proxy(function(b){if(b.namespace&&this._core.settings&&this._core.settings.lazyLoad&&(b.property&&"position"==b.property.name||"initialized"==b.type)){var c=this._core.settings,e=c.center&&Math.ceil(c.items/2)||c.items,f=c.center&&-1*e||0,g=(b.property&&b.property.value!==d?b.property.value:this._core.current())+f,h=this._core.clones().length,i=a.proxy(function(a,b){this.load(b)},this);for(c.lazyLoadEager>0&&(e+=c.lazyLoadEager,c.loop&&(g-=c.lazyLoadEager,e++));f++<e;)this.load(h/2+this._core.relative(g)),h&&a.each(this._core.clones(this._core.relative(g)),i),g++}},this)},this._core.options=a.extend({},e.Defaults,this._core.options),this._core.$element.on(this._handlers)};e.Defaults={lazyLoad:!1,lazyLoadEager:0},e.prototype.load=function(c){var d=this._core.$stage.children().eq(c),e=d&&d.find(".owl-lazy");!e||a.inArray(d.get(0),this._loaded)>-1||(e.each(a.proxy(function(c,d){var e,f=a(d),g=b.devicePixelRatio>1&&f.attr("data-src-retina")||f.attr("data-src")||f.attr("data-srcset");this._core.trigger("load",{element:f,url:g},"lazy"),f.is("img")?f.one("load.owl.lazy",a.proxy(function(){f.css("opacity",1),this._core.trigger("loaded",{element:f,url:g},"lazy")},this)).attr("src",g):f.is("source")?f.one("load.owl.lazy",a.proxy(function(){this._core.trigger("loaded",{element:f,url:g},"lazy")},this)).attr("srcset",g):(e=new Image,e.onload=a.proxy(function(){f.css({"background-image":'url("'+g+'")',opacity:"1"}),this._core.trigger("loaded",{element:f,url:g},"lazy")},this),e.src=g)},this)),this._loaded.push(d.get(0)))},e.prototype.destroy=function(){var a,b;for(a in this.handlers)this._core.$element.off(a,this.handlers[a]);for(b in Object.getOwnPropertyNames(this))"function"!=typeof this[b]&&(this[b]=null)},a.fn.owlCarousel.Constructor.Plugins.Lazy=e}(window.Zepto||window.jQuery,window,document),function(a,b,c,d){var e=function(c){this._core=c,this._previousHeight=null,this._handlers={"initialized.owl.carousel refreshed.owl.carousel":a.proxy(function(a){a.namespace&&this._core.settings.autoHeight&&this.update()},this),"changed.owl.carousel":a.proxy(function(a){a.namespace&&this._core.settings.autoHeight&&"position"===a.property.name&&this.update()},this),"loaded.owl.lazy":a.proxy(function(a){a.namespace&&this._core.settings.autoHeight&&a.element.closest("."+this._core.settings.itemClass).index()===this._core.current()&&this.update()},this)},this._core.options=a.extend({},e.Defaults,this._core.options),this._core.$element.on(this._handlers),this._intervalId=null;var d=this;a(b).on("load",function(){d._core.settings.autoHeight&&d.update()}),a(b).resize(function(){d._core.settings.autoHeight&&(null!=d._intervalId&&clearTimeout(d._intervalId),d._intervalId=setTimeout(function(){d.update()},250))})};e.Defaults={autoHeight:!1,autoHeightClass:"owl-height"},e.prototype.update=function(){var b=this._core._current,c=b+this._core.settings.items,d=this._core.settings.lazyLoad,e=this._core.$stage.children().toArray().slice(b,c),f=[],g=0;a.each(e,function(b,c){f.push(a(c).height())}),g=Math.max.apply(null,f),g<=1&&d&&this._previousHeight&&(g=this._previousHeight),this._previousHeight=g,this._core.$stage.parent().height(g).addClass(this._core.settings.autoHeightClass)},e.prototype.destroy=function(){var a,b;for(a in this._handlers)this._core.$element.off(a,this._handlers[a]);for(b in Object.getOwnPropertyNames(this))"function"!=typeof this[b]&&(this[b]=null)},a.fn.owlCarousel.Constructor.Plugins.AutoHeight=e}(window.Zepto||window.jQuery,window,document),function(a,b,c,d){var e=function(b){this._core=b,this._videos={},this._playing=null,this._handlers={"initialized.owl.carousel":a.proxy(function(a){a.namespace&&this._core.register({type:"state",name:"playing",tags:["interacting"]})},this),"resize.owl.carousel":a.proxy(function(a){a.namespace&&this._core.settings.video&&this.isInFullScreen()&&a.preventDefault()},this),"refreshed.owl.carousel":a.proxy(function(a){a.namespace&&this._core.is("resizing")&&this._core.$stage.find(".cloned .owl-video-frame").remove()},this),"changed.owl.carousel":a.proxy(function(a){a.namespace&&"position"===a.property.name&&this._playing&&this.stop()},this),"prepared.owl.carousel":a.proxy(function(b){if(b.namespace){var c=a(b.content).find(".owl-video");c.length&&(c.css("display","none"),this.fetch(c,a(b.content)))}},this)},this._core.options=a.extend({},e.Defaults,this._core.options),this._core.$element.on(this._handlers),this._core.$element.on("click.owl.video",".owl-video-play-icon",a.proxy(function(a){this.play(a)},this))};e.Defaults={video:!1,videoHeight:!1,videoWidth:!1},e.prototype.fetch=function(a,b){var c=function(){return a.attr("data-vimeo-id")?"vimeo":a.attr("data-vzaar-id")?"vzaar":"youtube"}(),d=a.attr("data-vimeo-id")||a.attr("data-youtube-id")||a.attr("data-vzaar-id"),e=a.attr("data-width")||this._core.settings.videoWidth,f=a.attr("data-height")||this._core.settings.videoHeight,g=a.attr("href");if(!g)throw new Error("Missing video URL.");if(d=g.match(/(http:|https:|)\/\/(player.|www.|app.)?(vimeo\.com|youtu(be\.com|\.be|be\.googleapis\.com|be\-nocookie\.com)|vzaar\.com)\/(video\/|videos\/|embed\/|channels\/.+\/|groups\/.+\/|watch\?v=|v\/)?([A-Za-z0-9._%-]*)(\&\S+)?/),d[3].indexOf("youtu")>-1)c="youtube";else if(d[3].indexOf("vimeo")>-1)c="vimeo";else{if(!(d[3].indexOf("vzaar")>-1))throw new Error("Video URL not supported.");c="vzaar"}d=d[6],this._videos[g]={type:c,id:d,width:e,height:f},b.attr("data-video",g),this.thumbnail(a,this._videos[g])},e.prototype.thumbnail=function(b,c){var d,e,f,g=c.width&&c.height?"width:"+c.width+"px;height:"+c.height+"px;":"",h=b.find("img"),i="src",j="",k=this._core.settings,l=function(c){e='<div class="owl-video-play-icon"></div>',d=k.lazyLoad?a("<div/>",{class:"owl-video-tn "+j,srcType:c}):a("<div/>",{class:"owl-video-tn",style:"opacity:1;background-image:url("+c+")"}),b.after(d),b.after(e)};if(b.wrap(a("<div/>",{class:"owl-video-wrapper",style:g})),this._core.settings.lazyLoad&&(i="data-src",j="owl-lazy"),h.length)return l(h.attr(i)),h.remove(),!1;"youtube"===c.type?(f="//img.youtube.com/vi/"+c.id+"/hqdefault.jpg",l(f)):"vimeo"===c.type?a.ajax({type:"GET",url:"//vimeo.com/api/v2/video/"+c.id+".json",jsonp:"callback",dataType:"jsonp",success:function(a){f=a[0].thumbnail_large,l(f)}}):"vzaar"===c.type&&a.ajax({type:"GET",url:"//vzaar.com/api/videos/"+c.id+".json",jsonp:"callback",dataType:"jsonp",success:function(a){f=a.framegrab_url,l(f)}})},e.prototype.stop=function(){this._core.trigger("stop",null,"video"),this._playing.find(".owl-video-frame").remove(),this._playing.removeClass("owl-video-playing"),this._playing=null,this._core.leave("playing"),this._core.trigger("stopped",null,"video")},e.prototype.play=function(b){var c,d=a(b.target),e=d.closest("."+this._core.settings.itemClass),f=this._videos[e.attr("data-video")],g=f.width||"100%",h=f.height||this._core.$stage.height();this._playing||(this._core.enter("playing"),this._core.trigger("play",null,"video"),e=this._core.items(this._core.relative(e.index())),this._core.reset(e.index()),c=a('<iframe frameborder="0" allowfullscreen mozallowfullscreen webkitAllowFullScreen ></iframe>'),c.attr("height",h),c.attr("width",g),"youtube"===f.type?c.attr("src","//www.youtube.com/embed/"+f.id+"?autoplay=1&rel=0&v="+f.id):"vimeo"===f.type?c.attr("src","//player.vimeo.com/video/"+f.id+"?autoplay=1"):"vzaar"===f.type&&c.attr("src","//view.vzaar.com/"+f.id+"/player?autoplay=true"),a(c).wrap('<div class="owl-video-frame" />').insertAfter(e.find(".owl-video")),this._playing=e.addClass("owl-video-playing"))},e.prototype.isInFullScreen=function(){var b=c.fullscreenElement||c.mozFullScreenElement||c.webkitFullscreenElement;return b&&a(b).parent().hasClass("owl-video-frame")},e.prototype.destroy=function(){var a,b;this._core.$element.off("click.owl.video");for(a in this._handlers)this._core.$element.off(a,this._handlers[a]);for(b in Object.getOwnPropertyNames(this))"function"!=typeof this[b]&&(this[b]=null)},a.fn.owlCarousel.Constructor.Plugins.Video=e}(window.Zepto||window.jQuery,window,document),function(a,b,c,d){var e=function(b){this.core=b,this.core.options=a.extend({},e.Defaults,this.core.options),this.swapping=!0,this.previous=d,this.next=d,this.handlers={"change.owl.carousel":a.proxy(function(a){a.namespace&&"position"==a.property.name&&(this.previous=this.core.current(),this.next=a.property.value)},this),"drag.owl.carousel dragged.owl.carousel translated.owl.carousel":a.proxy(function(a){a.namespace&&(this.swapping="translated"==a.type)},this),"translate.owl.carousel":a.proxy(function(a){a.namespace&&this.swapping&&(this.core.options.animateOut||this.core.options.animateIn)&&this.swap()},this)},this.core.$element.on(this.handlers)};e.Defaults={animateOut:!1,
animateIn:!1},e.prototype.swap=function(){if(1===this.core.settings.items&&a.support.animation&&a.support.transition){this.core.speed(0);var b,c=a.proxy(this.clear,this),d=this.core.$stage.children().eq(this.previous),e=this.core.$stage.children().eq(this.next),f=this.core.settings.animateIn,g=this.core.settings.animateOut;this.core.current()!==this.previous&&(g&&(b=this.core.coordinates(this.previous)-this.core.coordinates(this.next),d.one(a.support.animation.end,c).css({left:b+"px"}).addClass("animated owl-animated-out").addClass(g)),f&&e.one(a.support.animation.end,c).addClass("animated owl-animated-in").addClass(f))}},e.prototype.clear=function(b){a(b.target).css({left:""}).removeClass("animated owl-animated-out owl-animated-in").removeClass(this.core.settings.animateIn).removeClass(this.core.settings.animateOut),this.core.onTransitionEnd()},e.prototype.destroy=function(){var a,b;for(a in this.handlers)this.core.$element.off(a,this.handlers[a]);for(b in Object.getOwnPropertyNames(this))"function"!=typeof this[b]&&(this[b]=null)},a.fn.owlCarousel.Constructor.Plugins.Animate=e}(window.Zepto||window.jQuery,window,document),function(a,b,c,d){var e=function(b){this._core=b,this._call=null,this._time=0,this._timeout=0,this._paused=!0,this._handlers={"changed.owl.carousel":a.proxy(function(a){a.namespace&&"settings"===a.property.name?this._core.settings.autoplay?this.play():this.stop():a.namespace&&"position"===a.property.name&&this._paused&&(this._time=0)},this),"initialized.owl.carousel":a.proxy(function(a){a.namespace&&this._core.settings.autoplay&&this.play()},this),"play.owl.autoplay":a.proxy(function(a,b,c){a.namespace&&this.play(b,c)},this),"stop.owl.autoplay":a.proxy(function(a){a.namespace&&this.stop()},this),"mouseover.owl.autoplay":a.proxy(function(){this._core.settings.autoplayHoverPause&&this._core.is("rotating")&&this.pause()},this),"mouseleave.owl.autoplay":a.proxy(function(){this._core.settings.autoplayHoverPause&&this._core.is("rotating")&&this.play()},this),"touchstart.owl.core":a.proxy(function(){this._core.settings.autoplayHoverPause&&this._core.is("rotating")&&this.pause()},this),"touchend.owl.core":a.proxy(function(){this._core.settings.autoplayHoverPause&&this.play()},this)},this._core.$element.on(this._handlers),this._core.options=a.extend({},e.Defaults,this._core.options)};e.Defaults={autoplay:!1,autoplayTimeout:5e3,autoplayHoverPause:!1,autoplaySpeed:!1},e.prototype._next=function(d){this._call=b.setTimeout(a.proxy(this._next,this,d),this._timeout*(Math.round(this.read()/this._timeout)+1)-this.read()),this._core.is("interacting")||c.hidden||this._core.next(d||this._core.settings.autoplaySpeed)},e.prototype.read=function(){return(new Date).getTime()-this._time},e.prototype.play=function(c,d){var e;this._core.is("rotating")||this._core.enter("rotating"),c=c||this._core.settings.autoplayTimeout,e=Math.min(this._time%(this._timeout||c),c),this._paused?(this._time=this.read(),this._paused=!1):b.clearTimeout(this._call),this._time+=this.read()%c-e,this._timeout=c,this._call=b.setTimeout(a.proxy(this._next,this,d),c-e)},e.prototype.stop=function(){this._core.is("rotating")&&(this._time=0,this._paused=!0,b.clearTimeout(this._call),this._core.leave("rotating"))},e.prototype.pause=function(){this._core.is("rotating")&&!this._paused&&(this._time=this.read(),this._paused=!0,b.clearTimeout(this._call))},e.prototype.destroy=function(){var a,b;this.stop();for(a in this._handlers)this._core.$element.off(a,this._handlers[a]);for(b in Object.getOwnPropertyNames(this))"function"!=typeof this[b]&&(this[b]=null)},a.fn.owlCarousel.Constructor.Plugins.autoplay=e}(window.Zepto||window.jQuery,window,document),function(a,b,c,d){"use strict";var e=function(b){this._core=b,this._initialized=!1,this._pages=[],this._controls={},this._templates=[],this.$element=this._core.$element,this._overrides={next:this._core.next,prev:this._core.prev,to:this._core.to},this._handlers={"prepared.owl.carousel":a.proxy(function(b){b.namespace&&this._core.settings.dotsData&&this._templates.push('<div class="'+this._core.settings.dotClass+'">'+a(b.content).find("[data-dot]").addBack("[data-dot]").attr("data-dot")+"</div>")},this),"added.owl.carousel":a.proxy(function(a){a.namespace&&this._core.settings.dotsData&&this._templates.splice(a.position,0,this._templates.pop())},this),"remove.owl.carousel":a.proxy(function(a){a.namespace&&this._core.settings.dotsData&&this._templates.splice(a.position,1)},this),"changed.owl.carousel":a.proxy(function(a){a.namespace&&"position"==a.property.name&&this.draw()},this),"initialized.owl.carousel":a.proxy(function(a){a.namespace&&!this._initialized&&(this._core.trigger("initialize",null,"navigation"),this.initialize(),this.update(),this.draw(),this._initialized=!0,this._core.trigger("initialized",null,"navigation"))},this),"refreshed.owl.carousel":a.proxy(function(a){a.namespace&&this._initialized&&(this._core.trigger("refresh",null,"navigation"),this.update(),this.draw(),this._core.trigger("refreshed",null,"navigation"))},this)},this._core.options=a.extend({},e.Defaults,this._core.options),this.$element.on(this._handlers)};e.Defaults={nav:!1,navText:['<span aria-label="Previous">&#x2039;</span>','<span aria-label="Next">&#x203a;</span>'],navSpeed:!1,navElement:'button type="button" role="presentation"',navContainer:!1,navContainerClass:"owl-nav",navClass:["owl-prev","owl-next"],slideBy:1,dotClass:"owl-dot",dotsClass:"owl-dots",dots:!0,dotsEach:!1,dotsData:!1,dotsSpeed:!1,dotsContainer:!1},e.prototype.initialize=function(){var b,c=this._core.settings;this._controls.$relative=(c.navContainer?a(c.navContainer):a("<div>").addClass(c.navContainerClass).appendTo(this.$element)).addClass("disabled"),this._controls.$previous=a("<"+c.navElement+">").addClass(c.navClass[0]).html(c.navText[0]).prependTo(this._controls.$relative).on("click",a.proxy(function(a){this.prev(c.navSpeed)},this)),this._controls.$next=a("<"+c.navElement+">").addClass(c.navClass[1]).html(c.navText[1]).appendTo(this._controls.$relative).on("click",a.proxy(function(a){this.next(c.navSpeed)},this)),c.dotsData||(this._templates=[a('<button role="button">').addClass(c.dotClass).append(a("<span>")).prop("outerHTML")]),this._controls.$absolute=(c.dotsContainer?a(c.dotsContainer):a("<div>").addClass(c.dotsClass).appendTo(this.$element)).addClass("disabled"),this._controls.$absolute.on("click","button",a.proxy(function(b){var d=a(b.target).parent().is(this._controls.$absolute)?a(b.target).index():a(b.target).parent().index();b.preventDefault(),this.to(d,c.dotsSpeed)},this));for(b in this._overrides)this._core[b]=a.proxy(this[b],this)},e.prototype.destroy=function(){var a,b,c,d,e;e=this._core.settings;for(a in this._handlers)this.$element.off(a,this._handlers[a]);for(b in this._controls)"$relative"===b&&e.navContainer?this._controls[b].html(""):this._controls[b].remove();for(d in this.overides)this._core[d]=this._overrides[d];for(c in Object.getOwnPropertyNames(this))"function"!=typeof this[c]&&(this[c]=null)},e.prototype.update=function(){var a,b,c,d=this._core.clones().length/2,e=d+this._core.items().length,f=this._core.maximum(!0),g=this._core.settings,h=g.center||g.autoWidth||g.dotsData?1:g.dotsEach||g.items;if("page"!==g.slideBy&&(g.slideBy=Math.min(g.slideBy,g.items)),g.dots||"page"==g.slideBy)for(this._pages=[],a=d,b=0,c=0;a<e;a++){if(b>=h||0===b){if(this._pages.push({start:Math.min(f,a-d),end:a-d+h-1}),Math.min(f,a-d)===f)break;b=0,++c}b+=this._core.mergers(this._core.relative(a))}},e.prototype.draw=function(){var b,c=this._core.settings,d=this._core.items().length<=c.items,e=this._core.relative(this._core.current()),f=c.loop||c.rewind;this._controls.$relative.toggleClass("disabled",!c.nav||d),c.nav&&(this._controls.$previous.toggleClass("disabled",!f&&e<=this._core.minimum(!0)),this._controls.$next.toggleClass("disabled",!f&&e>=this._core.maximum(!0))),this._controls.$absolute.toggleClass("disabled",!c.dots||d),c.dots&&(b=this._pages.length-this._controls.$absolute.children().length,c.dotsData&&0!==b?this._controls.$absolute.html(this._templates.join("")):b>0?this._controls.$absolute.append(new Array(b+1).join(this._templates[0])):b<0&&this._controls.$absolute.children().slice(b).remove(),this._controls.$absolute.find(".active").removeClass("active"),this._controls.$absolute.children().eq(a.inArray(this.current(),this._pages)).addClass("active"))},e.prototype.onTrigger=function(b){var c=this._core.settings;b.page={index:a.inArray(this.current(),this._pages),count:this._pages.length,size:c&&(c.center||c.autoWidth||c.dotsData?1:c.dotsEach||c.items)}},e.prototype.current=function(){var b=this._core.relative(this._core.current());return a.grep(this._pages,a.proxy(function(a,c){return a.start<=b&&a.end>=b},this)).pop()},e.prototype.getPosition=function(b){var c,d,e=this._core.settings;return"page"==e.slideBy?(c=a.inArray(this.current(),this._pages),d=this._pages.length,b?++c:--c,c=this._pages[(c%d+d)%d].start):(c=this._core.relative(this._core.current()),d=this._core.items().length,b?c+=e.slideBy:c-=e.slideBy),c},e.prototype.next=function(b){a.proxy(this._overrides.to,this._core)(this.getPosition(!0),b)},e.prototype.prev=function(b){a.proxy(this._overrides.to,this._core)(this.getPosition(!1),b)},e.prototype.to=function(b,c,d){var e;!d&&this._pages.length?(e=this._pages.length,a.proxy(this._overrides.to,this._core)(this._pages[(b%e+e)%e].start,c)):a.proxy(this._overrides.to,this._core)(b,c)},a.fn.owlCarousel.Constructor.Plugins.Navigation=e}(window.Zepto||window.jQuery,window,document),function(a,b,c,d){"use strict";var e=function(c){this._core=c,this._hashes={},this.$element=this._core.$element,this._handlers={"initialized.owl.carousel":a.proxy(function(c){c.namespace&&"URLHash"===this._core.settings.startPosition&&a(b).trigger("hashchange.owl.navigation")},this),"prepared.owl.carousel":a.proxy(function(b){if(b.namespace){var c=a(b.content).find("[data-hash]").addBack("[data-hash]").attr("data-hash");if(!c)return;this._hashes[c]=b.content}},this),"changed.owl.carousel":a.proxy(function(c){if(c.namespace&&"position"===c.property.name){var d=this._core.items(this._core.relative(this._core.current())),e=a.map(this._hashes,function(a,b){return a===d?b:null}).join();if(!e||b.location.hash.slice(1)===e)return;b.location.hash=e}},this)},this._core.options=a.extend({},e.Defaults,this._core.options),this.$element.on(this._handlers),a(b).on("hashchange.owl.navigation",a.proxy(function(a){var c=b.location.hash.substring(1),e=this._core.$stage.children(),f=this._hashes[c]&&e.index(this._hashes[c]);f!==d&&f!==this._core.current()&&this._core.to(this._core.relative(f),!1,!0)},this))};e.Defaults={URLhashListener:!1},e.prototype.destroy=function(){var c,d;a(b).off("hashchange.owl.navigation");for(c in this._handlers)this._core.$element.off(c,this._handlers[c]);for(d in Object.getOwnPropertyNames(this))"function"!=typeof this[d]&&(this[d]=null)},a.fn.owlCarousel.Constructor.Plugins.Hash=e}(window.Zepto||window.jQuery,window,document),function(a,b,c,d){function e(b,c){var e=!1,f=b.charAt(0).toUpperCase()+b.slice(1);return a.each((b+" "+h.join(f+" ")+f).split(" "),function(a,b){if(g[b]!==d)return e=!c||b,!1}),e}function f(a){return e(a,!0)}var g=a("<support>").get(0).style,h="Webkit Moz O ms".split(" "),i={transition:{end:{WebkitTransition:"webkitTransitionEnd",MozTransition:"transitionend",OTransition:"oTransitionEnd",transition:"transitionend"}},animation:{end:{WebkitAnimation:"webkitAnimationEnd",MozAnimation:"animationend",OAnimation:"oAnimationEnd",animation:"animationend"}}},j={csstransforms:function(){return!!e("transform")},csstransforms3d:function(){return!!e("perspective")},csstransitions:function(){return!!e("transition")},cssanimations:function(){return!!e("animation")}};j.csstransitions()&&(a.support.transition=new String(f("transition")),a.support.transition.end=i.transition.end[a.support.transition]),j.cssanimations()&&(a.support.animation=new String(f("animation")),a.support.animation.end=i.animation.end[a.support.animation]),j.csstransforms()&&(a.support.transform=new String(f("transform")),a.support.transform3d=j.csstransforms3d())}(window.Zepto||window.jQuery,window,document);
```
  - templates/_head_en.html
```js
--- 66행 ---
var g5_bo_table  = "{{ g5_bo_table }}";
var g5_sca       = "";
var g5_editor    = "{{ g5_editor }}";
var g5_cookie_domain = "";
var g5_theme_shop_url = "";
var g5_shop_url = "";
</script>

<script src="%%ROOT%%js/jquery-1.12.4.min.js"></script>
<script src="%%ROOT%%js/jquery-migrate-1.4.1.min.js"></script>
<script src="%%ROOT%%js/common.js"></script>
<script src="%%ROOT%%js/wrest.js"></script>
<script src="%%ROOT%%theme/basic/js/jquery.fullpage.js"></script>
<script src="%%ROOT%%theme/basic/js/plugins.js"></script>
<script src="%%ROOT%%theme/basic/js/vanilla-tilt.js"></script>
<script src="%%ROOT%%theme/basic/js/jquery.placeholder.js"></script>
<script src="%%ROOT%%theme/basic/js/jquery_sly.js"></script>
<script src="%%ROOT%%theme/basic/js/scrolla.jquery.min.js"></script>
<script src="%%ROOT%%theme/basic/js/owl.carousel.min.js"></script>
<script src="%%ROOT%%theme/basic/js/slick.min.js"></script>
<script src="%%ROOT%%theme/basic/js/gsap.min.js"></script>
<script src="%%ROOT%%vendor/gsap-latest-beta.min.js"></script>
<script src="%%ROOT%%theme/basic/js/ScrollTrigger.min.js"></script>


<script src="%%ROOT%%js/jquery.menu.js"></script>
```
  - templates/_head_ko.html
```js
--- 65행 ---
var g5_bo_table  = "{{ g5_bo_table }}";
var g5_sca       = "";
var g5_editor    = "{{ g5_editor }}";
var g5_cookie_domain = "";
var g5_theme_shop_url = "";
var g5_shop_url = "";
</script>

<script src="%%ROOT%%js/jquery-1.12.4.min.js"></script>
<script src="%%ROOT%%js/jquery-migrate-1.4.1.min.js"></script>
<script src="%%ROOT%%js/common.js"></script>
<script src="%%ROOT%%js/wrest.js"></script>
<script src="%%ROOT%%theme/basic/js/jquery.fullpage.js"></script>
<script src="%%ROOT%%theme/basic/js/plugins.js"></script>
<script src="%%ROOT%%theme/basic/js/vanilla-tilt.js"></script>
<script src="%%ROOT%%theme/basic/js/jquery.placeholder.js"></script>
<script src="%%ROOT%%theme/basic/js/jquery_sly.js"></script>
<script src="%%ROOT%%theme/basic/js/scrolla.jquery.min.js"></script>
<script src="%%ROOT%%theme/basic/js/owl.carousel.min.js"></script>
<script src="%%ROOT%%theme/basic/js/slick.min.js"></script>
<script src="%%ROOT%%theme/basic/js/gsap.min.js"></script>
<script src="%%ROOT%%vendor/gsap-latest-beta.min.js"></script>
<script src="%%ROOT%%theme/basic/js/ScrollTrigger.min.js"></script>


<script src="%%ROOT%%js/jquery.menu.js"></script>
```
  - templates/_tail_en.html
```js
--- 93행 ---
<script>
$(function() {
    // 폰트 리사이즈 쿠키있으면 실행
    font_resize("container", get_cookie("ck_font_resize_rmv_class"), get_cookie("ck_font_resize_add_class"));
});
</script>
<script src="%%ROOT%%theme/basic/js/dawon.js"></script>
<script src="%%ROOT%%theme/basic/js/scroll.js"></script>
```
  - templates/_tail_ko.html
```js
--- 93행 ---
<script>
$(function() {
    // 폰트 리사이즈 쿠키있으면 실행
    font_resize("container", get_cookie("ck_font_resize_rmv_class"), get_cookie("ck_font_resize_add_class"));
});
</script>
<script src="%%ROOT%%theme/basic/js/dawon.js"></script>
<script src="%%ROOT%%theme/basic/js/scroll.js"></script>
```
  - templates/_top_en.html
```js
--- 2행 ---
<!-- 상단 시작 { -->
{{ popup_html }}<div class="header_all_wrap">
    <div class="header_wrap">
        <div class="header_mid_wrap">
            <div class="header_mid">
                <div class="logo_wrap">
                    <a href="%%ROOT%%en/index.html" class="logo" alt="Animotiontech" title="Animotiontech">
                        <span class="logo_off"><svg id="_레이어_2" data-name="레이어 2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 127.26 28.44">
<g>
    <path class="st1" d="M100.88,19.98c1.05.61,1.73,1.73,1.73,3.7,0,3.93-2.65,4.76-6.37,4.76h-10.27V12.04h10.27c3.45,0,6.06.81,6.06,4.53,0,1.7-.54,2.76-1.41,3.41M90.25,18.71h6.08c1.19,0,1.82-.45,1.82-1.61,0-1.3-.81-1.68-1.86-1.68h-6.03v3.3ZM90.25,21.44v3.45h6.1c1.1,0,1.93-.36,1.93-1.75s-.72-1.71-1.86-1.71h-6.17Z"/>
    <rect class="st1" x="105" y="12.05" width="4.4" height="16.4"/>
    <polygon class="st1" points="117.06 15.59 111.25 15.59 111.25 12.04 127.26 12.04 127.26 15.59 121.45 15.59 121.45 28.44 117.06 28.44 117.06 15.59"/>
    <polygon class="st1" points="47.54 28.44 42.96 28.44 50.99 12.04 55.75 12.04 63.78 28.44 59.33 28.44 53.41 15.95 47.54 28.44"/>
    <path class="st1" d="M36.83,22.05v-10h4.4v16.4h-4.4v-6.39ZM29.01,28.44h-4.4V12.05h4.4v16.4Z"/>
    <rect class="st1" x="27.66" y="18.71" width="11.23" height="3.06"/>
    <path class="st1" d="M65.81,12.73v15.71h4.08v-12.42c-1.29-1.19-2.65-2.29-4.08-3.29"/>
    <path class="st1" d="M82.91,26.09v-14.04h-4.06l.04,6.81c1.55,2.27,2.9,4.69,4.02,7.23"/>
    <path class="st0" d="M7.61,28.44C13.71,14.56,27.58,4.87,43.72,4.87s30.01,9.69,36.12,23.57h3.07C76.5,11.8,60.36,0,41.46,0S6.42,11.8,0,28.44h7.61Z"/>
  </g>
</svg></span>
                        <span class="logo_on"><svg id="_레이어_2" data-name="레이어 2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 127.26 28.44">
<g>
    <path class="st1" d="M100.88,19.98c1.05.61,1.73,1.73,1.73,3.7,0,3.93-2.65,4.76-6.37,4.76h-10.27V12.04h10.27c3.45,0,6.06.81,6.06,4.53,0,1.7-.54,2.76-1.41,3.41M90.25,18.71h6.08c1.19,0,1.82-.45,1.82-1.61,0-1.3-.81-1.68-1.86-1.68h-6.03v3.3ZM90.25,21.44v3.45h6.1c1.1,0,1.93-.36,1.93-1.75s-.72-1.71-1.86-1.71h-6.17Z"/>
    <rect class="st1" x="105" y="12.05" width="4.4" height="16.4"/>
    <polygon class="st1" points="117.06 15.59 111.25 15.59 111.25 12.04 127.26 12.04 127.26 15.59 121.45 15.59 121.45 28.44 117.06 28.44 117.06 15.59"/>
    <polygon class="st1" points="47.54 28.44 42.96 28.44 50.99 12.04 55.75 12.04 63.78 28.44 59.33 28.44 53.41 15.95 47.54 28.44"/>
    <path class="st1" d="M36.83,22.05v-10h4.4v16.4h-4.4v-6.39ZM29.01,28.44h-4.4V12.05h4.4v16.4Z"/>
    <rect class="st1" x="27.66" y="18.71" width="11.23" height="3.06"/>
    <path class="st1" d="M65.81,12.73v15.71h4.08v-12.42c-1.29-1.19-2.65-2.29-4.08-3.29"/>
    <path class="st1" d="M82.91,26.09v-14.04h-4.06l.04,6.81c1.55,2.27,2.9,4.69,4.02,7.23"/>
    <path class="st0" d="M7.61,28.44C13.71,14.56,27.58,4.87,43.72,4.87s30.01,9.69,36.12,23.57h3.07C76.5,11.8,60.36,0,41.46,0S6.42,11.8,0,28.44h7.61Z"/>
  </g>
</svg></span>
                    </a>
                </div>
                <div class="top_nav_wrap">
                    <div id="nav" class="top_nav">
                        <div class="menu menu_05 ">
    <a href="%%ROOT%%en/page/hanbit.html" class="menu_a void_link ">
		<span>
                   About Us
```
  - templates/_top_ko.html
```js
--- 2행 ---
<!-- 상단 시작 { -->
{{ popup_html }}<div class="header_all_wrap">
    <div class="header_wrap">
        <div class="header_mid_wrap">
            <div class="header_mid">
                <div class="logo_wrap">
                    <a href="%%ROOT%%index.html" class="logo" alt="Animotiontech" title="Animotiontech">
                        <span class="logo_off"><svg id="_레이어_2" data-name="레이어 2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 127.26 28.44">
<g>
    <path class="st1" d="M100.88,19.98c1.05.61,1.73,1.73,1.73,3.7,0,3.93-2.65,4.76-6.37,4.76h-10.27V12.04h10.27c3.45,0,6.06.81,6.06,4.53,0,1.7-.54,2.76-1.41,3.41M90.25,18.71h6.08c1.19,0,1.82-.45,1.82-1.61,0-1.3-.81-1.68-1.86-1.68h-6.03v3.3ZM90.25,21.44v3.45h6.1c1.1,0,1.93-.36,1.93-1.75s-.72-1.71-1.86-1.71h-6.17Z"/>
    <rect class="st1" x="105" y="12.05" width="4.4" height="16.4"/>
    <polygon class="st1" points="117.06 15.59 111.25 15.59 111.25 12.04 127.26 12.04 127.26 15.59 121.45 15.59 121.45 28.44 117.06 28.44 117.06 15.59"/>
    <polygon class="st1" points="47.54 28.44 42.96 28.44 50.99 12.04 55.75 12.04 63.78 28.44 59.33 28.44 53.41 15.95 47.54 28.44"/>
    <path class="st1" d="M36.83,22.05v-10h4.4v16.4h-4.4v-6.39ZM29.01,28.44h-4.4V12.05h4.4v16.4Z"/>
    <rect class="st1" x="27.66" y="18.71" width="11.23" height="3.06"/>
    <path class="st1" d="M65.81,12.73v15.71h4.08v-12.42c-1.29-1.19-2.65-2.29-4.08-3.29"/>
    <path class="st1" d="M82.91,26.09v-14.04h-4.06l.04,6.81c1.55,2.27,2.9,4.69,4.02,7.23"/>
    <path class="st0" d="M7.61,28.44C13.71,14.56,27.58,4.87,43.72,4.87s30.01,9.69,36.12,23.57h3.07C76.5,11.8,60.36,0,41.46,0S6.42,11.8,0,28.44h7.61Z"/>
  </g>
</svg></span>
                        <span class="logo_on"><svg id="_레이어_2" data-name="레이어 2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 127.26 28.44">
<g>
    <path class="st1" d="M100.88,19.98c1.05.61,1.73,1.73,1.73,3.7,0,3.93-2.65,4.76-6.37,4.76h-10.27V12.04h10.27c3.45,0,6.06.81,6.06,4.53,0,1.7-.54,2.76-1.41,3.41M90.25,18.71h6.08c1.19,0,1.82-.45,1.82-1.61,0-1.3-.81-1.68-1.86-1.68h-6.03v3.3ZM90.25,21.44v3.45h6.1c1.1,0,1.93-.36,1.93-1.75s-.72-1.71-1.86-1.71h-6.17Z"/>
    <rect class="st1" x="105" y="12.05" width="4.4" height="16.4"/>
    <polygon class="st1" points="117.06 15.59 111.25 15.59 111.25 12.04 127.26 12.04 127.26 15.59 121.45 15.59 121.45 28.44 117.06 28.44 117.06 15.59"/>
    <polygon class="st1" points="47.54 28.44 42.96 28.44 50.99 12.04 55.75 12.04 63.78 28.44 59.33 28.44 53.41 15.95 47.54 28.44"/>
    <path class="st1" d="M36.83,22.05v-10h4.4v16.4h-4.4v-6.39ZM29.01,28.44h-4.4V12.05h4.4v16.4Z"/>
    <rect class="st1" x="27.66" y="18.71" width="11.23" height="3.06"/>
    <path class="st1" d="M65.81,12.73v15.71h4.08v-12.42c-1.29-1.19-2.65-2.29-4.08-3.29"/>
    <path class="st1" d="M82.91,26.09v-14.04h-4.06l.04,6.81c1.55,2.27,2.9,4.69,4.02,7.23"/>
    <path class="st0" d="M7.61,28.44C13.71,14.56,27.58,4.87,43.72,4.87s30.01,9.69,36.12,23.57h3.07C76.5,11.8,60.36,0,41.46,0S6.42,11.8,0,28.44h7.61Z"/>
  </g>
</svg></span>
                    </a>
                </div>
                <div class="top_nav_wrap">
                    <div id="nav" class="top_nav">
                        <div class="menu menu_05 ">
    <a href="%%ROOT%%page/hanbit.html" class="menu_a void_link ">
		<span>
                    회사소개
```

## 6) CSS·JS 파일
| 파일 | 크기 | base.html 참조 | 첫 주석 |
|---|---|---|---|
| static/hb/board_search.js | 3KB |  |  |
| static/hb/lightbox.css | 1KB |  | 이미지 확대 보기 라이트박스 (lightbox.js) |
| static/hb/lightbox.js | 1KB |  |  |
| static/hb/popup.js | 1KB |  | 저장 불가(사생활 보호 모드 등): 이번 화면에서만 닫힘 |
| static/js/common.js | 20KB |  | 전역 변수 |
| static/js/font-awesome/css/font-awesome.min.css | 29KB |  | fontawesome.io - @fontawesome |
| static/js/html5.js | 2KB |  | github.com/aFarkas/html5shiv  */ |
| static/js/jquery-1.12.4.min.js | 94KB |  | ! jQuery v1.12.4 | (c) jQuery Foundation | jquery.org/license |
| static/js/jquery-migrate-1.4.1.min.js | 9KB |  |  |
| static/js/jquery.menu.js | 2KB |  | 주메뉴 |
| static/js/viewimageresize.js | 2KB |  |  |
| static/js/wrest.js | 10KB |  | var wrestFldBackColor = "#ff3061"; |
| static/theme/basic/css/animate.min.css | 70KB |  | daneden.me/animate |
| static/theme/basic/css/base.css | 3KB |  | base |
| static/theme/basic/css/board.css | 37KB |  |  |
| static/theme/basic/css/default.css | 26KB |  | 초기화 |
| static/theme/basic/css/jquery.fullpage.css | 4KB |  | github.com/alvarotrigo/fullPage.js |
| static/theme/basic/css/layout.css | 109KB |  |  |
| static/theme/basic/css/layout_en.css | 0KB |  |  |
| static/theme/basic/css/owl.carousel.min.css | 3KB |  | github.com/OwlCarousel2/OwlCarousel2/blob/master/LICENSE |
| static/theme/basic/css/owl.theme.default.min.css | 1KB |  | github.com/OwlCarousel2/OwlCarousel2/blob/master/LICENSE |
| static/theme/basic/css/res.css | 21KB |  |  |
| static/theme/basic/css/slick-theme.min.css | 2KB |  |  |
| static/theme/basic/css/slick.min.css | 1KB |  |  |
| static/theme/basic/css/xeicon.css | 43KB |  | xpressengine.github.io/XEIcon/ - @XEIcon |
| static/theme/basic/css/xeicon.min.css | 35KB |  | xpressengine.github.io/XEIcon/ - @XEIcon |
| static/theme/basic/js/dawon.js | 7KB |  | 메뉴 |
| static/theme/basic/js/gsap.min.js | 62KB |  | greensock.com |
| static/theme/basic/js/jquery.fullpage.js | 88KB |  | github.com/alvarotrigo/fullPage.js |
| static/theme/basic/js/jquery.placeholder.js | 8KB |  | github.com/mathiasbynens/jquery-placeholder |
| static/theme/basic/js/jquery_sly.js | 59KB |  | github.com/darsain/sly |
| static/theme/basic/js/main.js | 2KB |  |  |
| static/theme/basic/js/owl.carousel.min.js | 43KB |  | github.com/OwlCarousel2/OwlCarousel2/blob/master/LICENSE |
| static/theme/basic/js/plugins.js | 4KB |  | Avoid `console` errors in browsers that lack a console. |
| static/theme/basic/js/scroll.js | 3KB |  | cross browser support for document scrolling |
| static/theme/basic/js/scrolla.jquery.min.js | 2KB |  | this.click(); |
| static/theme/basic/js/ScrollTrigger.min.js | 23KB |  | greensock.com |
| static/theme/basic/js/slick.min.js | 42KB |  | kenwheeler.github.io |
| static/theme/basic/js/vanilla-tilt.js | 15KB |  | github.com/gijsroge/tilt.js |
| static/theme/basic/skin/board/notice/style.css | 27KB |  | 게시판 목록 |
| static/theme/basic/skin/board/reference/style.css | 27KB |  | 게시판 목록 |
| static/theme/basic/skin/latest/main_news/style.css | 2KB |  | 새글 스킨 (latest) |
| static/vendor/gsap-latest-beta.min.js | 71KB |  | gsap.com |

## 7) 게시판 검색창
- templates/404.html:
```html
--- 45행 ---
  var rest = "/" + path.slice(base.length);
  var params = {};
  location.search.replace(/^\?/, "").split("&").forEach(function (kv) {
    if (!kv) return;
    var p = kv.split("="), k = decodeURIComponent(p[0]), v = decodeURIComponent((p[1] || "").replace(/\+/g, " "));
    if (KEEP.indexOf(k) > -1 && v !== "") params[k] = v;
  });
  if (params.wr_id) delete params.page;   // 글 주소에 붙은 목록 쪽 번호는 무시(원본도 같은 글)
  function key(ps) {
    var ks = Object.keys(ps).sort();
    return rest + (ks.length ? "?" + ks.map(function (k) { return k + "=" + ps[k]; }).join("&") : "");
  }
  fetch(base + "redirects.json").then(function (r) { return r.json(); }).then(function (map) {
    var to = map[key(params)];
    if (!to && params.locale) { var p2 = {}; for (var k in params) if (k !== "locale") p2[k] = params[k]; to = map[key(p2)]; }
    if (!to && params.bo_table) {             // 없는 글 번호 등 → 그 게시판 목록
      to = map[rest + "?bo_table=" + params.bo_table];
```
- templates/board_list.html:
```html
--- 3행 ---
{#- 게시판 목록 (원본 theme/basic/skin/board/notice·reference 목록 화면을 그대로 옮김, 웹진형: 좌측 1건 + 우측 6건)
    - 관리용 목록 폼(board_list_update.php)은 정적 사이트에서 쓸 수 없어 action을 없앰
    - 검색: 원본처럼 검색창은 숨겨져 있고, 열리면 JS 제목 검색(board_search.js)으로 동작. 주소 ?stx=검색어 로도 검색 -#}
{% extends "base.html" %}
{% block content %}

<!-- 게시판 목록 시작 { -->
<div id="bo_list" style="width:100%">

    <!-- 게시판 카테고리 시작 { -->
        <!-- } 게시판 카테고리 끝 -->

    <form name="fboardlist" id="fboardlist" action="#" onsubmit="return false;" method="post">

        <input type="hidden" name="bo_table" value="{{ board.table }}">
        <input type="hidden" name="sfl" value="">
        <input type="hidden" name="stx" value="">
--- 13행 ---
        <!-- } 게시판 카테고리 끝 -->

    <form name="fboardlist" id="fboardlist" action="#" onsubmit="return false;" method="post">

        <input type="hidden" name="bo_table" value="{{ board.table }}">
        <input type="hidden" name="sfl" value="">
        <input type="hidden" name="stx" value="">
        <input type="hidden" name="spt" value="">
        <input type="hidden" name="sca" value="">
        <input type="hidden" name="sst" value="wr_num, wr_reply">
        <input type="hidden" name="sod" value="">
        <input type="hidden" name="page" value="{{ page }}">
        <input type="hidden" name="sw" value="">

        <!-- 게시판 페이지 정보 및 버튼 시작 { -->
        <div id="bo_btn_top">

--- 17행 ---
        <input type="hidden" name="bo_table" value="{{ board.table }}">
        <input type="hidden" name="sfl" value="">
        <input type="hidden" name="stx" value="">
        <input type="hidden" name="spt" value="">
        <input type="hidden" name="sca" value="">
        <input type="hidden" name="sst" value="wr_num, wr_reply">
        <input type="hidden" name="sod" value="">
        <input type="hidden" name="page" value="{{ page }}">
        <input type="hidden" name="sw" value="">

        <!-- 게시판 페이지 정보 및 버튼 시작 { -->
        <div id="bo_btn_top">

            <ul class="btn_bo_user">
                                                                            </ul>
        </div>
        <!-- } 게시판 페이지 정보 및 버튼 끝 -->
```
- 빌드된 notice 목록의 form 부분:
```html
--- 1664행 ---

    <form name="fboardlist" id="fboardlist" action="#" onsubmit="return false;" method="post">

        <input type="hidden" name="bo_table" value="notice">
        <input type="hidden" name="sfl" value="">
        <input type="hidden" name="stx" value="">
        <input type="hidden" name="spt" value="">
        <input type="hidden" name="sca" value="">
        <input type="hidden" name="sst" value="wr_num, wr_reply">
        <input type="hidden" name="sod" value="">
        <input type="hidden" name="page" value="1">
        <input type="hidden" name="sw" value="">

        <!-- 게시판 페이지 정보 및 버튼 시작 { -->
        <div id="bo_btn_top">

--- 1790행 ---
            <h3>검색</h3>
            <form name="fsearch" method="get" data-board-index="search.json">
                <input type="hidden" name="bo_table" value="notice">
                <input type="hidden" name="sca" value="">
                <input type="hidden" name="sop" value="and">
                <label for="sfl" class="sound_only">검색대상</label>
                <select name="sfl" id="sfl">
                    <option value="wr_subject" >제목</option><option value="wr_content" >내용</option><option value="wr_subject||wr_content" >제목+내용</option><option value="wr_name,1" >글쓴이</option><option value="wr_name,0" >글쓴이(코)</option>                </select>
                <label for="stx" class="sound_only">검색어<strong class="sound_only"> 필수</strong></label>
                <div class="sch_bar">
                    <input type="text" name="stx" value="" required id="stx" class="sch_input" size="25" maxlength="20" placeholder="검색어를 입력해주세요">
                    <button type="submit" value="검색" class="sch_btn"><i class="fa fa-search" aria-hidden="true"></i><span class="sound_only">검색</span></button>
                </div>
                <button type="button" class="bo_sch_cls" title="닫기"><i class="fa fa-times" aria-hidden="true"></i><span class="sound_only">닫기</span></button>
            </form>
        </fieldset>
```

- **판단**: 검색창 마크업(.bo_sch_wrap)과 JS 제목 검색(static/hb/board_search.js, search.json)은 있으나, 창을 여는 버튼(.btn_bo_sch)이
  `ul.btn_bo_user` 안에 없어 화면에서는 열 수 없다. 주소에 `?stx=검색어`를 붙일 때만 동작. spec 4장 "검색창 숨김"은 사실상 현재 상태와 같음(마크업 정리 수준).

## 8) 이전 작업 흔적
- admin/ 없음
- scripts/ 없음
- .github/workflows/ 있음: 파일 1개, 예 ['.github/workflows/deploy.yml']
- content/ 있음: 파일 60개, 예 ['content/boards.json', 'content/board_snapshot.json', 'content/optimize_manifest.json', 'content/posts.json', 'content/publish_exclude.json', 'content/redirects.json', 'content/renames.json', 'content/pages/meta.json']
- templates/ 있음: 파일 13개, 예 ['templates/404.html', 'templates/base.html', 'templates/board_list.html', 'templates/board_view.html', 'templates/page.html', 'templates/_board_head_en.html', 'templates/_board_head_ko.html', 'templates/_head_en.html']
- cms/ 없음
- build/ 있음: 파일 14개, 예 ['build/all.py', 'build/boards.py', 'build/build.py', 'build/extract_boards.py', 'build/extract_pages.py', 'build/extras.py', 'build/optimize.py', 'build/private_guard.py']
- uploads/ 없음
- _site/ 없음
  - build/all.py (23행): 전체 빌드 한 번에: optimize.py(이미지·동영상 최적화, 새 글 축소본·확대본) → build.py(페이지 생성 → public/)
  - build/boards.py (354행): 게시판 빌드 (build.py가 불러 씀). 저장소 안의 파일만 사용한다.
  - build/build.py (161행): 전체 빌드: templates/ + content/ + static/ → public/
  - build/extract_boards.py (142행): 게시판(4-4) 1회 추출: extract_pages.py가 불러서 실행한다 (내 PC 전용, crawl/·original/은 읽기만).
  - build/extract_pages.py (455행): 수집본(crawl/)에서 공통 틀과 페이지 본문 조각을 1회 추출하고, 필요한 자산을 original/www에서 static/으로 복사한다.
  - build/extras.py (136행): 4-6: 메인 회사소식(D12), 팝업, 옛 주소 이동(404.html + redirects.json), sitemap.xml·robots.txt.
  - build/optimize.py (344행): 이미지·동영상 최적화 (설계서 4장). build/all.py가 build.py 앞에서 실행한다. 몇 번을 다시 실행해도 결과가 같다.
  - build/private_guard.py (83행): 비공개 처리(D17)가 extract_pages.py 재실행으로 되살아나지 않게 막는다(내 PC 전용).
- .gitignore:
```
﻿.env
*.sql
*.bak
*.log
*.php
data/session/
data/tmp/
data/cache/
data/log/
Thumbs.db
.DS_Store
node_modules/
__pycache__/
*.dump
data/member/
public/
```

- 요약: admin/·scripts/·cms/·uploads/·_site/ **없음**. 기존 정적 변환 체계(.github/workflows/deploy.yml, build/ 8개 스크립트, templates/ 13개, content/ 60개)만 있음.
  관리자(CMS) 관련 흔적은 이 저장소에 없음.

## 9) spec.md 구현 시 예상 위험과 막히는 지점
1. **빌드 체계 불일치**: spec은 `scripts/build.py` → `_site`, 패키지 markdown·pyyaml만. 현재는 `build/all.py`(optimize → build) → `public/`, 패키지 pillow·jinja2.
   새로 만들면 이미지 최적화·비공개 가드·옛 주소(404/redirects)·sitemap·ENG 빌드를 다시 구현해야 함 → **기존 build/ 를 확장하고 출력 폴더·패키지 조건을 바꾸는 것**이 안전. 명세 수정 필요.
2. **원본 형식 불일치**: 게시글은 content/posts.json(그누보드 HTML 본문, files·hit 등) 한 파일. spec은 cms/<게시판>/*.md(markdown).
   기존 153건을 .md로 옮길지, posts.json + cms/*.md 를 함께 읽을지 결정 필요. HTML 본문을 markdown으로 바꾸면 화면이 달라질 위험.
3. **공통 영역이 여러 곳에 복사됨**: 메가메뉴·모바일 메뉴는 templates/_top_ko.html, 게시판용 _board_head_ko.html, 그리고 고정 페이지 조각(content/pages/ko/page/*.html)
   안의 하위 메뉴 드롭다운(sub_visual_nav, 페이지마다 2~3벌)까지 복사돼 있음. menu.yml로 "모든 한글 HTML" 자동 생성하려면 이 조각들을 템플릿 변수로 바꾸는 대량 수정 필요.
4. **ENG 분리**: 1차는 한국어만인데 ENG 게시판(notice_en·media_en)은 같은 posts.json·빌드에서 나옴. 한글 글이 cms로 넘어가도 ENG 빌드가 깨지지 않게 해야 하고, D1(상대 언어 링크) 유지 필요.
5. **비공개(D17) 보호**: Sveltia는 공개 저장소에 직접 커밋 → 비공개 현장 글이 올라오면 바로 공개·기록에 남음. private_guard.py는 "내 PC 전용"이라 Actions에서 막지 못함 →
   빌드에서 docs/비공개대상 키워드 차단 같은 검사를 추가할지 결정 필요(키워드 목록 자체도 공개 저장소에 남는 문제).
6. **이미지 경로·용량**: 업로드가 uploads/ 로 바뀌면 optimize.py(썸네일·확대본, D3)가 uploads/를 처리하도록 확장해야 함. 용량 300MB 규칙(D13): 현재 static 270MB로 여유 약 30MB뿐.
7. **Our Project**: 현재 고정 마크업 9칸(빈 칸 포함, 칸마다 별도 CSS 배경 이미지일 가능성). featured 자동 생성 시 칸 수·배경 이미지 처리 규칙을 정해야 함.
8. **팝업**: 기존 popup.js·마크업(data-begin/data-end, 크기·위치값)이 있으므로 popups.yml 필드(title,image,link,start,end,active)와 대응만 맞추면 됨. 크기·위치 필드는 spec에 없음.
9. **"회사소식" 라벨 버그**(4항)와 로고 title "Animotiontech"(_top_ko 등)는 단순 수정 가능.
10. **빌드 실패 시 유지**: Actions에서 build 실패 시 deploy가 안 돌므로 기존 사이트는 유지됨(현재 구조로 충족). 다만 optimize.py가 Actions에서 매번 이미지 처리 → 업로드 늘면 빌드 시간 증가.
11. **확인 못 한 것**: gh 미설치로 Pages 설정·Actions 실행 이력을 API로 확인하지 못함. 로컬 public/은 마지막 로컬 빌드 기준이라 운영본과 다를 수 있음.
