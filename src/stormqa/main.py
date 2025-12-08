import typer
import asyncio
import json
from pathlib import Path
from typing_extensions import Annotated

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.live import Live

from stormqa.core.loader import LoadTestEngine
from stormqa.core.network_sim import run_network_check, NETWORK_PROFILES
from stormqa.core.db_sim import run_smart_db_test
from stormqa.reporters.main_reporter import generate_report
from stormqa.ui.app import launch as launch_gui

app = typer.Typer(
    help="StormQA Enterprise CLI v2.0",
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
        Text("⚡️ StormQA Enterprise v2.0 ⚡️", justify="center", style="bold cyan"),
        subtitle="The Masterpiece Testing Tool",
        padding=(1, 2)
    ))
    console.print("\n[bold]Available Commands:[/bold]")
    console.print("  [green]stormqa open[/green]       -> Launch the GUI (Recommended)")
    console.print("  [green]stormqa load[/green]       -> Run a quick load test")
    console.print("  [green]stormqa network[/green]    -> Simulate network conditions")
    console.print("  [green]stormqa db[/green]         -> Discovery or Flood DB endpoints")

@app.command()
def open():
    """🎨 Launches the Graphical User Interface (GUI)."""
    console.print("[bold green]🚀 Launching StormQA Interface...[/bold green]")
    launch_gui()

@app.command()
def load(
    url: Annotated[str, typer.Argument(help="Target URL")],
    users: Annotated[int, typer.Option(help="Max concurrent users")] = 10,
    duration: Annotated[int, typer.Option(help="Test duration in seconds")] = 30,
    ramp: Annotated[int, typer.Option(help="Ramp-up time in seconds")] = 5,
    think: Annotated[float, typer.Option(help="Think time in seconds")] = 0.5,
):
    """🚀 Run a Load Test Scenario."""
    if not url.startswith("http"): url = f"http://{url}"
    
    console.print(f"[bold cyan]⚡ Starting Load Test on {url}[/bold cyan]")
    console.print(f"   Config: {users} Users | {duration}s Duration | {ramp}s Ramp | {think}s Think")

    step = {
        "users": users,
        "duration": duration,
        "ramp": ramp,
        "think": think
    }
    
    engine = LoadTestEngine()
    
    def cli_callback(stats):
        if int(stats['rps']) % 5 == 0:
            msg = f"   >> Active Users: {stats['users']} | RPS: {stats['rps']:.1f} | Latency: {stats['avg_latency']:.0f}ms"

            print(msg, end="\r")

    try:
        summary = asyncio.run(engine.start_scenario(url, [step], cli_callback))
        
        print(" " * 100)  
        console.print("\n[bold green]✅ Test Completed Successfully![/bold green]")
        
        table = Table(title="Execution Summary", show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Total Requests", str(summary['total_requests']))
        table.add_row("Successful", f"[green]{summary['successful_requests']}[/green]")
        table.add_row("Failed", f"[red]{summary['failed_requests']}[/red]")
        table.add_row("Avg Response Time", f"{summary['avg_response_time_ms']:.2f} ms")
        table.add_row("Throughput", f"{summary['throughput_rps']:.2f} req/s")
        
        console.print(table)
        write_to_cache("loadTest", summary)
        
    except Exception as e:
        console.print(f"\n[bold red]❌ Critical Error:[/bold red] {e}")

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
def report(
    format: Annotated[str, typer.Option(help="Output format: json or csv.")] = "json"
):
    """💾 Generates a consolidated report from the last test run."""
    cache_data = read_from_cache()
    if not cache_data:
        console.print("[yellow]⚠️ No test results found to report. Run a test first.[/yellow]")
        raise typer.Exit()
    
    filename = f"StormQA_CLI_Report.{format}"
    message = generate_report(cache_data, filename)
    console.print(f"[green]{message}[/green]")

if __name__ == "__main__":
    app()