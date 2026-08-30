async function fetchJSON(url, options = {}) {

    const response = await fetch(url, {
        credentials: "same-origin",
        ...options
    });

    const data = await response.json();

    if (!response.ok || data.success === false) {
        throw new Error(data.message || "Request failed");
    }

    return data;
}


async function loadReports() {

    const result = await fetchJSON("/api/admin/reports");

    const reports = result.reports || [];

    document.getElementById("totalReports").textContent =
        reports.length;

    document.getElementById("pendingReports").textContent =
        reports.filter(r => r.status === "pending").length;

    document.getElementById("verifiedReports").textContent =
        reports.filter(r => r.status === "verified").length;

    document.getElementById("rejectedReports").textContent =
        reports.filter(r => r.status === "rejected").length;


    const table = document.getElementById("reportsTable");

    if (reports.length === 0) {

        table.innerHTML = `
            <tr>
                <td colspan="7" class="loading">
                    No disaster reports found.
                </td>
            </tr>
        `;

        return;
    }


    table.innerHTML = reports.map(report => {

        const status = report.status || "unknown";

        let action = "";

        if (status === "pending") {

            action = `
                <button
                    class="action-btn verify-btn"
                    onclick="verifyReport(${report.id})">
                    Verify
                </button>

                <button
                    class="action-btn reject-btn"
                    onclick="rejectReport(${report.id})">
                    Reject
                </button>
            `;

        } else {

            action = `
                <button
                    class="action-btn disabled-btn"
                    disabled>
                    ${status}
                </button>
            `;
        }


        return `
            <tr>

                <td>#${report.id}</td>

                <td>
                    ${escapeHTML(report.disaster_type)}
                </td>

                <td>
                    <span class="severity ${report.severity}">
                        ${escapeHTML(report.severity)}
                    </span>
                </td>

                <td>
                    ${escapeHTML(report.description)}
                </td>

                <td>
                    <span class="status ${status}">
                        ${status.toUpperCase()}
                    </span>
                </td>

                <td>
                    ${Number(report.latitude).toFixed(4)},
                    ${Number(report.longitude).toFixed(4)}
                </td>

                <td>
                    ${action}
                </td>

            </tr>
        `;

    }).join("");
}


async function loadRiskData() {

    const result = await fetchJSON("/api/risk");

    const records = result.data || [];

    document.getElementById("riskObservations").textContent =
        records.length;

    const container = document.getElementById("riskList");


    if (records.length === 0) {

        container.innerHTML = `
            <div class="loading">
                No risk observations found.
            </div>
        `;

        return;
    }


    container.innerHTML = records.slice(0, 9).map(record => {

        const level =
            record.risk_level || "not calculated";

        const score =
            record.risk_score !== null
                ? Number(record.risk_score).toFixed(2)
                : "N/A";


        return `
            <div class="risk-card">

                <h3>
                    Risk Observation #${record.id}
                </h3>

                <p>
                    <b>Location:</b>
                    ${Number(record.latitude).toFixed(4)},
                    ${Number(record.longitude).toFixed(4)}
                </p>

                <p>
                    <b>Rainfall:</b>
                    ${record.rainfall_mm ?? "N/A"} mm
                </p>

                <p>
                    <b>Soil Moisture:</b>
                    ${record.soil_moisture ?? "N/A"}
                </p>

                <p>
                    <b>Slope:</b>
                    ${record.slope_degree ?? "N/A"}°
                </p>

                <p>
                    <b>Risk Score:</b>
                    ${score}
                </p>

                <p>
                    <b>Risk Level:</b>
                    <span class="risk-${level}">
                        ${level.toUpperCase()}
                    </span>
                </p>

                <p>
                    <b>Source:</b>
                    ${escapeHTML(record.source)}
                </p>

            </div>
        `;

    }).join("");
}


async function loadAlerts() {

    const result = await fetchJSON("/api/gis/map-data");

    const alerts = result.active_alerts || [];

    document.getElementById("activeAlerts").textContent =
        alerts.length;
}


async function verifyReport(id) {

    if (!confirm(
        `Are you sure you want to verify report #${id}?`
    )) {
        return;
    }


    try {

        const result = await fetchJSON(
            `/api/admin/reports/${id}/verify`,
            {
                method: "POST"
            }
        );

        alert(result.message);

        await loadReports();

    } catch (error) {

        alert(error.message);
    }
}


async function rejectReport(id) {

    const reason = prompt(
        "Enter rejection reason:"
    );


    if (reason === null) {
        return;
    }


    if (reason.trim().length < 5) {

        alert(
            "Rejection reason must contain at least 5 characters."
        );

        return;
    }


    try {

        const result = await fetchJSON(
            `/api/admin/reports/${id}/reject`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    reason: reason.trim()
                })
            }
        );

        alert(result.message);

        await loadReports();

    } catch (error) {

        alert(error.message);
    }
}


function escapeHTML(value) {

    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


async function loadDashboard() {

    try {

        await Promise.all([
            loadReports(),
            loadRiskData(),
            loadAlerts()
        ]);

    } catch (error) {

        console.error(
            "Admin dashboard error:",
            error
        );

        alert(
            "Unable to load admin dashboard. Please login as admin."
        );
    }
}


loadDashboard();
