// test_finance.js — tests for calculateFinancialImpact
// Run with:  node test_finance.js
"use strict";

const { calculateFinancialImpact } = require("./finance.js");

let pass = 0;
let fail = 0;

function check(label, fn) {
    try {
        fn();
        console.log("  PASS:", label);
        pass++;
    } catch (e) {
        console.log("  FAIL:", label, "->", e.message);
        fail++;
    }
}

console.log("\n=== Finance Agent Tests ===\n");

// ── TEST 1: Normal input – single sponsor decrease ──────────────────────────
check("single sponsor decrease", () => {
    const r = calculateFinancialImpact([
        { sponsor_name: "ABC Technologies", old_amount: 200000, new_amount: 120000 }
    ]);
    if (r.previous_total_sponsorship !== 200000)
        throw new Error("wrong previous: " + r.previous_total_sponsorship);
    if (r.updated_total_sponsorship !== 120000)
        throw new Error("wrong updated: " + r.updated_total_sponsorship);
    if (r.total_difference !== -80000)
        throw new Error("wrong diff: " + r.total_difference);
    if (r.financial_status !== "negative")
        throw new Error("wrong status: " + r.financial_status);
    if (r.sponsor_details.length !== 1)
        throw new Error("wrong details length");
    if (r.sponsor_details[0].change_type !== "decrease")
        throw new Error("wrong change_type: " + r.sponsor_details[0].change_type);
});

// ── TEST 1b: Multiple sponsors, mixed change ────────────────────────────────
check("multiple sponsors mixed", () => {
    const r = calculateFinancialImpact([
        { sponsor_name: "A", old_amount: 100000, new_amount: 150000 },
        { sponsor_name: "B", old_amount: 50000, new_amount: 30000 },
    ]);
    if (r.previous_total_sponsorship !== 150000)
        throw new Error("wrong previous: " + r.previous_total_sponsorship);
    if (r.updated_total_sponsorship !== 180000)
        throw new Error("wrong updated: " + r.updated_total_sponsorship);
    if (r.total_difference !== 30000)
        throw new Error("wrong diff: " + r.total_difference);
    if (r.financial_status !== "positive")
        throw new Error("wrong status: " + r.financial_status);
});

// ── TEST 2: Bad input – not an array must throw ─────────────────────────────
check("null input throws", () => {
    let threw = false;
    try { calculateFinancialImpact(null); } catch (e) { threw = true; }
    if (!threw) throw new Error("should have thrown for null");
});

check("string input throws", () => {
    let threw = false;
    try { calculateFinancialImpact("abc"); } catch (e) { threw = true; }
    if (!threw) throw new Error("should have thrown for string");
});

check("number input throws", () => {
    let threw = false;
    try { calculateFinancialImpact(42); } catch (e) { threw = true; }
    if (!threw) throw new Error("should have thrown for number");
});

check("undefined input throws", () => {
    let threw = false;
    try { calculateFinancialImpact(undefined); } catch (e) { threw = true; }
    if (!threw) throw new Error("should have thrown for undefined");
});

// ── TEST 2b: Null/bad individual sponsor inside array – recorded as error ───
check("null sponsor in array -> error entry, not crash", () => {
    const r = calculateFinancialImpact([null]);
    if (r.sponsor_details.length !== 1)
        throw new Error("should have one error entry");
    if (!r.sponsor_details[0].error)
        throw new Error("missing error field on bad entry");
    if (!r.sponsor_details[0].manual_review_required)
        throw new Error("missing manual_review_required");
    if (r.total_difference !== 0)
        throw new Error("bad entry should not add to totals, got: " + r.total_difference);
});

check("negative amount -> error entry, not crash", () => {
    const r = calculateFinancialImpact([
        { sponsor_name: "X", old_amount: -1000, new_amount: 5000 }
    ]);
    if (!r.sponsor_details[0].error)
        throw new Error("negative old_amount should produce error entry");
});

check("string amounts -> error entry (no silent NaN)", () => {
    // Number("abc") is NaN; must be caught, not silently added as NaN
    const r = calculateFinancialImpact([
        { sponsor_name: "X", old_amount: "abc", new_amount: 5000 }
    ]);
    if (!r.sponsor_details[0].error)
        throw new Error("NaN amount should produce error entry");
});

// ── TEST 3: Edge cases ───────────────────────────────────────────────────────
check("empty array -> zeros and neutral status", () => {
    const r = calculateFinancialImpact([]);
    if (r.previous_total_sponsorship !== 0) throw new Error("expected 0");
    if (r.updated_total_sponsorship !== 0) throw new Error("expected 0");
    if (r.total_difference !== 0) throw new Error("expected 0");
    if (r.financial_status !== "neutral") throw new Error("expected neutral");
    if (r.sponsor_details.length !== 0) throw new Error("expected empty details");
});

check("unchanged amount -> change_type unchanged, status neutral", () => {
    const r = calculateFinancialImpact([
        { sponsor_name: "Same Co", old_amount: 100000, new_amount: 100000 }
    ]);
    if (r.sponsor_details[0].change_type !== "unchanged")
        throw new Error("expected unchanged, got: " + r.sponsor_details[0].change_type);
    if (r.financial_status !== "neutral")
        throw new Error("expected neutral, got: " + r.financial_status);
});

check("string numbers coerce correctly (backend may send strings)", () => {
    // finance.js uses Number() so "200000" should work
    const r = calculateFinancialImpact([
        { sponsor_name: "A", old_amount: "200000", new_amount: "120000" }
    ]);
    if (r.total_difference !== -80000)
        throw new Error("string coercion failed, got: " + r.total_difference);
});

check("large amounts are rounded correctly", () => {
    const r = calculateFinancialImpact([
        { sponsor_name: "A", old_amount: 10000000, new_amount: 7500000 }
    ]);
    if (r.total_difference !== -2500000)
        throw new Error("wrong large diff: " + r.total_difference);
});

console.log("\n---");
if (fail === 0) {
    console.log(`ALL TESTS PASSED (${pass}/${pass + fail})`);
} else {
    console.log(`${fail} FAILED, ${pass} passed.`);
    process.exit(1);
}
