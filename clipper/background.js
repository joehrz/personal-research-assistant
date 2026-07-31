// Service worker: context menu + keyboard shortcut for one-shot clipping.

const API = "http://127.0.0.1:8734/api/capture";

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "clip-selection",
    title: "Clip to Research Assistant",
    contexts: ["selection", "page"],
  });
});

async function getSelection(tabId) {
  try {
    const [{ result }] = await chrome.scripting.executeScript({
      target: { tabId },
      func: () => window.getSelection()?.toString() ?? "",
    });
    return result || "";
  } catch {
    return ""; // restricted pages (chrome://, web store) don't allow injection
  }
}

async function clip(tab) {
  const selection = await getSelection(tab.id);
  // With no selection, clip the page itself as a bookmark-style snippet.
  const text = selection.trim() || `${tab.title}\n${tab.url}`;
  const res = await fetch(API, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      text,
      source_url: tab.url ?? "",
      source_title: tab.title ?? "",
    }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
}

async function clipWithBadge(tab) {
  try {
    await clip(tab);
    await chrome.action.setBadgeBackgroundColor({ color: "#22c55e" });
    await chrome.action.setBadgeText({ tabId: tab.id, text: "✓" });
  } catch {
    await chrome.action.setBadgeBackgroundColor({ color: "#ef4444" });
    await chrome.action.setBadgeText({ tabId: tab.id, text: "!" });
  }
  setTimeout(() => chrome.action.setBadgeText({ tabId: tab.id, text: "" }), 2000);
}

chrome.contextMenus.onClicked.addListener((_info, tab) => {
  if (tab) void clipWithBadge(tab);
});

chrome.commands.onCommand.addListener(async (command, tab) => {
  if (command === "clip-selection" && tab) void clipWithBadge(tab);
});
