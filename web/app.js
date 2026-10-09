"use strict";

// Counts are cells per microliter. Rules: NCI CTCAE v5.0, Investigations.
// https://dctd.cancer.gov/research/ctep-trials/for-sites/adverse-events/ctcae-v5-8x11.pdf
const LAB_TERMS = Object.freeze({
  "Neutrophil count decreased": Object.freeze([1500, 1000, 500]),
  "Platelet count decreased": Object.freeze([75000, 50000, 25000])
});

function gradeEvent(term, value, lln) {
  if (!Object.prototype.hasOwnProperty.call(LAB_TERMS, term)) {
    throw new Error("Select a supported CTCAE term.");
  }
  // Reject blank strings rather than converting them to zero.
  if (value === "" || value === null || lln === "" || lln === null) {
    throw new Error("A count and laboratory lower limit are required.");
  }
  const measured = Number(value);
  const lower = Number(lln);
  if (!Number.isFinite(measured) || !Number.isFinite(lower) || measured < 0) {
    throw new Error("Enter finite, nonnegative numerical counts.");
  }
  const [g1, g2, g3] = LAB_TERMS[term];
  if (lower <= g1) {
    throw new Error(`The laboratory LLN must exceed ${g1.toLocaleString("en-US")} /µL for this term.`);
  }
  const grade = measured >= lower ? null
    : measured >= g1 ? 1
    : measured >= g2 ? 2
    : measured >= g3 ? 3 : 4;
  return {
    term, value: measured, lln: lower, unit: "/µL",
    version: "5.0", grade,
    status: grade === null ? "No grade assigned — count at or above LLN" : `Grade ${grade}`
  };
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { gradeEvent, LAB_TERMS };
}

if (typeof document !== "undefined") {
  document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("grade-form");
    const term = document.getElementById("term");
    const value = document.getElementById("value");
    const lln = document.getElementById("lln");
    const output = document.getElementById("grade-output");
    const error = document.getElementById("form-error");
    const body = document.getElementById("results-body");
    const count = document.getElementById("record-count");
    const exportButton = document.getElementById("export");
    const clearButton = document.getElementById("clear");
    const empty = document.getElementById("empty-state");
    let records = [];

    function renderRecords() {
      body.replaceChildren();
      for (const record of records) {
        const tr = document.createElement("tr");
        for (const content of [record.timestamp, record.term,
          String(record.value), String(record.lln),
          record.grade === null ? "Not graded" : String(record.grade)]) {
          const td = document.createElement("td");
          td.textContent = content;
          tr.appendChild(td);
        }
        body.appendChild(tr);
      }
      count.textContent = String(records.length);
      empty.hidden = records.length > 0;
      exportButton.disabled = records.length === 0;
      clearButton.disabled = records.length === 0;
    }

    term.addEventListener("change", () => {
      lln.value = term.value === "Platelet count decreased" ? "150000" : "1800";
      output.textContent = "Enter a measurement to calculate a grade.";
      error.textContent = "";
    });

    form.addEventListener("submit", event => {
      event.preventDefault();
      try {
        const result = gradeEvent(term.value, value.value, lln.value);
        const timestamp = new Date().toISOString();
        records.push({ timestamp, ...result });
        output.textContent = `${result.status}. Measured ${result.value.toLocaleString("en-US")} /µL; LLN ${result.lln.toLocaleString("en-US")} /µL.`;
        error.textContent = "";
        renderRecords();
      } catch (exc) {
        output.textContent = "No result recorded.";
        error.textContent = exc.message;
      }
    });

    function cell(v) {
      const s = String(v ?? "");
      return /[",\r\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
    }

    exportButton.addEventListener("click", () => {
      const fields = ["timestamp", "term", "value", "lln", "unit", "ctcae_version", "ctcae_grade", "status"];
      const rows = [fields.join(",")];
      for (const r of records) {
        rows.push([r.timestamp, r.term, r.value, r.lln, r.unit,
          r.version, r.grade ?? "", r.status].map(cell).join(","));
      }
      const blob = new Blob([rows.join("\r\n") + "\r\n"], { type: "text/csv;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "ctcae-v5-lab-grades.csv";
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    });

    clearButton.addEventListener("click", () => {
      records = [];
      output.textContent = "Session results cleared.";
      error.textContent = "";
      renderRecords();
    });
    renderRecords();
  });
}
