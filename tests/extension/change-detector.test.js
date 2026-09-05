const test = require("node:test");
const assert = require("node:assert/strict");

test("screen OCR uses a change threshold and seven second throttle", () => {
  const shouldAnalyze = (score, elapsed) => score >= 0.12 && elapsed >= 7000;
  assert.equal(shouldAnalyze(0.05, 10000), false);
  assert.equal(shouldAnalyze(0.3, 7000), true);
});
