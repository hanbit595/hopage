/* 견적문의 폼 전송 (content/pages/{ko,en}/page/inquiry.html)
   - 받는 곳은 form 의 action(관리자 서버 /api/inquiry). form 형식으로 보내 사전 요청(preflight) 없이 전송한다.
   - 응답: 성공 {ok, message}, 실패 {ok:false, error, field}. 안내 문구는 언어별(아래 T). */
(function () {
    var form = document.getElementById("hb_inquiry");
    if (!form) return;
    var lang = form.getAttribute("data-lang") === "en" ? "en" : "ko";
    var T = {
        ko: {
            sending: "전송 중입니다. 잠시만 기다려 주세요…",
            done: "문의가 접수되었습니다. 담당자가 확인한 뒤 연락드리겠습니다. 감사합니다.",
            error: "전송하지 못했습니다. 잠시 후 다시 시도하시거나 전화로 문의해 주세요.",
            network: "인터넷 연결을 확인한 뒤 다시 시도해 주세요.",
            many: "짧은 시간에 문의가 많이 접수되었습니다. 10분쯤 뒤에 다시 시도해 주세요.",
            check: "입력 내용을 확인해 주세요: ",
            agree: "개인정보 수집·이용에 동의해야 문의할 수 있습니다.",
            email: "이메일 형식이 올바르지 않습니다."
        },
        en: {
            sending: "Sending… please wait.",
            done: "Thank you. Your inquiry has been received and we will contact you soon.",
            error: "Your inquiry could not be sent. Please try again later or call us.",
            network: "Please check your internet connection and try again.",
            many: "Too many inquiries in a short time. Please try again in about 10 minutes.",
            check: "Please check this field: ",
            agree: "You must agree to the collection and use of personal information to send an inquiry.",
            email: "Please enter a valid email address."
        }
    }[lang];
    var status = form.querySelector(".hb_status");
    var btn = form.querySelector(".hb_submit");

    function show(msg, kind) {
        status.hidden = false;
        status.className = "hb_status " + kind;
        status.textContent = msg;
    }
    function labelOf(name) {
        var el = form.elements[name];
        if (!el) return name;
        if (el.length && !el.tagName) el = el[0];
        var fs = el.closest("fieldset");
        if (fs) return fs.querySelector("legend").textContent.replace("*", "").trim();
        var lb = form.querySelector('label[for="' + el.id + '"]');
        return lb ? lb.textContent.replace("*", "").trim() : name;
    }
    function focusField(name) {
        var el = form.elements[name];
        if (!el) return;
        if (el.length && !el.tagName) el = el[0];
        if (el.focus) el.focus();
    }
    function check() {
        var req = ["customer_type", "place", "region", "name", "phone", "email", "message"];
        for (var i = 0; i < req.length; i++) {
            var v = form.elements[req[i]].value;
            if (!v || !String(v).trim()) return { field: req[i], msg: T.check + labelOf(req[i]) };
        }
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.elements.email.value.trim())) return { field: "email", msg: T.email };
        if (!form.elements.agree.checked) return { field: "agree", msg: T.agree };
        return null;
    }

    form.addEventListener("submit", function (e) {
        e.preventDefault();
        if (btn.disabled) return;
        var bad = check();
        if (bad) { show(bad.msg, "err"); focusField(bad.field); return; }
        var data = new URLSearchParams();
        ["lang", "customer_type", "place", "region", "scale", "interest", "name", "phone", "email", "message", "website"].forEach(function (k) {
            data.append(k, String(form.elements[k].value || "").trim());
        });
        data.append("agree", "true");
        btn.disabled = true;
        show(T.sending, "ing");
        fetch(form.action, { method: "POST", body: data, mode: "cors", credentials: "omit" })
            .then(function (r) {
                return r.json().catch(function () { return {}; }).then(function (j) { return { status: r.status, body: j }; });
            })
            .then(function (res) {
                var j = res.body || {};
                if (res.status >= 200 && res.status < 300 && j.ok) {
                    form.reset();
                    show(T.done, "ok");
                } else if (res.status === 429) {
                    show(T.many, "err");
                } else if (j.field) {
                    show(T.check + labelOf(j.field), "err");
                    focusField(j.field);
                } else {
                    show(T.error, "err");
                }
            })
            .catch(function () { show(T.network, "err"); })
            .then(function () { btn.disabled = false; });
    });
})();
