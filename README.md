<div align="center">

# ⚡ StormQA (v2.0)

**Professional Performance & Security Testing Suite.**
<br>
*Zero-config. Real-time Monitoring. Comprehensive Reporting.*

[![PyPI version](https://img.shields.io/pypi/v/stormqa?color=007EC6&label=PyPI&logo=pypi&logoColor=white)](https://pypi.org/project/stormqa/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## 📋 Requirements

Before running StormQA, ensure you have the following installed:
* **Python 3.8** or higher.
* **pip** (Python Package Installer).
* No complex drivers or external databases are required.

---

## 🚀 Introducing StormQA v2.0

StormQA v2.0 represents a major leap forward from basic scripting. It is designed to be the ultimate "Zero-Configuration" testing tool for developers and QA engineers who need immediate results without writing boilerplate code.

Whether you are stress-testing a new API deployment, checking network resilience, or auditing database endpoints, StormQA provides a unified, modern interface to get the job done.

---

## 💎 Core Module: Advanced Load Testing

The heart of StormQA is its powerful **Load Testing Engine**. It allows you to simulate realistic user behavior and visualize the impact on your server in real-time.

![Load Testing Dashboard](./assets/dashboard_hero.png)

### Key Capabilities:

* **Visual Scenario Builder:** Define your test logic instantly. Set the number of **Users**, test **Duration**, **Ramp-up** time (to simulate gradual traffic increase), and **Think Time** (to mimic human pauses).
* **Real-time Traffic Monitor:** Unlike traditional tools that provide post-test data, StormQA features a live, high-precision graph that visualizes active users and throughput (RPS) second-by-second.
* **Live Metrics Sidebar:** Monitor critical health indicators—Active Users, Requests Per Second (RPS), Average Latency, and Error Counts—directly from the sidebar.
* **PDF Reporting:** With a single click, generate a detailed PDF report containing execution summaries, pass/fail criteria, and performance metrics for stakeholders.

---

## 🛡️ Additional Diagnostic Modules

StormQA goes beyond load testing by integrating essential infrastructure diagnostics.

### 🌐 Network Simulation
Test how your application performs under unstable or slow network conditions. This module allows you to inject artificial latency and connection issues to ensure your app remains robust for users with poor connectivity.

![Network Simulation](./assets/network_sim.png)

* **Profile-Based Testing:** Quickly switch between presets like `3G`, `4G LTE`, `Metro WiFi`, or `Satellite`.
* **Latency Verification:** Verify the exact delay (in ms) introduced to the connection.

### 🗄️ Database Security & Stress
A dedicated module for backend discovery and stability testing.

![Database Testing](./assets/db_test.png)

* **Smart Endpoint Discovery:** Automatically scans for common and hidden API endpoints (e.g., `/api/admin`, `/wp-json`, `/health`) using intelligent user-agent spoofing to bypass basic filters.
* **Redirect Handling:** Smartly follows HTTP 301/302 redirects to identify the true destination of an endpoint.
* **Connection Flood:** Performs a stress test on your database connection pool to ensure it can handle a burst of concurrent connection attempts.

---

## 📦 Installation

StormQA is available on PyPI and can be installed with a single command.

Follow these steps to get StormQA running on your local machine.

#### 1️⃣ **Create a Virtual Environment**
It's recommended to create a separate virtual environment for the project.
```bash
python3 -m venv venv
```

#### 2️⃣ **Activate the Environment**
-   On **Linux/macOS**:
    ```bash
    source venv/bin/activate
    ```
-   On **Windows**:
    ```bash
    .\venv\Scripts\activate
    ```

#### 3️⃣ **Install StormQA**
Install the latest version of StormQA directly from PyPI.
```bash
pip install --upgrade stormqa
```
---

## 🎯 Getting Started

### Graphical User Interface (GUI)
For the full experience, launch the graphical interface:
```bash
stormqa open
```

---

## 📚 CLI Command Reference

-   `stormqa start`: Displays the welcome message and detailed command guide.
-   `stormqa open`: Launches the graphical user interface.
-   `stormqa load https://api.com --users 50 --think 0.5`: Runs a performance load test.
-   `stormqa network https://google.com --profile 3G_SLOW`: Simulates poor network conditions.
-   `stormqa db https://site.com --mode discovery`: Discovers and tests common API endpoints.
-   `stormqa report`: Generates a consolidated report.

*Use `stormqa [COMMAND] --help` for a full list of options for each command.*