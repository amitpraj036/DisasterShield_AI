"use strict";


/* ============================================================
   STATE
   ============================================================ */

let currentLocation = null;

let locationLinks = null;


/* ============================================================
   DOM HELPERS
   ============================================================ */

function $(id) {

    return document.getElementById(id);
}


function showMessage(message) {

    const element =
        $("locationMessage");

    if (element) {
        element.textContent =
            message;
    }
}


/* ============================================================
   LOCATION
   ============================================================ */

function detectLocation() {

    if (!navigator.geolocation) {

        showMessage(
            "Geolocation is not supported by this browser."
        );

        return;
    }


    const button =
        $("locationButton");

    if (button) {

        button.disabled = true;

        button.textContent =
            "📍 Detecting...";
    }


    showMessage(
        "Requesting your current location..."
    );


    navigator.geolocation.getCurrentPosition(

        function(position) {

            currentLocation = {

                latitude:
                    position.coords.latitude,

                longitude:
                    position.coords.longitude,

                accuracy:
                    position.coords.accuracy
            };


            updateLocationUI();

            loadLocationLinks();

        },


        function(error) {

            console.error(
                "Emergency location error:",
                error
            );


            let message =
                "Unable to detect your location.";

            if (
                error.code ===
                error.PERMISSION_DENIED
            ) {

                message =
                    "Location permission was denied. Please allow location access.";
            }

            else if (
                error.code ===
                error.TIMEOUT
            ) {

                message =
                    "Location request timed out. Please try again.";
            }


            showMessage(message);


            const button =
                $("locationButton");

            if (button) {

                button.disabled = false;

                button.textContent =
                    "📍 Detect My Location";
            }

        },

        {
            enableHighAccuracy: true,

            timeout: 10000,

            maximumAge: 60000
        }
    );
}


/* ============================================================
   LOCATION UI
   ============================================================ */

function updateLocationUI() {

    if (!currentLocation) {
        return;
    }


    $("latitude").textContent =
        currentLocation.latitude.toFixed(6);


    $("longitude").textContent =
        currentLocation.longitude.toFixed(6);


    $("accuracy").textContent =
        `±${Math.round(
            currentLocation.accuracy
        )} m`;


    const badge =
        $("locationBadge");

    if (badge) {

        badge.textContent =
            "LOCATION DETECTED";

        badge.classList.add(
            "detected"
        );
    }


    const button =
        $("locationButton");

    if (button) {

        button.disabled = false;

        button.textContent =
            "🔄 Update Location";
    }


    const copyButton =
        $("copyLocationButton");

    if (copyButton) {

        copyButton.disabled = false;
    }


    showMessage(
        "Your location was detected. You can now search nearby emergency facilities."
    );
}


/* ============================================================
   LOCATION LINKS
   ============================================================ */

async function loadLocationLinks() {

    if (!currentLocation) {
        return;
    }


    try {

        const query =
            new URLSearchParams({

                lat:
                    currentLocation.latitude,

                lon:
                    currentLocation.longitude
            });


        const response =
            await fetch(
                `/citizen/emergency/api/location-links?${query.toString()}`
            );


        if (!response.ok) {

            throw new Error(
                `HTTP ${response.status}`
            );
        }


        const data =
            await response.json();


        if (!data.success) {

            throw new Error(
                data.error ||
                "Unable to generate links."
            );
        }


        locationLinks =
            data.links;


    } catch (error) {

        console.error(
            "Location links error:",
            error
        );

        showMessage(
            "Location detected, but facility links could not be generated."
        );
    }
}


/* ============================================================
   FACILITY SEARCH
   ============================================================ */

function openFacility(type) {

    if (!currentLocation) {

        showMessage(
            "Please detect your location first."
        );

        detectLocation();

        return;
    }


    if (!locationLinks) {

        showMessage(
            "Preparing nearby facility search..."
        );

        loadLocationLinks();

        return;
    }


    const url =
        locationLinks[type];


    if (!url) {

        showMessage(
            "Facility search is unavailable."
        );

        return;
    }


    window.open(
        url,
        "_blank",
        "noopener,noreferrer"
    );
}


/* ============================================================
   COPY LOCATION
   ============================================================ */

async function copyLocation() {

    if (!currentLocation) {
        return;
    }


    const text =
        `DisasterShield AI Emergency Location\n` +
        `Latitude: ${currentLocation.latitude.toFixed(6)}\n` +
        `Longitude: ${currentLocation.longitude.toFixed(6)}`;


    try {

        await navigator.clipboard.writeText(
            text
        );


        showMessage(
            "Emergency coordinates copied to clipboard."
        );

    } catch (error) {

        console.error(
            "Clipboard error:",
            error
        );


        showMessage(
            text
        );
    }
}


/* ============================================================
   SOS
   ============================================================ */

function triggerSOS() {

    const confirmed =
        window.confirm(
            "If you are in immediate danger, call emergency services now.\n\n" +
            "Press OK to open the National Emergency number 112."
        );


    if (!confirmed) {
        return;
    }


    window.location.href =
        "tel:112";
}


/* ============================================================
   DISASTER GUIDE TABS
   ============================================================ */

function setupGuideTabs() {

    const tabs =
        document.querySelectorAll(
            ".guide-tab"
        );


    const panels =
        document.querySelectorAll(
            ".guide-panel"
        );


    tabs.forEach(tab => {

        tab.addEventListener(
            "click",
            function() {

                const target =
                    tab.dataset.guide;


                tabs.forEach(item => {

                    item.classList.remove(
                        "active"
                    );
                });


                panels.forEach(panel => {

                    panel.classList.remove(
                        "active"
                    );
                });


                tab.classList.add(
                    "active"
                );


                const panel =
                    document.querySelector(
                        `[data-guide-panel="${target}"]`
                    );


                if (panel) {

                    panel.classList.add(
                        "active"
                    );
                }

            }
        );

    });
}


/* ============================================================
   CHECKLIST
   ============================================================ */

function setupChecklist() {

    const items =
        document.querySelectorAll(
            "[data-check-item]"
        );


    const storageKey =
        "disasterShieldEmergencyChecklist";


    let saved = {};


    try {

        saved =
            JSON.parse(
                localStorage.getItem(
                    storageKey
                ) || "{}"
            );

    } catch (error) {

        saved = {};
    }


    items.forEach(item => {

        const id =
            item.dataset.checkItem;


        if (saved[id]) {

            item.checked = true;
        }


        item.addEventListener(
            "change",
            function() {

                saved[id] =
                    item.checked;


                localStorage.setItem(
                    storageKey,
                    JSON.stringify(saved)
                );


                updateChecklistProgress();

            }
        );

    });


    updateChecklistProgress();
}


/* ============================================================
   CHECKLIST PROGRESS
   ============================================================ */

function updateChecklistProgress() {

    const items =
        document.querySelectorAll(
            "[data-check-item]"
        );


    const checked =
        document.querySelectorAll(
            "[data-check-item]:checked"
        );


    const progress =
        $("checklistProgress");


    if (progress) {

        progress.textContent =
            `${checked.length} / ${items.length}`;
    }
}


/* ============================================================
   KEYBOARD SOS
   ============================================================ */

function setupKeyboardSafety() {

    document.addEventListener(
        "keydown",
        function(event) {

            if (
                event.key === "Escape"
            ) {

                const dialogs =
                    document.querySelectorAll(
                        "dialog"
                    );

                dialogs.forEach(
                    dialog => {
                        if (dialog.open) {
                            dialog.close();
                        }
                    }
                );
            }

        }
    );
}


/* ============================================================
   INITIALIZATION
   ============================================================ */

document.addEventListener(
    "DOMContentLoaded",
    function() {

        const locationButton =
            $("locationButton");


        if (locationButton) {

            locationButton.addEventListener(
                "click",
                detectLocation
            );
        }


        const copyButton =
            $("copyLocationButton");


        if (copyButton) {

            copyButton.addEventListener(
                "click",
                copyLocation
            );
        }


        const sosButton =
            $("sosButton");


        if (sosButton) {

            sosButton.addEventListener(
                "click",
                triggerSOS
            );
        }


        document
            .querySelectorAll(
                "[data-facility]"
            )
            .forEach(button => {

                button.addEventListener(
                    "click",
                    function() {

                        openFacility(
                            button.dataset.facility
                        );

                    }
                );

            });


        setupGuideTabs();

        setupChecklist();

        setupKeyboardSafety();

    }
);
