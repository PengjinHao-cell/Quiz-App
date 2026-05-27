/**
 * 刷题页面交互逻辑
 * - 加载题目（支持单选/多选/判断三种题型）
 * - 选项选择（单选题/判断题用 radio，多选题用 checkbox）
 * - 上一题 / 下一题导航
 * - 练习模式即时反馈
 * - 考试模式：选择后自动前进 + 交卷提交
 * - 答题卡侧边栏
 */

let questions = [];
let userAnswers = {};   // { questionId: "A" } or "AB" for multi
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
                userAnswers[q.id] = q.type === "multi" ? [] : "";
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
    const qtype = q.type || "single";

    const container = document.getElementById("question-container");
    const options = Object.entries(q.options);

    // 选择题型标签
    let typeLabel = "";
    if (qtype === "multi") {
        typeLabel = '<span class="question-type-badge multi">多选题</span>';
    } else if (qtype === "judge") {
        typeLabel = '<span class="question-type-badge judge">判断题</span>';
    } else {
        typeLabel = '<span class="question-type-badge single">单选题</span>';
    }

    // 根据题型生成不同 input type
    const inputType = (qtype === "multi") ? "checkbox" : "radio";
    const inputName = (qtype === "multi") ? `q-${q.id}-opt` : `q-${q.id}`;

    // 当前用户答案
    let currentAnswer = userAnswers[q.id];
    if (qtype === "multi" && !Array.isArray(currentAnswer)) {
        currentAnswer = [];
    }

    // 生成选项 HTML
    const optionsHTML = options
        .map(([letter, text]) => {
            let checked = "";
            let selectedClass = "";
            if (qtype === "multi") {
                if (Array.isArray(currentAnswer) && currentAnswer.includes(letter)) {
                    checked = "checked";
                    selectedClass = "selected";
                }
            } else {
                if (currentAnswer === letter) {
                    checked = "checked";
                    selectedClass = "selected";
                }
            }
            return `
                <li class="option-item ${selectedClass}"
                    onclick="selectOption(${q.id}, '${letter}')">
                    <input type="${inputType}" name="${inputName}" value="${letter}"
                           class="option-input" ${checked}
                           onclick="event.stopPropagation(); selectOption(${q.id}, '${letter}')">
                    <span class="option-label">${letter}.</span>
                    <span class="option-text">${escapeHTML(text)}</span>
                </li>
            `;
        })
        .join("");

    // 练习模式：选择后显示正确答案提示
    let hintHTML = "";
    if (config.mode === "practice") {
        if (qtype === "multi") {
            // 多选题：只有选够正确选项个数时才判定（避免选一个就提示错误）
            const userArr = Array.isArray(userAnswers[q.id]) ? userAnswers[q.id] : [];
            const correctLen = q.answer ? q.answer.replace(/\s/g, "").length : 0;
            if (userArr.length > 0 && userArr.length < correctLen) {
                hintHTML = `
                    <div class="practice-hint info">
                        ✅ 已选 <strong>${userArr.length}</strong> 个选项，正确答案共 <strong>${correctLen}</strong> 个，请继续选择
                    </div>
                `;
            } else if (userArr.length >= correctLen && q.answer) {
                const sortedUser = [...userArr].sort().join("");
                const sortedCorrect = [...q.answer.toUpperCase().replace(/\s/g, "")].sort().join("");
                const isCorrect = sortedUser === sortedCorrect;
                hintHTML = `
                    <div class="practice-hint ${isCorrect ? "correct" : "wrong"}">
                        ${isCorrect
                            ? "✅ 回答正确！"
                            : `❌ 回答错误！正确答案是 <strong>${q.answer}</strong>`}
                    </div>
                `;
            }
        } else {
            // 单选/判断题
            if (userAnswers[q.id] && q.answer) {
                const isCorrect = String(userAnswers[q.id]).toUpperCase() === q.answer.toUpperCase();
                hintHTML = `
                    <div class="practice-hint ${isCorrect ? "correct" : "wrong"}">
                        ${isCorrect
                            ? "✅ 回答正确！"
                            : `❌ 回答错误！正确答案是 <strong>${q.answer}</strong>`}
                    </div>
                `;
            }
        }
    }

    container.innerHTML = `
        <div class="question-card">
            <div class="question-number">
                ${typeLabel} 第 ${index + 1} / ${questions.length} 题
            </div>
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
    const q = questions.find(qq => qq.id === questionId);
    if (!q) return;
    const qtype = q.type || "single";

    if (qtype === "multi") {
        // 多选题：toggle
        if (!Array.isArray(userAnswers[questionId])) {
            userAnswers[questionId] = [];
        }
        const arr = userAnswers[questionId];
        const idx = arr.indexOf(letter);
        if (idx >= 0) {
            arr.splice(idx, 1);
        } else {
            arr.push(letter);
        }
        userAnswers[questionId] = [...arr]; // trigger reactivity
    } else {
        // 单选/判断
        userAnswers[questionId] = letter;
    }

    // 练习模式：立即刷新显示答案反馈
    if (config.mode === "practice") {
        showQuestion(currentIndex);
    } else {
        // 考试模式：仅更新选中样式
        const items = document.querySelectorAll(".option-item");
        if (qtype === "multi") {
            // 更新 checkbox 状态
            const currentArr = Array.isArray(userAnswers[questionId]) ? userAnswers[questionId] : [];
            items.forEach((item) => {
                const input = item.querySelector("input[type='checkbox']");
                if (input && currentArr.includes(input.value)) {
                    item.classList.add("selected");
                    input.checked = true;
                } else {
                    item.classList.remove("selected");
                    input.checked = false;
                }
            });
        } else {
            items.forEach((item) => {
                const input = item.querySelector("input[type='radio']");
                if (input && input.value === letter) {
                    item.classList.add("selected");
                    input.checked = true;
                } else {
                    item.classList.remove("selected");
                    input.checked = false;
                }
            });
        }
        updateProgress();

        // 考试模式：单选/判断选择后自动跳到下一题（多选题不自动跳）
        if (qtype !== "multi") {
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

    if (prevBtn) prevBtn.disabled = currentIndex === 0;
    if (nextBtn) nextBtn.disabled = currentIndex === questions.length - 1;
    if (indicator) indicator.textContent = `${currentIndex + 1} / ${questions.length}`;
}

function updateProgress() {
    const answered = Object.values(userAnswers).filter((a) => {
        if (Array.isArray(a)) return a.length > 0;
        return a !== "";
    }).length;
    const el = document.getElementById("progress-text");
    if (el) el.textContent = `${answered} / ${questions.length}`;
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
                } else if (e.key >= "a" && e.key <= "h") {
                    e.preventDefault();
                    const letter = e.key.toUpperCase();
                    const q = questions[currentIndex];
                    if (q && q.options && q.options[letter]) {
                        selectOption(q.id, letter);
                    }
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
        Object.values(userAnswers).filter((a) => {
            if (Array.isArray(a)) return a.length > 0;
            return a !== "";
        }).length;

    let html = "";
    for (let i = 0; i < total; i++) {
        const q = questions[i];
        const isAnswered = (() => {
            const ans = userAnswers[q.id];
            if (Array.isArray(ans)) return ans.length > 0;
            return ans !== "";
        })();
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
        const isAnswered = (() => {
            const ans = userAnswers[q.id];
            if (Array.isArray(ans)) return ans.length > 0;
            return ans !== "";
        })();
        const isCurrent = (i === currentIndex);
        el.className = "sheet-num";
        if (isCurrent) el.classList.add("current");
        if (isAnswered) el.classList.add("answered");
    });

    document.getElementById("sheet-answered-count").textContent =
        Object.values(userAnswers).filter((a) => {
            if (Array.isArray(a)) return a.length > 0;
            return a !== "";
        }).length;
}

// ---------- 提交考试 ----------

function submitExam() {
    const answered = Object.values(userAnswers).filter((a) => {
        if (Array.isArray(a)) return a.length > 0;
        return a !== "";
    }).length;
    const unanswered = questions.length - answered;

    let confirmMsg = `确定要交卷吗？`;
    if (unanswered > 0) {
        confirmMsg += `\n\n⚠️ 还有 ${unanswered} 道题未作答！`;
    }

    if (!confirm(confirmMsg)) return;

    // 构建提交数据：将多选题答案转换为排序字符串
    const answers = {};
    const question_ids = questions.map(q => q.id); // 实际展示的题目 ID

    Object.entries(userAnswers).forEach(([qid, ans]) => {
        if (Array.isArray(ans)) {
            if (ans.length > 0) {
                answers[qid] = [...ans].sort().join("");
            }
        } else if (ans) {
            answers[qid] = ans;
        }
    });

    fetch(`/api/bank/${config.bankId}/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answers, question_ids }),
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
            sessionStorage.setItem("quizBankId", config.bankId);

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