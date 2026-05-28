/**
 * 阅读理解页面交互逻辑
 * - 左栏显示文章，右栏显示题目
 * - 切换题目时左栏不动，右栏切换
 * - 先做答案，最后统一评判
 * - 题号旁有上一题/下一题按钮
 */

let passages = [];
let currentPassageIdx = 0;
let currentQuestionIdx = 0;
let userAnswers = {};
let submitted = false;

document.addEventListener("DOMContentLoaded", () => {
    if (typeof READING_CONFIG === "undefined") {
        document.getElementById("question-container").innerHTML =
            '<div class="loading">配置加载失败</div>';
        return;
    }
    loadReading();
});

function loadReading() {
    fetch(`/api/reading/${READING_CONFIG.bankId}`)
        .then(res => {
            if (!res.ok) throw new Error("加载失败");
            return res.json();
        })
        .then(data => {
            passages = data.passages;
            if (!passages || passages.length === 0) {
                document.getElementById("question-container").innerHTML =
                    '<div class="loading">没有阅读材料</div>';
                return;
            }
            userAnswers = {};
            passages.forEach(p => {
                p.questions.forEach(q => {
                    userAnswers[getQKey(p.id, q.id)] = "";
                });
            });
            submitted = false;
            showPassage(0);
        })
        .catch(err => {
            document.getElementById("reading-passage").innerHTML =
                `<div class="loading">加载失败：${err.message}</div>`;
        });
}

function getQKey(passageId, questionId) {
    return `${passageId}_${questionId}`;
}

function showPassage(pIdx) {
    currentPassageIdx = pIdx;
    currentQuestionIdx = 0;
    const p = passages[pIdx];

    // 左栏：文章
    document.getElementById("reading-passage").innerHTML = `
        <h2>${escapeHTML(p.title || "阅读材料")}</h2>
        ${p.text.split("\n").filter(Boolean).map(para => `<p>${escapeHTML(para)}</p>`).join("")}
    `;

    // 题号导航圆点
    renderQuestionNav(pIdx);
    // 渲染第一题
    showQuestion(0);
}

function renderQuestionNav(pIdx) {
    const nav = document.getElementById("reading-nav");
    const p = passages[pIdx];
    let html = `<span class="passage-title">📖 第 ${pIdx + 1} 篇</span>`;
    p.questions.forEach((q, qi) => {
        const key = getQKey(p.id, q.id);
        let cls = "reading-dot";
        if (qi === currentQuestionIdx) cls += " current";
        if (userAnswers[key] !== "") cls += " answered";
        if (submitted) {
            const correct = userAnswers[key] === q.answer;
            cls += correct ? " correct" : " wrong";
        }
        html += `<span class="${cls}" onclick="goToQuestion(${qi})" title="第${qi + 1}题"></span>`;
    });
    nav.innerHTML = html;
}

function goToQuestion(qi) {
    if (qi < 0 || qi >= passages[currentPassageIdx].questions.length) return;
    currentQuestionIdx = qi;
    showQuestion(qi);
    renderQuestionNav(currentPassageIdx);
    renderAnswerSheet();
}

function showQuestion(qi) {
    const p = passages[currentPassageIdx];
    const q = p.questions[qi];
    if (!q) return;

    const container = document.getElementById("question-container");
    const currentAnswer = userAnswers[getQKey(p.id, q.id)] || "";
    const qtype = q.type || "single";
    const total = p.questions.length;

    // 题型标签
    let typeLabel = qtype === "multi" ? "多选题" : qtype === "judge" ? "判断题" : "单选题";

    // 选项
    const opts = Object.entries(q.options);
    let optsHTML = opts.map(([letter, text]) => {
        const selected = currentAnswer === letter ? "selected" : "";
        const checked = currentAnswer === letter ? "checked" : "";
        // 评判后高亮正确/错误
        let extraCls = "";
        if (submitted) {
            if (letter === q.answer) extraCls = " correct-show";
            else if (letter === currentAnswer && currentAnswer !== q.answer) extraCls = " wrong-show";
        }
        return `
            <li class="option-item ${selected}${extraCls}"
                onclick="selectReadingOption('${getQKey(p.id, q.id)}', '${letter}')">
                <input type="radio" name="rq-${q.id}" value="${letter}"
                       class="option-input" ${checked} ${submitted ? "disabled" : ""}>
                <span class="option-label">${letter}.</span>
                <span class="option-text">${escapeHTML(text)}</span>
            </li>
        `;
    }).join("");

    // 评判后显示提示
    let hintHTML = "";
    if (submitted && currentAnswer) {
        const isCorrect = currentAnswer === q.answer;
        hintHTML = `
            <div class="practice-hint ${isCorrect ? "correct" : "wrong"}">
                ${isCorrect ? "✅ 回答正确！" : `❌ 回答错误！正确答案是 <strong>${q.options[q.answer] || q.answer}</strong>`}
            </div>
        `;
    } else if (submitted && !currentAnswer) {
        hintHTML = `
            <div class="practice-hint wrong">
                ⚠️ 未作答！正确答案是 <strong>${q.options[q.answer] || q.answer}</strong>
            </div>
        `;
    }

    // 上一题/下一题按钮
    const prevDisabled = qi <= 0 ? "disabled" : "";
    const nextDisabled = qi >= total - 1 ? "disabled" : "";

    container.innerHTML = `
        <div class="question-card">
            <div class="question-number">
                <span class="question-type-badge single">${typeLabel}</span>
                第 ${qi + 1} / ${total} 题
                <span style="margin-left:auto;display:flex;gap:6px;">
                    <button class="btn btn-secondary btn-sm" ${prevDisabled}
                            onclick="goToQuestion(${qi - 1})" style="padding:4px 10px;font-size:0.8rem;">◀</button>
                    <button class="btn btn-secondary btn-sm" ${nextDisabled}
                            onclick="goToQuestion(${qi + 1})" style="padding:4px 10px;font-size:0.8rem;">▶</button>
                </span>
            </div>
            <div class="question-text">${escapeHTML(q.text)}</div>
            <ul class="options-list">${optsHTML}</ul>
            ${hintHTML}
        </div>
    `;

    updateReadingProgress();
    renderAnswerSheet();
}

function selectReadingOption(key, letter) {
    if (submitted) return;
    userAnswers[key] = letter;
    showQuestion(currentQuestionIdx);
    renderQuestionNav(currentPassageIdx);
    renderAnswerSheet();
    // 自动跳到下一题（最后一题不跳）
    if (currentQuestionIdx < passages[currentPassageIdx].questions.length - 1) {
        setTimeout(() => goToQuestion(currentQuestionIdx + 1), 200);
    }
}

function submitReading() {
    if (submitted) return;
    const totalQ = passages.reduce((sum, p) => sum + p.questions.length, 0);
    const answered = Object.values(userAnswers).filter(a => a !== "").length;
    if (answered < totalQ && !confirm(`还有 ${totalQ - answered} 题未作答，确定提交评判吗？`)) {
        return;
    }
    submitted = true;
    // 禁用选项点击 + 显示评判结果
    renderQuestionNav(currentPassageIdx);
    showQuestion(currentQuestionIdx);
    renderAnswerSheet();
    // 更新提交按钮文字
    const submitBtn = document.getElementById("btn-submit-reading");
    if (submitBtn) {
        submitBtn.textContent = "✅ 已评判";
        submitBtn.disabled = true;
    }
}

function updateReadingProgress() {
    const totalQ = passages.reduce((sum, p) => sum + p.questions.length, 0);
    const answered = Object.values(userAnswers).filter(a => a !== "").length;
    document.getElementById("reading-passage-progress").textContent = `第 ${currentPassageIdx + 1} / ${passages.length} 篇`;
    document.getElementById("reading-progress").textContent = `${answered} / ${totalQ} 题`;
}

function renderAnswerSheet() {
    const grid = document.getElementById("reading-sheet-grid");
    if (!grid) return;
    let html = "";
    let idx = 0;
    passages.forEach((p, pi) => {
        p.questions.forEach((q, qi) => {
            idx++;
            const key = getQKey(p.id, q.id);
            const isCurrent = pi === currentPassageIdx && qi === currentQuestionIdx;
            const isAnswered = userAnswers[key] !== "";
            let cls = "sheet-num";
            if (isCurrent) cls += " current";
            if (isAnswered && !submitted) cls += " answered";
            if (submitted) {
                const correct = userAnswers[key] === q.answer;
                cls += correct ? " correct" : " wrong";
            }
            html += `<span class="${cls}" onclick="goToQuestionByGlobalIdx(${idx - 1})">${idx}</span>`;
        });
    });
    grid.innerHTML = html;

    const totalQ = passages.reduce((sum, p) => sum + p.questions.length, 0);
    const answered = Object.values(userAnswers).filter(a => a !== "").length;
    document.getElementById("reading-passage-progress").textContent = `第 ${currentPassageIdx + 1} / ${passages.length} 篇`;
    document.getElementById("reading-progress").textContent = `${answered} / ${totalQ} 题`;
    document.getElementById("answer-sheet").classList.remove("hidden");
}

function goToQuestionByGlobalIdx(gIdx) {
    let idx = 0;
    for (let pi = 0; pi < passages.length; pi++) {
        for (let qi = 0; qi < passages[pi].questions.length; qi++) {
            if (idx === gIdx) {
                if (pi !== currentPassageIdx) {
                    showPassage(pi);
                }
                goToQuestion(qi);
                return;
            }
            idx++;
        }
    }
}
