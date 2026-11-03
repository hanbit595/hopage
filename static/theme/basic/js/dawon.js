 // 메뉴

 VanillaTilt.init(document.querySelectorAll(".titani"));

 $(".top_nav").mouseenter(function () {
     $('.all_bg').stop(true, true).fadeIn();
     $("#wrap").addClass("open");
     $(".header_all_wrap").addClass("nav-open");
     $(".top_nav .sub_menu_wrap").stop(true, true).slideDown(300);
 }).mouseleave(function () {
     $("#wrap").removeClass("open");
     $('.all_bg').stop(true, true).fadeOut();
     $(".header_all_wrap").removeClass("nav-open");
     $(".top_nav .sub_menu_wrap").stop(true, true).slideUp(200);
 });
 
 // 스크롤 애니메이션
 $(document).ready(function () {
     $('.animate').css('visibility', 'hidden');
     $('.animate').scrolla({
         mobile: true,
         once: true
     });
 });
 



// 스크롤 이벤트
var headH = $(".header_all_wrap").height();
$(window).scroll(function(){
	var scrollTop = $(document).scrollTop();
	if (scrollTop > headH) {
		$("body").addClass("scroll");
	}else {
		$("body").removeClass("scroll");
	}
	return false;
});
$(document).ready(function(){
	var scrollTop = $(document).scrollTop();
	if (scrollTop > headH) {
		$("#wrap").addClass("scroll");
	}else {
		$("#wrap").removeClass("scroll");
	}
});
$(function () {
    var $win   = $(window);
    var $wrap  = $('#wrap');
    var $header= $('.header_all_wrap');
  
    function checkScroll() {
      var st = $win.scrollTop();
  
      if (st <= 0) {
        $wrap.removeClass('scroll');
        return;
      }
  
      var headH = $header.outerHeight() || 0;
      $wrap.toggleClass('scroll', st > headH);
    }
  
    checkScroll();
    $win.on('scroll resize load', checkScroll);
    window.addEventListener('pageshow', checkScroll);
  });
  

// 플레이스홀더
$(document).ready(function() {
	$('input, textarea').placeholder();
});


// a 태그 이동액션
$(function() {
	$('.go_ani').bind('click',function(event){
		var $anchor = $(this);

		$('html, body').stop().animate({
			scrollTop: $($anchor.attr('href')).offset().top
		}, 1000,'easeInOutExpo');

		event.preventDefault();
	});
});



// 카테고리 브레드
$(document).ready(function(){
	$(".bread_depth_01 .btn_open").click(function(){
		if ($('.sub_cate_top').hasClass('depth_01_open')) {
			$(".sub_cate_top").removeClass("depth_01_open");
		}
		else {
			$(".sub_cate_top").addClass("depth_01_open");
			$(".sub_cate_top").removeClass("depth_02_open");
			$(".sub_cate_top").removeClass("depth_03_open");
		}
	})
	$(".bread_depth_02 .btn_open").click(function(){
		if ($('.sub_cate_top').hasClass('depth_02_open')) {
			$(".sub_cate_top").removeClass("depth_02_open");
		}
		else {
			$(".sub_cate_top").addClass("depth_02_open");
			$(".sub_cate_top").removeClass("depth_01_open");
			$(".sub_cate_top").removeClass("depth_03_open");
		}
	})
	$(".bread_depth_03 .btn_open").click(function(){
		if ($('.sub_cate_top').hasClass('depth_03_open')) {
			$(".sub_cate_top").removeClass("depth_03_open");
		}
		else {
			$(".sub_cate_top").addClass("depth_03_open");
			$(".sub_cate_top").removeClass("depth_01_open");
			$(".sub_cate_top").removeClass("depth_02_open");
		}
	})
});

$(document).ready(function(){
	var breadDepth01 = $('.bread_depth_01 .bread_box_sub_wrap').width();
	$('.bread_depth_01 .bread_box_wrap ').css('width', breadDepth01 + 2 );
	var breadDepth02 = $('.bread_depth_02 .bread_box_sub_wrap').width();
	$('.bread_depth_02 .bread_box_wrap ').css('width', breadDepth02 + 2 );
	var breadDepth03 = $('.bread_depth_03 .bread_box_sub_wrap').width();
	$('.bread_depth_03 .bread_box_wrap ').css('width', breadDepth03 + 2 );
});
$(document).load(function(){
	var breadDepth01 = $('.bread_depth_01 .bread_box_sub_wrap').width();
	$('.bread_depth_01 .bread_box_wrap ').css('width', breadDepth01 + 2 );
	var breadDepth02 = $('.bread_depth_02 .bread_box_sub_wrap').width();
	$('.bread_depth_02 .bread_box_wrap ').css('width', breadDepth02 + 2 );
	var breadDepth03 = $('.bread_depth_03 .bread_box_sub_wrap').width();
	$('.bread_depth_03 .bread_box_wrap ').css('width', breadDepth03 + 2 );
});

// 별점
$(document).ready(function(){
	$(".star_open").click(function(){
		if($(".star_option ").css("display") == "none"){
			$('.star_option').show();
			$('.star_option').animate({
				height: "145px"
			}, 200);
		} else {
			$('.star_option').animate({
				height: "0px"
			}, 200);
			$('.star_option').hide({
			}, 10);
		}
	})
});
$(document).ready(function(){
	$(".star_option input").on('change', function() {
		var selectStar_name = $('.star_option input:checked').val();
		$('.star_top').addClass("txt_none");
		$('.star_top').removeClass("star_01");
		$('.star_top').removeClass("star_02");
		$('.star_top').removeClass("star_03");
		$('.star_top').removeClass("star_04");
		$('.star_top').removeClass("star_05");
		$('.star_top').addClass(selectStar_name);
		$('.star_option').animate({
			height: "0px"
		}, 200);
		$('.star_option').hide({
		}, 10);
	});
});


// 팝업
$(document).ready(function(){
	$(".pop_open_btn").bind('click',function(event){
		var PopTarget = $(this).attr("pop-target");
		var PopTargetClass = "."+ PopTarget;
		var PopTargetHtml = "<div class='"+PopTarget+"'>" + $(PopTargetClass).html() + "</div>";
		// alert(PopTargetHtml);
		$(".seok_pop").empty();
		$(".seok_pop").append(PopTargetHtml);
		$(".seok_pop_wrap").fadeIn();
		var SeokH = $('.seok_pop').height() ;
		var SeokW = $('.seok_pop').width() ;
		$(".seok_pop_box").css( { "margin-top" : - SeokH/2 } );
		$(".seok_pop_box").css( { "margin-left" : - SeokW/2 } );
		event.preventDefault();
	});
	$(".seok_pop_bg").bind('click',function(event){
		$(".seok_pop_wrap").fadeOut();
		$(".seok_pop").empty();
		event.preventDefault();
	});
});

$(document).ready(function(){
	$('.sub_cate_top').css( { "background-size":"2500px", "opacity":"0"} );
	$('.sub_cate_top').animate({"background-size":"2000px", "opacity":"1"},500);
});



// 탑
(function($){
	$.fn.UItoTop = function(options) {

		var defaults = {
			text: 'To Top',
			min: 200,
			inDelay:600,
			outDelay:400,
			containerID: 'toTop',
			containerHoverID: 'toTopHover',
			scrollSpeed: 1200,
			easingType: 'linear'
		},
		settings = $.extend(defaults, options),
		containerIDhash = '#' + settings.containerID,
		containerHoverIDHash = '#'+settings.containerHoverID;

		$('body').append('<a href="#" id="'+settings.containerID+'">'+settings.text+'</a>');
		$(containerIDhash).hide().on('click.UItoTop',function(){
			$('html, body').stop().animate({scrollTop:0}, settings.scrollSpeed, settings.easingType);
			$('#'+settings.containerHoverID, this).stop().animate({'opacity': 0 }, settings.inDelay, settings.easingType);
			return false;
		})
		.prepend('<span id="'+settings.containerHoverID+'"></span>')
		.hover(function() {
			$(containerHoverIDHash, this).stop().animate({
				'opacity': 1
			}, 600, 'linear');
		}, function() {
			$(containerHoverIDHash, this).stop().animate({
				'opacity': 0
			}, 700, 'linear');
		});

		$(window).scroll(function() {
			var sd = $(window).scrollTop();
			if(typeof document.body.style.maxHeight === "undefined") {
				$(containerIDhash).css({
					'position': 'absolute',
					'top': sd + $(window).height() - 50
				});
			}
			if ( sd > settings.min )
				$(containerIDhash).fadeIn(settings.inDelay);
			else
				$(containerIDhash).fadeOut(settings.Outdelay);
		});
	};
})(jQuery);


$(document).ready(function() {
	$().UItoTop({});
});


