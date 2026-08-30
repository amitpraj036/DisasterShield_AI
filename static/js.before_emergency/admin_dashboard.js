let allReports = [];


async function loadDashboard() {

    const table = document.getElementById("reportsTable");
    const message = document.getElementById("message");

    message.innerHTML = "";

    try {

        const response = await fetch(
            "/api/admin/reports",
            {
                credentials: "same-origin"
            }
        );

        const result = await response.json();

        if (response.status === 401) {
            window.location.href = "/admin/login";
            return;
        }

        if (response.status === 403) {
            throw new Error(
                "Admin access required."
            );
        }

        if (!result.success) {
            throw new Error(
                result.message || "Unable to load reports"
            );
        }

        allReports = result.reports || [];


        // REPORT COUNTS

        document.getElementById("totalReports").textContent =
            allReports.length;

        document.getElementById("pendingReports").textContent =
            allReports.filter(
                r => r.status === "pending"
            ).length;

        document.getElementById("verifiedReports").textContent =
            allReports.filter(
                r => r.status === "verified"
            ).length;

        document.getElementById("rejectedReports").textContent =
            allReports.filter(
                r => r.status === "rejected"
            ).length;


        // ACTIVE ALERTS

        try {

            const alertResponse =
                await fetch(
                    "/api/alerts",
                    {
                        credentials: "same-origin"
                    }
                );

            const alertResult =
                await alertResponse.json();

            if (alertResult.success) {

                const alerts =
                    alertResult.alerts ||
                    alertResult.data ||
                    [];

                document.getElementById(
                    "activeAlerts"
                ).textContent =
                    alerts.filter(
                        a => a.status === "active"
                    ).length;
            }

        } catch (error) {

            console.warn(
                "Alert API unavailable:",
                error
            );

            document.getElementById(
                "activeAlerts"
            ).textContent = "—";
        }


        // RISK DATA

        try {

            const riskResponse =
                await fetch(
                    "/api/risk",
                    {
                        credentials: "same-origin"
                    }
                );

            const riskResult =
                await riskResponse.json();

            if (riskResult.success) {

                const riskData =
                    riskResult.data || [];

                document.getElementById(
                    "riskObservations"
                ).textContent =
                    riskResult.count ??
                    riskData.length;
            }

        } catch (error) {

            console.warn(
                "Risk API unavailable:",
                error
            );

            document.getElementById(
                "riskObservations"
            ).textContent = "—";
        }


        applyFilters();

    } catch (error) {

        console.error(
            "Dashboard error:",
            error
        );

        table.innerHTML = `
            <tr>
                <td colspan="7" class="empty-row">
                    Unable to load dashboard data.
                </td>
            </tr>
        `;

        message.innerHTML = `
            <div class="error-message">
                ${escapeHtml(error.message)}
            </div>
        `;
    }
}


/* SEARCH + FILTER */

function applyFilters() {

    const searchInput =
        document.getElementById("searchInput");

    const statusFilter =
        document.getElementById("statusFilter");

    const search =
        searchInput.value
            .trim()
            .toLowerCase();

    const status =
        statusFilter.value;


    const filteredReports =
        allReports.filter(report => {

            const matchesStatus =
                status === "all" ||
                report.status === status;


            const searchableText = [
                report.id,
                report.disaster_type,
                report.severity,
                report.status,
                report.latitude,
                report.longitude,
                report.description
            ]
                .join(" ")
                .toLowerCase();


            const matchesSearch =
                !search ||
                searchableText.includes(search);


            return matchesStatus &&
                   matchesSearch;
        });


    renderReports(filteredReports);
}


/* REPORT TABLE */

function renderReports(reports) {

    const table =
        document.getElementById("reportsTable");


    if (reports.length === 0) {

        table.innerHTML = `
            <tr>
                <td colspan="7" class="empty-row">
                    No reports match your search/filter.
                </td>
            </tr>
        `;

        return;
    }


    table.innerHTML = reports.map(report => {

        const status =
            report.status || "unknown";


        const latitude =
            Number(report.latitude);

        const longitude =
            Number(report.longitude);


        const location =
            Number.isFinite(latitude) &&
            Number.isFinite(longitude)
                ? `${latitude.toFixed(4)}, ${longitude.toFixed(4)}`
                : "N/A";


        const created =
            report.created_at
                ? new Date(
                    report.created_at
                  ).toLocaleString()
                : "N/A";


        let actions = "—";


        if (status === "pending") {

            actions = `
                <button
                    class="action-btn verify-btn"
                    onclick="verifyReport(${report.id})"
                >
                    ✓ Verify
                </button>

                <button
                    class="action-btn reject-btn"
                    onclick="rejectReport(${report.id})"
                >
                    ✕ Reject
                </button>
            `;

        } else {

            actions = `
                <button
                    class="action-btn disabled-btn"
                    disabled
                >
                    ${escapeHtml(
                        status.toUpperCase()
                    )}
                </button>
            `;
        }


        return `
            <tr>

                <td>
                    #${report.id}
                </td>

                <td>
                    ${escapeHtml(
                        report.disaster_type
                    )}
                </td>

                <td>
                    ${escapeHtml(
                        report.severity
                    )}
                </td>

                <td>
                    <span class="status ${escapeHtml(status)}">
                        ${escapeHtml(
                            status.toUpperCase()
                        )}
                    </span>
                </td>

                <td>
                    ${location}
                </td>

                <td>
                    ${escapeHtml(created)}
                </td>

                <td>
                    ${actions}
                </td>

            </tr>
        `;

    }).join("");
}


/* VERIFY */

async function verifyReport(reportId) {

    if (!confirm(
        `Verify disaster report #${reportId}?`
    )) {
        return;
    }


    try {

        const response =
            await fetch(
                `/api/admin/reports/${reportId}/verify`,
                {
                    method: "POST",
                    credentials: "same-origin"
                }
            );


        const result =
            await response.json();


        if (response.status === 401) {

            window.location.href =
                "/admin/login";

            return;
        }


        if (!result.success) {

            throw new Error(
                result.message ||
                "Verification failed"
            );
        }


        showMessage(
            "Report verified successfully.",
            true
        );


        await loadDashboard();

    } catch (error) {

        showMessage(
            error.message,
            false
        );
    }
}


/* REJECT */

async function rejectReport(reportId) {

    const reason =
        prompt(
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

        const response =
            await fetch(
                `/api/admin/reports/${reportId}/reject`,
                {
                    method: "POST",
                    credentials: "same-origin",
                    headers: {
                        "Content-Type":
                            "application/json"
                    },
                    body: JSON.stringify({
                        reason:
                            reason.trim()
                    })
                }
            );


        const result =
            await response.json();


        if (response.status === 401) {

            window.location.href =
                "/admin/login";

            return;
        }


        if (!result.success) {

            throw new Error(
                result.message ||
                "Rejection failed"
            );
        }


        showMessage(
            "Report rejected successfully.",
            true
        );


        await loadDashboard();

    } catch (error) {

        showMessage(
            error.message,
            false
        );
    }
}


/* LOGOUT */

async function logoutAdmin() {

    if (!confirm(
        "Are you sure you want to logout?"
    )) {
        return;
    }


    try {

        const response =
            await fetch(
                "/api/auth/logout",
                {
                    method: "POST",
                    credentials: "same-origin"
                }
            );


        const result =
            await response.json();


        if (!result.success) {

            throw new Error(
                result.message ||
                "Logout failed"
            );
        }


        window.location.href =
            "/admin/login";

    } catch (error) {

        alert(
            "Logout failed: " +
            error.message
        );
    }
}


/* MESSAGE */

function showMessage(
    text,
    success
) {

    const message =
        document.getElementById("message");


    message.innerHTML = `
        <div class="${
            success
                ? "success-message"
                : "error-message"
        }">
            ${escapeHtml(text)}
        </div>
    `;


    setTimeout(() => {

        message.innerHTML = "";

    }, 4000);
}


/* SECURITY */

function escapeHtml(value) {

    if (
        value === null ||
        value === undefined
    ) {
        return "";
    }


    return String(value)
        .replaceAll(
            "&",
            "&amp;"
        )
        .replaceAll(
            "<",
            "&lt;"
        )
        .replaceAll(
            ">",
            "&gt;"
        )
        .replaceAll(
            '"',
            "&quot;"
        )
        .replaceAll(
            "'",
            "&#039;"
        );
}


/* START */

loadDashboard();
