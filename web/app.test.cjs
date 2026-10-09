"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { gradeEvent } = require("./app.js");

for (const [term, lln, boundaries] of [
  ["Neutrophil count decreased", 1800, [1500, 1000, 500]],
  ["Platelet count decreased", 150000, [75000, 50000, 25000]]
]) {
  test(`CTCAE v5 exact grade boundaries: ${term}`, () => {
    const [g1,g2,g3] = boundaries;
    for (const [value, grade] of [
      [lln, null], [lln - 1, 1], [g1, 1],
      [g1 - 1, 2], [g2, 2], [g2 - 1, 3],
      [g3, 3], [g3 - 1, 4], [0, 4]
    ]) {
      assert.equal(gradeEvent(term, value, lln).grade, grade);
    }
  });
}

test("Rejects nonfinite, negative, unsupported and missing inputs", () => {
  for (const args of [
    ["Anemia", 8, 12],
    ["Neutrophil count decreased", "", 1800],
    ["Neutrophil count decreased", "abc", 1800],
    ["Neutrophil count decreased", -1, 1800],
    ["Neutrophil count decreased", NaN, 1800],
    ["Neutrophil count decreased", 900, 1500],
    ["Platelet count decreased", 20000, Infinity]
  ]) {
    assert.throws(() => gradeEvent(...args));
  }
});
