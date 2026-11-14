// ------------------------------------------------------------
// Planning Agent
// Job: take the finance difference and return a plan + recommendations
// Input: { total_difference: number }
// Output: see return statement below
// ------------------------------------------------------------

function generateEventPlan(financeData) {

    // BUG 1 FIX: crash if financeData is null/undefined
    if (!financeData) {
        throw new Error("financeData is required");
    }

    // BUG 2 FIX: crash if total_difference is missing or not a real number
    if (!Number.isFinite(financeData.total_difference)) {
        throw new Error(
            "financeData.total_difference must be a finite number, got: " +
            JSON.stringify(financeData.total_difference)
        );
    }

    const totalDifference = financeData.total_difference;

    // NOTE: activities list is hardcoded for now.
    // To make it dynamic, pass an activities array in financeData.
    const activities = [
        {
            name: "Decoration",
            priority: "medium",
            action: "Review decoration expenses"
        },
        {
            name: "Marketing",
            priority: "medium",
            action: "Review promotional spending"
        },
        {
            name: "Logistics",
            priority: "high",
            action: "Check transportation and equipment costs"
        },
        {
            name: "Food and Hospitality",
            priority: "medium",
            action: "Review food and accommodation budget"
        }
    ];

    let recommendations = [];
    let budgetStatus;

    if (totalDifference < 0) {
        budgetStatus = "budget_decreased";
        recommendations = [
            "Review non-essential event expenses",
            "Prioritize critical event activities",
            "Explore additional sponsorship opportunities",
            "Get approval before reducing any activity budget"
        ];
    } else if (totalDifference > 0) {
        budgetStatus = "budget_increased";
        recommendations = [
            "Review additional event requirements",
            "Consider improving event facilities",
            "Keep additional funds within the approved budget",
            "Get approval before allocating extra funds"
        ];
    } else {
        budgetStatus = "budget_unchanged";
        recommendations = [
            "Continue with the existing event budget",
            "Monitor planned expenses",
            "Track sponsor commitments"
        ];
    }

    // BUG 4 FIX: approval only needed when budget actually changed
    // "unchanged" does not need approval — returning true was a silent wrong answer
    const approvalRequired = totalDifference !== 0;

    return {
        budget_status: budgetStatus,
        total_budget_change: totalDifference,   // ← field name used by verification agent
        affected_activities: activities,
        recommendations: recommendations,
        approval_required: approvalRequired
    };
}


// ---- Self-test or CLI runner (runs only when you do: node planning_agent.js) ----
if (require.main === module) {
    const inputStr = process.argv[2];
    if (inputStr && inputStr.trim()) {
        try {
            const data = JSON.parse(inputStr);
            const result = generateEventPlan(data);
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

    console.log("\n=== Planning Agent Tests ===\n");

    // Normal: budget decreased
    check("budget_decreased returns correct fields", () => {
        const r = generateEventPlan({ total_difference: -50000 });
        if (r.budget_status !== "budget_decreased") throw new Error("wrong status: " + r.budget_status);
        if (r.total_budget_change !== -50000) throw new Error("wrong change");
        if (r.approval_required !== true) throw new Error("should need approval");
        if (!Array.isArray(r.affected_activities)) throw new Error("activities missing");
        if (!Array.isArray(r.recommendations)) throw new Error("recommendations missing");
    });

    // Normal: budget increased
    check("budget_increased returns correct fields", () => {
        const r = generateEventPlan({ total_difference: 100000 });
        if (r.budget_status !== "budget_increased") throw new Error("wrong status");
        if (r.approval_required !== true) throw new Error("should need approval");
    });

    // Normal: budget unchanged — approval must be FALSE
    check("budget_unchanged sets approval_required false", () => {
        const r = generateEventPlan({ total_difference: 0 });
        if (r.budget_status !== "budget_unchanged") throw new Error("wrong status");
        if (r.approval_required !== false) throw new Error("unchanged should not need approval");
    });

    // Bad input: null
    check("null input throws", () => {
        let threw = false;
        try { generateEventPlan(null); } catch (e) { threw = true; }
        if (!threw) throw new Error("should have thrown");
    });

    // Bad input: empty object
    check("empty object throws", () => {
        let threw = false;
        try { generateEventPlan({}); } catch (e) { threw = true; }
        if (!threw) throw new Error("should have thrown");
    });

    // Bad input: string instead of number
    check("string value throws", () => {
        let threw = false;
        try { generateEventPlan({ total_difference: "abc" }); } catch (e) { threw = true; }
        if (!threw) throw new Error("should have thrown");
    });

    // Bad input: NaN
    check("NaN throws", () => {
        let threw = false;
        try { generateEventPlan({ total_difference: NaN }); } catch (e) { threw = true; }
        if (!threw) throw new Error("should have thrown");
    });

    // Edge: very large number
    check("large number works", () => {
        const r = generateEventPlan({ total_difference: 99999999 });
        if (r.budget_status !== "budget_increased") throw new Error("wrong status");
    });

    console.log("\nSample output for total_difference = -50000:");
    console.log(JSON.stringify(generateEventPlan({ total_difference: -50000 }), null, 2));
}

module.exports = { generateEventPlan };
