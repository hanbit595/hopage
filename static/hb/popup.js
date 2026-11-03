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
