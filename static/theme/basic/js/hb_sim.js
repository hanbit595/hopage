/* 시뮬레이션: 목록 분류 탭, 상세 3D 보기(PC=화면에 보이면 불러옴, 768px 미만=버튼 눌러 불러옴), 전체 화면 */
(function () {
    var each = function (list, fn) { Array.prototype.forEach.call(list, fn); };
    var box = document.querySelector("[data-hb-sim-list]");
    if (box) {
        var tabs = box.querySelectorAll(".hb_sim_tabs button"), cards = box.querySelectorAll(".hb_sim_cards li");
        each(tabs, function (tab) {
            tab.addEventListener("click", function () {
                var cat = tab.getAttribute("data-cat");
                each(tabs, function (t) { t.classList.toggle("on", t === tab); t.setAttribute("aria-selected", t === tab ? "true" : "false"); });
                each(cards, function (c) { c.hidden = !(cat === "all" || (" " + c.getAttribute("data-cats") + " ").indexOf(" " + cat + " ") >= 0); });
            });
        });
    }
    each(document.querySelectorAll("[data-hb-sim-3d]"), function (el) {
        var src = el.getAttribute("data-hb-sim-3d");
        function load() {
            if (el.classList.contains("on")) return;
            var f = document.createElement("iframe");
            f.src = src; f.title = "3D"; f.setAttribute("allow", "fullscreen"); f.setAttribute("allowfullscreen", "");
            el.insertBefore(f, el.firstChild);
            el.classList.add("on");
        }
        el.querySelector(".hb_sim_load").addEventListener("click", load);
        el.querySelector(".hb_sim_full").addEventListener("click", function () {
            load();
            var req = el.requestFullscreen || el.webkitRequestFullscreen;
            if (!req) { window.open(src, "_blank"); return; }
            var r = req.call(el);
            if (r && r.catch) r.catch(function () { window.open(src, "_blank"); });
        });
        if (window.matchMedia && window.matchMedia("(max-width: 767px)").matches) return;   // 모바일: 버튼 눌러야 불러옴
        if ("IntersectionObserver" in window) {
            var io = new IntersectionObserver(function (es) {
                if (es[0].isIntersecting) { io.disconnect(); load(); }
            }, { rootMargin: "200px" });
            io.observe(el);
        } else { load(); }
    });
})();
