/**
 * 结果页面逻辑
 * - 从 sessionStorage 读取答题结果
 * - 展示评分、逐题详情
 */

document.addEventListener("DOMContentLoaded", () => {
    // 启动画面淡出
    setTimeout(() => {
        const splash = document.getElementById("splash-screen");
        if (splash) {
            splash.classList.add("splash-fade-out");
            setTimeout(() => { splash.style.display = "none"; }, 500);
        }
    }, 300);

    // 从 sessionStorage 读取结果
    const resultStr = sessionStorage.getItem("quizResult");
    const quizMode = sessionStorage.getItem("quizMode") || "practice";
    const bankName = sessionStorage.getItem("quizBankName") || "";

    if (!resultStr) {
        document.getElementById("result-summary").innerHTML = `
            <div class="error-message">
                <p>没有找到答题结果数据。</p>
                <p>请返回刷题页面重新提交。</p>
            </div>
        `;
        return;
    }

    try {
        const data = JSON.parse(resultStr);
        saveToHistory(data, quizMode, bankName);
        renderResult(data, quizMode, bankName);
    } catch (e) {
        document.getElementById("result-summary").innerHTML = `
            <div class="error-message">
                <p>结果数据解析失败。</p>
            </div>
        `;
    }
});

function saveToHistory(data, quizMode, bankName) {
    const bankId = sessionStorage.getItem("quizBankId") || "";
    const record = {
        id: Date.now().toString(36) + Math.random().toString(36).slice(2, 6),
        bank_id: bankId,
        bank_name: bankName || "未知题库",
        mode: quizMode,
        score: data.score,
        correct: data.correct,
        total: data.total,
        time: new Date().toLocaleString("zh-CN", { hourCycle: "h23" }),
    };

    let history = [];
    try {
        const raw = localStorage.getItem("quizHistory");
        history = raw ? JSON.parse(raw) : [];
    } catch (_) {
        history = [];
    }

    history.unshift(record);
    // 最多保留 50 条
    if (history.length > 50) {
        history = history.slice(0, 50);
    }

    localStorage.setItem("quizHistory", JSON.stringify(history));
}

// 存储当前结果供分享使用
let _lastResult = null;

function renderResult(data, quizMode, bankName) {
    _lastResult = { data, quizMode, bankName };
    const { total, correct, score, details } = data;

    // ---------- 评分等级 ----------
    let level, levelClass;
    if (score >= 90) {
        level = "优秀 🎉";
        levelClass = "excellent";
    } else if (score >= 70) {
        level = "良好 👍";
        levelClass = "good";
    } else if (score >= 60) {
        level = "及格 💪";
        levelClass = "fair";
    } else {
        level = "需加强 📚";
        levelClass = "poor";
    }

    // ---------- 顶部摘要 ----------
    document.getElementById("result-summary").innerHTML = `
        <div class="result-score ${levelClass}">${score}分</div>
        <div class="result-meta">
            共 <strong>${total}</strong> 题 |
            答对 <strong>${correct}</strong> 题 |
            答错 <strong>${total - correct}</strong> 题
        </div>
        <div class="result-meta" style="margin-bottom: 12px;">
            等级：<strong>${level}</strong>
        </div>
        <div class="result-bar-bg">
            <div class="result-bar-fill ${levelClass}"
                 style="width: ${score}%"></div>
        </div>
        ${bankName ? `<div class="result-meta">题库：${escapeHTML(bankName)}</div>` : ""}
        <div class="result-meta">模式：${quizMode === "exam" ? "考试模式" : "练习模式"}</div>
    `;

    document.getElementById("result-summary").classList.remove("loading");

    // ---------- 逐题详情 ----------
    const detailsContainer = document.getElementById("result-details");
    let html = "";

    details.forEach((detail, idx) => {
        const { id, text, options, user_answer, correct_answer, is_correct } = detail;
        const cardClass = is_correct ? "correct" : "wrong";
        const headerIcon = is_correct
            ? '<span class="correct-icon">✅ 正确</span>'
            : '<span class="wrong-icon">❌ 错误</span>';

        // 填空题：无选项，直接显示答案
        const isFill = !options || Object.keys(options).length === 0;
        const optionsHTML = isFill
            ? ""
            : Object.entries(options)
                .map(([letter, optText]) => {
                    let cls = "";
                    if (letter === correct_answer) cls = "correct-show";
                    if (letter === user_answer && !is_correct) cls = "wrong-show";
                    return `<span class="${cls}" style="margin-right: 12px;">${letter}. ${escapeHTML(optText)}</span>`;
                })
                .join("<br>");

        html += `
            <div class="detail-card ${cardClass}">
                <div class="detail-header">
                    <span>第 ${idx + 1} 题</span>
                    ${headerIcon}
                </div>
                <div class="detail-question">${escapeHTML(text)}</div>
                <div class="detail-options">${optionsHTML}</div>
                <div class="detail-answers" style="margin-top: 8px;">
                    你的答案：<span class="${is_correct ? 'correct-ans' : 'user-ans'}">${user_answer || "未作答"}</span>
                    &nbsp;|&nbsp;
                    正确答案：<span class="correct-ans">${(correct_answer || "").split("").map(function(l){ return options[l] || l; }).filter(Boolean).join("；") || "无"}</span>
                </div>
            </div>
        `;
    });

    detailsContainer.innerHTML = html;
}

// ---------- 分享/导出 ----------

function buildShareText() {
    if (!_lastResult) return "";
    const { data, quizMode, bankName } = _lastResult;
    const { total, correct, score } = data;

    let level;
    if (score >= 90) level = "优秀 🎉";
    else if (score >= 70) level = "良好 👍";
    else if (score >= 60) level = "及格 💪";
    else level = "需加强 📚";

    const modeText = quizMode === "exam" ? "考试模式" : "练习模式";

    return [
        "📝 刷题通 - 答题结果",
        "━━━━━━━━━━━━━━━━━",
        `题库：${bankName || "未知"}`,
        `模式：${modeText}`,
        `得分：${score} 分  (${level})`,
        `正确：${correct} / ${total} 题`,
        `正确率：${total > 0 ? Math.round(correct / total * 100) : 0}%`,
        "━━━━━━━━━━━━━━━━━",
        "via 刷题通",
    ].join("\n");
}

function copyResult() {
    const text = buildShareText();
    if (!text) return;

    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(() => {
            showShareMsg("✅ 成绩已复制到剪贴板，快去分享吧！");
        }).catch(() => {
            fallbackCopy(text);
        });
    } else {
        fallbackCopy(text);
    }
}

function fallbackCopy(text) {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    try {
        document.execCommand("copy");
        showShareMsg("✅ 成绩已复制到剪贴板！");
    } catch (_) {
        showShareMsg("❌ 复制失败，请手动选取文本复制");
    }
    document.body.removeChild(ta);
}

function showShareMsg(msg) {
    const el = document.getElementById("share-msg");
    if (!el) return;
    el.textContent = msg;
    el.className = "msg success";
    el.style.display = "block";
    setTimeout(() => {
        el.style.display = "none";
    }, 3000);
}

