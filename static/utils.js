/**
 * 刷题通 - 全局共享工具函数
 */

/**
 * 启动画面淡出（统一函数，避免各页面重复定义）
 * 所有带 splash-screen 的页面共用此函数
 */
function dismissSplash() {
    const splash = document.getElementById("splash-screen");
    if (!splash) return;
    splash.classList.add("splash-fade-out");
    setTimeout(() => {
        splash.style.display = "none";
    }, 500);
}

/**
 * 弹窗式确认框（替代 confirm()，带样式，返回 Promise）
 * @param {string} message - 主消息
 * @param {string} [detail] - 次要说明（灰色小字）
 * @param {string} [confirmText] - 确认按钮文字，默认"确认"
 * @returns {Promise<boolean>}
 */
function showConfirmModal(message, detail, confirmText) {
    if (confirmText === undefined) confirmText = "确认";
    return new Promise((resolve) => {
        const overlay = document.createElement("div");
        overlay.style.cssText = "position:fixed;inset:0;z-index:10000;background:rgba(0,0,0,0.4);display:flex;align-items:center;justify-content:center;animation:fadeInModal 0.2s ease;";
        const modal = document.createElement("div");
        modal.style.cssText = "background:#fff;border-radius:16px;padding:28px 32px;max-width:400px;width:90%;box-shadow:0 12px 40px rgba(0,0,0,0.2);text-align:center;animation:slideUpModal 0.25s ease;";
        const detailHtml = detail ? `<p style="font-size:0.85rem;color:#a0aec0;margin-bottom:20px;">${escapeHTML(detail)}</p>` : '<div style="height:20px;"></div>';
        modal.innerHTML = `
            <div style="font-size:2rem;margin-bottom:12px;">⚠️</div>
            <p style="font-size:1rem;color:#2d3748;font-weight:600;margin-bottom:8px;">${escapeHTML(message)}</p>
            ${detailHtml}
            <div style="display:flex;gap:12px;justify-content:center;">
                <button id="modal-cancel" style="padding:10px 24px;border:2px solid #e2e8f0;border-radius:10px;background:#fff;font-size:0.9rem;font-weight:600;color:#4a5568;cursor:pointer;">取消</button>
                <button id="modal-confirm" style="padding:10px 24px;border:none;border-radius:10px;background:#e53e3e;font-size:0.9rem;font-weight:600;color:#fff;cursor:pointer;">${confirmText}</button>
            </div>
        `;
        overlay.appendChild(modal);
        document.body.appendChild(overlay);

        // 注入动画样式（仅一次）
        if (!document.getElementById("modal-style-injected")) {
            const s = document.createElement("style");
            s.id = "modal-style-injected";
            s.textContent = "@keyframes fadeInModal{from{opacity:0}to{opacity:1}}@keyframes slideUpModal{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:translateY(0)}}";
            document.head.appendChild(s);
        }

        function close(result) {
            overlay.style.opacity = "0";
            setTimeout(() => overlay.remove(), 200);
            resolve(result);
        }

        document.getElementById("modal-confirm").onclick = () => close(true);
        document.getElementById("modal-cancel").onclick = () => close(false);
        overlay.addEventListener("click", (e) => { if (e.target === overlay) close(false); });
    });
}

/**
 * 转义 HTML 特殊字符，防止 XSS
 */
function escapeHTML(str) {
    if (str === null || str === undefined) return "";
    const div = document.createElement("div");
    div.textContent = String(str);
    return div.innerHTML;
}

// ========== 错题本 (localStorage) ==========

const WRONG_BOOK_KEY = "quizWrongBook";

/** 获取全部错题 */
function getWrongBook() {
    try {
        return JSON.parse(localStorage.getItem(WRONG_BOOK_KEY)) || {};
    } catch {
        return {};
    }
}

/** 保存错题本 */
function saveWrongBook(book) {
    localStorage.setItem(WRONG_BOOK_KEY, JSON.stringify(book));
}

/** 添加一道错题（自动去重累加） */
function addToWrongBook(question, userAnswer, bankId, bankName) {
    const book = getWrongBook();
    const key = `${bankId}_${question.id}`;

    if (book[key]) {
        book[key].wrong_count += 1;
        book[key].last_wrong_time = new Date().toLocaleString("zh-CN");
        book[key].user_wrong_answer = userAnswer;
    } else {
        book[key] = {
            bank_id: bankId,
            bank_name: bankName,
            question_id: question.id,
            question_text: question.text,
            question_options: question.options,
            correct_answer: question.answer,
            user_wrong_answer: userAnswer,
            type: question.type || "single",
            wrong_count: 1,
            last_wrong_time: new Date().toLocaleString("zh-CN"),
        };
    }

    saveWrongBook(book);
    // 登录用户同步到服务器
    syncWrongBookToServer();
}

/** 从错题本移除一道题 */
function removeFromWrongBook(key) {
    const book = getWrongBook();
    delete book[key];
    saveWrongBook(book);
    // 加入删除黑名单，防止刷新后被服务器加回来
    _markDeleted("wrong", key);
    // 登录用户同步到服务器
    deleteWrongBookFromServer(key);
}

/** 按题库分组统计错题数 */
function groupWrongBook() {
    const book = getWrongBook();
    const groups = {};
    for (const key of Object.keys(book)) {
        const item = book[key];
        const gKey = item.bank_id || "__unknown__";
        if (!groups[gKey]) {
            groups[gKey] = {
                bank_id: item.bank_id,
                bank_name: item.bank_name,
                questions: [],
            };
        }
        groups[gKey].questions.push({ key, ...item });
    }
    return groups;
}

// ========== 题目收藏 (localStorage) ==========

const FAVORITE_KEY = "quizFavorites";

/** 获取全部收藏 */
function getFavorites() {
    try {
        return JSON.parse(localStorage.getItem(FAVORITE_KEY)) || {};
    } catch {
        return {};
    }
}

/** 保存收藏 */
function saveFavorites(book) {
    localStorage.setItem(FAVORITE_KEY, JSON.stringify(book));
}

/** 切换收藏状态。返回新的状态 true=已收藏 / false=未收藏 */
function toggleFavorite(question, bankId, bankName) {
    const book = getFavorites();
    const key = `${bankId}_${question.id}`;

    if (book[key]) {
        delete book[key];
        saveFavorites(book);
        // 加入删除黑名单
        _markDeleted("fav", key);
        // 登录用户同步到服务器
        deleteFavoriteFromServer(key);
        return false;
    } else {
        book[key] = {
            bank_id: bankId,
            bank_name: bankName,
            question_id: question.id,
            question_text: question.text,
            question_options: question.options,
            answer: question.answer,
            type: question.type || "single",
            added_time: new Date().toLocaleString("zh-CN"),
        };
        saveFavorites(book);
        // 登录用户同步到服务器
        syncFavoritesToServer();
        return true;
    }
}

/** 检查某题是否已收藏 */
function isFavorited(bankId, questionId) {
    const book = getFavorites();
    return !!book[`${bankId}_${questionId}`];
}

/** 按题库分组收藏 */
function groupFavorites() {
    const book = getFavorites();
    const groups = {};
    for (const key of Object.keys(book)) {
        const item = book[key];
        const gKey = item.bank_id || "__unknown__";
        if (!groups[gKey]) {
            groups[gKey] = {
                bank_id: item.bank_id,
                bank_name: item.bank_name,
                questions: [],
            };
        }
        groups[gKey].questions.push({ key, ...item });
    }
    return groups;
}

// ========== 删除黑名单（防止服务器数据回弹） ==========
// 本地删除了但服务器还没同步完的 key，刷新时不会从服务器加回来
const _DELETED_KEYS_KEY = "_deletedSyncKeys";

function _getDeletedKeys() {
    try {
        return JSON.parse(localStorage.getItem(_DELETED_KEYS_KEY)) || {};
    } catch { return {}; }
}

function _saveDeletedKeys(keys) {
    // 清理超过1小时的旧记录
    const now = Date.now();
    for (const [k, t] of Object.entries(keys)) {
        if (now - t > 3600000) delete keys[k];
    }
    localStorage.setItem(_DELETED_KEYS_KEY, JSON.stringify(keys));
}

function _markDeleted(type, key) {
    const keys = _getDeletedKeys();
    keys[`${type}:${key}`] = Date.now();
    _saveDeletedKeys(keys);
}

function _isDeleted(type, key) {
    const keys = _getDeletedKeys();
    return `${type}:${key}` in keys;
}

function _unmarkDeleted(type, key) {
    const keys = _getDeletedKeys();
    delete keys[`${type}:${key}`];
    _saveDeletedKeys(keys);
}

// ========== 云端同步（登录用户自动推送到服务器） ==========

/**
 * 检测当前用户是否已登录（由模板注入的全局变量判断）
 */
function isLoggedIn() {
    return typeof window._IS_LOGGED_IN !== "undefined" && window._IS_LOGGED_IN === true;
}

function isAdmin() {
    return typeof window._IS_ADMIN !== "undefined" && window._IS_ADMIN === true;
}

/**
 * 带 CSRF 防护头的 fetch 封装（fire-and-forget，不关心结果）
 */
function _syncFetch(url, options) {
    options.headers = options.headers || {};
    options.headers["X-Requested-By"] = "QuizApp";
    fetch(url, options).catch(() => {});
}

/**
 * 带 CSRF 防护头的 fetch（关心结果）
 */
function _syncFetchResult(url, options) {
    options.headers = options.headers || {};
    options.headers["X-Requested-By"] = "QuizApp";
    return fetch(url, options);
}

/**
 * 同步错题本到服务器
 */
/**
 * 同步错题本到服务器（带 500ms 去抖，避免连续答题时频繁全量推送）
 */
var _syncWrongBookTimer = null;
function syncWrongBookToServer() {
    if (_syncWrongBookTimer) clearTimeout(_syncWrongBookTimer);
    _syncWrongBookTimer = setTimeout(function() {
        _syncWrongBookTimer = null;
        if (!isLoggedIn()) return;
        const book = getWrongBook();
        const items = Object.entries(book).map(([key, item]) => ({
            question_key: key,
            ...item,
            question_options: JSON.stringify(item.question_options || {}),
        }));
        if (items.length === 0) return;
        _syncFetch("/api/sync/wrong-book", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ items }),
        });
    }, 500);
}

/**
 * 从服务器删除指定错题
 */
function deleteWrongBookFromServer(questionKey) {
    if (!isLoggedIn()) return;
    _syncFetchResult("/api/sync/wrong-book", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question_key: questionKey }),
    }).then(() => _unmarkDeleted("wrong", questionKey))
    .catch(() => {});
}

/**
 * 清空服务器上的全部错题
 */
function clearWrongBookOnServer() {
    if (!isLoggedIn()) return;
    _syncFetch("/api/sync/wrong-book/clear", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
    });
}

/**
 * 同步收藏到服务器
 */
function syncFavoritesToServer() {
    if (!isLoggedIn()) return;
    const book = getFavorites();
    const items = Object.entries(book).map(([key, item]) => ({
        question_key: key,
        ...item,
        question_options: JSON.stringify(item.question_options || {}),
    }));
    if (items.length === 0) return;
    _syncFetch("/api/sync/favorites", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ items }),
    });
}

/**
 * 清空服务器全部收藏
 */
function clearFavoritesOnServer() {
    if (!isLoggedIn()) return;
    _syncFetch("/api/sync/favorites/clear", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
    });
}

/**
 * 从服务器取消收藏
 */
function deleteFavoriteFromServer(questionKey) {
    if (!isLoggedIn()) return;
    _syncFetchResult("/api/sync/favorites", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question_key: questionKey }),
    }).then(() => _unmarkDeleted("fav", questionKey))
    .catch(() => {});
}

/**
 * 同步学习记录到服务器
 */
function syncHistoryToServer(record) {
    if (!isLoggedIn()) return;
    const answersJson = record.answers_json || (record.details ? JSON.stringify(record.details) : "{}");
    const item = {
        id: record.id,
        bank_id: record.bank_id || "",
        bank_name: record.bank_name || "",
        mode: record.mode || "practice",
        score: record.score || 0,
        correct: record.correct || 0,
        total: record.total || 0,
        answers_json: answersJson,
        time: record.time || new Date().toLocaleString("zh-CN", { hourCycle: "h23" }),
    };
    _syncFetch("/api/sync/history", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ items: [item] }),
    });
}

/**
 * 从服务器删除单条学习记录
 */
function deleteHistoryFromServer(recordId) {
    if (!isLoggedIn()) return;
    _syncFetchResult("/api/sync/history", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: recordId }),
    }).then(() => _unmarkDeleted("hist", recordId))
    .catch(() => {});
}

/**
 * 清空服务器全部学习记录
 */
function clearHistoryOnServer() {
    if (!isLoggedIn()) return;
    _syncFetch("/api/sync/history/clear", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
    });
}

/**
 * 从云端恢复数据到本地（跨设备数据恢复）
 * 用于新设备/重装浏览器后，将服务器备份拉回 localStorage
 * 依赖 showConfirmModal（utils.js）和 showToast（各页面自行定义）
 */
async function restoreFromServer() {
    if (!isLoggedIn()) {
        if (typeof showToast === "function") showToast(
            (typeof USER_LANG !== "undefined" && USER_LANG === "en") ? "Please log in first" : "请先登录", "error"
        );
        return false;
    }

    try {
        const res = await _syncFetchResult("/api/sync/all", { method: "GET" });
        if (!res.ok) {
            if (typeof showToast === "function") showToast(
                (typeof USER_LANG !== "undefined" && USER_LANG === "en") ? "Failed to fetch cloud data" : "获取云端数据失败", "error"
            );
            return false;
        }

        const data = await res.json();
        const wbCount = Object.keys(data.wrong_book || {}).length;
        const favCount = Object.keys(data.favorites || {}).length;
        const histCount = (data.history || []).length;

        if (wbCount === 0 && favCount === 0 && histCount === 0) {
            if (typeof showToast === "function") showToast(
                (typeof USER_LANG !== "undefined" && USER_LANG === "en") ? "No cloud data to restore" : "云端没有可恢复的数据", "info"
            );
            return false;
        }

        // 确认弹窗
        const _lang = (typeof USER_LANG !== "undefined" && USER_LANG === "en") ? "en" : "zh";
        const confirmMsg = _lang === "en"
            ? "Restore from cloud?"
            : "从云端恢复数据？";
        const confirmDetail = _lang === "en"
            ? `This will merge ${wbCount} wrong answers, ${favCount} favorites, ${histCount} records into this device.\nLocal items with the same key will be overwritten.`
            : `将从云端合并 ${wbCount} 道错题、${favCount} 个收藏、${histCount} 条记录到当前设备。\n本地的同名数据将被覆盖。`;

        const confirmed = await showConfirmModal(confirmMsg, confirmDetail);
        if (!confirmed) return false;

        // ----- 恢复错题本 -----
        if (wbCount > 0) {
            const localBook = getWrongBook();
            for (const [key, item] of Object.entries(data.wrong_book)) {
                let options = item.question_options || "{}";
                if (typeof options === "string") {
                    try { options = JSON.parse(options); } catch { options = {}; }
                }
                localBook[key] = {
                    bank_id: item.bank_id || "",
                    bank_name: item.bank_name || "",
                    question_id: item.question_id || "",
                    question_text: item.question_text || "",
                    question_options: options,
                    correct_answer: item.correct_answer || "",
                    user_wrong_answer: item.user_wrong_answer || "",
                    type: item.type || "single",
                    wrong_count: item.wrong_count || 1,
                    last_wrong_time: item.last_wrong_time || "",
                };
            }
            saveWrongBook(localBook);
        }

        // ----- 恢复收藏 -----
        if (favCount > 0) {
            const localFavs = getFavorites();
            for (const [key, item] of Object.entries(data.favorites)) {
                let options = item.question_options || "{}";
                if (typeof options === "string") {
                    try { options = JSON.parse(options); } catch { options = {}; }
                }
                localFavs[key] = {
                    bank_id: item.bank_id || "",
                    bank_name: item.bank_name || "",
                    question_id: item.question_id || "",
                    question_text: item.question_text || "",
                    question_options: options,
                    answer: item.answer || "",
                    type: item.type || "single",
                    added_time: item.added_time || "",
                };
            }
            saveFavorites(localFavs);
        }

        // ----- 恢复学习记录 -----
        if (histCount > 0) {
            let localHistory = [];
            try { localHistory = JSON.parse(localStorage.getItem("quizHistory") || "[]"); } catch { localHistory = []; }
            const existingIds = new Set(localHistory.map(h => h.id).filter(Boolean));
            // 额外去重：用 (bank_id + time) 组合防止 ID 生成算法不一致导致的重复
            const existingSignatures = new Set(
                localHistory.map(h => (h.bank_id || "") + "|" + (h.time || "")).filter(s => s !== "|")
            );

            for (const record of data.history) {
                const rid = record.record_id || record.id || "";
                const sig = (record.bank_id || "") + "|" + (record.time_label || "");
                if (!rid || existingIds.has(rid) || existingSignatures.has(sig)) continue;
                localHistory.push({
                    id: rid,
                    bank_id: record.bank_id || "",
                    bank_name: record.bank_name || "",
                    mode: record.mode || "practice",
                    score: record.score || 0,
                    correct: record.correct || 0,
                    total: record.total || 0,
                    details: record.answers_json || "{}",
                    time: record.time_label || "",
                });
                existingIds.add(rid);
            }

            // 按时间倒序排列，上限 200 条
            localHistory.sort((a, b) => (b.time || "").localeCompare(a.time || ""));
            if (localHistory.length > 200) localHistory.length = 200;
            localStorage.setItem("quizHistory", JSON.stringify(localHistory));
        }

        if (typeof showToast === "function") showToast(
            _lang === "en"
                ? `✅ Restored: ${wbCount} wrong, ${favCount} favorites, ${histCount} records`
                : `✅ 恢复完成：${wbCount} 道错题、${favCount} 个收藏、${histCount} 条记录`,
            "success"
        );
        return true;
    } catch (e) {
        if (typeof showToast === "function") showToast(
            (typeof USER_LANG !== "undefined" && USER_LANG === "en") ? "Restore failed" : "恢复失败", "error"
        );
        return false;
    }
}

// ========== 统一操作入口（本地 + 服务器同步） ==========

/**
 * 删除单条收藏（本地 + 服务器同步）
 * 对应的渲染侧 deleteFavoriteItem(key) 只负责 UI 动画，数据操作委托给此函数
 */
function removeFavoriteItem(key) {
    const book = getFavorites();
    delete book[key];
    saveFavorites(book);
    _markDeleted("fav", key);
    deleteFavoriteFromServer(key);
}

/**
 * 删除单条学习记录（本地 + 服务器同步）
 * 对应的渲染侧 deleteHistoryItem(id) 只负责 UI 动画，数据操作委托给此函数
 */
function removeHistoryItem(id) {
    let history = [];
    try { history = JSON.parse(localStorage.getItem("quizHistory") || "[]"); } catch { history = []; }
    const idx = history.findIndex(h => (h.id || '') === id);
    if (idx !== -1) {
        history.splice(idx, 1);
        localStorage.setItem("quizHistory", JSON.stringify(history));
        _markDeleted("hist", id);
        deleteHistoryFromServer(id);
    }
}

/**
 * 清空全部收藏（本地 + 服务器同步）
 */
function clearAllFavoritesLocal() {
    localStorage.removeItem(FAVORITE_KEY);
    clearFavoritesOnServer();
}

/**
 * 清空全部错题（本地 + 服务器同步）
 */
function clearAllWrongBookLocal() {
    localStorage.removeItem(WRONG_BOOK_KEY);
    clearWrongBookOnServer();
}

/**
 * 清空全部学习记录（本地 + 服务器同步）
 */
function clearAllHistoryLocal() {
    localStorage.removeItem("quizHistory");
    clearHistoryOnServer();
}

// ========== 用户切换检测 ==========

const _QUIZ_DATA_KEYS = ["quizWrongBook", "quizFavorites", "quizHistory", "quizWrongBookDeletedKeys"];

/**
 * 清空当前设备上所有答题相关 localStorage 数据
 * 用于用户切换时防止数据残留
 */
function clearLocalQuizData() {
    _QUIZ_DATA_KEYS.forEach(function(k) { localStorage.removeItem(k); });
}

/**
 * 登录/注册成功后调用，检测用户是否切换，必要时清空旧数据
 * @param {string} username - 当前登录用户名
 */
function onUserLogin(username) {
    var prevUser = localStorage.getItem("quizLastUser");
    if (prevUser !== username) {
        clearLocalQuizData();
    }
    localStorage.setItem("quizLastUser", username);
}

// ========== 模态框工具 ==========

// ========== 学习统计计算（app.js 和 user.html 共用） ==========

function computeStats(history) {
    if (!history || history.length === 0) return null;

    var totalSessions = history.length;
    var totalQuestions = history.reduce(function(s, r) { return s + (r.total || 0); }, 0);
    var totalCorrect = history.reduce(function(s, r) { return s + (r.correct || 0); }, 0);
    var overallAccuracy = totalQuestions > 0 ? Math.round(totalCorrect / totalQuestions * 100) : 0;

    // 按题库统计
    var bankStats = {};
    history.forEach(function(r) {
        var key = r.bank_id || "__unknown__";
        if (!bankStats[key]) bankStats[key] = { name: r.bank_name || "未知", total: 0, correct: 0, sessions: 0 };
        bankStats[key].total += r.total || 0;
        bankStats[key].correct += r.correct || 0;
        bankStats[key].sessions += 1;
    });

    // 按模式统计
    var modeStats = { practice: { total: 0, correct: 0 }, exam: { total: 0, correct: 0 } };
    history.forEach(function(r) {
        var m = r.mode === "exam" ? "exam" : "practice";
        modeStats[m].total += r.total || 0;
        modeStats[m].correct += r.correct || 0;
    });

    // 最近10次得分
    var recent = history.slice(0, 10).reverse();

    // 7日活跃
    function fmtDate(d) {
        return d.getFullYear() + '-' + String(d.getMonth()+1).padStart(2,'0') + '-' + String(d.getDate()).padStart(2,'0');
    }
    var dayMap = {};
    var now = new Date();
    for (var i = 6; i >= 0; i--) {
        var d = new Date(now);
        d.setDate(d.getDate() - i);
        dayMap[fmtDate(d)] = 0;
    }
    history.forEach(function(r) {
        try {
            var parts = (r.time || "").split(" ")[0].split(/[\/\-]/);
            if (parts.length === 3) {
                var key = parts[0] + '-' + String(parseInt(parts[1])).padStart(2,'0') + '-' + String(parseInt(parts[2])).padStart(2,'0');
                if (dayMap[key] !== undefined) dayMap[key] += r.total || 0;
            }
        } catch (_) {}
    });

    return {
        totalSessions: totalSessions,
        totalQuestions: totalQuestions,
        totalCorrect: totalCorrect,
        overallAccuracy: overallAccuracy,
        bankStats: bankStats,
        modeStats: modeStats,
        recent: recent,
        dayMap: dayMap,
    };
}


function _createModal(html) {
    const overlay = document.createElement("div");
    overlay.style.cssText = "position:fixed;inset:0;z-index:10000;background:rgba(0,0,0,0.4);display:flex;align-items:center;justify-content:center;animation:fadeInModal 0.2s ease;";
    const box = document.createElement("div");
    box.style.cssText = "background:#fff;border-radius:16px;padding:28px 32px;max-width:420px;width:90%;box-shadow:0 12px 40px rgba(0,0,0,0.2);animation:slideUpModal 0.25s ease;";
    box.innerHTML = html;
    overlay.appendChild(box);
    document.body.appendChild(overlay);
    if (!document.getElementById("modal-style-inj")) {
        const s = document.createElement("style"); s.id = "modal-style-inj";
        s.textContent = "@keyframes fadeInModal{from{opacity:0}to{opacity:1}}@keyframes slideUpModal{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:translateY(0)}}";
        document.head.appendChild(s);
    }
    overlay.addEventListener("click", e => { if (e.target === overlay) _closeModal(overlay); });
    return overlay;
}
function _closeModal(el) { el.style.opacity = "0"; setTimeout(() => el.remove(), 200); }

// ========== 数据备份到本地 ==========

/**
 * 一键备份：收集所有 localStorage + 服务器同步数据，保存到 localStorage 并触发 JSON 下载。
 * 可在首页公告栏和用户中心侧边栏两处调用。
 */
function backupAndDownload(evt) {
    var btn = evt ? evt.target : document.querySelector(".backup-btn");
    if (btn) { btn.disabled = true; btn.textContent = "⏳ 备份中..."; }

    var localData = {
        quizHistory: JSON.parse(localStorage.getItem("quizHistory") || "[]"),
        quizFavorites: JSON.parse(localStorage.getItem("quizFavorites") || "{}"),
        quizWrongBook: JSON.parse(localStorage.getItem("quizWrongBook") || "{}"),
        vocabBook: (function(){
            try { return JSON.parse(localStorage.getItem("vocabBook") || "{}"); } catch(_) { return {}; }
        })(),
        quizSettings: {
            examDuration: localStorage.getItem("examDuration") || "60",
            quizLastUser: localStorage.getItem("quizLastUser") || "",
        },
    };

    var backup = {
        exportedAt: new Date().toISOString(),
        version: "1.5.0",
        local: localData,
        server: null,
    };

    function finishBackup(data) {
        localStorage.setItem("quizBackup", JSON.stringify(data));
        var blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
        var url = URL.createObjectURL(blob);
        var a = document.createElement("a");
        a.href = url;
        a.download = "quizmaster_backup_" + new Date().toISOString().slice(0, 10) + ".json";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        if (btn) { btn.textContent = "✅ 已备份"; btn.classList.add("done"); btn.disabled = true; }
        if (typeof showToast === "function") {
            showToast("✅ 数据已备份到本地并下载！", "success");
        }
    }

    if (isLoggedIn()) {
        _syncFetchResult("/api/sync/all", { method: "GET" })
            .then(function(res) { return res.json(); })
            .then(function(serverData) {
                backup.server = serverData;
                finishBackup(backup);
            })
            .catch(function() {
                finishBackup(backup);
            });
    } else {
        finishBackup(backup);
    }
}

/**
 * 管理员：全量导出所有用户数据
 * 弹出密码输入框，验证后跳转到导出 API
 */
function adminExportAll(evt) {
    var btn = evt ? evt.target : document.querySelector(".backup-btn[style*='#d97706']");
    var pwd = prompt("请输入管理员密码以导出全部用户数据：");
    if (!pwd) return;
    if (btn) { btn.textContent = "⏳ 导出中..."; btn.disabled = true; }
    // 直接跳转到导出 API，浏览器自动下载 JSON 文件
    window.location.href = "/api/admin/export?key=" + encodeURIComponent(pwd);
}


