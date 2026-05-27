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
    renderHistory();
});

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
        renderHistory();
    }
}

function clearHistory() {
    if (!confirm("确定要清空所有答题记录吗？此操作不可恢复。")) return;
    localStorage.removeItem("quizHistory");
    renderHistory();
}


