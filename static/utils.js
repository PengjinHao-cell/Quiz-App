/**
 * 刷题通 - 全局共享工具函数
 */

/**
 * 转义 HTML 特殊字符，防止 XSS
 */
function escapeHTML(str) {
    if (str === null || str === undefined) return "";
    const div = document.createElement("div");
    div.textContent = String(str);
    return div.innerHTML;
}
