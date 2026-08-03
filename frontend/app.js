// ============================================================
// VOGON WEATHER DASHBOARD
// Frontend data loading and charts
// ============================================================


// ---------------- GENERAL HELPERS ----------------

function fmt(value, decimals = 1, fallback = "--") {
    const number = Number(value);

    if (!Number.isFinite(number)) {
        return fallback;
    }

    return number.toFixed(decimals);
}


function setText(id, text) {
    const element = document.getElementById(id);

    if (element) {
        element.textContent = text;
    }
}


function degToCompass(degrees) {
    const directions = [
        "N", "NNE", "NE", "ENE",
        "E", "ESE", "SE", "SSE",
        "S", "SSW", "SW", "WSW",
        "W", "WNW", "NW", "NNW"
    ];

    const direction = Number(degrees);

    if (!Number.isFinite(direction)) {
        return "---";
    }

    const normalized = ((direction % 360) + 360) % 360;
    const index = Math.round(normalized / 22.5) % 16;

    return directions[index];
}


async function fetchJson(url) {
    const response = await fetch(url, { cache: "no-store" });

    if (!response.ok) {
        throw new Error(`${url} returned HTTP ${response.status}`);
    }

    return response.json();
}


// ---------------- WIND DIRECTION ----------------

let displayedWindDirection = null;


function updateWindDirection(direction) {
    const compassNeedle = document.getElementById("compass-arrow");
    const windText = document.getElementById("wind-direction");
    const value = Number(direction);

    if (!Number.isFinite(value)) {
        if (windText) {
            windText.textContent = "---";
        }
        return;
    }

    const normalized = ((value % 360) + 360) % 360;

    /*
     * Continue from the previous displayed angle using the shortest turn.
     * This prevents the needle from rotating almost a full revolution
     * when the direction changes across north, for example 359° -> 1°.
     */
    if (displayedWindDirection === null) {
        displayedWindDirection = normalized;
    } else {
        const previousNormalized =
            ((displayedWindDirection % 360) + 360) % 360;

        let difference = normalized - previousNormalized;

        if (difference > 180) {
            difference -= 360;
        } else if (difference < -180) {
            difference += 360;
        }

        displayedWindDirection += difference;
    }

    if (compassNeedle) {
    compassNeedle.style.transform =
        `translate(-50%, -100%) rotate(${displayedWindDirection}deg)`;
}

    if (windText) {
        windText.textContent =
            `${Math.round(normalized)}° · ${degToCompass(normalized)}`;
    }
}


// ---------------- STATUS HELPERS ----------------

function updatePressureStatus(trend, stationPressure) {
    const pressureStatus = document.getElementById("pressure_status");

    if (!pressureStatus) {
        return;
    }

    const delta6h = Number(trend.delta);
    const delta24h = Number(trend.delta24);

    pressureStatus.textContent =
        `${trend.arrow ?? "→"} ${fmt(delta6h)} /6h | ` +
        `24h Δ ${fmt(delta24h)}\n` +
        `Station ${fmt(stationPressure)} hPa`;

    pressureStatus.className = "status-line";

    if (delta6h <= -2) {
        pressureStatus.classList.add("trend-falling-fast");
    } else if (delta6h < -0.5) {
        pressureStatus.classList.add("trend-falling");
    } else if (delta6h >= 2) {
        pressureStatus.classList.add("trend-rising-fast");
    } else if (delta6h > 0.5) {
        pressureStatus.classList.add("trend-rising");
    } else {
        pressureStatus.classList.add("trend-stable");
    }
}


function dewpointStatus(temp, dewpoint) {
    const temperature = Number(temp);
    const dew = Number(dewpoint);

    if (!Number.isFinite(temperature) || !Number.isFinite(dew)) {
        return "---";
    }

    const spread = temperature - dew;

    if (dew <= 0 && temperature <= 3) {
        return "❄ Frost risk";
    }

    if (spread <= 2) {
        return "🌫 Fog possible";
    }

    if (dew > 15) {
        return "💧 Humid air";
    }

    if (dew < 5) {
        return "☀ Dry air";
    }

    return "○ Stable";
}


// ---------------- LIVE DATA ----------------

async function loadLiveData() {
    try {
        const [data, trend, rainSummary] = await Promise.all([
            fetchJson("/api/live"),
            fetchJson("/api/trend/pressure?hours=6"),
            fetchJson("/api/rain/summary")
        ]);

        setText("temp", `${fmt(data.temp)} °C`);
        setText(
            "temp-direction",
            data.temp_selected_direction ?? "---"
        );

        setText("humidity", `${fmt(data.humidity)} %`);

        setText("pressure", `${fmt(data.pressure_slp)} hPa`);
        updatePressureStatus(trend, data.pressure);

        setText("dewpoint", `${fmt(data.dewpoint)} °C`);
        setText(
            "dewpoint_status",
            dewpointStatus(data.temp, data.dewpoint)
        );

        setText("wind_avg", `${fmt(data.wind_avg)} m/s`);
        setText("wind_gust", `${fmt(data.wind_gust)} m/s`);
        updateWindDirection(data.wind_dir);

        setText("rain", `${fmt(rainSummary.rain_24h)} mm`);
        setText(
            "rain_status",
            `1h: ${fmt(rainSummary.rain_1h)} mm`
        );

    } catch (error) {
        console.error("LIVE DATA ERROR:", error);
    }
}


// ---------------- CHART HELPERS ----------------

function chartLabels(rows) {
    return rows.map(row => row.timestamp.slice(11, 16));
}


function chartCanvas(id) {
    const canvas = document.getElementById(id);

    if (!canvas) {
        throw new Error(`Chart canvas #${id} was not found`);
    }

    return canvas;
}


// ---------------- ENVIRONMENT CHART ----------------

let envChart = null;


async function loadEnvChart() {
    try {
        const result = await fetchJson(
            "/api/history/env?hours=24"
        );

        const rows = result.data ?? [];
        const labels = chartLabels(rows);

        if (envChart) {
            envChart.destroy();
        }

        envChart = new Chart(chartCanvas("envChart"), {
            type: "line",
            data: {
                labels,
                datasets: [
                    {
                        label: "Temp °C",
                        data: rows.map(row => row.temp ?? null),
                        borderWidth: 2,
                        tension: 0.25
                    },
                    {
                        label: "Humidity %",
                        data: rows.map(row => row.humidity ?? null),
                        borderWidth: 2,
                        tension: 0.25
                    },
                    {
                        label: "Dewpoint °C",
                        data: rows.map(row => row.dewpoint ?? null),
                        borderWidth: 2,
                        tension: 0.25
                    }
                ]
            },
            options: {
                responsive: true,
                animation: false,
                spanGaps: true,
                scales: {
                    y: {
                        beginAtZero: false
                    }
                }
            }
        });

    } catch (error) {
        console.error("ENV CHART ERROR:", error);
    }
}


// ---------------- PRESSURE CHART ----------------

let pressureChart = null;


async function loadPressureChart() {
    try {
        const result = await fetchJson(
            "/api/history/env?hours=24"
        );

        const rows = result.data ?? [];
        const labels = chartLabels(rows);

        if (pressureChart) {
            pressureChart.destroy();
        }

        pressureChart = new Chart(
            chartCanvas("pressureChart"),
            {
                type: "line",
                data: {
                    labels,
                    datasets: [
                        {
                            label: "Pressure hPa",
                            data: rows.map(
                                row => row.pressure_slp ?? null
                            ),
                            borderWidth: 2,
                            tension: 0.25
                        }
                    ]
                },
                options: {
                    responsive: true,
                    animation: false,
                    spanGaps: true,
                    scales: {
                        y: {
                            min: 970,
                            max: 1030
                        }
                    }
                }
            }
        );

    } catch (error) {
        console.error("PRESSURE CHART ERROR:", error);
    }
}


// ---------------- RAIN CHART ----------------

let rainChart = null;


async function loadRainChart() {
    try {
        const result = await fetchJson(
            "/api/history/rain?hours=24"
        );

        const rows = result.data ?? [];
        const labels = chartLabels(rows);

        if (rainChart) {
            rainChart.destroy();
        }

        rainChart = new Chart(chartCanvas("rainChart"), {
            type: "bar",
            data: {
                labels,
                datasets: [
                    {
                        label: "Rain mm / interval",
                        data: rows.map(
                            row => row.rain_interval_mm ?? 0
                        ),
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                animation: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });

    } catch (error) {
        console.error("RAIN CHART ERROR:", error);
    }
}


// ---------------- STARTUP ----------------

async function startDashboard() {
    await Promise.allSettled([
        loadLiveData(),
        loadEnvChart(),
        loadPressureChart(),
        loadRainChart()
    ]);

    setInterval(loadLiveData, 5_000);
    setInterval(loadEnvChart, 60_000);
    setInterval(loadPressureChart, 60_000);
    setInterval(loadRainChart, 60_000);
}


startDashboard();
