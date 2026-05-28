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
}

/** 从错题本移除一道题 */
function removeFromWrongBook(key) {
    const book = getWrongBook();
    delete book[key];
    saveWrongBook(book);
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
