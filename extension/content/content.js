(() => {
  if (!window.VoxVisionWidget) return;

  if (!window.__voxvisionToggleListenerInstalled) {
    window.__voxvisionToggleListenerInstalled = true;
    chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
      if (message?.type !== "voxvision-toggle") return;
      window.VoxVisionWidget.toggleFromToolbar()
        .then((result) => sendResponse({ handled: true, ...result }))
        .catch((error) => sendResponse({ handled: true, ok: false, error: error?.message || "VoxVision could not be toggled." }));
      return true;
    });
  }

})();
