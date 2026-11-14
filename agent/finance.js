// ------------------------------------------------------------
// Finance Agent
// Job: Calculate the financial impact of sponsor commitment changes
// Input: Array of { sponsor_name, old_amount, new_amount }
// Output: Previous total, updated total, difference,
//         financial status, and sponsor details
// ------------------------------------------------------------

function calculateFinancialImpact(sponsors) {

    // BUG 1 FIX: Validate input array
    if (!Array.isArray(sponsors)) {
        throw new Error(
            "calculateFinancialImpact: sponsors must be an array"
        );
    }

    let previousTotal = 0;
    let updatedTotal = 0;

    const sponsorDetails = [];

    for (const sponsor of sponsors) {

        // BUG 2 FIX: Validate individual sponsor entry
        if (!sponsor || typeof sponsor !== "object" || Array.isArray(sponsor)) {
            sponsorDetails.push({
                sponsor_name: null,
                error: "Sponsor entry is null or not an object",
                manual_review_required: true
            });
            continue;
        }

        // BUG 3 FIX: Safely capture sponsor name
        const sponsorName = sponsor.sponsor_name || null;

        const oldAmount = Number(sponsor.old_amount);
        const newAmount = Number(sponsor.new_amount);

        // Validate contribution amounts
        if (
            !Number.isFinite(oldAmount) ||
            !Number.isFinite(newAmount) ||
            oldAmount < 0 ||
            newAmount < 0
        ) {
            sponsorDetails.push({
                sponsor_name: sponsorName,
                error: "Invalid contribution amount",
                manual_review_required: true
            });
            continue;
        }

        previousTotal += oldAmount;
        updatedTotal += newAmount;

        const difference = newAmount - oldAmount;

        sponsorDetails.push({
            sponsor_name: sponsorName,
            previous_amount: Math.round(oldAmount),
            updated_amount: Math.round(newAmount),
            difference: Math.round(difference),

            change_type: difference > 0
                ? "increase"
                : difference < 0
                    ? "decrease"
                    : "unchanged"
        });
    }

    // BUG 4 FIX: Round all financial totals
    const roundedPrevious = Math.round(previousTotal);
    const roundedUpdated = Math.round(updatedTotal);
    const totalDifference = Math.round(updatedTotal - previousTotal);

    return {
        previous_total_sponsorship: roundedPrevious,
        updated_total_sponsorship: roundedUpdated,
        total_difference: totalDifference,

        financial_status: totalDifference > 0
            ? "positive"
            : totalDifference < 0
                ? "negative"
                : "neutral",

        sponsor_details: sponsorDetails
    };
}

// Export function for backend integration
module.exports = { calculateFinancialImpact };

// CLI runner: allows Python or external processes to call:
// node finance.js '<json_string>'
if (require.main === module) {
    const inputStr = process.argv[2];
    if (inputStr && inputStr.trim()) {
        try {
            const data = JSON.parse(inputStr);
            const result = calculateFinancialImpact(data);
            process.stdout.write(JSON.stringify(result));
            process.exit(0);
        } catch (err) {
            process.stderr.write(JSON.stringify({ error: err.message }));
            process.exit(1);
        }
    }
}
