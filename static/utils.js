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
 * @returns {Promise<boolean>}
 */
function showConfirmModal(message, detail) {
    return new Promise((resolve) => {
        // 创建遮罩+弹窗
        const overlay = document.createElement("div");
        overlay.style.cssText = "position:fixed;inset:0;z-index:10000;background:rgba(0,0,0,0.4);display:flex;align-items:center;justify-content:center;animation:fadeInModal 0.2s ease;";
        const modal = document.createElement("div");
        modal.style.cssText = "background:#fff;border-radius:16px;padding:28px 32px;max-width:400px;width:90%;box-shadow:0 12px 40px rgba(0,0,0,0.2);text-align:center;animation:slideUpModal 0.25s ease;";
        modal.innerHTML = `
            <div style="font-size:2rem;margin-bottom:12px;">⚠️</div>
            <p style="font-size:1rem;color:#2d3748;font-weight:600;margin-bottom:8px;">${escapeHTML(message)}</p>
            ${detail ? `<p style="font-size:0.85rem;color:#a0aec0;margin-bottom:20px;">${escapeHTML(detail)}</p>` : '<div style="height:20px;"></div>'}
            <div style="display:flex;gap:12px;justify-content:center;">
                <button id="modal-cancel" style="padding:10px 24px;border:2px solid #e2e8f0;border-radius:10px;background:#fff;font-size:0.9rem;font-weight:600;color:#4a5568;cursor:pointer;">取消</button>
                <button id="modal-confirm" style="padding:10px 24px;border:none;border-radius:10px;background:#e53e3e;font-size:0.9rem;font-weight:600;color:#fff;cursor:pointer;">确认</button>
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
function syncWrongBookToServer() {
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
