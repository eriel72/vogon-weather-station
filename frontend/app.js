function fmt(value, decimals = 1) {
    return (value ?? 0).toFixed(decimals);
}


// ---------------- LIVE DATA ----------------

async function loadLiveData() {
    try {
        const response = await fetch("/api/live");
        const data = await response.json();
	const trendResponse = await fetch("/api/trend/pressure?hours=6");
	const trend = await trendResponse.json();
	const rainResponse = await fetch("/api/rain/summary");
	const rainSummary = await rainResponse.json();

        document.getElementById("temp").innerText =
            fmt(data.temp) + " °C";

        document.getElementById("humidity").innerText =
            fmt(data.humidity) + " %";

        const pressureStatus = document.getElementById("pressure_status");

	document.getElementById("pressure").innerText =
    	fmt(data.pressure_slp) + " hPa";

	pressureStatus.innerText =
	(trend.arrow ?? "→") + " " +
	fmt(trend.delta) + " /6h | 24h Δ " +
	fmt(trend.delta24) + "\n" +
	"Station " + fmt(data.pressure) + " hPa";

	pressureStatus.className = "status-line";

	if ((trend.delta ?? 0) <= -2) {
    	pressureStatus.classList.add("trend-falling-fast");
	} else if ((trend.delta ?? 0) < -0.5) {
    	pressureStatus.classList.add("trend-falling");
	} else if ((trend.delta ?? 0) >= 2) {
    	pressureStatus.classList.add("trend-rising-fast");
	} else if ((trend.delta ?? 0) > 0.5) {
    	pressureStatus.classList.add("trend-rising");
	} else {
    	pressureStatus.classList.add("trend-stable");
	}

        document.getElementById("dewpoint").innerText =
            fmt(data.dewpoint) + " °C";
	const spread = (data.temp ?? 0) - (data.dewpoint ?? 0);

	let dewStatus = "○ Stable";

	if ((data.dewpoint ?? 99) <= 0 && (data.temp ?? 99) <= 3) {
    	dewStatus = "❄ Frost risk";
	} else if (spread <= 2) {
    	dewStatus = "🌫 Fog possible";
	} else if ((data.dewpoint ?? 0) > 15) {
    	dewStatus = "💧 Humid air";
	} else if ((data.dewpoint ?? 0) < 5) {
    	dewStatus = "☀ Dry air";
	}

	document.getElementById("dewpoint_status").innerText = dewStatus;
        document.getElementById("wind_avg").innerText =
            fmt(data.wind_avg) + " m/s";

        document.getElementById("wind_gust").innerText =
            fmt(data.wind_gust) + " m/s";

        document.getElementById("rain").innerText =
		fmt(rainSummary.rain_24h) + " mm";

	document.getElementById("rain_status").innerText =
    		"1h: " + fmt(rainSummary.rain_1h) + " mm";

    } catch (err) {
        console.error("LIVE DATA ERROR:", err);
    }
}


// ---------------- ENVIRONMENT CHART ----------------

let envChart = null;

async function loadEnvChart() {
    try {
        const response = await fetch("/api/history/env?hours=24");
        const result = await response.json();

        const labels = result.data.map(row => row.timestamp.slice(11, 16));

        const temp = result.data.map(row => row.temp ?? 0);
        const humidity = result.data.map(row => row.humidity ?? 0);
        const dewpoint = result.data.map(row => row.dewpoint ?? 0);

        const ctx = document.getElementById("envChart");

        if (envChart) {
            envChart.destroy();
        }

        envChart = new Chart(ctx, {
            type: "line",
            data: {
                labels: labels,
                datasets: [
                    {
                        label: "Temp °C",
                        data: temp,
                        borderWidth: 2,
                        tension: 0.25
                    },
                    {
                        label: "Humidity %",
                        data: humidity,
                        borderWidth: 2,
                        tension: 0.25
                    },
                    {
                        label: "Dewpoint °C",
                        data: dewpoint,
                        borderWidth: 2,
                        tension: 0.25
                    }
                ]
            },
            options: {
                responsive: true,
                animation: false,
                scales: {
                    y: {
                        beginAtZero: false
                    }
                }
            }
        });

    } catch (err) {
        console.error("ENV CHART ERROR:", err);
    }
}


// ---------------- PRESSURE CHART ----------------

let pressureChart = null;

async function loadPressureChart() {
    try {
        const response = await fetch("/api/history/env?hours=24");
        const result = await response.json();

        const labels = result.data.map(row => row.timestamp.slice(11, 16));
        const pressure = result.data.map(row => row.pressure_slp ?? 0);

        const ctx = document.getElementById("pressureChart");

        if (pressureChart) {
            pressureChart.destroy();
        }

        pressureChart = new Chart(ctx, {
            type: "line",
            data: {
                labels: labels,
                datasets: [
                    {
                        label: "Pressure hPa",
                        data: pressure,
                        borderWidth: 2,
                        tension: 0.25
                    }
                ]
            },
            options: {
                responsive: true,
                animation: false,
                scales: {
                    y: {
        		min: 970,
        		max: 1030
   		 }
                }
            }
        });

    } catch (err) {
        console.error("PRESSURE CHART ERROR:", err);
    }
}


// ---------------- RAIN CHART ----------------

let rainChart = null;

async function loadRainChart() {
    try {
        const response = await fetch("/api/history/rain?hours=24");
        const result = await response.json();

        const labels = result.data.map(row => row.timestamp.slice(11, 16));
        const rain = result.data.map(row => row.rain_interval_mm ?? 0);

        const ctx = document.getElementById("rainChart");

        if (rainChart) {
            rainChart.destroy();
        }

        rainChart = new Chart(ctx, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [
                    {
                        label: "Rain mm / interval",
                        data: rain,
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

    } catch (err) {
        console.error("RAIN CHART ERROR:", err);
    }
}


// ---------------- STARTUP ----------------

loadLiveData();
loadEnvChart();
loadPressureChart();
loadRainChart();

setInterval(loadLiveData, 5000);
setInterval(loadEnvChart, 60000);
setInterval(loadPressureChart, 60000);
setInterval(loadRainChart, 60000);
