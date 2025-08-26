import flet as ft
import time
import asyncio
import threading
import json
from pathlib import Path
from typing import Dict, Any

from stormqa.core.loader import run_load_test
from stormqa.core.network_sim import run_network_test
from stormqa.core.db_sim import run_db_test
from stormqa.reporters.main_reporter import generate_report

# Cache management
CACHE_FILE = Path(".stormqa_cache.json")

def read_from_cache() -> dict:
    if not CACHE_FILE.exists():
        return {}
    try:
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def write_to_cache(key: str, data: dict):
    cache_data = read_from_cache()
    cache_data[key] = data
    with open(CACHE_FILE, "w") as f:
        json.dump(cache_data, f, indent=4)

def clear_cache():
    if CACHE_FILE.exists():
        CACHE_FILE.unlink()

def launch():
    """StormQA graphical application with reporting capability."""

    def main(page: ft.Page):
        page.title = "StormQA ⚡️"
        page.window_height = 750
        page.theme_mode = ft.ThemeMode.DARK
        page.padding = 20
        page.vertical_alignment = ft.MainAxisAlignment.START

        # FilePicker for selecting folder to save reports
        def on_dir_selected(ev: ft.FilePickerResultEvent):
            if ev.path:
                full_path = str(Path(ev.path) / f"{file_name_input.value.strip()}.{file_format_dropdown.value}")
                cache_data = read_from_cache()
                if not cache_data:
                    page.snack_bar = ft.SnackBar(ft.Text("⚠️ No test results found to report."), bgcolor=ft.Colors.YELLOW)
                    page.snack_bar.open = True
                    page.update()
                    return
                message = generate_report(cache_data, full_path)
                page.snack_bar = ft.SnackBar(ft.Text(message), bgcolor=ft.Colors.GREEN if "✅" in message else ft.Colors.RED)
                page.snack_bar.open = True
                page.update()

        dir_picker = ft.FilePicker(on_result=on_dir_selected)
        page.overlay.append(dir_picker)

        # Custom dialog for file name and format
        file_name_input = ft.TextField(label="File Name", value="stormqa_report", expand=True)
        file_format_dropdown = ft.Dropdown(
            label="Format",
            options=[ft.dropdown.Option("json"), ft.dropdown.Option("csv"), ft.dropdown.Option("pdf")],
            value="json",
            expand=True,
        )

        def confirm_save(e):
            name = file_name_input.value.strip()
            if not name:
                page.snack_bar = ft.SnackBar(ft.Text("❌ Please enter a file name."), bgcolor=ft.Colors.RED)
                page.snack_bar.open = True
                page.update()
                return
            dlg.open = False
            page.update()
            dir_picker.get_directory_path(dialog_title="Select Folder to Save Report")

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Save Report"),
            content=ft.Column([file_name_input, file_format_dropdown], tight=True),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: (setattr(dlg, "open", False), page.update())),
                ft.FilledButton("Save", icon=ft.Icons.SAVE_ALT, on_click=confirm_save),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.overlay.append(dlg)

        def open_save_dialog(e):
            dlg.open = True
            page.update()

        # Widgets
        txt_url = ft.TextField(label="Target URL", hint_text="https://api.example.com", expand=True)
        txt_requests = ft.TextField(label="Requests", value="50", expand=True, text_align=ft.TextAlign.CENTER)
        txt_concurrency = ft.TextField(label="Concurrency", value="10", expand=True, text_align=ft.TextAlign.CENTER)
        txt_latency = ft.TextField(label="Latency (ms)", value="200", expand=True, text_align=ft.TextAlign.CENTER)
        txt_packet_loss = ft.TextField(label="Packet Loss (%)", value="5", expand=True, text_align=ft.TextAlign.CENTER)

        console_output = ft.ListView(spacing=5, auto_scroll=True)
        console_container = ft.Container(
            content=console_output,
            border=ft.border.all(1, ft.Colors.GREY_700),
            border_radius=10,
            expand=True,
            padding=10,
        )
        progress_bar = ft.ProgressBar(value=None, visible=False)

        # Display functions
        def test_finished():
            btn_start.disabled = False
            progress_bar.visible = False
            page.update()

        def display_load_summary(summary: Dict[str, Any]):
            console_output.controls.append(ft.Text("--- Load Test Results ---", color=ft.Colors.CYAN, weight="bold"))
            console_output.controls.append(ft.Text(f"Total Time: {summary['total_duration_sec']:.2f}s | Throughput: {summary['throughput_rps']:.2f} RPS"))
            console_output.controls.append(ft.Text(f"Avg Response: {summary['avg_response_time_ms']:.2f}ms | Min: {summary['min_response_time_ms']:.2f}ms | Max: {summary['max_response_time_ms']:.2f}ms"))
            console_output.controls.append(ft.Text(f"Successful: {summary['successful_requests']} | Failed: {summary['failed_requests']} ({summary['error_rate_percent']:.2f}%)", color=ft.Colors.GREEN if summary["failed_requests"] == 0 else ft.Colors.RED))
            write_to_cache("loadTest", summary)
            test_finished()

        def display_network_summary(summary: Dict[str, Any]):
            console_output.controls.append(ft.Text("--- Network Test Results ---", color=ft.Colors.PINK, weight="bold"))
            if summary["request_successful"]:
                console_output.controls.append(ft.Text("✅ Request successful under simulated conditions.", color=ft.Colors.GREEN))
            else:
                console_output.controls.append(ft.Text("❌ Request failed under simulated conditions.", color=ft.Colors.RED))
            write_to_cache("networkTest", summary)
            test_finished()

        def display_db_summary(summary: Dict[str, Any]):
            console_output.controls.append(ft.Text("--- DB Test Summary ---", color=ft.Colors.BLUE, weight="bold"))
            if summary["total_simulated_tx"] == 0:
                console_output.controls.append(ft.Text("⚠️ No common API patterns found.", color=ft.Colors.YELLOW))
            else:
                console_output.controls.append(ft.Text(f"Simulated Transactions: {summary['total_simulated_tx']} | Success: {summary['successful_tx']} | Failed: {summary['failed_tx']}"))
                console_output.controls.append(ft.Text(f"Avg Response Time: {summary['avg_response_time_ms']:.2f} ms"))
            write_to_cache("dbTest", summary)
            test_finished()

        # Run tests in thread and bridge to UI
        def run_test_in_thread(target_func, display_func, *args):
            summary = asyncio.run(target_func(*args))
            page.run_thread(lambda: display_func(summary))

        # Start test handler
        def on_start_test(e):
            if not txt_url.value:
                console_output.controls.clear()
                console_output.controls.append(ft.Text("❌ Error: Target URL cannot be empty.", color=ft.Colors.RED))
                page.update()
                return

            # Clear cache before starting new test
            clear_cache()

            console_output.controls.clear()
            console_output.controls.append(ft.Text(f"[{time.strftime('%H:%M:%S')}] ▶ Test initiated...", color=ft.Colors.GREY))
            btn_start.disabled = True
            progress_bar.visible = True
            page.update()

            url = txt_url.value
            active_test = dd_test_type.value
            target_thread = None

            try:
                if active_test == "🚀 Load Test":
                    args = (url, int(txt_requests.value), int(txt_concurrency.value))
                    target_thread = threading.Thread(target=run_test_in_thread, args=(run_load_test, display_load_summary, *args))
                elif active_test == "🌐 Network Test":
                    args = (url, int(txt_latency.value), float(txt_packet_loss.value))
                    target_thread = threading.Thread(target=run_test_in_thread, args=(run_network_test, display_network_summary, *args))
                else:  # DB Test
                    args = (url,)
                    target_thread = threading.Thread(target=run_test_in_thread, args=(run_db_test, display_db_summary, *args))
            except ValueError:
                console_output.controls.append(ft.Text("❌ Error: Please enter valid numbers for test parameters.", color=ft.Colors.RED))
                test_finished()
                return

            if target_thread:
                target_thread.start()

        btn_start = ft.FilledButton("Start Test", icon=ft.Icons.PLAY_ARROW, on_click=on_start_test)
        btn_generate_report = ft.OutlinedButton("Generate Report", icon=ft.Icons.SAVE_ALT, on_click=open_save_dialog)

        load_inputs = ft.Row([txt_requests, txt_concurrency], spacing=10, visible=True)
        network_inputs = ft.Row([txt_latency, txt_packet_loss], spacing=10, visible=False)

        dd_test_type = ft.Dropdown(
            label="Select Test Type",
            expand=True,
            options=[
                ft.dropdown.Option("🚀 Load Test"),
                ft.dropdown.Option("🌐 Network Test"),
                ft.dropdown.Option("🗄 DB Test"),
            ],
            value="🚀 Load Test",
        )

        def update_inputs(e):
            load_inputs.visible = dd_test_type.value == "🚀 Load Test"
            network_inputs.visible = dd_test_type.value == "🌐 Network Test"
            page.update()

        dd_test_type.on_change = update_inputs

        page.add(
            ft.Column(
                [
                    ft.Row([ft.Icon(ft.Icons.BOLT, color=ft.Colors.AMBER, size=30), ft.Text("StormQA", size=26, weight="bold")], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row([dd_test_type]),
                    ft.Row([txt_url]),
                    load_inputs,
                    network_inputs,
                    ft.Row([btn_start, btn_generate_report], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
                    progress_bar,
                    ft.Divider(),
                    ft.Text("📜 Console Output", size=18, weight="bold"),
                    console_container,
                ],
                spacing=15,
                expand=True,
            )
        )

    ft.app(target=main)
