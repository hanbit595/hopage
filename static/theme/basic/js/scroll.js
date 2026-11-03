function init(){
    new SmoothScroll(document,120,12)
}

function SmoothScroll(target, speed, smooth) {
    if (target === document)
        target = (document.scrollingElement
              || document.documentElement
              || document.body.parentNode
              || document.body
              || document.querySelector('.m_menu_wrap')
              || document.querySelector('.m_menu_all_wrap')
              ) // cross browser support for document scrolling

    var moving = false
    var pos = target.scrollTop
  var frame = target === document.body
              && document.documentElement
              ? document.documentElement
              : target // safari is the new IE

    target.addEventListener('mousewheel', scrolled, { passive: false })
    target.addEventListener('DOMMouseScroll', scrolled, { passive: false })
    $(function() {
        $('#toTop').bind('click',function(event){
            pos = 0;
            $( 'html, body' ).animate( { scrollTop : 0 }, 400 );
            return false;
            event.preventDefault();
        });
    });
    $(function() {
        $('.go_ani').bind('click',function(event){
            var $anchor = $(this);
            pos = $($anchor.attr('href')).offset().top;
            event.preventDefault();
        });
    });

    function scrolled(e) {
        // if currently not animating make sure our pos is up to date with the current scroll postion
        if(!moving) {
            pos = target.scrollTop;
        }
        e.preventDefault(); // disable default scrolling

        var delta = normalizeWheelDelta(e)

        pos += -delta * speed
        pos = Math.max(0, Math.min(pos, target.scrollHeight - frame.clientHeight)) // limit scrolling
        if (!moving) update()
    }

    function normalizeWheelDelta(e){
        if(e.detail){
            if(e.wheelDelta)
                return e.wheelDelta/e.detail/40 * (e.detail>0 ? 1 : -1) // Opera
            else
                return -e.detail/3 // Firefox
        }else
            return e.wheelDelta/120 // IE,Safari,Chrome
    }

     function update() {
         if ($('html').hasClass('on')) {
            target = (document.querySelector('.m_menu_wrap'))
        }
        else {
            target = (document.scrollingElement
              || document.documentElement
              || document.body.parentNode
              || document.body
              || document.querySelector('.m_menu_wrap')
              || document.querySelector('.m_menu_all_wrap')
              )
        }
                moving = true;
        // scrollTop is an integer and moving it by anything less than a whole number wont do anything
        // to prevent a noop and an infinite loop we need to round it
        var delta = absRound((pos - target.scrollTop) / smooth)

        target.scrollTop += delta


        if (Math.abs(delta) >= 1) {
            requestFrame(update)
        } else {
            moving = false
        }
    }
     function absRound(num) {
        if(num < 0) {
            return -1*Math.round(-1*num);
        } else {
            return Math.round(num);
        }
    }

    var requestFrame = function() { // requestAnimationFrame cross browser
        return (
            window.requestAnimationFrame ||
            window.webkitRequestAnimationFrame ||
            window.mozRequestAnimationFrame ||
            window.oRequestAnimationFrame ||
            window.msRequestAnimationFrame ||
            function(func) {
                window.setTimeout(func, 1000 / 50);
            }
        );
    }()
}

init();
