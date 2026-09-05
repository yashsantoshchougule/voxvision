(() => {
  const DEFAULTS = { top: 76, right: 20, width: 320, height: 260, threshold: 0.12, intervalSeconds: 7 };

  const escapeHtml = (value) => String(value ?? "").replace(/[&<>'"]/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[character]));
  const trimPreview = (value) => value ? value.slice(-220) : "Nothing captured yet.";

  class VoxVisionWidget {
    static async mount() {
      if (document.getElementById("voxvision-ai-host")) return window.__voxvisionWidget || null;
      const widget = new VoxVisionWidget();
      window.__voxvisionWidget = widget;
      await widget.initialize();
      return widget;
    }

    static async toggleFromToolbar() {
      const existingHost = document.getElementById("voxvision-ai-host");
      if (!existingHost) {
        await VoxVisionWidget.mount();
        return { ok: true, visible: true, downloaded: false };
      }
      const widget = window.__voxvisionWidget;
      if (!widget) {
        existingHost.remove();
        return { ok: true, visible: false, downloaded: false };
      }
      return widget.closeFromToolbar();
    }

    constructor() {
      this.state = { meetingId: null, active: false, paused: false, audio: "off", screen: "off", backend: "checking", lastTranscript: "", lastScreen: "", report: null, tab: "session" };
      this.transcriptBuffer = [];
      this.recognition = null;
      this.screenStream = null;
      this.video = document.createElement("video");
      this.canvas = document.createElement("canvas");
      this.previousPixels = null;
      this.frameTimer = null;
      this.lastOcrAt = 0;
    }

    async initialize() {
      this.host = document.createElement("div");
      this.host.id = "voxvision-ai-host";
      this.host.style.all = "initial";
      document.documentElement.append(this.host);
      this.shadow = this.host.attachShadow({ mode: "open" });
      const style = document.createElement("link");
      style.rel = "stylesheet";
      style.href = chrome.runtime.getURL("widget/widget.css");
      this.shadow.append(style);
      this.shadow.innerHTML += this.template();
      this.root = this.shadow.querySelector(".vv-widget");
      const saved = await chrome.storage.local.get("voxvisionWidget");
      this.geometry = { ...DEFAULTS, ...(saved.voxvisionWidget || {}) };
      this.applyGeometry();
      this.bindEvents();
      this.render();
      this.checkBackend();
    }

    template() {
      return `<section class="vv-widget" aria-label="VoxVision AI meeting assistant"><header class="vv-titlebar"><span class="vv-logo">VV</span><strong>VoxVision AI</strong><span class="vv-spacer"></span><button class="vv-icon" data-action="minimize" title="Minimize">−</button><button class="vv-icon" data-action="close" title="Close">×</button></header><main class="vv-body"><label class="vv-view-picker">View<select name="tab"><option value="session">Session</option><option value="transcript">Transcript</option><option value="screen">Screen text</option><option value="graph">Graph data</option><option value="important">Important points</option><option value="report">Report</option><option value="settings">Settings</option></select></label><div class="vv-tab-panel"></div></main></section>`;
    }

    bindEvents() {
      this.shadow.addEventListener("click", (event) => this.handleClick(event));
      this.shadow.addEventListener("change", (event) => this.handleChange(event));
      const bar = this.shadow.querySelector(".vv-titlebar");
      bar.addEventListener("pointerdown", (event) => this.beginDrag(event));
      const observer = new ResizeObserver(() => { this.saveGeometry().catch(() => {}); });
      observer.observe(this.root);
    }

    handleChange(event) {
      if (event.target.name === "tab") { this.state.tab = event.target.value; this.render(); return; }
      if (event.target.name === "mode") this.selectedMode = event.target.value;
      if (event.target.name === "threshold") this.geometry.threshold = Number(event.target.value) / 100;
      if (event.target.name === "interval") this.geometry.intervalSeconds = Number(event.target.value);
    }

    async handleClick(event) {
      const action = event.target.dataset.action;
      const tab = event.target.dataset.tab;
      if (tab) { this.state.tab = tab; this.render(); return; }
      if (!action) return;
      try {
        if (action === "start") await this.start();
        if (action === "pause") await this.pause();
        if (action === "resume") await this.resume();
        if (action === "important") await this.markImportant();
        if (action === "stop") await this.stopAndGenerate();
        if (action === "minimize") { this.root.classList.toggle("vv-minimized"); await this.saveGeometry(); }
        if (action === "close") await this.closeFromToolbar();
        if (action === "retry") await this.checkBackend();
        if (action === "save-report") await this.saveReport();
        if (action === "download") await this.downloadReport();
      } catch (error) {
        this.state.error = error.message || "An unexpected error occurred.";
        this.render();
      }
    }

    async request(path, options = {}) {
      if (!this.isExtensionActive()) throw new Error("VoxVision was updated. Refresh this page, then try again.");
      let body;
      if (options.body instanceof FormData) {
        const file = options.body.get("file");
        if (!(file instanceof Blob)) throw new Error("The screen image could not be prepared.");
        body = { type: "multipart-image", file: { fieldName: "file", fileName: file.name || "frame.jpg", contentType: file.type || "image/jpeg", data: await this.blobToBase64(file) } };
      } else if (options.body !== undefined) {
        body = { type: "json", data: typeof options.body === "string" ? options.body : JSON.stringify(options.body) };
      }
      let result;
      try {
        result = await chrome.runtime.sendMessage({ type: "voxvision-api-request", path, method: options.method || "GET", body });
      } catch (error) {
        if (!this.isExtensionActive() || /context invalidated/i.test(String(error?.message || error))) {
          throw new Error("VoxVision was updated. Refresh this page, then try again.");
        }
        throw error;
      }
      if (!result?.ok) throw new Error(result?.error || "Backend unavailable. Start FastAPI, then retry.");
      const headers = new Headers({ "content-type": result.contentType || (result.kind === "json" ? "application/json" : "application/octet-stream") });
      if (result.kind === "binary") return new Response(this.base64ToBlob(result.data, result.contentType), { status: result.status, headers });
      return result.data;
    }

    async blobToBase64(blob) {
      const dataUrl = await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(blob);
      });
      return String(dataUrl).split(",", 2)[1];
    }

    base64ToBlob(base64, contentType) {
      const binary = atob(base64);
      const bytes = new Uint8Array(binary.length);
      for (let index = 0; index < binary.length; index += 1) bytes[index] = binary.charCodeAt(index);
      return new Blob([bytes], { type: contentType || "application/octet-stream" });
    }

    isExtensionActive() {
      try { return typeof chrome !== "undefined" && Boolean(chrome.runtime?.id); }
      catch (_) { return false; }
    }

    async checkBackend() {
      try { await this.request("/health"); this.state.backend = "on"; this.state.error = ""; }
      catch (error) {
        this.state.backend = "off";
        this.state.error = error?.message || "Backend unavailable. Start FastAPI, then retry.";
      }
      this.render();
    }

    async start() {
      if (this.state.backend !== "on") throw new Error("Backend is unavailable. Start it and retry.");
      const pageTitle = document.title?.trim() || location.hostname || "Untitled session";
      const title = (this.shadow.querySelector("[name=title]")?.value.trim() || pageTitle).slice(0, 200);
      this.selectedMode = this.selectedMode || this.shadow.querySelector("[name=mode]")?.value || "combined";
      const screenRequest = navigator.mediaDevices.getDisplayMedia({ video: { frameRate: 2 }, audio: true });
      let meeting;
      try {
        meeting = await this.request("/api/meetings", { method: "POST", body: JSON.stringify({ title, platform: location.hostname || "Web", selected_mode: this.selectedMode, audio_mode: "microphone", audio_enabled: true, screen_analysis_enabled: true }) });
      } catch (error) {
        screenRequest.then((stream) => stream.getTracks().forEach((track) => track.stop())).catch(() => {});
        throw error;
      }
      this.state.meetingId = meeting.id;
      this.state.active = true;
      this.state.paused = false;
      this.state.error = "";
      this.startSpeech();
      await this.startScreen(screenRequest);
      this.render();
    }

    startSpeech() {
      const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!Recognition) { this.state.audio = "unsupported"; this.state.error = "Speech Recognition is unavailable. Screen text collection can still continue."; return; }
      this.recognition = new Recognition();
      this.recognition.continuous = true;
      this.recognition.interimResults = true;
      this.recognition.lang = navigator.language || "en-US";
      this.recognition.onresult = (event) => {
        let finalText = "";
        for (let index = event.resultIndex; index < event.results.length; index += 1) if (event.results[index].isFinal) finalText += event.results[index][0].transcript;
        if (finalText.trim()) this.recordTranscript(finalText.trim());
      };
      this.recognition.onerror = (event) => { if (event.error !== "aborted" && event.error !== "no-speech") { this.state.audio = "error"; this.state.error = `Microphone transcription: ${event.error}.`; this.render(); } };
      this.recognition.onend = () => { if (this.state.active && !this.state.paused) try { this.recognition.start(); } catch (_) {} };
      try { this.recognition.start(); this.state.audio = "microphone"; } catch (_) { this.state.audio = "error"; }
    }

    async recordTranscript(text) {
      this.state.lastTranscript = text;
      this.transcriptBuffer.push({ text, is_final: true, source: "microphone" });
      this.render();
      try { await this.flushTranscripts(); } catch (_) { /* Retain the local buffer for a later stop attempt. */ }
    }

    async flushTranscripts() {
      if (!this.state.meetingId || !this.transcriptBuffer.length) return;
      const items = this.transcriptBuffer.splice(0);
      try { await this.request(`/api/meetings/${this.state.meetingId}/transcripts/batch`, { method: "POST", body: JSON.stringify({ items }) }); }
      catch (error) { this.transcriptBuffer.unshift(...items); throw error; }
    }

    async startScreen(streamRequest) {
      try {
        this.screenStream = await (streamRequest || navigator.mediaDevices.getDisplayMedia({ video: { frameRate: 2 }, audio: true }));
        this.video.srcObject = this.screenStream;
        await this.video.play();
        this.screenStream.getVideoTracks()[0].addEventListener("ended", () => this.stopScreen());
        this.frameTimer = window.setInterval(() => this.processFrame(), 1000);
        this.state.screen = this.screenStream.getAudioTracks().length ? "tab audio + screen" : "screen";
      } catch (_) { this.state.screen = "denied"; this.state.error = "Screen sharing was cancelled or denied. Microphone transcription continues."; }
    }

    async processFrame() {
      if (!this.state.active || this.state.paused || !this.video.videoWidth || Date.now() - this.lastOcrAt < this.geometry.intervalSeconds * 1000) return;
      const width = 160, height = 90;
      this.canvas.width = width; this.canvas.height = height;
      const context = this.canvas.getContext("2d", { willReadFrequently: true });
      context.drawImage(this.video, 0, 0, width, height);
      const pixels = context.getImageData(0, 0, width, height).data;
      let score = 1;
      if (this.previousPixels) {
        let total = 0;
        for (let index = 0; index < pixels.length; index += 16) total += Math.abs(pixels[index] - this.previousPixels[index]) + Math.abs(pixels[index + 1] - this.previousPixels[index + 1]) + Math.abs(pixels[index + 2] - this.previousPixels[index + 2]);
        score = total / ((pixels.length / 16) * 765);
      }
      this.previousPixels = new Uint8ClampedArray(pixels);
      if (score < this.geometry.threshold) return;
      this.lastOcrAt = Date.now();
      this.canvas.width = this.video.videoWidth; this.canvas.height = this.video.videoHeight;
      context.drawImage(this.video, 0, 0);
      const blob = await new Promise((resolve) => this.canvas.toBlob(resolve, "image/jpeg", 0.8));
      if (!blob) return;
      const form = new FormData(); form.append("file", blob, "frame.jpg");
      try {
        const result = await this.request(`/api/meetings/${this.state.meetingId}/screen/analyze?change_score=${score.toFixed(3)}`, { method: "POST", body: form });
        if (result.extracted_text && result.extracted_text !== this.state.lastScreen) this.state.lastScreen = result.extracted_text;
        this.state.lastChart = result;
      } catch (error) { this.state.error = error.message; }
      this.render();
    }

    stopScreen() {
      if (this.frameTimer) window.clearInterval(this.frameTimer);
      this.frameTimer = null;
      this.screenStream?.getTracks().forEach((track) => track.stop());
      this.screenStream = null;
      this.video.srcObject = null;
      this.state.screen = "off";
    }

    async pause() { this.state.paused = true; this.recognition?.stop(); await this.request(`/api/meetings/${this.state.meetingId}/pause`, { method: "POST" }); this.render(); }
    async resume() { this.state.paused = false; await this.request(`/api/meetings/${this.state.meetingId}/resume`, { method: "POST" }); this.startSpeech(); this.render(); }

    async markImportant() {
      if (!this.state.meetingId) throw new Error("Start analysis before marking a point.");
      const label = this.shadow.querySelector("[name=important-label]")?.value || "Important";
      const user_note = this.shadow.querySelector("[name=important-note]")?.value.trim() || null;
      await this.request(`/api/meetings/${this.state.meetingId}/important-points`, { method: "POST", body: JSON.stringify({ label, user_note, transcript_context: this.state.lastTranscript, screen_context: this.state.lastScreen }) });
      this.state.importantMessage = "Marked important."; this.render();
    }

    async stopAndGenerate() {
      if (!this.state.meetingId) return;
      if (this.stopPromise) return this.stopPromise;
      this.stopPromise = this.performStopAndGenerate();
      try { return await this.stopPromise; }
      finally { this.stopPromise = null; }
    }

    async performStopAndGenerate() {
      this.state.processing = true; this.render();
      try {
        this.state.active = false; this.recognition?.stop(); this.stopScreen();
        await this.flushTranscripts();
        await this.request(`/api/meetings/${this.state.meetingId}/stop`, { method: "POST" });
        this.state.report = await this.request(`/api/meetings/${this.state.meetingId}/reports/generate`, { method: "POST" });
        this.state.tab = "report";
      } finally {
        this.state.processing = false;
        this.render();
      }
    }

    async saveReport() {
      const raw = this.shadow.querySelector("[name=report-json]")?.value;
      let edited;
      try { edited = JSON.parse(raw); } catch (_) { throw new Error("The report editor must contain valid JSON."); }
      this.state.report = await this.request(`/api/meetings/${this.state.meetingId}/report`, { method: "PUT", body: JSON.stringify(edited) });
      this.state.error = ""; this.render();
    }

    async downloadReport() {
      if (!this.state.meetingId) throw new Error("Generate a report before downloading it.");
      const response = await this.request(`/api/meetings/${this.state.meetingId}/export/pdf`);
      const blob = await response.blob();
      const result = await chrome.runtime.sendMessage({
        type: "voxvision-download",
        filename: `voxvision-report-${this.state.meetingId}.pdf`,
        contentType: "application/pdf",
        data: await this.blobToBase64(blob),
      });
      if (!result?.ok) throw new Error(result?.error || "The PDF could not be downloaded.");
    }

    async cleanup() { this.state.active = false; this.recognition?.stop(); this.stopScreen(); await this.flushTranscripts().catch(() => {}); }

    async closeFromToolbar() {
      const hadActiveWork = Boolean(this.state.active || this.state.paused || this.state.processing);
      this.host.style.display = "none";
      try {
        if (hadActiveWork) {
          await this.stopAndGenerate();
          await this.downloadReport();
        } else {
          await this.cleanup();
        }
        this.host.remove();
        if (window.__voxvisionWidget === this) window.__voxvisionWidget = null;
        return { ok: true, visible: false, downloaded: hadActiveWork };
      } catch (error) {
        this.host.style.display = "";
        this.state.error = error?.message || "VoxVision could not finish the session.";
        this.render();
        throw error;
      }
    }

    beginDrag(event) {
      if (event.target.closest("button")) return;
      const rect = this.root.getBoundingClientRect(); const offsetX = event.clientX - rect.left; const offsetY = event.clientY - rect.top;
      const move = (moveEvent) => { this.root.style.left = `${Math.max(0, moveEvent.clientX - offsetX)}px`; this.root.style.top = `${Math.max(0, moveEvent.clientY - offsetY)}px`; this.root.style.right = "auto"; };
      const up = () => { document.removeEventListener("pointermove", move); document.removeEventListener("pointerup", up); this.saveGeometry().catch(() => {}); };
      document.addEventListener("pointermove", move); document.addEventListener("pointerup", up);
    }

    applyGeometry() { Object.assign(this.root.style, { top: `${this.geometry.top}px`, right: `${this.geometry.right}px`, width: `${this.geometry.width}px`, height: `${this.geometry.height}px` }); }
    async saveGeometry() {
      if (!this.isExtensionActive()) return;
      const rect = this.root.getBoundingClientRect();
      try {
        await chrome.storage.local.set({ voxvisionWidget: { ...this.geometry, top: Math.round(rect.top), right: Math.round(window.innerWidth - rect.right), width: Math.round(rect.width), height: Math.round(rect.height) } });
      } catch (error) {
        if (this.isExtensionActive()) throw error;
      }
    }

    status(name, value, state = "") { return `<span class="vv-chip"><span class="vv-dot ${state}">●</span> ${name}: ${escapeHtml(value)}</span>`; }
    render() {
      if (!this.root) return;
      const panel = this.shadow.querySelector(".vv-tab-panel");
      const mode = this.selectedMode || "combined";
      const data = { session: `<div class="vv-grid"><label class="vv-field">Meeting title<input name="title" maxlength="200" placeholder="Optional meeting title"></label><label class="vv-field">Output mode<select name="mode"><option value="combined" ${mode === "combined" ? "selected" : ""}>Combined</option><option value="notes">Notes</option><option value="summary">Summary</option><option value="insights">Insights</option></select></label></div><div class="vv-status">${this.status("Session", this.state.processing ? "Processing" : this.state.paused ? "Paused" : this.state.active ? "Active" : "Idle", this.state.active ? "on" : "")}${this.status("Mic", this.state.audio, this.state.audio === "microphone" ? "on" : "warn")}${this.status("Screen", this.state.screen, this.state.screen.includes("screen") ? "on" : "")}${this.status("Backend", this.state.backend === "on" ? "Connected" : "Offline", this.state.backend)}</div><div class="vv-preview"><strong>Latest transcript:</strong><br>${escapeHtml(trimPreview(this.state.lastTranscript))}</div><div class="vv-preview"><strong>Latest screen text:</strong><br>${escapeHtml(trimPreview(this.state.lastScreen))}</div><div class="vv-actions">${!this.state.active && !this.state.processing ? `<button class="primary" data-action="start">Start Analysis</button>` : ""}${this.state.active && !this.state.paused ? `<button data-action="pause">Pause</button>` : ""}${this.state.active && this.state.paused ? `<button data-action="resume">Resume</button>` : ""}${this.state.active ? `<button data-action="important">Mark Important</button><button class="danger" data-action="stop">Stop & Generate</button>` : ""}<button data-action="retry">Retry Backend</button></div>`, transcript: `<p>${escapeHtml(this.state.lastTranscript || "Final microphone speech will appear here.")}</p>`, screen: `<p>${escapeHtml(this.state.lastScreen || "Select a screen or tab after starting.")}</p>`, graph: this.state.lastChart ? `<p><strong>${escapeHtml(this.state.lastChart.chart_type || "No chart")}</strong></p><p>${escapeHtml(this.state.lastChart.basic_observation || "No reliable graph observation.")}</p><pre>${escapeHtml(JSON.stringify(this.state.lastChart.parsed_values || [], null, 2))}</pre>` : "<p>No chart data captured.</p>", important: `<div class="vv-label-row"><select name="important-label"><option>Important</option><option>Decision</option><option>Task</option><option>Question</option><option>Risk</option><option>Follow-up</option></select><button data-action="important">Mark Important</button></div><textarea name="important-note" placeholder="Optional note"></textarea><p>${escapeHtml(this.state.importantMessage || "Marking uses the current transcript and OCR context.")}</p>`, report: this.state.report ? `<div class="vv-report"><textarea name="report-json">${escapeHtml(JSON.stringify(this.state.report, null, 2))}</textarea><div class="vv-actions"><button data-action="save-report">Save edits</button><button class="primary" data-action="download">Download PDF</button></div></div>` : "<p>Stop the meeting to generate an editable report.</p>", settings: `<label class="vv-field">Screen-change threshold (%)<input name="threshold" type="number" min="1" max="100" value="${Math.round(this.geometry.threshold * 100)}"></label><label class="vv-field">Minimum OCR interval (seconds)<input name="interval" type="number" min="5" max="60" value="${this.geometry.intervalSeconds}"></label><p>Lower thresholds process more changes.</p>` };
      panel.innerHTML = data[this.state.tab];
      const viewSelect = this.shadow.querySelector("[name=tab]");
      if (viewSelect) viewSelect.value = this.state.tab;
      const modeSelect = this.shadow.querySelector("[name=mode]");
      if (modeSelect) modeSelect.value = mode;
      this.shadow.querySelectorAll("[data-tab]").forEach((button) => button.classList.toggle("primary", button.dataset.tab === this.state.tab));
      const previousError = this.shadow.querySelector(".vv-error"); if (previousError) previousError.remove();
      if (this.state.error) this.shadow.querySelector(".vv-body").insertAdjacentHTML("beforeend", `<p class="vv-error">${escapeHtml(this.state.error)}</p>`);
    }
  }

  window.VoxVisionWidget = VoxVisionWidget;
})();
