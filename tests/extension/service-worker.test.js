const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

function loadWorker(fetchImplementation, controls = {}) {
  let messageListener;
  let actionListener;
  const actionState = { badgeText: [], badgeColor: [], titles: [] };
  const context = {
    atob,
    btoa,
    Blob,
    FormData,
    Response,
    Uint8Array,
    fetch: fetchImplementation,
    console,
    chrome: {
      storage: { local: { set() {} } },
      action: {
        onClicked: { addListener(listener) { actionListener = listener; } },
        async setBadgeText(options) { actionState.badgeText.push(options); },
        async setBadgeBackgroundColor(options) { actionState.badgeColor.push(options); },
        async setTitle(options) { actionState.titles.push(options); },
      },
      tabs: { sendMessage: controls.sendMessage || (async () => { throw new Error("No content script"); }) },
      scripting: { executeScript: controls.executeScript || (async () => {}) },
      downloads: { download: controls.download || (async () => 1) },
      runtime: {
        onInstalled: { addListener() {} },
        onMessage: { addListener(listener) { messageListener = listener; } },
      },
    },
  };
  const source = fs.readFileSync(path.join(__dirname, "../../extension/background/service-worker.js"), "utf8");
  vm.runInNewContext(source, context, { filename: "service-worker.js" });
  return { messageListener, actionListener, actionState };
}

function send(listener, message) {
  return new Promise((resolve) => {
    const keepChannelOpen = listener(message, {}, resolve);
    assert.equal(keepChannelOpen, true);
  });
}

test("background worker proxies backend JSON responses", async () => {
  const { messageListener } = loadWorker(async (url, options) => {
    assert.equal(url, "http://127.0.0.1:8000/health");
    assert.equal(options.method, "GET");
    return new Response(JSON.stringify({ status: "ok" }), { status: 200, headers: { "content-type": "application/json" } });
  });
  const result = await send(messageListener, { type: "voxvision-api-request", path: "/health", method: "GET" });
  assert.equal(result.ok, true);
  assert.equal(result.data.status, "ok");
});

test("background worker returns a useful offline result", async () => {
  const { messageListener } = loadWorker(async () => { throw new Error("connection refused"); });
  const result = await send(messageListener, { type: "voxvision-api-request", path: "/health", method: "GET" });
  assert.equal(result.ok, false);
  assert.match(result.error, /Backend unavailable/);
});

test("background worker transports Word responses as base64", async () => {
  const { messageListener } = loadWorker(async () => new Response(new Uint8Array([80, 75, 3, 4]), {
    status: 200,
    headers: { "content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document" },
  }));
  const result = await send(messageListener, { type: "voxvision-api-request", path: "/api/meetings/example/export/docx", method: "GET" });
  assert.equal(result.ok, true);
  assert.equal(result.kind, "binary");
  assert.equal(result.data, "UEsDBA==");
});

test("toolbar click injects the widget into the active webpage", async () => {
  let injection;
  let messageAttempts = 0;
  const { actionListener } = loadWorker(async () => new Response(), {
    sendMessage: async () => {
      messageAttempts += 1;
      if (messageAttempts === 1) throw new Error("No content script");
      return { handled: true, visible: true };
    },
    executeScript: async (options) => { injection = options; },
  });

  await actionListener({ id: 42 });

  assert.equal(injection.target.tabId, 42);
  assert.deepEqual(Array.from(injection.files), ["content/widget-injector.js", "content/content.js"]);
  assert.equal(messageAttempts, 2);
});

test("toolbar click toggles an existing widget without reinjecting", async () => {
  let injected = false;
  const { actionListener } = loadWorker(async () => new Response(), {
    sendMessage: async () => ({ handled: true, visible: false }),
    executeScript: async () => { injected = true; },
  });

  await actionListener({ id: 7 });

  assert.equal(injected, false);
});

test("toolbar click shows an error badge when Chrome blocks injection", async () => {
  const { actionListener, actionState } = loadWorker(async () => new Response(), {
    executeScript: async () => { throw new Error("Cannot access chrome:// page"); },
  });

  await actionListener({ id: 13 });

  assert.equal(actionState.badgeText.at(-1).text, "ERR");
  assert.match(actionState.titles.at(-1).title, /cannot run/i);
});

test("background worker downloads generated PDFs", async () => {
  let downloadOptions;
  const { messageListener } = loadWorker(async () => new Response(), {
    download: async (options) => { downloadOptions = options; return 99; },
  });

  const result = await send(messageListener, {
    type: "voxvision-download",
    filename: "voxvision-report.pdf",
    contentType: "application/pdf",
    data: "JVBERi0=",
  });

  assert.equal(result.ok, true);
  assert.equal(result.downloadId, 99);
  assert.equal(downloadOptions.filename, "voxvision-report.pdf");
  assert.match(downloadOptions.url, /^data:application\/pdf;base64,JVBERi0=/);
  assert.equal(downloadOptions.saveAs, false);
});
