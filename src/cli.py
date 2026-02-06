"""
Command-line interface for the Health Canada Medical Device Regulatory Agent.
"""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint

app = typer.Typer(
    name="meddev-agent",
    help="Health Canada Medical Device Regulatory Compliance Assistant",
    add_completion=False,
)
console = Console()


@app.command()
def classify(
    name: str = typer.Option(..., "--name", "-n", help="Device name"),
    description: str = typer.Option(..., "--desc", "-d", help="Device description"),
    intended_use: str = typer.Option(..., "--use", "-u", help="Intended use statement"),
    software: bool = typer.Option(False, "--software", "-s", help="Is this a software device?"),
    manufacturer: str = typer.Option("Unknown", "--manufacturer", "-m", help="Manufacturer name"),
):
    """Classify a medical device according to Health Canada regulations."""
    from src.core.models import DeviceInfo
    from src.core.classification import classify_device

    device = DeviceInfo(
        name=name,
        description=description,
        intended_use=intended_use,
        is_software=software,
        manufacturer_name=manufacturer,
    )

    result = classify_device(device)

    # Display results
    console.print(Panel(
        f"[bold green]Device Class: {result.device_class.value}[/bold green]\n"
        f"[dim]{result.device_class.risk_level}[/dim]",
        title="Classification Result",
    ))

    console.print(f"\n[bold]Rationale:[/bold]\n{result.rationale}")

    if result.warnings:
        console.print("\n[yellow]Warnings:[/yellow]")
        for warning in result.warnings:
            console.print(f"  - {warning}")

    if result.references:
        console.print("\n[blue]References:[/blue]")
        for ref in result.references:
            console.print(f"  - {ref}")


@app.command()
def pathway(
    device_class: str = typer.Option(..., "--class", "-c", help="Device class (I, II, III, IV)"),
    has_mdel: bool = typer.Option(False, "--has-mdel", help="Already have MDEL?"),
    has_qms: bool = typer.Option(False, "--has-qms", help="Already have QMS certificate?"),
    software: bool = typer.Option(False, "--software", "-s", help="Is this a software device?"),
):
    """Get the regulatory pathway for a device class."""
    from src.core.models import DeviceClass, DeviceInfo, ClassificationResult
    from src.core.pathway import get_pathway

    # Map input to DeviceClass
    class_map = {
        "I": DeviceClass.CLASS_I,
        "II": DeviceClass.CLASS_II,
        "III": DeviceClass.CLASS_III,
        "IV": DeviceClass.CLASS_IV,
    }
    dc = class_map.get(device_class.upper())
    if not dc:
        console.print("[red]Invalid device class. Use I, II, III, or IV[/red]")
        raise typer.Exit(1)

    # Create minimal objects for pathway calculation
    device_info = DeviceInfo(
        name="Generic Device",
        description="Device for pathway calculation",
        intended_use="Pathway planning",
        is_software=software,
        manufacturer_name="Planning",
    )

    classification = ClassificationResult(
        device_class=dc,
        rationale="User-specified classification",
        is_samd=software,
    )

    pathway_result = get_pathway(classification, device_info, has_mdel, has_qms)

    # Display pathway
    console.print(Panel(
        f"[bold]{pathway_result.pathway_name}[/bold]",
        title="Regulatory Pathway",
    ))

    # Steps table
    table = Table(title="Pathway Steps")
    table.add_column("#", style="cyan", width=3)
    table.add_column("Step", style="white")
    table.add_column("Duration", style="green")
    table.add_column("Fee (CAD)", style="yellow")

    for step in pathway_result.steps:
        duration = f"{step.estimated_duration_days} days" if step.estimated_duration_days else "Variable"
        fee = f"${step.fees:,.0f}" if step.fees else "-"
        table.add_row(str(step.step_number), step.name, duration, fee)

    console.print(table)

    # Timeline
    console.print(f"\n[bold]Timeline:[/bold]")
    console.print(f"  Minimum: {pathway_result.timeline.total_days_min} days")
    console.print(f"  Maximum: {pathway_result.timeline.total_days_max} days")

    # Fees
    console.print(f"\n[bold]Total Fees:[/bold] ${pathway_result.fees.total:,.2f} CAD")


@app.command()
def ingest(
    path: str = typer.Argument(..., help="Path to document or directory to ingest"),
    recursive: bool = typer.Option(True, "--recursive", "-r", help="Process subdirectories"),
):
    """Ingest regulatory documents into the knowledge base."""
    from pathlib import Path
    from src.ingestion.pipeline import IngestionPipeline

    source_path = Path(path)
    if not source_path.exists():
        console.print(f"[red]Path not found: {path}[/red]")
        raise typer.Exit(1)

    console.print(f"[bold]Ingesting documents from:[/bold] {path}")

    pipeline = IngestionPipeline()
    stats = pipeline.ingest_path(source_path, recursive=recursive)

    console.print(f"\n[green]Ingestion complete![/green]")
    console.print(f"  Documents processed: {stats['documents_processed']}")
    console.print(f"  Chunks created: {stats['chunks_created']}")
    console.print(f"  Errors: {stats['errors']}")


@app.command()
def chat():
    """Start an interactive chat session with the regulatory agent."""
    from src.agents.regulatory_agent import RegulatoryAgent

    console.print(Panel(
        "[bold]Health Canada Medical Device Regulatory Assistant[/bold]\n"
        "Ask questions about device classification, regulatory pathways,\n"
        "documentation requirements, and more.\n\n"
        "[dim]Type 'quit' or 'exit' to end the session.[/dim]",
        title="Welcome",
    ))

    agent = RegulatoryAgent()

    while True:
        try:
            user_input = console.input("\n[bold cyan]You:[/bold cyan] ")

            if user_input.lower() in ["quit", "exit", "q"]:
                console.print("[dim]Goodbye![/dim]")
                break

            if not user_input.strip():
                continue

            response = agent.chat(user_input)
            console.print(f"\n[bold green]Agent:[/bold green] {response}")

        except KeyboardInterrupt:
            console.print("\n[dim]Session interrupted. Goodbye![/dim]")
            break


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind to"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload"),
):
    """Start the API server."""
    import uvicorn

    console.print(f"[bold]Starting API server at http://{host}:{port}[/bold]")
    uvicorn.run(
        "src.api.main:app",
        host=host,
        port=port,
        reload=reload,
    )


@app.command()
def ui():
    """Launch the Streamlit web interface."""
    import subprocess
    import sys

    console.print("[bold]Launching Streamlit UI...[/bold]")
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        "src/ui/app.py",
        "--server.headless", "true",
    ])


if __name__ == "__main__":
    app()
