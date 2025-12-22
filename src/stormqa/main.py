import typer
import asyncio
import json
import os
from pathlib import Path
from typing_extensions import Annotated

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn

from stormqa.core.loader import LoadTestEngine
from stormqa.core.network_sim import run_network_check, NETWORK_PROFILES
from stormqa.core.db_sim import run_smart_db_test
from stormqa.core.ws_engine import run_websocket_test  # اضافه شده
from stormqa.reporters.main_reporter import generate_report

from stormqa.ui.app import start_gui

app = typer.Typer(
    help="⚡ StormQA CLI v3",
    rich_markup_mode="rich"
)
CACHE_FILE = Path(".stormqa_cache.json")
console = Console()

# --- Cache Helpers ---
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

# --- Commands ---

@app.command()
def start():
    """🌟 Shows welcome message and guide."""
    console.print(Panel(
        Text("⚡️ StormQA v3 ⚡️", justify="center", style="bold cyan"),
        subtitle="The Ultimate Testing Platform (React + Python Core)",
        padding=(1, 2),
        style="on #0f172a"
    ))
    console.print("\n[bold]Available Commands:[/bold]")
    console.print("  [green]stormqa open[/green]       -> Launch the Modern UI (React/Webview)")
    console.print("  [cyan]stormqa load[/cyan]       -> Run Load Test (Supports Chaos & Thresholds)")
    console.print("  [magenta]stormqa ws[/magenta]         -> Run WebSocket Stress Test")
    console.print("  [blue]stormqa network[/blue]    -> Simulate network conditions")
    console.print("  [yellow]stormqa db[/yellow]         -> Discovery or Flood DB endpoints")
    console.print("  [white]stormqa report[/white]     -> Generate Professional PDF Report")

@app.command()
def open():
    """🎨 Launches the Modern Graphical User Interface (React)."""
    console.print("[bold green]🚀 Launching StormQA...[/bold green]")
    start_gui()

@app.command()
def load(
    url: Annotated[str, typer.Argument(help="Target URL")],
    users: Annotated[int, typer.Option(help="Max concurrent users")] = 10,
    duration: Annotated[int, typer.Option(help="Test duration in seconds")] = 30,
    ramp: Annotated[int, typer.Option(help="Ramp-up time in seconds")] = 5,
    think: Annotated[float, typer.Option(help="Think time in seconds")] = 0.5,

    chaos: Annotated[bool, typer.Option(help="Enable Chaos Injection (Failure Simulation)")] = False,
    chaos_rate: Annotated[int, typer.Option(help="Chaos Rate (1-100%)")] = 10,
    chaos_type: Annotated[str, typer.Option(help="Chaos Type: 'latency' or 'exception'")] = "latency",

    thresholds: Annotated[str, typer.Option(help="Pass/Fail Rules e.g. 'p95<500,error<1'")] = None
):
    """🚀 Run a Load Test Scenario (Headless Mode with Chaos Support)."""
    if not url.startswith("http"): url = f"http://{url}"
    
    console.print(f"[bold cyan]⚡ Starting Headless Load Test on {url}[/bold cyan]")
    
    chaos_config = {"enabled": chaos, "rate": chaos_rate, "type": chaos_type}
    if chaos:
        console.print(f"[bold red]🔥 Chaos Injection Active:[/bold red] Type={chaos_type}, Rate={chaos_rate}%")
    
    if thresholds:
        console.print(f"[bold yellow]Funnel Rules:[/bold yellow] {thresholds}")

    step = {
        "users": users,
        "duration": duration,
        "ramp": ramp,
        "think": think
    }
    
    engine = LoadTestEngine()
    
    def cli_callback(stats):
        if int(stats['rps']) % 5 == 0:
            msg = f"   >> Active Users: {stats['users']} | RPS: {stats['rps']:.1f} | Latency: {stats['avg_latency']:.0f}ms | Fail: {stats['failed']}"
            if chaos: msg += " (🔥)"
            print(msg, end="\r")

    try:
        summary = asyncio.run(engine.start_scenario(
            url=url, 
            steps=[step], 
            stats_callback=cli_callback,
            thresholds=thresholds,
            chaos_config=chaos_config
        ))
        
        summary["url"] = url
        
        print(" " * 120)  
        
        result_status = "UNKNOWN"
        if "test_result" in summary:
            result_status = summary["test_result"].get("status", "UNKNOWN").upper()
            
        status_style = "bold green" if result_status == "PASSED" else "bold red"
        console.print(f"\n[{status_style}]✅ Test Completed! Final Status: {result_status}[/{status_style}]")
        
        table = Table(title="Execution Summary", show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Total Requests", str(summary['total_requests']))
        table.add_row("Successful", f"[green]{summary['successful_requests']}[/green]")
        table.add_row("Failed", f"[red]{summary['failed_requests']}[/red]")
        table.add_row("Avg Response Time", f"{summary['avg_response_time_ms']:.2f} ms")
        table.add_row("P95 Latency", f"{summary['p95_latency']:.2f} ms")
        table.add_row("Throughput", f"{summary['throughput_rps']:.2f} req/s")
        
        console.print(table)
        
        if result_status == "FAILED" and "test_result" in summary:
            console.print("[red]Violations:[/red]")
            for fail in summary["test_result"]["failures"]:
                console.print(f"  - {fail}")

        write_to_cache("loadTest", summary)
        write_to_cache("last_run_type", "load") 
        
    except Exception as e:
        console.print(f"\n[bold red]❌ Critical Error:[/bold red] {e}")

@app.command()
def ws(
    url: Annotated[str, typer.Argument(help="WebSocket URL (ws://...)")],
    message: Annotated[str, typer.Option(help="Message to send")] = "Ping",
    duration: Annotated[int, typer.Option(help="Test duration in seconds")] = 5
):
    """🔌 Run WebSocket Stress Test."""
    console.print(f"[bold magenta]🔌 Connecting to WebSocket: {url}[/bold magenta]")
    
    with Console().status("[bold green]Sending traffic...[/bold green]"):
        res = asyncio.run(run_websocket_test(url, message, duration))
    
    status_color = "green" if res['status'] == 'success' else "red"
    console.print(f"[{status_color}]Status: {res['status'].upper()}[/{status_color}]")
    
    table = Table(title="WebSocket Results", header_style="bold cyan")
    table.add_column("Metric", style="white")
    table.add_column("Value", style="yellow")
    
    table.add_row("Messages Sent", str(res['sent']))
    table.add_row("Messages Received", str(res['received']))
    table.add_row("Avg Latency", f"{res['avg_latency']:.2f} ms")
    table.add_row("Errors", str(res['errors']))
    
    console.print(table)
    
    if res['logs']:
        console.print("\n[dim]Recent Logs:[/dim]")
        for l in res['logs'][-5:]:
            console.print(f"  {l}")

@app.command()
def network(
    url: Annotated[str, typer.Argument(help="Target URL")],
    profile: Annotated[str, typer.Option(help=f"Profile: {', '.join(NETWORK_PROFILES.keys())}")] = "4G_LTE"
):
    """🌐 Run Network Simulation Check."""
    if not url.startswith("http"): url = f"http://{url}"
    
    console.print(f"[bold magenta]🌐 Checking Network: {url} (Profile: {profile})[/bold magenta]")
    
    with console.status("[bold green]Ping/Tracing...[/bold green]"):
        res = asyncio.run(run_network_check(url, profile))
    
    if res['status'] == 'success':
        console.print(f"[green]✅ Connection Established[/green]")
        console.print(f"   Simulated Latency: [bold]{res['simulated_delay']} ms[/bold]")
        console.print(f"   Real Network Time: {res['real_network_time']:.2f} ms")
    else:
        console.print(f"[bold red]❌ Connection Failed:[/bold red] {res.get('message')}")
    
    write_to_cache("networkTest", res)

@app.command()
def db(
    url: Annotated[str, typer.Argument(help="Base URL")],
    mode: Annotated[str, typer.Option(help="Mode: 'discovery' or 'connection_flood'")] = "discovery"
):
    """🗄️ Run Database API Tests."""
    if not url.startswith("http"): url = f"http://{url}"
    
    console.print(f"[bold blue]🗄️ Running DB Test ({mode}): {url}[/bold blue]")
    
    with console.status("[bold yellow]Scanning endpoints...[/bold yellow]"):
        res = asyncio.run(run_smart_db_test(url, mode))
    
    if mode == "discovery":
        if res['count'] > 0:
            console.print(f"[green]✅ Found {res['count']} endpoints:[/green]")
            for ep in res['endpoints_found']:
                console.print(f"   - {ep}")
        else:
            console.print("[yellow]⚠️ No common DB endpoints found (Secure or Custom paths).[/yellow]")
    else:
        console.print(f"   Attempts: {res['attempted_connections']}")
        console.print(f"   Held Successfully: [green]{res['held_successfully']}[/green]")
        console.print(f"   Dropped/Failed: [red]{res['dropped_or_timeout']}[/red]")
    
    write_to_cache("dbTest", res)

@app.command()
def report():
    """📄 Generates a Professional PDF Report (Dark Mode)."""
    cache_data = read_from_cache()
    
    data_to_report = cache_data.get("loadTest")
    if not data_to_report:

        console.print("[yellow]⚠️ No recent Load Test data found. Run 'stormqa load ...' first.[/yellow]")
        raise typer.Exit()
    
    console.print("[bold blue]🤖 Generating AI-Enhanced PDF Report...[/bold blue]")
    
    try:
        pdf_path = generate_report(data_to_report)
        console.print(f"\n[bold green]✅ Report Saved Successfully![/bold green]")
        console.print(f"   📂 Path: [underline]{pdf_path}[/underline]")
        
        
    except Exception as e:
        console.print(f"[red]Error generating PDF: {e}[/red]")

if __name__ == "__main__":
    app()