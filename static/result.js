/**
 * 结果页面逻辑
 * - 从 sessionStorage 读取答题结果
 * - 展示评分、逐题详情
 */

document.addEventListener("DOMContentLoaded", () => {
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
        renderResult(data, quizMode, bankName);
    } catch (e) {
        document.getElementById("result-summary").innerHTML = `
            <div class="error-message">
                <p>结果数据解析失败。</p>
            </div>
        `;
    }
});

function renderResult(data, quizMode, bankName) {
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

        const optionsHTML = Object.entries(options)
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
                    你的答案：<span class="user-ans">${user_answer || "未作答"}</span>
                    &nbsp;|&nbsp;
                    正确答案：<span class="correct-ans">${correct_answer || "无"}</span>
                </div>
            </div>
        `;
    });

    detailsContainer.innerHTML = html;
}

function escapeHTML(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}