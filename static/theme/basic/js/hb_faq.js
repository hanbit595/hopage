/* FAQ 페이지: 분류 탭 + 질문 클릭 시 답변 펼침 (content/pages/{ko,en}/page/faq.html) */
(function () {
    var box = document.querySelector("[data-hb-faq]");
    if (!box) return;
    var tabs = box.querySelectorAll(".hb_tabs button");
    var items = box.querySelectorAll(".hb_faq_item");
    function toggle(item, open) {
        var btn = item.querySelector("dt button"), dd = item.querySelector("dd");
        btn.setAttribute("aria-expanded", open ? "true" : "false");
        dd.hidden = !open;
        item.classList.toggle("on", open);
    }
    Array.prototype.forEach.call(tabs, function (tab) {
        tab.addEventListener("click", function () {
            var cat = tab.getAttribute("data-cat");
            Array.prototype.forEach.call(tabs, function (t) {
                t.classList.toggle("on", t === tab);
                t.setAttribute("aria-selected", t === tab ? "true" : "false");
            });
            Array.prototype.forEach.call(items, function (it) {
                it.hidden = !(cat === "all" || it.getAttribute("data-cat") === cat);
                toggle(it, false);
            });
        });
    });
    Array.prototype.forEach.call(items, function (it) {
        it.querySelector("dt button").addEventListener("click", function () {
            toggle(it, this.getAttribute("aria-expanded") !== "true");
        });
    });
})();
