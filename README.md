<div align="center">

<img src="./src/stormqa/ui/storm_logo.png" alt="StormQA Logo" width="300"/>

# ⚡ StormQA (v2.1)

**The Modern Load Testing Suite for Professionals.**
<br>
*Zero-Config. cURL Import. Real-time Analytics.*

[![PyPI version](https://img.shields.io/pypi/v/stormqa?color=007EC6&label=PyPI&logo=pypi&logoColor=white)](https://pypi.org/project/stormqa/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## 🌪️ What is StormQA?

**Forget the complexity of JMeter. Forget the boilerplate of k6.**

StormQA v2.1 is designed for developers and QA engineers who need **immediate power**. We believe that load testing shouldn't require writing hundreds of lines of code. With StormQA, you can simulate heavy traffic, analyze server bottlenecks, and verify API health in seconds, not hours.

> **"Pour the coffee, paste the cURL, and let the storm begin."**

---

## 🔥 New in v2.1: The Game Changers

We listened to the community. Version 2.1 introduces features that bridge the gap between simple pingers and enterprise-grade testing tools.

### 📋 1. Magic cURL Import (New!)
Stop manually typing headers and bodies.
* **Copy** a request as cURL from your browser's Network tab.
* **Paste** it into StormQA.
* **Done.** We automatically parse the URL, Method, Headers, Cookies, and Body JSON for you.

### 🛠️ 2. Full HTTP Method Support
StormQA is no longer just for GET requests. We now fully support:
* `GET` - Retrieve data.
* `POST` - Create resources (JSON body support).
* `PUT` - Update existing data.
* `DELETE` - Remove resources.

### ✅ 3. Smart Assertions
Traffic is meaningless if the responses are wrong.
* Define a keyword (e.g., `"success": true` or `token`).
* StormQA will mark any response missing that keyword as a **Failure**, even if the HTTP status is 200.

---

## 💎 Core Module: Advanced Load Testing

The heart of StormQA is its powerful **Load Testing Engine**. It allows you to simulate realistic user behavior and visualize the impact on your server in real-time.

![Load Testing Dashboard](./assets/dashboard_hero.png)

### Key Capabilities:
* **Visual Scenario Builder:** Define your test logic instantly. Set the number of **Users**, test **Duration**, **Ramp-up** time, and **Think Time**.
* **CyberChart™ Monitor:** Unlike traditional tools that provide post-test data, StormQA features a live, high-precision graph that visualizes active users and throughput (RPS) second-by-second.
* **Live Metrics Sidebar:** Monitor critical health indicators—Active Users, Requests Per Second (RPS), Average Latency, and Error Counts.
* **PDF Reporting:** With a single click, generate a detailed PDF report containing execution summaries and performance metrics.

---

## 🛡️ Additional Diagnostic Modules

StormQA goes beyond load testing by integrating essential infrastructure diagnostics.

### 🌐 Network Simulation
Test how your application performs under unstable or slow network conditions. Inject artificial latency to ensure robustness.

![Network Simulation](./assets/network_sim.png)

* **Profile-Based Testing:** Quickly switch between presets like `3G`, `4G LTE`, `Metro WiFi`, or `Satellite`.
* **Latency Verification:** Verify the exact delay (in ms) introduced to the connection.

### 🗄️ Database Security & Stress
A dedicated module for backend discovery and stability testing.

![Database Testing](./assets/db_test.png)

* **Smart Endpoint Discovery:** Automatically scans for common API endpoints using intelligent user-agent spoofing.
* **Connection Flood:** Performs a stress test on your database connection pool to ensure it can handle concurrent bursts.

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

### 🚀 Usage
Launch the modernized graphical interface:
```bash
stormqa open
```

Once the interface loads:

Select Method: Choose GET, POST, PUT, or DELETE.

Target: Enter URL or use the "Import cURL" button.

Config: Set your desired user load (e.g., 50 users).

Start: Click "START STORM ⚡" and watch the metrics fly.

---

## 🔮 Roadmap: Coming Soon (v2.2)
We are already working on the next big thing:
🗂️ Test Collections: Save, organize, and load your favorite test scenarios.
🔄 Chain Requests: Use the output of one request (like a token) as the input for the next.
and updated CLI Commands

---

## Enjoying StormQA?
Consider supporting the development or starring the repo!

<div align="center">

<br>

### ❤️ Support the Development

[**💎 Donate & Support**](https://pay.oxapay.com/14009511/156840325)

<br>

Powered by Testeto | Developed by [**Pouya Rezapour**](https://pouyarezapour.ir)

</div>

## 📚 CLI Command Reference

-   `stormqa start`: Displays the welcome message and detailed command guide.
-   `stormqa open`: Launches the graphical user interface.
-   `stormqa load https://api.com --users 50 --think 0.5`: Runs a performance load test.
-   `stormqa network https://google.com --profile 3G_SLOW`: Simulates poor network conditions.
-   `stormqa db https://site.com --mode discovery`: Discovers and tests common API endpoints.
-   `stormqa report`: Generates a consolidated report.

*Use `stormqa [COMMAND] --help` for a full list of options for each command.*
