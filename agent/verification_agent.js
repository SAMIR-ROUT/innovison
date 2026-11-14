// ------------------------------------------------------------
// Verification Agent
// Job: cross-check outputs from all 4 agents before human approval
// Input: { communicationData, knowledgeData, financeData, planningData }
// Output: { overall_status, errors, warnings, message }
// ------------------------------------------------------------

function verifyEventData(data) {

    // BUG FIX: guard against entire data object being null/undefined
    if (!data || typeof data !== "object") {
        throw new Error("verifyEventData: input must be a non-null object");
    }

    const errors = [];
    const warnings = [];

    const {
        communicationData,
        knowledgeData,
        financeData,
        planningData
    } = data;

    // ---- 1. Check communication data ----
    if (!communicationData) {
        errors.push("Communication data is missing.");
    } else {
        if (!communicationData.sponsor_name) {
            errors.push("Sponsor name is missing.");
        }

        if (
            !Number.isFinite(communicationData.old_amount) ||
            !Number.isFinite(communicationData.new_amount)
        ) {
            errors.push("Invalid or missing sponsor amounts.");
        } else {
            // ---- 2. Cross-check change_type ----
            const oldAmount = communicationData.old_amount;
            const newAmount = communicationData.new_amount;

            const expectedChange =
                newAmount > oldAmount ? "increase" :
                newAmount < oldAmount ? "decrease" :
                "unchanged";

            if (communicationData.change_type !== expectedChange) {
                errors.push(
                    "Incorrect change type detected. Expected: " +
                    expectedChange + ", got: " + communicationData.change_type
                );
            }
        }
    }

    // ---- 3. Check knowledge agent verification ----
    if (!knowledgeData) {
        errors.push("Knowledge data is missing.");
    } else if (knowledgeData.verification_status !== "verified") {
        // BUG FIX (bug 7): unverified sponsor is an ERROR, not just a warning.
        // A warning would let an unverified sponsor pass through silently.
        errors.push(
            "Sponsor record not verified. Status: " +
            (knowledgeData.verification_status || "unknown")
        );
    }

    // ---- 4. Check finance calculation ----
    if (!financeData || !Number.isFinite(financeData.total_difference)) {
        errors.push("Finance calculation is missing or invalid.");
    }

    // ---- 5. Check planning data ----
    // BUG 5 FIX: planning agent returns total_budget_change, NOT total_difference.
    // The original code checked planningData.total_difference which is always undefined,
    // so the mismatch check never worked.
    if (!planningData) {
        errors.push("Event planning data is missing.");
    } else if (
        financeData &&
        Number.isFinite(financeData.total_difference) &&       // BUG 6 FIX: guard
        planningData.total_budget_change !== financeData.total_difference
    ) {
        errors.push(
            "Planning and finance totals do not match. " +
            "Planning: " + planningData.total_budget_change +
            ", Finance: " + financeData.total_difference
        );
    }

    const overallStatus =
        errors.length === 0 && warnings.length === 0
            ? "passed"
            : "review_required";

    return {
        overall_status: overallStatus,
        errors,
        warnings,
        message:
            overallStatus === "passed"
                ? "All agent outputs verified successfully."
                : "Some information requires correction or manual review."
    };
}


// ---- Self-test or CLI runner (runs only when you do: node verification_agent.js) ----
if (require.main === module) {
    const inputStr = process.argv[2];
    if (inputStr && inputStr.trim()) {
        try {
            const data = JSON.parse(inputStr);
            const result = verifyEventData(data);
            process.stdout.write(JSON.stringify(result));
            process.exit(0);
        } catch (err) {
            process.stderr.write(JSON.stringify({ error: err.message }));
            process.exit(1);
        }
    }

    function check(label, fn) {
        try {
            fn();
            console.log("  PASS:", label);
        } catch (e) {
            console.log("  FAIL:", label, "→", e.message);
        }
    }

    console.log("\n=== Verification Agent Tests ===\n");

    // Normal: everything correct — should PASS
    check("all valid data passes", () => {
        const r = verifyEventData({
            communicationData: {
                sponsor_name: "ABC Technologies",
                old_amount: 200000,
                new_amount: 100000,
                change_type: "decrease"
            },
            knowledgeData: {
                record_found: true,
                verification_status: "verified"
            },
            financeData: { total_difference: -100000 },
            // NOTE: use total_budget_change (what planning agent actually returns)
            planningData: { total_budget_change: -100000 }
        });
        if (r.overall_status !== "passed") {
            throw new Error("should pass, got errors: " + JSON.stringify(r.errors));
        }
    });

    // Bad input: entire object is null
    check("null input throws", () => {
        let threw = false;
        try { verifyEventData(null); } catch (e) { threw = true; }
        if (!threw) throw new Error("should have thrown");
    });

    // Bad input: communicationData is null
    check("missing communicationData gives error", () => {
        const r = verifyEventData({
            communicationData: null,
            knowledgeData: { verification_status: "verified" },
            financeData: { total_difference: 0 },
            planningData: { total_budget_change: 0 }
        });
        if (!r.errors.includes("Communication data is missing.")) {
            throw new Error("missing expected error. Got: " + JSON.stringify(r.errors));
        }
    });

    // Edge: wrong change_type
    check("wrong change_type produces error", () => {
        const r = verifyEventData({
            communicationData: {
                sponsor_name: "ABC Tech",
                old_amount: 100000,
                new_amount: 200000,
                change_type: "decrease"   // wrong — should be increase
            },
            knowledgeData: { verification_status: "verified" },
            financeData: { total_difference: 100000 },
            planningData: { total_budget_change: 100000 }
        });
        const found = r.errors.some(e => e.includes("Incorrect change type"));
        if (!found) throw new Error("should catch wrong change_type. Got: " + JSON.stringify(r.errors));
    });

    // Edge: planning vs finance mismatch (the bug that was silently broken)
    check("planning vs finance mismatch produces error", () => {
        const r = verifyEventData({
            communicationData: {
                sponsor_name: "ABC Tech",
                old_amount: 200000,
                new_amount: 100000,
                change_type: "decrease"
            },
            knowledgeData: { verification_status: "verified" },
            financeData: { total_difference: -100000 },
            planningData: { total_budget_change: -50000 }   // different from finance
        });
        const found = r.errors.some(e => e.includes("do not match"));
        if (!found) throw new Error("should catch mismatch. Got: " + JSON.stringify(r.errors));
    });

    // Edge: unverified sponsor is now an ERROR (not a warning)
    check("unverified sponsor gives error", () => {
        const r = verifyEventData({
            communicationData: {
                sponsor_name: "ABC Tech",
                old_amount: 200000,
                new_amount: 100000,
                change_type: "decrease"
            },
            knowledgeData: { verification_status: "pending" },
            financeData: { total_difference: -100000 },
            planningData: { total_budget_change: -100000 }
        });
        if (r.overall_status === "passed") {
            throw new Error("unverified sponsor should not pass");
        }
        const found = r.errors.some(e => e.includes("not verified"));
        if (!found) throw new Error("missing unverified error. Got: " + JSON.stringify(r.errors));
    });

    console.log("\nSample output for valid input:");
    console.log(JSON.stringify(verifyEventData({
        communicationData: { sponsor_name: "ABC Tech", old_amount: 200000, new_amount: 100000, change_type: "decrease" },
        knowledgeData: { verification_status: "verified" },
        financeData: { total_difference: -100000 },
        planningData: { total_budget_change: -100000 }
    }), null, 2));
}

module.exports = { verifyEventData };
