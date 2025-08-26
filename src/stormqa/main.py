import typer
import asyncio
import json
from pathlib import Path
from typing_extensions import Annotated

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from stormqa.core.loader import run_load_test
from stormqa.core.network_sim import run_network_test 
from stormqa.core.db_sim import run_db_test
from stormqa.reporters.main_reporter import generate_report
from stormqa.ui.app import launch as launch_gui

app = typer.Typer(
    help="StormQA: The ultimate testing tool.",
    rich_markup_mode="rich"
)
CACHE_FILE = Path(".stormqa_cache.json")
console = Console()

# Cache helpers
def write_to_cache(key: str, data: dict):
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r") as f:
                cache_data = json.load(f)
        except json.JSONDecodeError:
            cache_data = {}
    else:
        cache_data = {}
    
    cache_data[key] = data
    with open(CACHE_FILE, "w") as f:
        json.dump(cache_data, f, indent=4)

def read_from_cache() -> dict:
    if not CACHE_FILE.exists():
        return {}
    with open(CACHE_FILE, "r") as f:
        return json.load(f)


@app.command()
def start():
    """
    🌟 Shows a welcome message and a detailed guide of commands.
    """
    console.print(
        Panel(
            Text("⚡️ Welcome to StormQA ⚡️", justify="center", style="bold cyan"),
            subtitle="The ultimate, zero-config testing tool for developers.",
            padding=(1, 2)
        )
    )

    console.print(
        Panel(
            Text.from_markup(
                "For the best experience, launch the graphical user interface:\n\n"
                "[bold green]stormqa open[/bold green]",
                justify="center"
            ),
            title="🚀 Recommended Start",
            border_style="green",
            padding=1
        )
    )

    console.print("\n[bold]CLI Commands Guide:[/bold]")

    # Load Test
    load_content = """
[cyan]stormqa load [SITE_URL][/cyan]

Runs a performance load test to measure your server's capabilities.

[bold yellow]--concurrency[/bold yellow]: Simultaneous Users
[italic]Analogy: Imagine a restaurant with 5 cashiers. Concurrency is how many customers are ordering [bold]at the exact same moment[/bold]. If concurrency=5, all cashiers are busy. If concurrency=20, 15 customers are waiting in line, increasing their response time (latency).[/italic]

[bold yellow]--requests[/bold yellow]: Total Number of Requests
[italic]Analogy: This is the total number of customers visiting your restaurant during a specific period. It's the total workload your server must handle.[/italic]
    """
    console.print(Panel(Text.from_markup(load_content.strip()), title="🚀 Load & Stress Test", border_style="yellow", padding=(1, 2)))

    # Network Test
    network_content = """
[cyan]stormqa network [SITE_URL][/cyan]

Simulates poor or unstable network conditions.

[bold yellow]--latency[/bold yellow]: Latency (Ping)
[italic]Analogy: Latency is like the physical distance to the server. The further away, the longer it takes for your request to arrive and the response to come back. This parameter simulates that delay in milliseconds.[/italic]

[bold yellow]--packet-loss[/bold yellow]: Packet Loss Percentage
[italic]Analogy: On an unstable network (like mobile internet), some data packets get lost. This parameter simulates the percentage of your requests that never reach their destination.[/italic]
    """
    console.print(Panel(Text.from_markup(network_content.strip()), title="🌐 Network Test", border_style="magenta", padding=(1, 2)))

    # DB Test
    db_content = "[cyan]stormqa db [SITE_URL][/cyan]\n\nAutomatically discovers and tests common API endpoints to check backend health."
    console.print(Panel(Text.from_markup(db_content), title="🗄️ DB Test", border_style="blue"))
    
    # Report
    report_content = "[cyan]stormqa report[/cyan]\n\nGenerates a consolidated JSON/CSV/PDF report from the last test runs."
    console.print(Panel(Text.from_markup(report_content), title="💾 Report", border_style="red"))

    # Open GUI
    open_content = "[cyan]stormqa open[/cyan]\n\nLaunches the graphical user interface (GUI)."
    console.print(Panel(Text.from_markup(open_content), title="🎨 Open GUI", border_style="green"))


@app.command()
def open():
    """🎨 Launches the graphical user interface (GUI)."""
    console.print("🎨 Launching StormQA GUI...", style="green")
    launch_gui()

@app.command()
def load(
    site: Annotated[str, typer.Argument(help="The target site URL to test.")],
    requests: Annotated[int, typer.Option(help="Total number of requests to send.")] = 50,
    concurrency: Annotated[int, typer.Option(help="Number of concurrent requests.")] = 10,
):
    """🚀 Runs a load test with advanced performance metrics."""
    typer.secho("--- StormQA Load Test ---", fg=typer.colors.CYAN, bold=True)
    typer.echo(f"🎯 Target: {site}")
    typer.echo(f"🔄 Total Requests: {requests}")
    typer.echo(f"👥 Concurrency: {concurrency}")
    
    summary = asyncio.run(run_load_test(url=site, requests_count=requests, concurrency=concurrency))
    
    typer.secho("\n--- Test Results ---", fg=typer.colors.CYAN, bold=True)
    typer.secho("\n📊 Performance Summary:", bold=True)
    typer.echo(f"   - Total Time: {summary['total_duration_sec']:.2f} seconds")
    typer.echo(f"   - Throughput (RPS): {summary['throughput_rps']:.2f} req/sec")
    typer.secho("\n⏱️ Response Time (ms):", bold=True)
    typer.secho(f"   - Average: {summary['avg_response_time_ms']:.2f} ms", fg=typer.colors.GREEN)
    typer.secho(f"   - Minimum: {summary['min_response_time_ms']:.2f} ms", fg=typer.colors.BLUE)
    typer.secho(f"   - Maximum: {summary['max_response_time_ms']:.2f} ms", fg=typer.colors.YELLOW)
    typer.secho("\n📈 Request Status:", bold=True)
    typer.secho(f"   - Successful: {summary['successful_requests']}", fg=typer.colors.GREEN)
    typer.secho(f"   - Failed: {summary['failed_requests']}", fg=typer.colors.RED)
    typer.secho(f"   - Error Rate: {summary['error_rate_percent']:.2f} %", fg=typer.colors.RED if summary['error_rate_percent'] > 0 else typer.colors.WHITE)
    typer.secho("--------------------------", fg=typer.colors.CYAN, bold=True)
    
    write_to_cache("loadTest", summary)
    typer.echo("💾 Results saved for reporting.")


@app.command()
def network(
    site: Annotated[str, typer.Argument(help="The target site URL to test.")],
    latency: Annotated[int, typer.Option(help="Simulated latency in milliseconds.")] = 200,
    packet_loss: Annotated[float, typer.Option(help="Simulated packet loss in percentage (0-100).")] = 5.0,
):
    """🌐 Simulates network conditions like latency and packet loss."""
    typer.secho("--- StormQA Network Test ---", fg=typer.colors.MAGENTA, bold=True)
    typer.echo(f"🎯 Target: {site}")
    typer.echo(f"⏱️ Simulating Latency: {latency} ms")
    typer.echo(f"📉 Simulating Packet Loss: {packet_loss} %")

    summary = asyncio.run(run_network_test(url=site, latency_ms=latency, packet_loss_percent=packet_loss))

    typer.secho("\n--- Test Results ---", fg=typer.colors.MAGENTA, bold=True)
    if summary["request_successful"]:
        typer.secho("✅ Request was successful under simulated conditions.", fg=typer.colors.GREEN)
    else:
        typer.secho("❌ Request failed under simulated conditions.", fg=typer.colors.RED)
    typer.secho("--------------------------", fg=typer.colors.MAGENTA, bold=True)
    
    write_to_cache("networkTest", summary)
    typer.echo("💾 Results saved for reporting.")


@app.command()
def db(
    site: Annotated[str, typer.Argument(help="The base site or API URL to test.")],
):
    """🗄️ Runs an automatic, simulated database performance test."""
    typer.secho("--- StormQA Simulated DB Test ---", fg=typer.colors.BLUE, bold=True)
    typer.echo(f"🎯 Target: {site}")

    summary = asyncio.run(run_db_test(base_url=site))

    typer.secho("\n--- DB Test Summary ---", fg=typer.colors.BLUE, bold=True)
    if summary["total_simulated_tx"] == 0:
        typer.secho("⚠️ No common API patterns found to simulate.", fg=typer.colors.YELLOW)
    else:
        typer.echo(f"   - Simulated Transactions: {summary['total_simulated_tx']}")
        typer.secho(f"   - Success: {summary['successful_tx']}", fg=typer.colors.GREEN)
        typer.secho(f"   - Failed: {summary['failed_tx']}", fg=typer.colors.RED)
        typer.echo(f"   - Avg Response Time: {summary['avg_response_time_ms']:.2f} ms")
    typer.secho("---------------------------------", fg=typer.colors.BLUE, bold=True)
    
    write_to_cache("dbTest", summary)
    typer.echo("💾 Results saved for reporting.")


@app.command()
def report(
    format: Annotated[str, typer.Option(help="Output format: json or csv.")] = "json"
):
    """💾 Generates a consolidated report of the latest test runs."""
    cache_data = read_from_cache()
    if not cache_data:
        typer.secho("⚠️ No test results found to report. Please run a test first.", fg=typer.colors.YELLOW)
        raise typer.Exit()
        
    message = generate_report(cache_data, format)
    typer.secho(message, fg=typer.colors.GREEN)
