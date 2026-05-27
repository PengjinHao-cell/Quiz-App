/**
 * 刷题页面交互逻辑
 * - 加载题目
 * - 选项选择
 * - 上一题 / 下一题导航
 * - 练习模式即时反馈
 * - 考试模式：选择后自动前进 + 交卷提交
 * - 答题卡侧边栏
 */

let questions = [];
let userAnswers = {};   // { questionId: "A" }
let currentIndex = 0;
let config = {};

// ---------- 初始化 ----------

document.addEventListener("DOMContentLoaded", () => {
    if (typeof QUIZ_CONFIG === "undefined") {
        document.getElementById("question-container").innerHTML =
            '<div class="loading">配置加载失败，请返回首页重试</div>';
        return;
    }

    config = QUIZ_CONFIG;
    loadQuestions();
    initAnswerSheet();
});

// ---------- 加载题目 ----------

function loadQuestions() {
    fetch(`/api/bank/${config.bankId}/questions?mode=${config.mode}&count=${config.count || 0}`)
        .then((res) => {
            if (!res.ok) throw new Error("加载题目失败");
            return res.json();
        })
        .then((data) => {
            questions = data.questions;
            if (!questions || questions.length === 0) {
                document.getElementById("question-container").innerHTML =
                    '<div class="loading">题库中没有题目</div>';
                return;
            }

            // 初始化用户答案
            userAnswers = {};
            questions.forEach((q) => {
                userAnswers[q.id] = "";
            });

            // 显示导航栏
            document.getElementById("quiz-navigation").classList.remove("hidden");

            // 如果是考试模式，显示交卷按钮
            if (config.mode === "exam") {
                document.getElementById("btn-submit").classList.remove("hidden");
            }

            // 渲染第一题
            showQuestion(0);

            // 渲染答题卡
            renderAnswerSheet();
            document.getElementById("answer-sheet").classList.remove("hidden");
        })
        .catch((err) => {
            document.getElementById("question-container").innerHTML =
                `<div class="loading">加载失败：${err.message}</div>`;
        });
}

// ---------- 渲染题目 ----------

function showQuestion(index) {
    if (index < 0 || index >= questions.length) return;

    currentIndex = index;
    const q = questions[index];

    const container = document.getElementById("question-container");
    const options = Object.entries(q.options);

    // 生成选项 HTML
    const optionsHTML = options
        .map(([letter, text]) => {
            const checked = userAnswers[q.id] === letter ? "checked" : "";
            const selectedClass = userAnswers[q.id] === letter ? "selected" : "";
            return `
                <li class="option-item ${selectedClass}"
                    onclick="selectOption(${q.id}, '${letter}')">
                    <input type="radio" name="q-${q.id}" value="${letter}"
                           class="option-radio" ${checked}
                           onclick="event.stopPropagation(); selectOption(${q.id}, '${letter}')">
                    <span class="option-label">${letter}.</span>
                    <span class="option-text">${escapeHTML(text)}</span>
                </li>
            `;
        })
        .join("");

    // 练习模式：选择后显示正确答案提示
    let hintHTML = "";
    if (config.mode === "practice" && userAnswers[q.id]) {
        const isCorrect = userAnswers[q.id] === q.answer;
        hintHTML = `
            <div class="practice-hint ${isCorrect ? "correct" : "wrong"}">
                ${isCorrect
                    ? "✅ 回答正确！"
                    : `❌ 回答错误！正确答案是 <strong>${q.answer}</strong>`}
            </div>
        `;
    }

    container.innerHTML = `
        <div class="question-card">
            <div class="question-number">第 ${index + 1} / ${questions.length} 题</div>
            <div class="question-text">${escapeHTML(q.text)}</div>
            <ul class="options-list">
                ${optionsHTML}
            </ul>
            ${hintHTML}
        </div>
    `;

    // 更新导航状态
    updateNavigation();

    // 更新进度
    updateProgress();

    // 更新答题卡高亮
    updateSheetHighlight();
}

// ---------- 选择选项 ----------

function selectOption(questionId, letter) {
    userAnswers[questionId] = letter;

    // 练习模式：立即刷新显示答案反馈
    if (config.mode === "practice") {
        showQuestion(currentIndex);
    } else {
        // 考试模式：仅更新选中样式
        const items = document.querySelectorAll(".option-item");
        items.forEach((item) => {
            const radio = item.querySelector("input[type='radio']");
            if (radio && radio.value === letter) {
                item.classList.add("selected");
            } else {
                item.classList.remove("selected");
            }
        });
        updateProgress();

        // 考试模式：选择后自动跳到下一题
        const nextIndex = currentIndex + 1;
        if (nextIndex < questions.length) {
            setTimeout(() => {
                showQuestion(nextIndex);
            }, 300);
        } else {
            // 最后一题已答完，高亮交卷按钮
            const submitBtn = document.getElementById("btn-submit");
            if (submitBtn) {
                submitBtn.style.animation = "pulse 0.8s ease 3";
            }
        }
    }

    // 更新答题卡
    renderAnswerSheet();
    updateSheetHighlight();
}

// ---------- 导航 ----------

function updateNavigation() {
    const prevBtn = document.getElementById("btn-prev");
    const nextBtn = document.getElementById("btn-next");
    const indicator = document.getElementById("question-indicator");

    prevBtn.disabled = currentIndex === 0;
    nextBtn.disabled = currentIndex === questions.length - 1;
    indicator.textContent = `${currentIndex + 1} / ${questions.length}`;
}

function updateProgress() {
    const answered = Object.values(userAnswers).filter((a) => a !== "").length;
    document.getElementById("progress-text").textContent =
        `${answered} / ${questions.length}`;
}

// ---------- 上一题 / 下一题 ----------

document.addEventListener("DOMContentLoaded", () => {
    // 延迟绑定（因为按钮在 loadQuestions 后才可见）
    const bindNav = setInterval(() => {
        const prevBtn = document.getElementById("btn-prev");
        const nextBtn = document.getElementById("btn-next");
        const submitBtn = document.getElementById("btn-submit");

        if (prevBtn && nextBtn) {
            clearInterval(bindNav);

            prevBtn.addEventListener("click", () => {
                if (currentIndex > 0) {
                    showQuestion(currentIndex - 1);
                }
            });

            nextBtn.addEventListener("click", () => {
                if (currentIndex < questions.length - 1) {
                    showQuestion(currentIndex + 1);
                }
            });

            if (submitBtn) {
                submitBtn.addEventListener("click", submitExam);
            }

            // 键盘快捷键
            document.addEventListener("keydown", (e) => {
                if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
                    e.preventDefault();
                    if (currentIndex > 0) showQuestion(currentIndex - 1);
                } else if (e.key === "ArrowRight" || e.key === "ArrowDown") {
                    e.preventDefault();
                    if (currentIndex < questions.length - 1) showQuestion(currentIndex + 1);
                }
            });
        }
    }, 100);
});

// ---------- 答题卡侧边栏 ----------

function initAnswerSheet() {
    // 收起/展开答题卡
    const bindSheet = setInterval(() => {
        const toggleBtn = document.getElementById("btn-sheet-toggle");
        const expandBtn = document.getElementById("btn-sheet-expand");
        if (toggleBtn) {
            clearInterval(bindSheet);
            toggleBtn.addEventListener("click", () => {
                document.getElementById("answer-sheet").classList.add("hidden");
                expandBtn.classList.remove("hidden");
            });
            expandBtn.addEventListener("click", () => {
                document.getElementById("answer-sheet").classList.remove("hidden");
                expandBtn.classList.add("hidden");
            });
        }
    }, 100);
}

function renderAnswerSheet() {
    const grid = document.getElementById("sheet-grid");
    const total = questions.length;
    document.getElementById("sheet-total").textContent = total;
    document.getElementById("sheet-answered-count").textContent =
        Object.values(userAnswers).filter((a) => a !== "").length;

    let html = "";
    for (let i = 0; i < total; i++) {
        const q = questions[i];
        const isAnswered = userAnswers[q.id] !== "";
        const isCurrent = (i === currentIndex);
        let cls = "sheet-num";
        if (isCurrent) cls += " current";
        if (isAnswered) cls += " answered";

        html += `<span class="${cls}" onclick="showQuestion(${i})" title="第${i + 1}题">${i + 1}</span>`;
    }
    grid.innerHTML = html;
}

function updateSheetHighlight() {
    const items = document.querySelectorAll(".sheet-num");
    items.forEach((el, i) => {
        const q = questions[i];
        const isAnswered = userAnswers[q.id] !== "";
        const isCurrent = (i === currentIndex);
        el.className = "sheet-num";
        if (isCurrent) el.classList.add("current");
        if (isAnswered) el.classList.add("answered");
    });

    document.getElementById("sheet-answered-count").textContent =
        Object.values(userAnswers).filter((a) => a !== "").length;
}

// ---------- 提交考试 ----------

function submitExam() {
    const answered = Object.values(userAnswers).filter((a) => a !== "").length;
    const unanswered = questions.length - answered;

    let confirmMsg = `确定要交卷吗？`;
    if (unanswered > 0) {
        confirmMsg += `\n\n⚠️ 还有 ${unanswered} 道题未作答！`;
    }

    if (!confirm(confirmMsg)) return;

    // 构建提交数据
    const answers = {};
    Object.entries(userAnswers).forEach(([qid, ans]) => {
        if (ans) answers[qid] = ans;
    });

    fetch(`/api/bank/${config.bankId}/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answers }),
    })
        .then((res) => {
            if (!res.ok) throw new Error("提交失败");
            return res.json();
        })
        .then((data) => {
            // 将结果数据存入 sessionStorage 供结果页使用
            sessionStorage.setItem("quizResult", JSON.stringify(data));
            sessionStorage.setItem("quizMode", config.mode);
            sessionStorage.setItem("quizBankName", config.bankName);

            // 跳转到结果页
            window.location.href = `/result/${config.bankId}`;
        })
        .catch((err) => {
            alert("交卷失败：" + err.message);
        });
}

// ---------- 辅助函数 ----------

function escapeHTML(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}