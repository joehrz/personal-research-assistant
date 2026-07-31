const API = "http://127.0.0.1:8734/api/capture";

const $ = (id) => document.getElementById(id);

async function init() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab) return;
  $("source-url").value = tab.url ?? "";
  $("source-title").value = tab.title ?? "";
  try {
    const [{ result }] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => window.getSelection()?.toString() ?? "",
    });
    if (result) $("text").value = result.trim();
  } catch {
    /* restricted page — leave the textarea empty */
  }
  $("text").focus();
}

async function save() {
  const status = $("status");
  let text = $("text").value.trim();
  if (!text) {
    // nothing selected/typed: clip the page itself
    text = `${$("source-title").value}\n${$("source-url").value}`.trim();
  }
  if ($("as-task").checked && !/^(todo|task)\s*:/i.test(text)) {
    text = `todo: ${text}`;
  }
  status.textContent = "Saving…";
  status.className = "";
  try {
    const res = await fetch(API, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text,
        source_url: $("source-url").value,
        source_title: $("source-title").value,
      }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const body = await res.json();
    status.textContent = body.kind === "task" ? "Task created ✓" : "Saved to inbox ✓";
    status.className = "ok";
    setTimeout(() => window.close(), 700);
  } catch (e) {
    status.textContent = `Failed — is the app running? (${e.message})`;
    status.className = "err";
  }
}

document.addEventListener("DOMContentLoaded", init);
$("save").addEventListener("click", save);
document.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) save();
});
