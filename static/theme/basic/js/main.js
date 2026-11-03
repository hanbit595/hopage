/* ============================
   Main Slider (Slick + Video)
============================ */

const $wrap   = $('.slider-wrap');
const $slider = $('.main-slider');

let rafId = null;
let v = null;
let pausedByBtn = false;

const isPaused = () =>
    $wrap.attr('data-slick-autoplay-status') === 'N';

const stopRAF = () => {
    if (rafId) cancelAnimationFrame(rafId);
    rafId = null;
};

const hardResetVideos = () => {
    $slider.find('.slick-slide video').each(function () {
        try {
            this.pause();
            this.currentTime = 0;
        } catch (e) {}
        this.removeAttribute('autoplay');
    });
};

function cleanup() {
    stopRAF();
    if (v) {
        try { v.pause(); } catch (e) {}
        v = null;
    }
}

function runSlide() {
    cleanup();

    const $cur = $slider.find('.slick-current');
    v = $cur.find('video').get(0);

    if (!v) {
        const delay = Number($cur.data('delay') || 5000);

        rafId = requestAnimationFrame(() => {
            setTimeout(() => {
                if (!isPaused()) {
                    $slider.slick('slickNext');
                }
            }, delay);
        });

        return;
    }

    if (!isPaused()) {
        v.play().catch(() =>
            $(document).one('pointerdown keydown', () =>
                v.play().catch(() => {})
            )
        );
    }

    v.addEventListener(
        'ended',
        () => {
            if (!pausedByBtn) {
                $slider.slick('slickNext');
            }
        },
        { once: true }
    );
}

$slider
    .on('init reInit', () => {
        hardResetVideos();
        runSlide();
    })
    .on('beforeChange', () => cleanup())
    .on('afterChange', () => runSlide());

$slider.slick({
    dots: false,
    fade: true,
    arrows: false,
    autoplay: false,

    customPaging: function (slider, i) {
        const num = (i + 1).toString().padStart(2, '0');
        return `<button type="button" class="s-dot-num">${num}</button>`;
    }
});

$('.s-autoplay-btn').on('click', function () {
    const next =
        $wrap.attr('data-slick-autoplay-status') === 'Y' ? 'N' : 'Y';

    $wrap.attr('data-slick-autoplay-status', next);
    pausedByBtn = next === 'N';

    const cv = $slider.find('.slick-current video').get(0);

    if (next === 'N') {
        if (cv) {
            try { cv.pause(); } catch (e) {}
        }
        cleanup();
    } else {
        runSlide();
    }
});

document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        cleanup();
    } else {
        runSlide();
    }
});
