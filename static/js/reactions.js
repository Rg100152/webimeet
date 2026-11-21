/**
 * WebiMeet — floating emoji reactions over the video stage.
 * Local clicks animate immediately and are posted to the shared feed;
 * reactions from other viewers arrive through the liveChat.js polling event.
 */
(function () {
  "use strict";

  const layer = document.getElementById("reaction-layer");
  const buttons = document.querySelectorAll(".emoji-btn");
  const webinarId = document.getElementById("chat-app")?.dataset.webinarId;
  if (!layer) return;

  function floatEmoji(emoji) {
    const node = document.createElement("span");
    node.className = "floating-emoji";
    node.textContent = emoji;
    node.style.left = `${8 + Math.random() * 78}%`;
    node.style.animationDuration = `${3 + Math.random() * 1.8}s`;
    node.style.fontSize = `${24 + Math.random() * 16}px`;
    layer.appendChild(node);
    node.addEventListener("animationend", () => node.remove());
  }

  buttons.forEach((button) => {
    button.addEventListener("click", async () => {
      const emoji = button.dataset.emoji;
      if (!emoji) return;
      floatEmoji(emoji);
      if (!webinarId) return;
      try {
        await fetch(`/api/reactions/${webinarId}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ emoji }),
        });
      } catch (_error) {
        /* local animation still works offline */
      }
    });
  });

  document.addEventListener("webimeet:reaction", (event) => {
    if (event.detail?.emoji) floatEmoji(event.detail.emoji);
  });
})();
