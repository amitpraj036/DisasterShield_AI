let allReports = [];


/* =========================
   LOAD DASHBOARD
========================= */

async function loadDashboard() {

    const table = document.getElementById("reportsTable");
    const message = document.getElementById("message");

    message.innerHTML = "";

    table.innerHTML = `
        <tr>
            <td colspan="7" class="empty-row">
                Loading reports...
            </td>
        </tr>
    `;

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
            throw new Error("Admin access required.");
        }

        if (!result.success) {
            throw new Error(
                result.message || "Unable to load reports."
            );
        }

        allReports = result.reports || [];

        updateReportStats();

        await loadAlertStats();

        await loadRiskStats();

        applyFilters();

    } catch (error) {

        console.error("Dashboard error:", error);

        table.innerHTML = `
            <tr>
                <td colspan="7" class="empty-row">
                    Unable to load dashboard data.
                </td>
            </tr>
        `;

        showMessage(error.message, false);
    }
}


/* =========================
   REPORT STATISTICS
========================= */

function updateReportStats() {

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
}


/* =========================
   ALERT STATISTICS
========================= */

async function loadAlertStats() {

    try {

        const response = await fetch(
            "/api/alerts",
            {
                credentials: "same-origin"
            }
        );

        const result = await response.json();

        if (!result.success) {
            throw new Error("Alert API failed");
        }

        const alerts =
            result.alerts ||
            result.data ||
            [];

        const active = alerts.filter(
            alert => alert.status === "active"
        ).length;

        document.getElementById(
            "activeAlerts"
        ).textContent = active;

    } catch (error) {

        console.warn(
            "Alert API unavailable:",
            error
        );

        document.getElementById(
            "activeAlerts"
        ).textContent = "—";
    }
}


/* =========================
   RISK STATISTICS
========================= */

async function loadRiskStats() {

    try {

        const response = await fetch(
            "/api/risk",
            {
                credentials: "same-origin"
            }
        );

        const result = await response.json();

        if (!result.success) {
            throw new Error("Risk API failed");
        }

        const data =
            result.data || [];

        document.getElementById(
            "riskObservations"
        ).textContent =
            result.count ?? data.length;

    } catch (error) {

        console.warn(
            "Risk API unavailable:",
            error
        );

        document.getElementById(
            "riskObservations"
        ).textContent = "—";
    }
}


/* =========================
   SEARCH + FILTER
========================= */

function applyFilters() {

    const searchInput =
        document.getElementById("searchInput");

    const statusFilter =
        document.getElementById("statusFilter");

    const severityFilter =
        document.getElementById("severityFilter");

    const search =
        searchInput.value
            .trim()
            .toLowerCase();

    const status =
        statusFilter.value;

    const severity =
        severityFilter.value;

    const filteredReports =
        allReports.filter(report => {

            const matchesStatus =
                status === "all" ||
                report.status === status;

            const matchesSeverity =
                severity === "all" ||
                report.severity === severity;

            const searchableText = [

                report.id,
                report.user_id,
                report.disaster_type,
                report.description,
                report.severity,
                report.status,
                report.latitude,
                report.longitude

            ]
                .join(" ")
                .toLowerCase();

            const matchesSearch =
                !search ||
                searchableText.includes(search);

            return (
                matchesStatus &&
                matchesSeverity &&
                matchesSearch
            );
        });

    renderReports(filteredReports);
}


/* =========================
   RENDER REPORTS
========================= */

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

    table.innerHTML =
        reports.map(report => {

            const status =
                String(
                    report.status || "unknown"
                ).toLowerCase();

            const severity =
                String(
                    report.severity || "unknown"
                ).toLowerCase();

            const latitude =
                Number(report.latitude);

            const longitude =
                Number(report.longitude);

            let location = "N/A";

            if (
                Number.isFinite(latitude) &&
                Number.isFinite(longitude)
            ) {

                const mapsUrl =
                    `https://www.google.com/maps?q=${latitude},${longitude}`;

                location = `
                    <a
                        class="location-link"
                        href="${mapsUrl}"
                        target="_blank"
                        rel="noopener noreferrer"
                    >
                        📍 ${latitude.toFixed(4)},
                        ${longitude.toFixed(4)}
                    </a>
                `;
            }

            const created =
                formatDate(report.created_at);

            let actions = `
                <button
                    class="action-btn view-btn"
                    onclick="viewReport(${report.id})"
                >
                    👁 View
                </button>
            `;

            if (status === "pending") {

                actions += `
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

                actions += `
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

            let rowClass = "";

            if (severity === "critical") {
                rowClass = "critical-risk";
            } else if (severity === "high") {
                rowClass = "high-risk";
            }

            return `
                <tr class="${rowClass}">

                    <td>
                        <strong>#${report.id}</strong>
                    </td>

                    <td>
                        ${escapeHtml(
                            report.disaster_type
                        )}
                    </td>

                    <td>
                        <span class="severity ${escapeHtml(severity)}">
                            ${escapeHtml(
                                severity.toUpperCase()
                            )}
                        </span>
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


/* =========================
   VIEW REPORT
========================= */

function viewReport(reportId) {

    const report =
        allReports.find(
            r => Number(r.id) === Number(reportId)
        );

    if (!report) {

        showMessage(
            "Report details not found.",
            false
        );

        return;
    }

    const latitude =
        Number(report.latitude);

    const longitude =
        Number(report.longitude);

    let locationHtml = "N/A";

    if (
        Number.isFinite(latitude) &&
        Number.isFinite(longitude)
    ) {

        const mapsUrl =
            `https://www.google.com/maps?q=${latitude},${longitude}`;

        locationHtml = `
            <a
                href="${mapsUrl}"
                target="_blank"
                rel="noopener noreferrer"
                class="location-link"
            >
                Open in Google Maps
            </a>
            <br>
            ${latitude.toFixed(6)}, ${longitude.toFixed(6)}
        `;
    }

    document.getElementById(
        "reportDetails"
    ).innerHTML = `

        <div class="detail-grid">

            <div class="detail-item">
                <span class="detail-label">
                    Report ID
                </span>
                <span class="detail-value">
                    #${report.id}
                </span>
            </div>

            <div class="detail-item">
                <span class="detail-label">
                    Citizen ID
                </span>
                <span class="detail-value">
                    ${escapeHtml(
                        report.user_id
                    )}
                </span>
            </div>

            <div class="detail-item">
                <span class="detail-label">
                    Disaster Type
                </span>
                <span class="detail-value">
                    ${escapeHtml(
                        report.disaster_type
                    )}
                </span>
            </div>

            <div class="detail-item">
                <span class="detail-label">
                    Severity
                </span>
                <span class="detail-value">
                    ${escapeHtml(
                        report.severity
                    )}
                </span>
            </div>

            <div class="detail-item">
                <span class="detail-label">
                    Status
                </span>
                <span class="detail-value">
                    ${escapeHtml(
                        report.status
                    )}
                </span>
            </div>

            <div class="detail-item">
                <span class="detail-label">
                    Created
                </span>
                <span class="detail-value">
                    ${escapeHtml(
                        formatDate(
                            report.created_at
                        )
                    )}
                </span>
            </div>

            <div class="detail-item full">
                <span class="detail-label">
                    Location
                </span>
                <span class="detail-value">
                    ${locationHtml}
                </span>
            </div>

            <div class="detail-item full">
                <span class="detail-label">
                    Description
                </span>
                <div class="detail-value description-box">
                    ${escapeHtml(
                        report.description ||
                        "No description provided."
                    )}
                </div>
            </div>

            <div class="detail-item">
                <span class="detail-label">
                    Verified By
                </span>
                <span class="detail-value">
                    ${escapeHtml(
                        report.verified_by ??
                        "Not verified"
                    )}
                </span>
            </div>

            <div class="detail-item">
                <span class="detail-label">
                    Verified At
                </span>
                <span class="detail-value">
                    ${escapeHtml(
                        report.verified_at
                            ? formatDate(
                                report.verified_at
                            )
                            : "Not verified"
                    )}
                </span>
            </div>

            ${
                report.rejection_reason
                ? `
                    <div class="detail-item full">
                        <span class="detail-label">
                            Rejection Reason
                        </span>
                        <div class="detail-value description-box">
                            ${escapeHtml(
                                report.rejection_reason
                            )}
                        </div>
                    </div>
                `
                : ""
            }

        </div>
    `;

    document
        .getElementById("reportModal")
        .classList.add("show");
}


/* =========================
   CLOSE MODAL
========================= */

function closeReportModal() {

    document
        .getElementById("reportModal")
        .classList.remove("show");
}


function closeModalOutside(event) {

    if (
        event.target.id === "reportModal"
    ) {
        closeReportModal();
    }
}


/* =========================
   VERIFY REPORT
========================= */

async function verifyReport(reportId) {

    const confirmed =
        confirm(
            `Verify disaster report #${reportId}?`
        );

    if (!confirmed) {
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
                "Verification failed."
            );
        }

        let message =
            "Report verified successfully.";

        if (result.automatic_alert) {

            message +=
                " Automatic disaster alert created.";
        }

        showMessage(
            message,
            true
        );

        closeReportModal();

        await loadDashboard();

    } catch (error) {

        console.error(error);

        showMessage(
            error.message,
            false
        );
    }
}


/* =========================
   REJECT REPORT
========================= */

async function rejectReport(reportId) {

    const reason =
        prompt(
            "Enter rejection reason:"
        );

    if (reason === null) {
        return;
    }

    const cleanReason =
        reason.trim();

    if (cleanReason.length < 5) {

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
                        reason: cleanReason
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
                "Rejection failed."
            );
        }

        showMessage(
            "Report rejected successfully.",
            true
        );

        closeReportModal();

        await loadDashboard();

    } catch (error) {

        console.error(error);

        showMessage(
            error.message,
            false
        );
    }
}


/* =========================
   LOGOUT
========================= */

async function logoutAdmin() {

    if (
        !confirm(
            "Are you sure you want to logout?"
        )
    ) {
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
                "Logout failed."
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


/* =========================
   MESSAGE
========================= */

function showMessage(
    text,
    success
) {

    const message =
        document.getElementById(
            "message"
        );

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

    }, 5000);
}


/* =========================
   DATE
========================= */

function formatDate(value) {

    if (!value) {
        return "N/A";
    }

    const date =
        new Date(value);

    if (
        Number.isNaN(
            date.getTime()
        )
    ) {
        return String(value);
    }

    return date.toLocaleString();
}


/* =========================
   SECURITY
========================= */

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


/* =========================
   INITIAL LOAD
========================= */

document.addEventListener(
    "DOMContentLoaded",
    () => {
        loadDashboard();
    }
);


/* ============================================================
   ALERT MANAGEMENT
   ============================================================ */

let allAlerts = [];


/* LOAD ALERTS */

async function loadAlerts() {

    const table = document.getElementById("alertsTable");

    if (!table) {
        return;
    }

    table.innerHTML = `
        <tr>
            <td colspan="8" class="loading">
                Loading alerts...
            </td>
        </tr>
    `;

    try {

        const response = await fetch(
            "/api/alerts",
            {
                credentials: "same-origin"
            }
        );

        const result = await response.json();

        if (!response.ok || !result.success) {

            throw new Error(
                result.message || "Unable to load alerts"
            );
        }

        allAlerts = result.alerts || [];

        updateAlertStats();

        applyAlertFilters();

    } catch (error) {

        console.error("Alert loading error:", error);

        table.innerHTML = `
            <tr>
                <td colspan="8" class="empty-row">
                    Unable to load alerts.
                </td>
            </tr>
        `;
    }
}


/* ALERT STATISTICS */

function updateAlertStats() {

    const total = allAlerts.length;

    const active = allAlerts.filter(
        alert => alert.status === "active"
    ).length;

    const inactive = allAlerts.filter(
        alert => alert.status === "inactive"
    ).length;

    const critical = allAlerts.filter(
        alert => alert.severity === "critical" &&
        alert.status === "active"
    ).length;


    const totalElement =
        document.getElementById("totalAlerts");

    const activeElement =
        document.getElementById("activeAlertCount");

    const inactiveElement =
        document.getElementById("inactiveAlertCount");

    const criticalElement =
        document.getElementById("criticalAlertCount");


    if (totalElement) {
        totalElement.textContent = total;
    }

    if (activeElement) {
        activeElement.textContent = active;
    }

    if (inactiveElement) {
        inactiveElement.textContent = inactive;
    }

    if (criticalElement) {
        criticalElement.textContent = critical;
    }
}


/* FILTERS */

function applyAlertFilters() {

    const searchElement =
        document.getElementById("alertSearch");

    const statusElement =
        document.getElementById("alertStatusFilter");

    const severityElement =
        document.getElementById("alertSeverityFilter");

    const typeElement =
        document.getElementById("alertTypeFilter");


    if (!searchElement) {
        return;
    }


    const search =
        searchElement.value
        .trim()
        .toLowerCase();

    const status =
        statusElement
            ? statusElement.value
            : "all";

    const severity =
        severityElement
            ? severityElement.value
            : "all";

    const type =
        typeElement
            ? typeElement.value
            : "all";


    const filtered =
        allAlerts.filter(alert => {

            const text = [
                alert.id,
                alert.title,
                alert.message,
                alert.alert_type,
                alert.severity,
                alert.source,
                alert.latitude,
                alert.longitude
            ]
            .join(" ")
            .toLowerCase();


            return (
                (!search || text.includes(search)) &&
                (status === "all" || alert.status === status) &&
                (severity === "all" || alert.severity === severity) &&
                (type === "all" || alert.alert_type === type)
            );

        });


    renderAlerts(filtered);
}


/* RENDER ALERTS */

function renderAlerts(alerts) {

    const table =
        document.getElementById("alertsTable");

    if (!table) {
        return;
    }


    if (alerts.length === 0) {

        table.innerHTML = `
            <tr>
                <td colspan="8" class="empty-row">
                    No alerts match your filters.
                </td>
            </tr>
        `;

        return;
    }


    table.innerHTML =
        alerts.map(alert => {

            const location =
                Number.isFinite(Number(alert.latitude)) &&
                Number.isFinite(Number(alert.longitude))
                    ? `${Number(alert.latitude).toFixed(4)},
                       ${Number(alert.longitude).toFixed(4)}`
                    : "N/A";


            const created =
                alert.created_at
                    ? new Date(
                        alert.created_at
                    ).toLocaleString()
                    : "N/A";


            const expires =
                alert.expires_at
                    ? new Date(
                        alert.expires_at
                    ).toLocaleString()
                    : "Never";


            let actionButtons = "";


            if (alert.status === "active") {

                actionButtons += `
                    <button
                        class="action-btn reject-btn"
                        onclick="deactivateAlert(${alert.id})"
                    >
                        🔴 Deactivate
                    </button>
                `;

            } else {

                actionButtons += `
                    <button
                        class="action-btn verify-btn"
                        onclick="activateAlert(${alert.id})"
                    >
                        🟢 Activate
                    </button>
                `;
            }


            actionButtons += `
                <button
                    class="action-btn edit-alert-btn"
                    onclick="openEditAlert(${alert.id})"
                >
                    ✏️ Edit
                </button>
            `;


            if (alert.source !== "automatic") {

                actionButtons += `
                    <button
                        class="action-btn reject-btn"
                        onclick="deleteAlert(${alert.id})"
                    >
                        🗑️ Delete
                    </button>
                `;
            }


            return `
                <tr>

                    <td>#${alert.id}</td>

                    <td>
                        ${escapeHtml(alert.title)}
                    </td>

                    <td>
                        ${escapeHtml(alert.alert_type)}
                    </td>

                    <td>
                        <span class="alert-severity ${escapeHtml(
                            alert.severity
                        )}">
                            ${escapeHtml(
                                alert.severity.toUpperCase()
                            )}
                        </span>
                    </td>

                    <td>
                        <span class="status ${escapeHtml(
                            alert.status
                        )}">
                            ${escapeHtml(
                                alert.status.toUpperCase()
                            )}
                        </span>
                    </td>

                    <td>
                        ${location}
                    </td>

                    <td>
                        ${escapeHtml(expires)}
                    </td>

                    <td>
                        ${actionButtons}
                    </td>

                </tr>
            `;

        }).join("");
}


/* CREATE ALERT */

async function createAlert() {

    const title =
        document.getElementById("alertTitle").value.trim();

    const message =
        document.getElementById("alertMessage").value.trim();

    const type =
        document.getElementById("alertType").value.trim();

    const severity =
        document.getElementById("alertSeverity").value;

    const latitude =
        document.getElementById("alertLatitude").value;

    const longitude =
        document.getElementById("alertLongitude").value;

    const radius =
        document.getElementById("alertRadius").value;

    const expires =
        document.getElementById("alertExpires").value;


    if (!title || !message || !type) {

        alert(
            "Title, message and alert type are required."
        );

        return;
    }


    const payload = {

        title: title,

        message: message,

        alert_type: type,

        severity: severity,

        latitude: latitude || null,

        longitude: longitude || null,

        radius_km: radius || null,

        expires_at: expires
            ? new Date(expires).toISOString()
            : null

    };


    try {

        const response =
            await fetch(
                "/api/alerts",
                {
                    method: "POST",

                    credentials: "same-origin",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify(payload)
                }
            );


        const result =
            await response.json();


        if (!response.ok || !result.success) {

            throw new Error(
                result.message ||
                "Failed to create alert"
            );
        }


        showMessage(
            "Alert created successfully.",
            true
        );


        closeAlertModal();

        clearAlertForm();

        await loadAlerts();


    } catch (error) {

        showMessage(
            error.message,
            false
        );
    }
}


/* DEACTIVATE */

async function deactivateAlert(id) {

    if (!confirm(
        `Deactivate alert #${id}?`
    )) {
        return;
    }


    await changeAlertStatus(
        id,
        "deactivate"
    );
}


/* ACTIVATE */

async function activateAlert(id) {

    await changeAlertStatus(
        id,
        "activate"
    );
}


/* STATUS CHANGE */

async function changeAlertStatus(
    id,
    action
) {

    try {

        const response =
            await fetch(
                `/api/alerts/${id}/${action}`,
                {
                    method: "POST",
                    credentials: "same-origin"
                }
            );


        const result =
            await response.json();


        if (!response.ok || !result.success) {

            throw new Error(
                result.message ||
                `Unable to ${action} alert`
            );
        }


        showMessage(
            `Alert ${action}d successfully.`,
            true
        );


        await loadAlerts();


    } catch (error) {

        showMessage(
            error.message,
            false
        );
    }
}


/* DELETE */

async function deleteAlert(id) {

    if (!confirm(
        `Permanently delete alert #${id}? This cannot be undone.`
    )) {
        return;
    }


    try {

        const response =
            await fetch(
                `/api/alerts/${id}`,
                {
                    method: "DELETE",
                    credentials: "same-origin"
                }
            );


        const result =
            await response.json();


        if (!response.ok || !result.success) {

            throw new Error(
                result.message ||
                "Unable to delete alert"
            );
        }


        showMessage(
            "Alert deleted successfully.",
            true
        );


        await loadAlerts();


    } catch (error) {

        showMessage(
            error.message,
            false
        );
    }
}


/* EDIT */

async function openEditAlert(id) {

    const alert =
        allAlerts.find(
            item => item.id === id
        );


    if (!alert) {
        return;
    }


    const title =
        prompt(
            "Alert title:",
            alert.title
        );


    if (title === null) {
        return;
    }


    const message =
        prompt(
            "Alert message:",
            alert.message
        );


    if (message === null) {
        return;
    }


    const severity =
        prompt(
            "Severity (low / moderate / high / critical):",
            alert.severity
        );


    if (severity === null) {
        return;
    }


    const type =
        prompt(
            "Alert type:",
            alert.alert_type
        );


    if (type === null) {
        return;
    }


    try {

        const response =
            await fetch(
                `/api/alerts/${id}`,
                {
                    method: "PUT",

                    credentials: "same-origin",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        title: title.trim(),

                        message: message.trim(),

                        severity: severity.trim(),

                        alert_type: type.trim()

                    })
                }
            );


        const result =
            await response.json();


        if (!response.ok || !result.success) {

            throw new Error(
                result.message ||
                "Unable to update alert"
            );
        }


        showMessage(
            "Alert updated successfully.",
            true
        );


        await loadAlerts();


    } catch (error) {

        showMessage(
            error.message,
            false
        );
    }
}


/* MODAL */

function openCreateAlertModal() {

    const modal =
        document.getElementById("alertModal");

    if (modal) {
        modal.style.display = "flex";
    }
}


function closeAlertModal() {

    const modal =
        document.getElementById("alertModal");

    if (modal) {
        modal.style.display = "none";
    }
}


function clearAlertForm() {

    [
        "alertTitle",
        "alertMessage",
        "alertType",
        "alertLatitude",
        "alertLongitude",
        "alertRadius",
        "alertExpires"
    ].forEach(id => {

        const element =
            document.getElementById(id);

        if (element) {
            element.value = "";
        }

    });
}


/* INITIAL ALERT LOAD */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        loadAlerts();

    }
);

