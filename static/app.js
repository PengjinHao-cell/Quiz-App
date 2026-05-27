/**
 * 首页交互逻辑
 * - 文件上传
 * - 题库删除
 * - 示例题库初始化
 */

document.addEventListener("DOMContentLoaded", () => {
    const uploadForm = document.getElementById("upload-form");
    if (uploadForm) {
        uploadForm.addEventListener("submit", handleUpload);
    }
    renderStats();
    renderHistory();
    renderFavorites();
    renderWrongBook();

    // 有题库时显示搜索区
    const searchSection = document.getElementById("search-section");
    const bankSelect = document.getElementById("search-bank-select");
    if (searchSection && bankSelect && bankSelect.options.length > 1) {
        searchSection.style.display = "block";
    }

    // 搜索框回车触发搜索
    const searchInput = document.getElementById("search-input");
    if (searchInput) {
        searchInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") doSearch();
        });
    }

    // 启动画面消失
    setTimeout(dismissSplash, 400);
});

function dismissSplash() {
    const splash = document.getElementById("splash-screen");
    if (!splash) return;
    splash.classList.add("splash-fade-out");
    setTimeout(() => {
        splash.style.display = "none";
    }, 500);
}

// ---------- 文件上传 ----------

function handleUpload(e) {
    e.preventDefault();

    const fileInput = document.getElementById("file-input");
    const uploadBtn = document.getElementById("upload-btn");
    const msgDiv = document.getElementById("upload-msg");

    if (!fileInput.files || fileInput.files.length === 0) {
        showMessage("请先选择一个文件", "error");
        return;
    }

    const file = fileInput.files[0];
    const mode = document.querySelector('input[name="mode"]:checked').value;

    // 客户端校验
    const allowedExts = [".pdf", ".docx"];
    const fileName = file.name.toLowerCase();
    const isValid = allowedExts.some(ext => fileName.endsWith(ext));

    if (!isValid) {
        showMessage("仅支持 PDF 和 DOCX 格式的文件", "error");
        return;
    }

    if (file.size > 32 * 1024 * 1024) {
        showMessage("文件大小不能超过 32 MB", "error");
        return;
    }

    // 禁用按钮，显示上传中
    uploadBtn.disabled = true;
    uploadBtn.textContent = "⏳ 正在上传并解析...";
    msgDiv.className = "msg";
    msgDiv.textContent = "";

    const formData = new FormData();
    formData.append("file", file);
    formData.append("mode", mode);

    fetch("/upload", {
        method: "POST",
        body: formData,
    })
        .then(async (res) => {
            const data = await res.json();
            if (!res.ok) {
                throw new Error(data.error || "上传失败");
            }
            return data;
        })
        .then((data) => {
            if (data.success && data.redirect) {
                showMessage(`解析成功！共 ${data.question_count} 道题，即将跳转...`, "success");
                setTimeout(() => {
                    window.location.href = data.redirect;
                }, 800);
            } else {
                throw new Error(data.error || "未知错误");
            }
        })
        .catch((err) => {
            showMessage(err.message, "error");
            uploadBtn.disabled = false;
            uploadBtn.textContent = "🚀 上传并开始刷题";
        });
}

// ---------- 删除题库 ----------

function deleteBank(bankId) {
    if (!confirm("确定要删除这个题库吗？\n\n删除后不可恢复。")) {
        return;
    }

    fetch(`/api/bank/${bankId}/delete`, {
        method: "POST",
    })
        .then((res) => res.json())
        .then((data) => {
            if (data.success) {
                const card = document.getElementById(`bank-${bankId}`);
                if (card) {
                    card.style.transition = "opacity 0.3s";
                    card.style.opacity = "0";
                    setTimeout(() => card.remove(), 300);
                }

                // 如果所有题库都被删了，刷新以显示空状态
                const remaining = document.querySelectorAll(".bank-card");
                if (remaining.length <= 1) {
                    setTimeout(() => window.location.reload(), 400);
                }

                showMessage("题库已删除", "success");
            } else {
                showMessage(data.error || "删除失败", "error");
            }
        })
        .catch((err) => {
            showMessage("删除失败：" + err.message, "error");
        });
}

// ---------- 示例题库 ----------

function initSample() {
    const btn = document.querySelector(".empty-state .btn");
    if (btn) {
        btn.disabled = true;
        btn.textContent = "⏳ 初始化中...";
    }

    fetch("/api/init-sample", {
        method: "POST",
    })
        .then((res) => res.json())
        .then((data) => {
            if (data.success) {
                window.location.reload();
            } else {
                showMessage(data.error || "初始化失败", "error");
                if (btn) {
                    btn.disabled = false;
                    btn.textContent = "📥 加载示例题库";
                }
            }
        })
        .catch((err) => {
            showMessage("初始化失败：" + err.message, "error");
            if (btn) {
                btn.disabled = false;
                btn.textContent = "📥 加载示例题库";
            }
        });
}

// ---------- 文件选择显示 ----------

function updateFileName(input) {
    const display = document.getElementById("file-name-display");
    if (input.files && input.files.length > 0) {
        display.textContent = `已选择: ${input.files[0].name}`;
    } else {
        display.textContent = "选择文件 (PDF / DOCX)";
    }
}

// ---------- 开始刷题（带题数选择） ----------

function startQuiz(bankId, mode) {
    const countEl = document.getElementById(`count-${bankId}`);
    const count = countEl ? countEl.value : "0";
    window.location.href = `/quiz/${bankId}?mode=${mode}&count=${count}`;
}

// ---------- 搜题 ----------

function doSearch() {
    const bankId = document.getElementById("search-bank-select").value;
    const keyword = document.getElementById("search-input").value.trim();
    const resultsDiv = document.getElementById("search-results");

    if (!bankId) {
        resultsDiv.innerHTML = '<div class="search-error">请先选择题库</div>';
        return;
    }
    if (!keyword) {
        resultsDiv.innerHTML = '<div class="search-error">请输入搜索关键词</div>';
        return;
    }

    resultsDiv.innerHTML = '<div class="search-loading">搜索中...</div>';

    fetch(`/api/bank/${bankId}/questions?mode=practice&q=${encodeURIComponent(keyword)}`)
        .then(res => {
            if (!res.ok) throw new Error("搜索失败");
            return res.json();
        })
        .then(data => {
            const qs = data.questions;
            if (!qs || qs.length === 0) {
                resultsDiv.innerHTML = '<div class="search-empty">未找到匹配的题目，试试其他关键词</div>';
                return;
            }

            const bankName = data.bank_name;
            let html = `
                <div class="search-result-header">
                    找到 <strong>${qs.length}</strong> 道匹配的题目
                    <a href="/quiz/${bankId}?mode=practice&q=${encodeURIComponent(keyword)}"
                       class="btn btn-primary btn-small">📝 练习这 ${qs.length} 道题</a>
                </div>
            `;

            qs.forEach((q, idx) => {
                const typeLabel = q.type === "multi" ? "多选题" : q.type === "judge" ? "判断题" : "单选题";
                const typeClass = q.type || "single";
                // 高亮关键词
                const highlightedText = highlightKeyword(q.text, keyword);
                const optHtml = Object.entries(q.options)
                    .map(([k, v]) => `<span class="search-opt">${k}. ${highlightKeyword(escapeHTML(String(v)), keyword)}</span>`)
                    .join(" ");

                html += `
                    <div class="search-result-item">
                        <div class="search-q-header">
                            <span class="wrongbook-type ${typeClass}">${typeLabel}</span>
                            <span class="search-q-num">#${idx + 1}</span>
                        </div>
                        <div class="search-q-text">${highlightedText}</div>
                        <div class="search-q-opts">${optHtml}</div>
                    </div>
                `;
            });

            resultsDiv.innerHTML = html;
        })
        .catch(err => {
            resultsDiv.innerHTML = `<div class="search-error">搜索失败：${err.message}</div>`;
        });
}

function highlightKeyword(text, keyword) {
    if (!keyword) return escapeHTML(text);
    const escaped = escapeHTML(text);
    const kw = escapeHTML(keyword);
    const regex = new RegExp(`(${kw.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    return escaped.replace(regex, '<mark class="search-highlight">$1</mark>');
}

// ---------- 上传方式切换 ----------

function switchUploadTab(tab) {
    document.getElementById("tab-file").classList.toggle("active", tab === "file");
    document.getElementById("tab-text").classList.toggle("active", tab === "text");
    document.getElementById("upload-panel-file").style.display = tab === "file" ? "block" : "none";
    document.getElementById("upload-panel-text").style.display = tab === "text" ? "block" : "none";
}

// ---------- AI 文本解析 ----------

function handleAiParse() {
    const textarea = document.getElementById("ai-text-input");
    const btn = document.getElementById("ai-parse-btn");
    const msgDiv = document.getElementById("ai-parse-msg");

    const text = textarea.value.trim();
    if (!text) {
        msgDiv.textContent = "请先粘贴题目文本";
        msgDiv.className = "msg error";
        return;
    }
    if (text.length < 20) {
        msgDiv.textContent = "文本太短，请粘贴更多内容";
        msgDiv.className = "msg error";
        return;
    }

    // 禁用按钮
    btn.disabled = true;
    btn.textContent = "⏳ AI 正在解析...（约 10-30 秒）";
    msgDiv.className = "msg";
    msgDiv.textContent = "";

    fetch("/api/parse-text", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
    })
        .then(async (res) => {
            const data = await res.json();
            if (!res.ok) throw new Error(data.error || "解析失败");
            return data;
        })
        .then((data) => {
            if (data.success && data.redirect) {
                msgDiv.className = "msg success";
                msgDiv.textContent = `✅ AI 解析成功！共 ${data.question_count} 道题，即将跳转...`;
                setTimeout(() => {
                    window.location.href = data.redirect;
                }, 1000);
            }
        })
        .catch((err) => {
            msgDiv.textContent = "❌ " + err.message;
            msgDiv.className = "msg error";
            btn.disabled = false;
            btn.textContent = "🤖 AI 智能解析";
        });
}

// ---------- 重命名题库 ----------

function renameBank(bankId) {
    const nameEl = document.getElementById(`bname-${bankId}`);
    if (!nameEl) return;

    const oldName = nameEl.textContent;
    const newName = prompt("请输入新的题库名称：", oldName);

    if (!newName || newName.trim() === oldName) return;
    if (newName.trim().length > 100) {
        alert("名称不能超过 100 个字符");
        return;
    }

    fetch(`/api/bank/${bankId}/rename`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: newName.trim() }),
    })
        .then((res) => {
            if (!res.ok) return res.json().then(d => { throw new Error(d.error); });
            return res.json();
        })
        .then((data) => {
            if (data.success) {
                nameEl.textContent = newName.trim();
                nameEl.title = newName.trim();
                // 同时更新搜索下拉框中的名称
                const sel = document.getElementById("search-bank-select");
                if (sel) {
                    for (const opt of sel.options) {
                        if (opt.value === bankId) {
                            // 更新选项文本，保留题数部分
                            const countMatch = opt.text.match(/\((\d+)题\)/);
                            const count = countMatch ? countMatch[1] : "";
                            opt.text = count ? `${newName.trim()} (${count}题)` : newName.trim();
                            break;
                        }
                    }
                }
            }
        })
        .catch((err) => {
            alert("重命名失败：" + err.message);
        });
}

// ---------- 消息提示 ----------

function showMessage(text, type) {
    const msgDiv = document.getElementById("upload-msg");
    if (!msgDiv) return;

    msgDiv.textContent = text;
    msgDiv.className = `msg ${type}`;

    // 成功后 3 秒自动清除
    if (type === "success") {
        setTimeout(() => {
            msgDiv.textContent = "";
            msgDiv.className = "msg";
        }, 3000);
    }
}

// ---------- 学习统计 ----------

function renderStats() {
    const section = document.getElementById("stats-section");
    if (!section) return;

    let history = [];
    try {
        const raw = localStorage.getItem("quizHistory");
        if (raw) history = JSON.parse(raw);
    } catch (_) {}

    if (history.length === 0) {
        section.style.display = "none";
        return;
    }

    section.style.display = "block";

    // ---- 总览数据 ----
    const totalSessions = history.length;
    const totalQuestions = history.reduce((s, r) => s + r.total, 0);
    const totalCorrect = history.reduce((s, r) => s + r.correct, 0);
    const overallAccuracy = totalQuestions > 0 ? Math.round(totalCorrect / totalQuestions * 100) : 0;

    // ---- 按题库统计 ----
    const bankStats = {};
    history.forEach(r => {
        const key = r.bank_id || "__unknown__";
        if (!bankStats[key]) {
            bankStats[key] = { name: r.bank_name || "未知", total: 0, correct: 0, sessions: 0 };
        }
        bankStats[key].total += r.total;
        bankStats[key].correct += r.correct;
        bankStats[key].sessions += 1;
    });

    // ---- 按模式统计 ----
    const modeStats = { practice: { total: 0, correct: 0 }, exam: { total: 0, correct: 0 } };
    history.forEach(r => {
        const m = r.mode === "exam" ? "exam" : "practice";
        modeStats[m].total += r.total;
        modeStats[m].correct += r.correct;
    });

    // ---- 最近 10 次得分趋势 ----
    const recent = history.slice(0, 10).reverse();

    // ---- 每日活跃（近 7 天） ----
    const dayMap = {};
    const now = new Date();
    for (let i = 6; i >= 0; i--) {
        const d = new Date(now);
        d.setDate(d.getDate() - i);
        const key = d.toLocaleDateString("zh-CN");
        dayMap[key] = 0;
    }
    history.forEach(r => {
        // 尝试从时间字符串解析日期
        try {
            const dateStr = r.time.split(" ")[0]; // "2026/5/27" 或 "2026-5-27"
            if (dateStr && dayMap[dateStr] !== undefined) {
                dayMap[dateStr] += r.total;
            } else {
                // 尝试匹配格式
                for (const dk of Object.keys(dayMap)) {
                    if (dk.startsWith(dateStr.slice(0, 4))) {
                        dayMap[dk] += r.total;
                        break;
                    }
                }
            }
        } catch (_) {}
    });

    const maxDayQuestions = Math.max(...Object.values(dayMap), 1);

    // ---- 构建 HTML ----
    const scoreClass = overallAccuracy >= 90 ? "excellent"
        : overallAccuracy >= 70 ? "good"
        : overallAccuracy >= 60 ? "fair" : "poor";

    let html = `
        <!-- 总览卡片 -->
        <div class="stats-overview">
            <div class="stats-card">
                <div class="stats-card-icon">📝</div>
                <div class="stats-card-value">${totalSessions}</div>
                <div class="stats-card-label">练习次数</div>
            </div>
            <div class="stats-card">
                <div class="stats-card-icon">📄</div>
                <div class="stats-card-value">${totalQuestions}</div>
                <div class="stats-card-label">答题总数</div>
            </div>
            <div class="stats-card">
                <div class="stats-card-icon">✅</div>
                <div class="stats-card-value ${scoreClass}">${overallAccuracy}%</div>
                <div class="stats-card-label">总正确率</div>
            </div>
            <div class="stats-card">
                <div class="stats-card-icon">🎯</div>
                <div class="stats-card-value">${totalCorrect}/${totalQuestions}</div>
                <div class="stats-card-label">正确/总数</div>
            </div>
        </div>

        <!-- 得分趋势 -->
        <div class="stats-chart-section">
            <h3>📈 最近 ${recent.length} 次得分趋势</h3>
            <div class="stats-bar-chart">
    `;

    recent.forEach(r => {
        const pct = r.score;
        const cls = pct >= 90 ? "excellent" : pct >= 70 ? "good" : pct >= 60 ? "fair" : "poor";
        html += `
            <div class="stats-bar-item">
                <div class="stats-bar-fill ${cls}" style="height:${Math.max(pct, 5)}%"></div>
                <div class="stats-bar-label">${pct}分</div>
            </div>
        `;
    });

    html += `
            </div>
        </div>

        <div class="stats-grid">
            <!-- 按题库 -->
            <div class="stats-sub-section">
                <h3>📚 各题库正确率</h3>
    `;

    const sortedBanks = Object.entries(bankStats).sort((a, b) => b[1].total - a[1].total);
    sortedBanks.forEach(([key, bs]) => {
        const acc = bs.total > 0 ? Math.round(bs.correct / bs.total * 100) : 0;
        const cls = acc >= 90 ? "excellent" : acc >= 70 ? "good" : acc >= 60 ? "fair" : "poor";
        html += `
            <div class="stats-bank-item">
                <div class="stats-bank-info">
                    <span class="stats-bank-name">${escapeHTML(bs.name)}</span>
                    <span class="stats-bank-meta">${bs.sessions} 次 · ${bs.total} 题</span>
                </div>
                <div class="stats-bank-bar-bg">
                    <div class="stats-bank-bar-fill ${cls}" style="width:${acc}%"></div>
                </div>
                <span class="stats-bank-pct ${cls}">${acc}%</span>
            </div>
        `;
    });

    html += `
            </div>

            <!-- 模式对比 & 每日活跃 -->
            <div class="stats-sub-section">
                <h3>📋 模式对比</h3>
                <div class="stats-mode-compare">
    `;

    const modes = [
        { key: "practice", label: "练习模式", icon: "✏️" },
        { key: "exam", label: "考试模式", icon: "📝" },
    ];
    modes.forEach(m => {
        const st = modeStats[m.key];
        const acc = st.total > 0 ? Math.round(st.correct / st.total * 100) : 0;
        const cls = acc >= 90 ? "excellent" : acc >= 70 ? "good" : acc >= 60 ? "fair" : "poor";
        html += `
            <div class="stats-mode-item">
                <div class="stats-mode-header">${m.icon} ${m.label}</div>
                <div class="stats-mode-nums">${st.correct}/${st.total} 题</div>
                <div class="stats-mode-bar-bg">
                    <div class="stats-bank-bar-fill ${cls}" style="width:${acc}%"></div>
                </div>
                <div class="stats-mode-acc ${cls}">${acc}%</div>
            </div>
        `;
    });

    // 每日活跃
    html += `
                </div>
                <h3 style="margin-top:16px;">🔥 近 7 天做题量</h3>
                <div class="stats-day-chart">
    `;

    Object.entries(dayMap).forEach(([day, count]) => {
        const pct = Math.max(Math.round(count / maxDayQuestions * 100), 5);
        html += `
            <div class="stats-day-item">
                <div class="stats-day-bar" style="height:${pct}%"></div>
                <div class="stats-day-label">${count}</div>
                <div class="stats-day-name">${day.slice(5)}</div>
            </div>
        `;
    });

    html += `
                </div>
            </div>
        </div>
    `;

    section.innerHTML = html;
}

// ---------- 历史记录 ----------

function renderHistory() {
    const section = document.getElementById("history-section");
    const tbody = document.getElementById("history-tbody");
    if (!section || !tbody) return;

    let history = [];
    try {
        const raw = localStorage.getItem("quizHistory");
        if (raw) {
            history = JSON.parse(raw);
        }
    } catch (_) {
        history = [];
    }

    if (history.length === 0) {
        section.style.display = "none";
        return;
    }

    section.style.display = "block";

    let html = "";
    history.forEach((r, idx) => {
        const modeLabel = r.mode === "exam" ? "📋 考试" : "✏️ 练习";
        const scoreClass =
            r.score >= 90
                ? "excellent"
                : r.score >= 70
                    ? "good"
                    : r.score >= 60
                        ? "fair"
                        : "poor";

        // 如果有 bank_id，生成可点击链接
        const bankNameHtml = r.bank_id
            ? `<a href="#" onclick="startQuiz('${r.bank_id}', '${r.mode}')" title="再次刷题">${escapeHTML(r.bank_name)}</a>`
            : escapeHTML(r.bank_name);

        html += `
            <tr data-index="${idx}">
                <td class="hist-time">${escapeHTML(r.time)}</td>
                <td class="hist-bank">${bankNameHtml}</td>
                <td>${modeLabel}</td>
                <td><span class="hist-score ${scoreClass}">${r.score}分</span> (${r.correct}/${r.total})</td>
                <td>
                    <button class="btn btn-small btn-danger-outline" onclick="deleteHistoryItem(${idx})">删除</button>
                </td>
            </tr>
        `;
    });

    tbody.innerHTML = html;
}

function deleteHistoryItem(idx) {
    let history = [];
    try {
        const raw = localStorage.getItem("quizHistory");
        history = raw ? JSON.parse(raw) : [];
    } catch (_) {
        history = [];
    }

    if (idx >= 0 && idx < history.length) {
        history.splice(idx, 1);
        localStorage.setItem("quizHistory", JSON.stringify(history));
        renderStats();
        renderHistory();
    }
}

function clearHistory() {
    if (!confirm("确定要清空所有答题记录吗？此操作不可恢复。")) return;
    localStorage.removeItem("quizHistory");
    renderStats();
    renderHistory();
}

// ---------- 题目收藏 ----------

function renderFavorites() {
    const section = document.getElementById("fav-section");
    const container = document.getElementById("fav-container");
    if (!section || !container) return;

    const groups = groupFavorites();
    const totalFav = Object.values(groups).reduce((sum, g) => sum + g.questions.length, 0);

    if (totalFav === 0) {
        section.style.display = "none";
        return;
    }

    section.style.display = "block";

    let html = "";
    for (const [gKey, group] of Object.entries(groups)) {
        const qs = group.questions;
        html += `
            <div class="wrongbook-group">
                <div class="wrongbook-group-header">
                    <span class="wrongbook-bank-name">📄 ${escapeHTML(group.bank_name)}</span>
                    <span class="fav-count">${qs.length} 道收藏</span>
                </div>
                <div class="wrongbook-items">
        `;

        qs.forEach((item) => {
            const typeLabel = item.type === "multi" ? "多选题" : item.type === "judge" ? "判断题" : "单选题";

            html += `
                <div class="fav-item" id="fav-${escapeHTML(item.key)}">
                    <div class="wrongbook-q-header">
                        <span class="wrongbook-type ${item.type}">${typeLabel}</span>
                        <span class="wrongbook-qtext">${escapeHTML(item.question_text)}</span>
                    </div>
                    <div class="wrongbook-meta" style="margin-top:4px;">
                        收藏于 ${escapeHTML(item.added_time)}
                    </div>
                    <div class="wrongbook-actions">
                        <button class="btn btn-small btn-danger-outline" onclick="removeFav('${escapeHTML(item.key)}')">取消收藏 ✕</button>
                    </div>
                </div>
            `;
        });

        const favCount = qs.length;
        html += `
                </div>
                <div class="wrongbook-group-footer">
                    <a href="/quiz/${group.bank_id}?mode=practice&count=${favCount}" class="btn btn-primary btn-small">📝 复习这 ${favCount} 道收藏题</a>
                </div>
            </div>
        `;
    }

    container.innerHTML = html;
}

function removeFav(key) {
    const book = getFavorites();
    delete book[key];
    saveFavorites(book);
    const el = document.getElementById(`fav-${key}`);
    if (el) {
        el.style.transition = "opacity 0.3s";
        el.style.opacity = "0";
        setTimeout(() => {
            el.remove();
            renderFavorites();
        }, 300);
    }
}

function clearFavorites() {
    if (!confirm("确定要清空所有收藏吗？")) return;
    localStorage.removeItem(FAVORITE_KEY);
    renderFavorites();
}

// ---------- 错题本 ----------

function renderWrongBook() {
    const section = document.getElementById("wrongbook-section");
    const container = document.getElementById("wrongbook-container");
    if (!section || !container) return;

    const groups = groupWrongBook();
    const totalWrong = Object.values(groups).reduce((sum, g) => sum + g.questions.length, 0);

    if (totalWrong === 0) {
        section.style.display = "none";
        return;
    }

    section.style.display = "block";

    let html = "";
    for (const [gKey, group] of Object.entries(groups)) {
        const qs = group.questions;
        html += `
            <div class="wrongbook-group">
                <div class="wrongbook-group-header">
                    <span class="wrongbook-bank-name">📄 ${escapeHTML(group.bank_name)}</span>
                    <span class="wrongbook-count">${qs.length} 道错题</span>
                </div>
                <div class="wrongbook-items">
        `;

        qs.forEach((item) => {
            const typeLabel = item.type === "multi" ? "多选题" : item.type === "judge" ? "判断题" : "单选题";
            const optText = Object.entries(item.question_options || {})
                .map(([k, v]) => `${k}. ${escapeHTML(String(v))}`)
                .join("　");

            html += `
                <div class="wrongbook-item" id="wrong-${escapeHTML(item.key)}">
                    <div class="wrongbook-q-header">
                        <span class="wrongbook-type ${item.type}">${typeLabel}</span>
                        <span class="wrongbook-qtext">${escapeHTML(item.question_text)}</span>
                    </div>
                    <div class="wrongbook-q-body" style="display:none;">
                        <div class="wrongbook-opts">${optText}</div>
                        <div class="wrongbook-answers">
                            <span class="wrongbook-user-ans">你的答案：<strong>${escapeHTML(item.user_wrong_answer)}</strong></span>
                            <span class="wrongbook-correct-ans">正确答案：<strong>${escapeHTML(item.correct_answer)}</strong></span>
                        </div>
                        <div class="wrongbook-meta">
                            答错 <strong>${item.wrong_count}</strong> 次
                            · 最后 ${escapeHTML(item.last_wrong_time)}
                        </div>
                    </div>
                    <div class="wrongbook-actions">
                        <button class="btn btn-small btn-secondary" onclick="toggleWrongDetail(this)">查看详情</button>
                        <button class="btn btn-small btn-danger-outline" onclick="deleteWrongItem('${escapeHTML(item.key)}')">已掌握 ✕</button>
                    </div>
                </div>
            `;
        });

        // "重新练习" 按钮
        const wrongCount = qs.length;
        html += `
                </div>
                <div class="wrongbook-group-footer">
                    <a href="/quiz/${group.bank_id}?mode=practice&count=${wrongCount}" class="btn btn-primary btn-small">📝 重练这 ${wrongCount} 道错题</a>
                </div>
            </div>
        `;
    }

    container.innerHTML = html;
}

function toggleWrongDetail(btn) {
    const item = btn.closest(".wrongbook-item");
    const body = item.querySelector(".wrongbook-q-body");
    const isHidden = body.style.display === "none" || !body.style.display;
    body.style.display = isHidden ? "block" : "none";
    btn.textContent = isHidden ? "收起详情" : "查看详情";
}

function deleteWrongItem(key) {
    removeFromWrongBook(key);
    const el = document.getElementById(`wrong-${key}`);
    if (el) {
        el.style.transition = "opacity 0.3s";
        el.style.opacity = "0";
        setTimeout(() => {
            el.remove();
            // 如果整个组空了，重新渲染
            renderWrongBook();
        }, 300);
    }
}

function clearWrongBook() {
    if (!confirm("确定要清空所有错题吗？")) return;
    localStorage.removeItem(WRONG_BOOK_KEY);
    renderWrongBook();
}


