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

// 考试倒计时（默认每题 1.5 分钟，最短 10 分钟，最长 60 分钟）
let examTimer = null;
let timeRemaining = 0;

function calcExamDuration(totalQuestions) {
    // 优先使用用户自定义时长
    const dur = config.duration || "auto";
    if (dur === "0") return 0; // 不限时
    if (dur !== "auto") {
        const minutes = parseInt(dur, 10);
        if (!isNaN(minutes) && minutes > 0) return minutes * 60;
    }
    // 智能：每题 90 秒，最短 10 分钟，最长 60 分钟
    const perQuestion = 90;
    const minTime = 10 * 60;
    const maxTime = 60 * 60;
    return Math.max(minTime, Math.min(maxTime, totalQuestions * perQuestion));
}

// ---------- 初始化 ----------

document.addEventListener("DOMContentLoaded", () => {
    if (typeof QUIZ_CONFIG === "undefined") {
        document.getElementById("question-container").innerHTML =
            '<div class="loading">配置加载失败，请返回首页重试</div>';
        return;
    }

    config = QUIZ_CONFIG;
    loadQuestions();

    // 启动画面至少显示 300ms 后开始淡出
    setTimeout(dismissSplash, 300);
});



document.addEventListener("DOMContentLoaded", () => {
});

// ---------- 加载题目 ----------

function loadQuestions() {
    const searchParam = config.q ? `&q=${encodeURIComponent(config.q)}` : "";
    const qidsParam = config.qids ? `&qids=${encodeURIComponent(config.qids)}` : "";
    fetch(`/api/bank/${config.bankId}/questions?mode=${config.mode}&count=${config.count || 0}${searchParam}${qidsParam}`)
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

            // 更新题数显示为实际题目数（搜索/筛选后的）
            const actualTotal = questions.length;
            document.getElementById("progress-text").textContent = `0 / ${actualTotal}`;

            // 初始化用户答案
            userAnswers = {};
            questions.forEach((q) => {
                userAnswers[q.id] = q.type === "multi" ? [] : "";
            });

            // 显示导航栏
            document.getElementById("quiz-navigation").classList.remove("hidden");

            // 如果是考试模式，显示交卷按钮并启动倒计时
            if (config.mode === "exam") {
                document.getElementById("btn-submit").classList.remove("hidden");
                startExamTimer(questions.length);
            }

            // 绑定事件（数据已就绪，DOM 已存在）
            bindNavigation();
            initAnswerSheet();

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

// 将答案字母串转为选项文本（如 "AC" → "A. 内容1, C. 内容2"）
function formatAnswerText(answer, options) {
    if (!answer || !options) return answer || "";
    // 直接返回内容文本，不返回字母（因为选项已重新标号，字母对不上）
    var parts = answer.split("").map(function(letter) {
        return options[letter];
    }).filter(function(t) { return t; });
    return parts.length > 0 ? parts.join("；") : answer;
}

// ---------- 渲染题目 ----------

function showQuestion(index) {
    if (index < 0 || index >= questions.length) return;

    currentIndex = index;
    const q = questions[index];
    const qtype = q.type || "single";

    const container = document.getElementById("question-container");
    const options = Object.entries(q.options);
    // 选项乱序并重新标号 A/B/C/D
    let letterMap = {};  // 新标签 -> 原始字母
    let shuffledOptions = [...options];
    if (shuffledOptions.length >= 3) {
        for (let i = shuffledOptions.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [shuffledOptions[i], shuffledOptions[j]] = [shuffledOptions[j], shuffledOptions[i]];
        }
    }
    // 重新标号为 A/B/C/D...
    const relabeled = shuffledOptions.map(([origLetter, text], idx) => {
        const newLabel = String.fromCharCode(65 + idx);  // A, B, C, D...
        letterMap[newLabel] = origLetter;
        return [newLabel, origLetter, text];
    });

    // 选择题型标签
    let typeLabel = "";
    if (qtype === "multi") {
        typeLabel = '<span class="question-type-badge multi">多选题</span>';
    } else if (qtype === "judge") {
        typeLabel = '<span class="question-type-badge judge">判断题</span>';
    } else if (qtype === "fill") {
        typeLabel = '<span class="question-type-badge fill">填空题</span>';
    } else {
        typeLabel = '<span class="question-type-badge single">单选题</span>';
    }

    // 当前用户答案
    let currentAnswer = userAnswers[q.id];
    if (qtype === "multi" && !Array.isArray(currentAnswer)) {
        currentAnswer = [];
    }

    // 填空题：生成文本输入框
    let inputAreaHTML = "";
    if (qtype === "fill") {
        const val = typeof currentAnswer === "string" ? currentAnswer : "";
        inputAreaHTML = `
            <div class="fill-input-area">
                <label class="fill-label">请输入答案：</label>
                <input type="text" class="fill-input" id="fill-input-${q.id}"
                       value="${escapeHTML(val)}" autocomplete="off"
                       placeholder="输入你的答案..."
                       oninput="onFillInput(${q.id}, this.value)">
            </div>
        `;
    }

    // 根据题型生成不同 input type
    const inputType = (qtype === "multi") ? "checkbox" : "radio";
    const inputName = (qtype === "multi") ? `q-${q.id}-opt` : `q-${q.id}`;
    if (qtype === "multi" && !Array.isArray(currentAnswer)) {
        currentAnswer = [];
    }

    // 生成选项 HTML（已乱序并重新标号）（填空题跳过）
    let optionsHTML = "";
    if (qtype !== "fill") {
        optionsHTML = relabeled
        .map(([newLabel, origLetter, text]) => {
            let checked = "";
            let selectedClass = "";
            // 用新标签显示，但用原始字母提交
            const displayLetter = newLabel;
            const submitLetter = origLetter;
            if (qtype === "multi") {
                if (Array.isArray(currentAnswer) && currentAnswer.includes(submitLetter)) {
                    checked = "checked";
                    selectedClass = "selected";
                }
            } else {
                if (currentAnswer === submitLetter) {
                    checked = "checked";
                    selectedClass = "selected";
                }
            }
            return `
                <li class="option-item ${selectedClass}"
                    onclick="selectOption(${q.id}, '${submitLetter}')">
                    <input type="${inputType}" name="${inputName}" value="${submitLetter}"
                           class="option-input" ${checked}
                           onclick="event.stopPropagation(); selectOption(${q.id}, '${submitLetter}')">
                    <span class="option-label">${displayLetter}.</span>
                    <span class="option-text">${escapeHTML(text)}</span>
                </li>
            `;
        })
        .join("");
    }

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
                        ✅ 已选 <strong>${userArr.length}</strong> 个选项，继续选择或点击已选项取消
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
                            : `❌ 回答错误！正确答案是 <strong>${formatAnswerText(q.answer, q.options)}</strong>`}
                    </div>
                `;
            }
        } else if (qtype === "fill") {
            // 填空题
            if (userAnswers[q.id] && q.answer) {
                const userStr = String(userAnswers[q.id]).replace(/\s/g, "");
                const correctStr = q.answer.replace(/\s/g, "");
                const isCorrect = userStr === correctStr;
                hintHTML = `
                    <div class="practice-hint ${isCorrect ? "correct" : "wrong"}">
                        ${isCorrect
                            ? "✅ 回答正确！"
                            : `❌ 回答错误！正确答案是 <strong>${escapeHTML(q.answer)}</strong>`}
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
                            : `❌ 回答错误！正确答案是 <strong>${formatAnswerText(q.answer, q.options)}</strong>`}
                    </div>
                `;
            }
        }
    }

    const isFav = isFavorited(config.bankId, q.id);
    const starIcon = isFav ? "⭐" : "☆";
    const starTitle = isFav ? "取消收藏" : "收藏此题";

    container.innerHTML = `
        <div class="question-card">
            <div class="question-number">
                ${typeLabel} 第 ${index + 1} / ${questions.length} 题
                <span class="fav-btn ${isFav ? 'fav-active' : ''}"
                      onclick="toggleFav(${q.id})" title="${starTitle}">${starIcon}</span>
            </div>
            <div class="question-text">${escapeHTML(q.text)}</div>
            ${qtype === "fill"
                ? `<div class="fill-input-wrap">${inputAreaHTML}</div>`
                : `<ul class="options-list">${optionsHTML}</ul>`
            }
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

// ---------- 填空题输入 ----------

function onFillInput(questionId, value) {
    userAnswers[questionId] = value;
    const q = questions.find(qq => qq.id === questionId);
    if (!q) return;

    // 练习模式：实时反馈
    if (config.mode === "practice") {
        const userStr = value.replace(/\s/g, "");
        const correctStr = (q.answer || "").replace(/\s/g, "");
        if (value && q.answer) {
            if (userStr === correctStr) {
                const key = `${config.bankId}_${q.id}`;
                const book = getWrongBook();
                if (book[key]) removeFromWrongBook(key);
            } else {
                addToWrongBook(q, value, config.bankId, config.bankName);
            }
        }
        // 更新提示
        updatePracticeFeedback(currentIndex);
    }

    updateProgress();
    renderAnswerSheet();
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

    // 自动收录错题到错题本（练习模式：选完判定后）
    if (config.mode === "practice") {
        // 单选题/判断题：选完即判定
        if (qtype !== "multi") {
            const userAns = String(userAnswers[questionId] || "").toUpperCase();
            const correctAns = (q.answer || "").toUpperCase();
            if (userAns && correctAns && userAns !== correctAns) {
                addToWrongBook(q, userAns, config.bankId, config.bankName);
            } else if (userAns && correctAns && userAns === correctAns) {
                // 答对了 → 如果有错题记录则移除
                const key = `${config.bankId}_${q.id}`;
                const book = getWrongBook();
                if (book[key]) {
                    removeFromWrongBook(key);
                }
            }
        }
        // 多选题的判定在 updatePracticeFeedback 中做
    }

    // 练习模式：只更新提示和选项样式，不重渲染整张卡片
    if (config.mode === "practice") {
        updatePracticeFeedback(currentIndex);
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

        // 考试模式：单选/判断选择后自动跳到下一题（多选题/填空题不自动跳）
        if (qtype !== "multi" && qtype !== "fill") {
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

// ---------- 收藏切换 ----------

function toggleFav(questionId) {
    const q = questions.find(qq => qq.id === questionId);
    if (!q) return;
    const nowFav = toggleFavorite(q, config.bankId, config.bankName);
    // 更新星标样式
    const container = document.getElementById("question-container");
    const favBtn = container.querySelector(".fav-btn");
    if (favBtn) {
        favBtn.textContent = nowFav ? "⭐" : "☆";
        favBtn.title = nowFav ? "取消收藏" : "收藏此题";
        favBtn.classList.toggle("fav-active", nowFav);
    }
}

// ---------- 练习模式反馈（原地更新，不重渲染） ----------

function updatePracticeFeedback(index) {
    const q = questions[index];
    if (!q) return;

    const container = document.getElementById("question-container");
    const items = container.querySelectorAll(".option-item");
    const qtype = q.type || "single";
    const currentAnswer = userAnswers[q.id];

    // 更新选项选中样式（填空题跳过）
    if (qtype !== "fill") {
        items.forEach((item) => {
            const input = item.querySelector("input");
            if (!input) return;
            const letter = input.value;
            let shouldSelect = false;
            if (qtype === "multi") {
                shouldSelect = Array.isArray(currentAnswer) && currentAnswer.includes(letter);
            } else {
                shouldSelect = currentAnswer === letter;
            }
            item.classList.toggle("selected", shouldSelect);
            input.checked = shouldSelect;
        });
    }

    // 构建提示 HTML
    let hintHTML = "";
    if (qtype === "multi") {
        const userArr = Array.isArray(currentAnswer) ? currentAnswer : [];
        const correctLen = q.answer ? q.answer.replace(/\s/g, "").length : 0;
        if (userArr.length > 0 && userArr.length < correctLen) {
            hintHTML = `
                <div class="practice-hint info">
                    ✅ 已选 <strong>${userArr.length}</strong> 个选项，继续选择或点击已选项取消
                </div>
            `;
        } else if (userArr.length >= correctLen && q.answer) {
            const sortedUser = [...userArr].sort().join("");
            const sortedCorrect = [...q.answer.toUpperCase().replace(/\s/g, "")].sort().join("");
            const isCorrect = sortedUser === sortedCorrect;
            // 错题本自动收录（多选题）
            if (!isCorrect) {
                addToWrongBook(q, sortedUser, config.bankId, config.bankName);
            } else {
                const key = `${config.bankId}_${q.id}`;
                const book = getWrongBook();
                if (book[key]) removeFromWrongBook(key);
            }
            hintHTML = `
                <div class="practice-hint ${isCorrect ? "correct" : "wrong"}">
                    ${isCorrect
                        ? "✅ 回答正确！"
                        : `❌ 回答错误！正确答案是 <strong>${formatAnswerText(q.answer, q.options)}</strong>`}
                </div>
            `;
        }
    } else if (qtype === "fill") {
        if (currentAnswer && q.answer) {
            const userStr = String(currentAnswer).replace(/\s/g, "");
            const correctStr = q.answer.replace(/\s/g, "");
            const isCorrect = userStr === correctStr;
            hintHTML = `
                <div class="practice-hint ${isCorrect ? "correct" : "wrong"}">
                    ${isCorrect
                        ? "✅ 回答正确！"
                        : `❌ 回答错误！正确答案是 <strong>${escapeHTML(q.answer)}</strong>`}
                </div>
            `;
        }
    } else {
        if (currentAnswer && q.answer) {
            const isCorrect = String(currentAnswer).toUpperCase() === q.answer.toUpperCase();
            hintHTML = `
                <div class="practice-hint ${isCorrect ? "correct" : "wrong"}">
                    ${isCorrect
                        ? "✅ 回答正确！"
                        : `❌ 回答错误！正确答案是 <strong>${formatAnswerText(q.answer, q.options)}</strong>`}
                </div>
            `;
        }
    }

    // 替换或插入提示
    const existingHint = container.querySelector(".practice-hint");
    if (hintHTML) {
        if (existingHint) {
            existingHint.outerHTML = hintHTML;
        } else {
            const optionsList = container.querySelector(".options-list");
            if (optionsList) {
                optionsList.insertAdjacentHTML("afterend", hintHTML);
            } else {
                const fillWrap = container.querySelector(".fill-input-wrap");
                if (fillWrap) {
                    fillWrap.insertAdjacentHTML("afterend", hintHTML);
                }
            }
        }
    } else if (existingHint) {
        existingHint.remove();
    }

    updateProgress();
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

function bindNavigation() {
    const prevBtn = document.getElementById("btn-prev");
    const nextBtn = document.getElementById("btn-next");
    const submitBtn = document.getElementById("btn-submit");

    prevBtn.addEventListener("click", () => {
        if (currentIndex > 0) showQuestion(currentIndex - 1);
    });

    nextBtn.addEventListener("click", () => {
        if (currentIndex < questions.length - 1) showQuestion(currentIndex + 1);
    });

    if (submitBtn) {
        submitBtn.addEventListener("click", submitExam);
    }

    // 键盘快捷键（事件委托，全局生效）
    document.addEventListener("keydown", (e) => {
        if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
            e.preventDefault();
            if (currentIndex > 0) showQuestion(currentIndex - 1);
        } else if (e.key === "ArrowRight" || e.key === "ArrowDown") {
            e.preventDefault();
            if (currentIndex < questions.length - 1) showQuestion(currentIndex + 1);
        } else if (/^[a-h]$/i.test(e.key)) {
            e.preventDefault();
            const letter = e.key.toUpperCase();
            const q = questions[currentIndex];
            if (q && q.options && q.options[letter]) {
                selectOption(q.id, letter);
            }
        }
    });
}

// ---------- 答题卡侧边栏 ----------

function initAnswerSheet() {
    const toggleBtn = document.getElementById("btn-sheet-toggle");
    const expandBtn = document.getElementById("btn-sheet-expand");

    toggleBtn.addEventListener("click", () => {
        document.getElementById("answer-sheet").classList.add("hidden");
        expandBtn.classList.remove("hidden");
    });

    expandBtn.addEventListener("click", () => {
        document.getElementById("answer-sheet").classList.remove("hidden");
        expandBtn.classList.add("hidden");
    });
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

// ---------- 考试倒计时 ----------

function startExamTimer(totalQuestions) {
    timeRemaining = calcExamDuration(totalQuestions);
    // 在计时器旁边显示时长说明
    const totalMin = Math.round(timeRemaining / 60);
    const timerEl = document.getElementById("exam-timer");
    let note = "";
    if (timeRemaining === 0) {
        timerEl.innerHTML = `⏱️ <span id="timer-display">--:--</span> <small style="color:#718096;font-size:0.7rem;">不限时</small>`;
        timerEl.classList.add("hidden");
        return;
    }
    // 时长显示精简，避免换行
    const shortNote = config.duration === "auto" ? `共${totalMin}分` : `共${totalMin}分`;
    timerEl.innerHTML = `⏱️ <span id="timer-display">00:00</span> <small style="color:#718096;font-size:0.65rem;font-weight:400;white-space:nowrap;">${shortNote}</small>`;
    timerEl.classList.remove("hidden");

    updateTimerDisplay();
    examTimer = setInterval(() => {
        timeRemaining--;
        updateTimerDisplay();

        if (timeRemaining <= 0 && timeRemaining > -10) {
            clearInterval(examTimer);
            examTimer = null;
            alert("⏰ 时间到！正在自动交卷...");
            submitExam();
        }
    }, 1000);
}

function updateTimerDisplay() {
    const minutes = Math.floor(timeRemaining / 60);
    const seconds = timeRemaining % 60;
    const display = document.getElementById("timer-display");
    display.textContent = `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;

    // 少于 5 分钟时变红闪烁
    const timerEl = document.getElementById("exam-timer");
    if (timeRemaining <= 300) {
        display.style.color = "#e53e3e";
        timerEl.classList.add("timer-warning");
    } else {
        display.style.color = "";
        timerEl.classList.remove("timer-warning");
    }
}

// ---------- 提交考试 ----------

function submitExam() {
    // 停止倒计时
    if (examTimer) {
        clearInterval(examTimer);
        examTimer = null;
    }
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
            // 将错题存入错题本
            if (data.details) {
                data.details.forEach((detail) => {
                    if (!detail.is_correct) {
                        const q = questions.find(qq => qq.id === detail.id);
                        if (q) {
                            addToWrongBook(q, detail.user_answer, config.bankId, config.bankName);
                        }
                    } else {
                        // 答对了的题从错题本移除
                        const key = `${config.bankId}_${detail.id}`;
                        const book = getWrongBook();
                        if (book[key]) removeFromWrongBook(key);
                    }
                });
            }

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

