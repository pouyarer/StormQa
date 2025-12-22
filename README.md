<div align="center">

<img src="./src/stormqa/ui/storm_logo.png" alt="StormQA Logo" width="300"/>

# ⚡ StormQA Enterprise (v3.0)

**The Ultimate Load & Chaos Engineering Platform.**
<br>
*Zero-Config. Python Core. React UI. Infinite Power.*

[![PyPI version](https://img.shields.io/pypi/v/stormqa?color=007EC6&label=PyPI&logo=pypi&logoColor=white)](https://pypi.org/project/stormqa/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![React](https://img.shields.io/badge/Frontend-React_18-61DAFB?logo=react&logoColor=white)](https://react.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## 🌪️ Why StormQA? (The JMeter Killer)

**Stop wrestling with XML in Apache JMeter. Stop writing boilerplate JavaScript in k6.**

StormQA v3.0 is built for the modern engineer who values **speed** and **power**. We combined the raw performance of a Python Async engine with the beauty of a React frontend to create the ultimate testing suite.

With StormQA, you get **Chaos Engineering**, **WebSocket Testing**, and **AI Analysis** out of the box—features that other tools require complex plugins or scripts to achieve.

> **"StormQA makes JMeter look like a fossil and k6 look like homework."**

---

## 🔥 Key Features: The Full Arsenal

### ⚛️ 1. Next-Gen Dashboard & UI
A completely redesigned interface using **React & Glassmorphism**.
* **Real-time Monitoring:** Watch Users, RPS, and Latency update in milliseconds.
* **Trend History:** Track your API performance over time with historical charts stored in a local SQLite database.

### 🐢💣 2. Chaos Injection (Chaos Engineering)
Test your system's resilience, not just its speed.
* **Latency Injection:** Randomly slow down requests to simulate poor network conditions (e.g., 3G simulation).
* **Connection Drops:** Intentionally fail a percentage of requests to verify your API's error handling and retry logic.

### 📂 3. Data-Driven Testing (CSV)
Simulate real-world traffic with real data.
* **Attach CSV:** Upload a file with thousands of rows (e.g., `users.csv`).
* **Dynamic Injection:** Use `{{username}}` or `{{token}}` in your URL, Headers, or Body. StormQA cycles through the data automatically.

### 🔗 4. Smart Logic: Extract & Assert
Build complex workflows without writing code.
* **Variable Extraction:** Extract a value (like an `AuthToken`) from a login response and use it in subsequent requests.
* **Success Criteria:** Define strict Pass/Fail rules (e.g., `p95 < 500ms` OR `error_rate < 1%`). If the rule breaks, the test fails.

### 🔌 5. Native WebSocket Support
HTTP is not enough.
* **Socket Stress:** Open thousands of concurrent WebSocket connections.
* **Message Echo:** Send messages and measure the precise Round-Trip Time (RTT).

### 💾 6. Portable Scenarios
* **Import/Export:** Save your complex test configurations as `.sqa` files and share them with your team.
* **cURL Import:** Paste a cURL command, and StormQA automatically configures the test.

### 🤖 7. AI-Powered Analysis
* **Smart Insights:** The engine analyzes your results and generates a human-readable summary.
* **Friendly Report:** Generates a PDF report that tells you exactly where the bottlenecks are.

---

## 💎 Visual Tour

### ⚡ The Command Center
The new dashboard provides a comprehensive view of your system's health.

![Main Dashboard](./assets/dashboard_v3.png)

### 🔥 Chaos & Advanced Logic
Configure failure scenarios, thresholds, and data extraction in one place.

![Chaos Injection](./assets/chaos_panel.png)

### 🔌 WebSocket Monitor
Test your real-time infrastructure with a dedicated socket stress tool.

![WebSocket Test](./assets/websocket_mode.png)

---

## 📦 Installation

StormQA is available on PyPI. Follow these steps to get started correctly.

#### 1️⃣ Create a Virtual Environment
It's recommended to create a separate virtual environment for the project to avoid conflicts.
```bash
python3 -m venv venv

```

#### 2️⃣ Activate the Environment

* On **Linux/macOS**:
```bash
source venv/bin/activate

```


* On **Windows**:
```bash
.\venv\Scripts\activate

```



#### 3️⃣ Install StormQA

Now that your environment is active, install the package:

```bash
pip install --upgrade stormqa

```

---

## 🎯 Usage Modes

### 🖥️ GUI Mode

The graphical interface is perfect for designing scenarios, visualizing chaos, and monitoring live metrics.

```bash
stormqa open

```

### 💻 CLI Mode (CI/CD Ready)

StormQA includes a powerful CLI for headless execution in pipelines (Jenkins, GitLab CI, GitHub Actions).

**Run a Load Test with Chaos:**

```bash
stormqa load [http://api.server.com](http://api.server.com) --users 100 --chaos --chaos-type latency

```

**Run a WebSocket Test:**

```bash
stormqa ws ws://chat.server.com --duration 30

```

**Generate AI Report:**

```bash
stormqa report

```

---

## 📚 CLI Command Reference

| Command | Description | Example |
| --- | --- | --- |
| `stormqa start` | Shows the welcome banner and guide. | `stormqa start` |
| `stormqa open` | Launches the React-based GUI. | `stormqa open` |
| `stormqa load` | Runs a headless load test. Supports Chaos & Thresholds. | `stormqa load google.com --chaos` |
| `stormqa ws` | **(NEW)** Runs a WebSocket stress test. | `stormqa ws ws://echo.org` |
| `stormqa network` | Simulates network conditions. | `stormqa network google.com --profile 3G` |
| `stormqa db` | Discovers and floods DB endpoints. | `stormqa db api.com --mode discovery` |
| `stormqa report` | **(NEW)** Generates a PDF report from the last run. | `stormqa report` |

---

## Enjoying StormQA?

<div align="center">

### ❤️ Support the Development

Building enterprise-grade tools requires coffee and dedication. Support the project here:

**[💎 Donate & Support](https://pay.oxapay.com/14009511)**

Powered by **Testeto** | Developed by **[Pouya Rezapour](https://pouyarezapour.ir)**

</div>

```

```
