/**
 * WebiMeet — incremental real-time chat & Q&A engine.
 * Polls only messages newer than the highest id seen (after_id), every 2s.
 * No page reloads, no WebSockets, no heavy libraries.
 */
(function () {
  "use strict";

  const root = document.getElementById("chat-app");
  if (!root) return;

  const webinarId = root.dataset.webinarId;
  const feed = document.getElementById("chat-messages");
  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");
  const nameInput = document.getElementById("display-name");
  const questionToggle = document.getElementById("is-question");
  const counter = document.getElementById("char-count");
  const status = document.getElementById("conn-status");
  const emptyState = document.getElementById("chat-empty");

  let lastId = parseInt(root.dataset.lastId || "0", 10) || 0;
  let polling = true;

  const escapeHTML = (value) =>
    String(value).replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));

  const initials = (name) =>
    name.trim().split(/\s+/).map((w) => w[0]).join("").slice(0, 2).toUpperCase() || "?";

  const savedName = localStorage.getItem("webimeet:name");
  if (savedName && nameInput) nameInput.value = savedName;

  if (nameInput) {
    nameInput.addEventListener("change", () => {
      localStorage.setItem("webimeet:name", nameInput.value.trim());
    });
  }

  if (input && counter) {
    input.addEventListener("input", () => {
      counter.textContent = `${input.value.length}/500`;
    });
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        form.requestSubmit();
      }
    });
  }

  function isNearBottom() {
    return feed.scrollHeight - feed.scrollTop - feed.clientHeight < 120;
  }

  function scrollToBottom() {
    feed.scrollTop = feed.scrollHeight;
  }

  function renderMessage(msg) {
    if (emptyState) emptyState.remove();
    const article = document.createElement("article");
    article.className = "chat-msg" + (msg.is_question ? " is-question" : "");
    article.dataset.id = msg.id;
    article.innerHTML = `
      <div class="chat-msg-head">
        <div class="avatar">${escapeHTML(initials(msg.name))}</div>
        <strong>${escapeHTML(msg.name)}</strong>
        ${msg.is_question ? '<span class="qa-tag">◆ Q&A</span>' : ""}
        <time>${escapeHTML(msg.time_label || "")}</time>
      </div>
      <p>${escapeHTML(msg.message)}</p>`;
    return article;
  }

  async function poll() {
    if (!polling) return;
    try {
      const response = await fetch(`/api/chat/${webinarId}?after_id=${lastId}`, {
        headers: { Accept: "application/json" },
        cache: "no-store",
      });
      if (!response.ok) throw new Error("poll failed");
      const data = await response.json();

      const stick = isNearBottom();
      (data.messages || []).forEach((msg) => {
        if (feed.querySelector(`[data-id="${msg.id}"]`)) return;
        feed.appendChild(renderMessage(msg));
        if (parseInt(msg.id, 10) > lastId) lastId = parseInt(msg.id, 10);
      });

      (data.reactions || []).forEach((reaction) => {
        document.dispatchEvent(new CustomEvent("webimeet:reaction", {
          detail: { emoji: reaction.emoji, id: reaction.id },
        }));
        if (parseInt(reaction.id, 10) > lastId) lastId = parseInt(reaction.id, 10);
      });

      if (data.max_id && parseInt(data.max_id, 10) > lastId && (data.messages || []).length === 0 && (data.reactions || []).length === 0) {
        lastId = parseInt(data.max_id, 10);
      }
      if (stick) scrollToBottom();
      setStatus(true);
    } catch (_error) {
      setStatus(false);
    }
  }

  function setStatus(online) {
    if (!status) return;
    status.innerHTML = online
      ? '<span class="dot"></span> Live · 2s sync'
      : '<span class="dot" style="background:#f59e0b"></span> Reconnecting…';
    status.style.color = online ? "#10b981" : "#f59e0b";
  }

  if (form) {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const name = (nameInput?.value || "").trim();
      const message = (input?.value || "").trim();
      if (!name || !message) {
        if (!name) nameInput?.focus();
        return;
      }

      const submitBtn = form.querySelector('button[type="submit"]');
      if (submitBtn) submitBtn.disabled = true;

      try {
        const response = await fetch(`/api/chat/${webinarId}`, {
          method: "POST",
          headers: { "Content-Type": "application/json", Accept: "application/json" },
          body: JSON.stringify({
            name,
            message,
            is_question: questionToggle?.checked ? 1 : 0,
          }),
        });
        if (!response.ok) throw new Error("send failed");
        const data = await response.json();
        feed.appendChild(renderMessage(data.message));
        if (parseInt(data.message.id, 10) > lastId) lastId = parseInt(data.message.id, 10);
        input.value = "";
        if (questionToggle) questionToggle.checked = false;
        if (counter) counter.textContent = "0/500";
        localStorage.setItem("webimeet:name", name);
        scrollToBottom();
        setStatus(true);
      } catch (_error) {
        setStatus(false);
        alert("Message could not be sent. Please check your connection and try again.");
      } finally {
        if (submitBtn) submitBtn.disabled = false;
        input?.focus();
      }
    });
  }

  scrollToBottom();
  poll();
  setInterval(poll, 2000);
  document.addEventListener("visibilitychange", () => { if (!document.hidden) poll(); });
})();
