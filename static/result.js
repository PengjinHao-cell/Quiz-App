/**
 * 结果页面逻辑
 * - 从 sessionStorage 读取答题结果
 * - 展示评分、逐题详情
 */

document.addEventListener("DOMContentLoaded", () => {
    // 启动画面淡出（使用 utils.js 中的共享函数）
    setTimeout(dismissSplash, 300);

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
        details: data.details || [],
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

    // 登录用户同步到服务器
    syncHistoryToServer(record);
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

// ---------- 分享为图片（按需加载 html2canvas） ----------

function saveAsImage() {
    if (!_lastResult) return;

    // 动态加载 html2canvas（不阻塞页面初始化）
    if (typeof html2canvas === "undefined") {
        const btn = document.querySelector(".result-actions .btn-primary:last-child");
        if (btn) { btn.disabled = true; btn.textContent = "⏳ 加载中..."; }

        const script = document.createElement("script");
        script.src = "https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js";
        script.onload = () => {
            if (btn) { btn.disabled = false; btn.textContent = "📸 保存为图片"; }
            _doSaveAsImage();
        };
        script.onerror = () => {
            if (btn) { btn.disabled = false; btn.textContent = "📸 保存为图片"; }
            showShareMsg("❌ 图片库加载失败，请检查网络后重试");
        };
        document.head.appendChild(script);
        return;
    }

    _doSaveAsImage();
}

function _doSaveAsImage() {
    const { data, quizMode, bankName } = _lastResult;
    const { total, correct, score } = data;

    let level, levelClass;
    if (score >= 90) { level = "优秀 🎉"; levelClass = "#38a169"; }
    else if (score >= 70) { level = "良好 👍"; levelClass = "#3182ce"; }
    else if (score >= 60) { level = "及格 💪"; levelClass = "#d69e2e"; }
    else { level = "需加强 📚"; levelClass = "#e53e3e"; }

    const modeText = quizMode === "exam" ? "考试模式" : "练习模式";

    const body = document.getElementById("share-card-body");
    body.innerHTML = `
        <div style="text-align:center;margin-bottom:16px;">
            <div style="font-size:3rem;font-weight:800;color:${levelClass};">
                ${score}<span style="font-size:1.2rem;color:#94a3b8;"> 分</span>
            </div>
            <div style="font-size:1.1rem;font-weight:600;color:#2d3748;margin-top:4px;">${level}</div>
        </div>
        <div style="background:#f7fafc;border-radius:12px;padding:16px;">
            <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
                <span style="color:#64748b;">题库</span>
                <span style="color:#2d3748;font-weight:600;">${escapeHTML(bankName || "未知")}</span>
            </div>
            <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
                <span style="color:#64748b;">模式</span>
                <span style="color:#2d3748;font-weight:600;">${modeText}</span>
            </div>
            <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
                <span style="color:#64748b;">正确</span>
                <span style="color:#2d3748;font-weight:600;">${correct} / ${total} 题</span>
            </div>
            <div style="display:flex;justify-content:space-between;">
                <span style="color:#64748b;">正确率</span>
                <span style="color:#2d3748;font-weight:600;">${total > 0 ? Math.round(correct / total * 100) : 0}%</span>
            </div>
        </div>
        <div style="margin-top:12px;background:#e2e8f0;border-radius:8px;height:10px;overflow:hidden;">
            <div style="height:100%;border-radius:8px;background:${levelClass};width:${total > 0 ? Math.round(correct / total * 100) : 0}%;transition:width 0.5s;"></div>
        </div>
    `;

    const card = document.getElementById("share-card");

    setTimeout(() => {
        html2canvas(card, {
            scale: 2,
            backgroundColor: "#ffffff",
            useCORS: true,
            logging: false,
        }).then((canvas) => {
            const link = document.createElement("a");
            link.download = `quiz-result-${Date.now()}.png`;
            link.href = canvas.toDataURL("image/png");
            link.click();
            showShareMsg("✅ 成绩图片已保存！");
        }).catch(() => {
            showShareMsg("❌ 图片生成失败，请使用复制文本分享");
        });
    }, 100);
}

