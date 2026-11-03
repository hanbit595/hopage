/* 이미지 확대 보기 (원본 그누보드의 view_image.php 새 창을 대신하는 라이트박스)
   사용: hanbitLightbox.open(이미지주소, 설명)  — 닫기: 배경·닫기 버튼 클릭, Esc 키 */
(function (w, d) {
  var box, img, cap, lastFocus;

  function build() {
    box = d.createElement("div");
    box.className = "hb-lightbox";
    box.setAttribute("role", "dialog");
    box.setAttribute("aria-modal", "true");
    box.setAttribute("aria-label", "이미지 확대 보기");
    box.innerHTML =
      '<button type="button" class="hb-lightbox-close" aria-label="닫기">&times;</button>' +
      '<figure class="hb-lightbox-figure"><img class="hb-lightbox-img" alt=""><figcaption class="hb-lightbox-cap"></figcaption></figure>';
    d.body.appendChild(box);
    img = box.querySelector(".hb-lightbox-img");
    cap = box.querySelector(".hb-lightbox-cap");
    box.addEventListener("click", function (e) {
      if (e.target === box || e.target.classList.contains("hb-lightbox-close")) close();
    });
    d.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && box.classList.contains("is-open")) close();
    });
  }

  function open(src, alt) {
    if (!box) build();
    lastFocus = d.activeElement;
    img.src = src;
    img.alt = alt || "";
    cap.textContent = "";
    box.classList.add("is-open");
    d.documentElement.classList.add("hb-lightbox-lock");
    box.querySelector(".hb-lightbox-close").focus();
  }

  function close() {
    box.classList.remove("is-open");
    d.documentElement.classList.remove("hb-lightbox-lock");
    img.removeAttribute("src");
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }

  w.hanbitLightbox = { open: open, close: close, isOpen: function () { return !!box && box.classList.contains("is-open"); } };
})(window, document);
