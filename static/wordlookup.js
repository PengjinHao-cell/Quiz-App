/**
 * 单词点击查词 — 独立模块
 * 在 app.js 之前引入，所有英文内容页面共享
 */
(function() {
    "use strict";

    var popupEl = null;
    var menuEl = null;
    var lastLookupWord = "";
    var lastLookupTime = 0;
    var lastLookupData = null;  // 缓存最近一次查词结果

    // ===== 初始化 =====
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }

    function init() {
        document.addEventListener("dblclick", onDoubleClick);
        document.addEventListener("contextmenu", onRightClick);
        document.addEventListener("click", onDocumentClick);
        document.addEventListener("keydown", onKeyDown);
    }

    // ===== 双击查词 =====
    function onDoubleClick(e) {
        if (isInputElement(e.target)) return;

        var sel = getSelectionText();
        if (!sel) return;

        if (sel.text === lastLookupWord && Date.now() - lastLookupTime < 10000) return;
        lastLookupWord = sel.text;
        lastLookupTime = Date.now();

        showPopup(e.clientX, e.clientY, sel.text, sel.isPhrase);
        fetchWord(sel.text);
    }

    // ===== 右键菜单 =====
    function onRightClick(e) {
        // 优先取拖拽选区（支持词组），再退到光标位置单词
        var sel = getSelectionText();
        var target;
        if (sel) {
            target = sel;
        } else {
            var word = getWordAtPoint(e.clientX, e.clientY);
            if (!word) return;
            target = { text: word, isPhrase: false };
        }

        e.preventDefault();
        hidePopup();
        showMenu(e.clientX, e.clientY, target);
    }

    // ===== 点击其他地方关闭 =====
    function onDocumentClick(e) {
        if (popupEl && !popupEl.contains(e.target)) hidePopup();
        if (menuEl && !menuEl.contains(e.target)) hideMenu();
    }

    // ===== ESC 关闭 =====
    function onKeyDown(e) {
        if (e.key === "Escape") { hidePopup(); hideMenu(); }
    }

    function isInputElement(el) {
        var tag = el.tagName;
        return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || el.isContentEditable;
    }

    function getSelectionText() {
        var sel = window.getSelection();
        if (!sel || sel.isCollapsed) return null;
        var text = sel.toString().trim().toLowerCase();

        // 单 token 单词（含连字符、撇号）
        if (/^[a-zA-Z]+(?:[-'][a-zA-Z]+)*$/.test(text) && text.length >= 2) {
            return { text: text, isPhrase: false };
        }

        // 词组：2-5 词，空格分隔
        var words = text.split(/\s+/);
        if (words.length >= 2 && words.length <= 5
            && /^[a-zA-Z]+(?:[-\s'][a-zA-Z]+)*$/.test(text)) {
            return { text: text, isPhrase: true };
        }

        return null;
    }

    function getWordAtPoint(x, y) {
        var range;
        if (document.caretRangeFromPoint) {
            range = document.caretRangeFromPoint(x, y);
        } else if (document.caretPositionFromPoint) {
            var pos = document.caretPositionFromPoint(x, y);
            if (pos) {
                range = document.createRange();
                range.setStart(pos.offsetNode, pos.offset);
                range.setEnd(pos.offsetNode, pos.offset);
            }
        } else {
            return null;
        }

        if (!range || !range.startContainer) return null;
        var node = range.startContainer;
        if (node.nodeType !== Node.TEXT_NODE) return null;

        var text = node.textContent;
        var offset = range.startOffset;
        var start = offset, end = offset;
        while (start > 0 && /[a-zA-Z'-]/.test(text[start - 1])) start--;
        while (end < text.length && /[a-zA-Z'-]/.test(text[end])) end++;

        var word = text.slice(start, end).trim();
        if (word.length >= 2 && /^[a-zA-Z]+(?:[-'][a-zA-Z]+)*$/.test(word)) {
            return word.toLowerCase();
        }
        return null;
    }

    // ===== API 查词 =====
    function fetchWord(word) {
        fetch("/api/dict/" + encodeURIComponent(word))
            .then(function(res) {
                if (!res.ok) throw new Error("not_found");
                return res.json();
            })
            .then(function(data) {
                lastLookupData = data;
                updatePopupContent(data);
            })
            .catch(function() {
                lastLookupData = null;
                hidePopup();
            });
    }

    // ===== 浮窗 =====
    function showPopup(x, y, word, isPhrase) {
        hideMenu();
        hidePopup();

        var tagHtml = isPhrase ? '<span class="wl-tag wl-tag-phrase">词组</span>' : '';

        popupEl = document.createElement("div");
        popupEl.className = "wl-popup";
        popupEl.innerHTML =
            '<div class="wl-popup-word">' +
                _esc(word) + ' ' + tagHtml +
                '<button class="wl-popup-close" title="关闭">✕</button>' +
            '</div>' +
            '<div class="wl-popup-meta" style="display:none;"></div>' +
            '<div class="wl-popup-loading">' +
                '<span class="wl-skeleton wl-skeleton-word"></span>' +
                '<span class="wl-skeleton wl-skeleton-meaning"></span>' +
            '</div>';

        popupEl.querySelector(".wl-popup-close").addEventListener("click", function(e) {
            e.stopPropagation();
            hidePopup();
        });

        document.body.appendChild(popupEl);
        positionElement(popupEl, x, y);
    }

    function updatePopupContent(data) {
        if (!popupEl) return;
        var isPhrase = data.is_phrase;
        var tagHtml = isPhrase ? '<span class="wl-tag wl-tag-phrase">词组</span>' : '';

        // meta: 词形还原提示
        var metaHtml = '';
        if (data.lemma && data.lemma_note) {
            metaHtml = '<span class="wl-lemma-note">' + _esc(data.lemma_note) + '</span>';
        } else if (data.lemma) {
            metaHtml = '<span class="wl-lemma-note">原形: ' + _esc(data.lemma) + '</span>';
        }

        popupEl.innerHTML =
            '<div class="wl-popup-word">' +
                _esc(data.word) + ' ' + tagHtml +
                '<button class="wl-popup-close" title="关闭">✕</button>' +
            '</div>' +
            (metaHtml ? '<div class="wl-popup-meta">' + metaHtml + '</div>' : '') +
            '<div class="wl-popup-meaning">' + _esc(data.meaning) + '</div>';

        popupEl.querySelector(".wl-popup-close").addEventListener("click", function(e) {
            e.stopPropagation();
            hidePopup();
        });

        var rect = popupEl.getBoundingClientRect();
        positionElement(popupEl, rect.left, rect.top);
    }

    function hidePopup() {
        if (popupEl) { popupEl.remove(); popupEl = null; }
    }

    // ===== 右键菜单 =====
    function showMenu(x, y, target) {
        hideMenu();

        var isReading = (typeof window.applyHighlight === "function");
        var word = target.text;
        var isPhrase = target.isPhrase;

        menuEl = document.createElement("div");
        menuEl.className = "wl-menu";

        var html = '';
        html += '<div class="wl-menu-item" data-action="lookup">🔍 查词</div>';
        html += '<div class="wl-menu-item" data-action="copy">📋 ' + (isPhrase ? '复制词组' : '复制单词') + '</div>';
        html += '<div class="wl-menu-item" data-action="vocab">⭐ 加入生词本</div>';

        if (isReading) {
            html += '<div class="wl-menu-separator"></div>';
            html += '<div class="wl-menu-item" data-action="highlight">🖍 荧光标记</div>';
            html += '<div class="wl-menu-item" data-action="underline">＿ 下划线标记</div>';
        }

        menuEl.innerHTML = html;

        menuEl.querySelectorAll(".wl-menu-item").forEach(function(item) {
            item.addEventListener("click", function() {
                handleMenuAction(item.getAttribute("data-action"), target);
                hideMenu();
            });
        });

        document.body.appendChild(menuEl);
        positionElement(menuEl, x, y);
    }

    function hideMenu() {
        if (menuEl) { menuEl.remove(); menuEl = null; }
    }

    function handleMenuAction(action, target) {
        var word = target.text;
        var isPhrase = target.isPhrase;

        switch (action) {
            case "lookup":
                showPopup(
                    menuEl ? parseInt(menuEl.style.left) : 0,
                    menuEl ? parseInt(menuEl.style.top) : 0,
                    word,
                    isPhrase
                );
                fetchWord(word);
                break;
            case "copy":
                if (navigator.clipboard) {
                    navigator.clipboard.writeText(word).then(function() {
                        _toast("已复制: " + word, "success");
                    });
                }
                break;
            case "vocab":
                addToVocabBook(word);
                break;
            case "highlight":
                if (typeof window.applyHighlight === "function") window.applyHighlight("highlight");
                break;
            case "underline":
                if (typeof window.applyHighlight === "function") window.applyHighlight("underline");
                break;
        }
    }

    // ===== 加入生词本 =====
    function addToVocabBook(word) {
        fetch("/api/dict/" + encodeURIComponent(word))
            .then(function(res) { return res.json(); })
            .then(function(data) {
                if (!data.meaning) throw new Error("no meaning");
                var payload = {
                    word: data.word,
                    meaning: data.meaning,
                    source: data.source || "unknown",
                    context: document.title || "",
                    lemma: data.lemma || "",
                    is_phrase: data.is_phrase || false,
                };
                lastLookupData = data;

                if (_isLoggedIn()) {
                    return fetch("/api/vocab/add", {
                        method: "POST",
                        credentials: "same-origin",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(payload),
                    }).then(function(res) {
                        if (!res.ok) throw new Error("failed");
                        return res.json();
                    });
                } else {
                    var book = _getVocabLocal();
                    if (book[word]) return { success: false, message: "已在生词本中" };
                    book[word] = {
                        word: data.word,
                        meaning: data.meaning,
                        source: data.source || "unknown",
                        context: document.title || "",
                        lemma: data.lemma || "",
                        is_phrase: data.is_phrase || false,
                        created_at: new Date().toISOString(),
                    };
                    _saveVocabLocal(book);
                    var label = data.is_phrase ? "词组「" + data.word + "」" : "「" + data.word + "」";
                    return { success: true, message: label + "已加入生词本" };
                }
            })
            .then(function(result) {
                if (result && result.message) _toast(result.message, result.success !== false ? "success" : "info");
            })
            .catch(function() {
                _toast("加入生词本失败", "error");
            });
    }

    // ===== 本地生词本 =====
    var VOCAB_BOOK_KEY = "vocabBook";

    function _getVocabLocal() {
        try { return JSON.parse(localStorage.getItem(VOCAB_BOOK_KEY)) || {}; }
        catch(e) { return {}; }
    }
    function _saveVocabLocal(book) {
        localStorage.setItem(VOCAB_BOOK_KEY, JSON.stringify(book));
    }

    // 暴露给 vocab 页面
    window.getVocabBookLocal = _getVocabLocal;
    window.saveVocabBookLocal = _saveVocabLocal;
    window.VOCAB_BOOK_KEY = VOCAB_BOOK_KEY;

    // ===== 内联工具（不依赖外部） =====

    function _isLoggedIn() {
        return typeof window._IS_LOGGED_IN !== "undefined" && window._IS_LOGGED_IN === true;
    }

    function _esc(str) {
        if (str === null || str === undefined) return "";
        var div = document.createElement("div");
        div.textContent = String(str);
        return div.innerHTML;
    }

    function _toast(text, type) {
        var container = document.getElementById("toast-container");
        if (!container) {
            container = document.createElement("div");
            container.id = "toast-container";
            container.style.cssText =
                "position:fixed;top:20px;right:20px;z-index:99999;display:flex;flex-direction:column;gap:10px;max-width:380px;";
            document.body.appendChild(container);
        }

        var icons = { success: "✅", error: "❌", warning: "⚠️", info: "ℹ️" };
        var bgColors = { success: "#f0fff4", error: "#fff5f5", warning: "#fffbeb", info: "#eff6ff" };
        var borderColors = { success: "#38a169", error: "#e53e3e", warning: "#d69e2e", info: "#3182ce" };

        var toast = document.createElement("div");
        toast.style.cssText =
            "background:" + (bgColors[type] || "#eff6ff") + ";" +
            "border-left:4px solid " + (borderColors[type] || "#3182ce") + ";" +
            "padding:12px 16px;border-radius:8px;font-size:0.875rem;color:#2d3748;" +
            "box-shadow:0 4px 12px rgba(0,0,0,0.1);animation:wlToastIn 0.25s ease;" +
            "word-break:break-word;";
        toast.textContent = (icons[type] || "") + " " + text;

        container.appendChild(toast);
        setTimeout(function() {
            toast.style.opacity = "0";
            toast.style.transition = "opacity 0.3s";
            setTimeout(function() { toast.remove(); }, 300);
        }, 2500);
    }

    // Toast 动画（只注入一次）
    if (!document.getElementById("wl-toast-style")) {
        var s = document.createElement("style");
        s.id = "wl-toast-style";
        s.textContent = "@keyframes wlToastIn{from{opacity:0;transform:translateX(20px)}to{opacity:1;transform:translateX(0)}}";
        document.head.appendChild(s);
    }

    // ===== 定位工具 =====
    function positionElement(el, x, y) {
        var rect = el.getBoundingClientRect();
        var w = rect.width || 200;
        var h = rect.height || 60;
        var vw = window.innerWidth;
        var vh = window.innerHeight;

        var left = x;
        var top = y + 12;

        if (top + h > vh - 8) top = y - h - 12;
        if (top < 8) top = 8;
        if (left + w > vw - 8) left = vw - w - 8;
        if (left < 8) left = 8;

        el.style.left = left + "px";
        el.style.top = top + "px";
    }
})();
