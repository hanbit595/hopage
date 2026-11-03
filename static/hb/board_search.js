/* 게시판 제목 검색 (원본의 서버 검색 board.php?stx= 를 대신함)
   - 목록의 검색창(form[name=fsearch])을 제출하거나, 주소에 ?stx=검색어 를 붙이면 같은 게시판 글 제목에서 찾는다
   - 결과는 원본 목록과 같은 모양(좌측 1건 + 우측)으로 보여 주고, 페이지 번호는 숨긴다
   - 글 목록: 같은 폴더의 search.json (빌드 때 생성) */
(function ($) {
  var form = document.querySelector('form[name="fsearch"]');
  if (!form) return;
  var layout = document.querySelector(".webzine_layout");
  var pager = document.querySelector(".pg_wrap");
  var original = layout ? layout.innerHTML : "";
  var labelEl = document.querySelector(".webzine_left .label");
  var label = labelEl ? labelEl.textContent.trim() : (document.documentElement.lang === "en" ? "Notice" : "회사소식");
  var cache = null;

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function load() {
    if (cache) return Promise.resolve(cache);
    return fetch(form.getAttribute("data-board-index") || "search.json")
      .then(function (r) { return r.json(); })
      .then(function (j) { cache = j; return j; });
  }

  function cut(s) { return s.length > 60 ? s.slice(0, 60) + "…" : s; }   // 원본 목록처럼 60자에서 자름

  function render(items) {
    items = items.map(function (it) { return { href: it.href, left: it.left, right: it.right, date: it.date, subject: cut(it.subject) }; });
    var h = "\n\n                <!-- 좌측 : 최신글 1건 -->\n";
    if (items.length) {
      var a = items[0];
      h += '<div class="webzine_left"><a href="' + esc(a.href) + '" >' +
        (a.left ? '<div class="left_thumb"><img src="' + esc(a.left) + '" alt=""></div>' : "") +
        '<div class="left_txt"><span class="label">' + esc(label) + '</span><h2>' + esc(a.subject) + '</h2><p class="date">' +
        esc(a.date) + "</p></div></a></div>";
    }
    h += '\n                <!-- 우측 : 다음 6건 -->\n<div class="webzine_right">';
    items.slice(1).forEach(function (it) {
      h += '<div class="right_item"><a href="' + esc(it.href) + '">' +
        (it.right ? '<div class="thumb"><img src="' + esc(it.right) + '" alt=""></div>' : "") +
        '<div class="txt"><p class="tit">' + esc(it.subject) + '</p><span class="date">' + esc(it.date) + "</span></div></a></div>";
    });
    h += "</div>";
    layout.innerHTML = h;
    if (pager) pager.style.display = "none";
  }

  function search(q) {
    q = (q || "").trim();
    if (!q) {
      layout.innerHTML = original;
      if (pager) pager.style.display = "";
      return Promise.resolve(null);
    }
    var words = q.toLowerCase().split(/\s+/);
    return load().then(function (list) {
      var hits = list.filter(function (it) {
        var t = it.subject.toLowerCase();
        return words.every(function (w) { return t.indexOf(w) > -1; });   // 원본 sop=and 와 같이 모든 단어 포함
      });
      render(hits);
      return hits;
    });
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var q = form.querySelector('[name="stx"]').value;
    search(q).then(function () {
      if (window.history && history.replaceState) {
        var url = location.pathname + (q.trim() ? "?stx=" + encodeURIComponent(q.trim()) : "");
        history.replaceState(null, "", url);
      }
      if ($) $(".bo_sch_wrap").hide();
    });
  });

  var m = /[?&]stx=([^&]*)/.exec(location.search);
  if (m) {
    var q = decodeURIComponent(m[1].replace(/\+/g, " "));
    form.querySelector('[name="stx"]').value = q;
    search(q);
  }
  window.hanbitBoardSearch = search;
})(window.jQuery);
