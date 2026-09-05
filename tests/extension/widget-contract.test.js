const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const extensionRoot = path.join(__dirname, "../../extension");

test("canonical extension manifest points to existing scripts", () => {
  const manifest = JSON.parse(fs.readFileSync(path.join(extensionRoot, "manifest.json"), "utf8"));
  assert.equal(manifest.manifest_version, 3);
  assert.equal(manifest.version, "1.2.1");
  assert.equal(manifest.version_name, "Toolbar Fix 1.2.1");
  assert.equal(manifest.content_scripts.length, 1);
  assert.deepEqual(manifest.content_scripts[0].matches, ["http://*/*", "https://*/*"]);
  for (const permission of ["activeTab", "scripting", "downloads"]) assert.equal(manifest.permissions.includes(permission), true);
  assert.deepEqual(manifest.web_accessible_resources[0].matches, ["<all_urls>"]);

  const referencedScripts = [
    manifest.background.service_worker,
    ...manifest.content_scripts.flatMap((entry) => entry.js),
  ];
  for (const script of referencedScripts) {
    assert.equal(fs.existsSync(path.join(extensionRoot, script)), true, `${script} should exist`);
  }
});

test("widget uses the native screen picker and preserves the selected report mode", () => {
  const source = fs.readFileSync(path.join(extensionRoot, "content/widget-injector.js"), "utf8");
  assert.match(source, /navigator\.mediaDevices\.getDisplayMedia/);
  assert.doesNotMatch(source, /authorize tab audio/i);
  assert.doesNotMatch(source, /vv-notice|not permanently stored|immediately discarded|only text returned by OCR is saved/i);
  assert.match(source, /modeSelect\.value = mode/);
  assert.match(source, /toggleFromToolbar/);
  assert.match(source, /export\/pdf/);
  assert.match(source, /voxvision-download/);

  const contentSource = fs.readFileSync(path.join(extensionRoot, "content/content.js"), "utf8");
  assert.match(contentSource, /voxvision-toggle/);
  assert.doesNotMatch(contentSource, /window\.VoxVisionWidget\.mount\(\);/);
});
