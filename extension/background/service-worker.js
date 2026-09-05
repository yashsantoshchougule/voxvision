const API_BASE_URL = "http://127.0.0.1:8000";
const WIDGET_SCRIPT_FILES = ["content/widget-injector.js", "content/content.js"];

function bytesToBase64(buffer) {
  const bytes = new Uint8Array(buffer);
  let binary = "";
  const chunkSize = 0x8000;
  for (let index = 0; index < bytes.length; index += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(index, index + chunkSize));
  }
  return btoa(binary);
}

function base64ToBlob(base64, type) {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) bytes[index] = binary.charCodeAt(index);
  return new Blob([bytes], { type });
}

async function proxyApiRequest(message) {
  const options = { method: message.method || "GET", headers: {} };
  if (message.body?.type === "json") {
    options.headers["Content-Type"] = "application/json";
    options.body = message.body.data;
  }
  if (message.body?.type === "multipart-image") {
    const form = new FormData();
    const file = message.body.file;
    form.append(file.fieldName || "file", base64ToBlob(file.data, file.contentType), file.fileName || "frame.jpg");
    options.body = form;
  }

  try {
    const response = await fetch(`${API_BASE_URL}${message.path}`, options);
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      const data = await response.json().catch(() => ({}));
      const error = data.detail?.error || data.error || data.detail || `Backend request failed (${response.status}).`;
      return { ok: response.ok, status: response.status, kind: "json", data, error, contentType };
    }
    const data = bytesToBase64(await response.arrayBuffer());
    return { ok: response.ok, status: response.status, kind: "binary", data, contentType, error: response.ok ? "" : `Backend request failed (${response.status}).` };
  } catch (error) {
    return { ok: false, status: 0, error: "Backend unavailable. Start FastAPI, then retry." };
  }
}

async function downloadBase64File(message) {
  try {
    const mediaType = message.contentType || "application/octet-stream";
    const filename = String(message.filename || "voxvision-download").replace(/[\\/:*?"<>|]+/g, "-");
    const downloadId = await chrome.downloads.download({
      url: `data:${mediaType};base64,${message.data}`,
      filename,
      saveAs: false,
    });
    return { ok: true, downloadId };
  } catch (error) {
    return { ok: false, error: "The generated file could not be downloaded." };
  }
}

async function toggleWidgetForTab(tab) {
  if (!tab?.id) return;
  await clearActionError(tab.id);
  try {
    const response = await chrome.tabs.sendMessage(tab.id, { type: "voxvision-toggle" });
    if (response?.handled) return;
  } catch (_) {
    // The widget has not been injected into this tab yet.
  }

  try {
    await chrome.scripting.executeScript({ target: { tabId: tab.id }, files: WIDGET_SCRIPT_FILES });
    const response = await chrome.tabs.sendMessage(tab.id, { type: "voxvision-toggle" });
    if (!response?.handled) throw new Error("The widget controller did not respond.");
  } catch (error) {
    console.warn("VoxVision cannot run on this page.", error);
    await showActionError(tab.id);
  }
}

async function clearActionError(tabId) {
  await chrome.action.setBadgeText({ tabId, text: "" });
  await chrome.action.setTitle({ tabId, title: "VoxVision AI" });
}

async function showActionError(tabId) {
  await chrome.action.setBadgeBackgroundColor({ tabId, color: "#b91c1c" });
  await chrome.action.setBadgeText({ tabId, text: "ERR" });
  await chrome.action.setTitle({ tabId, title: "VoxVision cannot run on this page" });
}

chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.set({ voxvisionInstalledAt: new Date().toISOString() });
});

chrome.action.onClicked.addListener((tab) => {
  return toggleWidgetForTab(tab);
});

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type === "voxvision-ping") {
    sendResponse({ ok: true });
    return;
  }
  if (message?.type === "voxvision-api-request") {
    proxyApiRequest(message).then(sendResponse);
    return true;
  }
  if (message?.type === "voxvision-download") {
    downloadBase64File(message).then(sendResponse);
    return true;
  }
});
