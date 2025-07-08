#!/usr/bin/env python3
"""
End-to-end test for the multi-agent system.
Tests the orchestrator's ability to coordinate between weather and citymapper agents.
"""

import os
import sys
import json
import time
import requests
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()

# Configuration
ORCHESTRATOR_URL = f"http://localhost:{os.environ.get('ORCHESTRATOR_PORT', '3000')}"
WEATHER_URL = f"http://localhost:{os.environ.get('WEATHER_FASTAPI_PORT', '3001')}"
CITYMAPPER_URL = f"http://localhost:{os.environ.get('CITYMAPPER_FASTAPI_PORT', '3002')}"

def check_service_health(name, url):
    """Check if a service is healthy"""
    try:
        response = requests.get(f"{url}/health", timeout=5)
        if response.status_code == 200:
            console.print(f"[green]✓[/green] {name} is healthy")
            return True
        else:
            console.print(f"[red]✗[/red] {name} returned status code {response.status_code}")
            return False
    except requests.RequestException as e:
        console.print(f"[red]✗[/red] {name} is not available: {str(e)}")
        return False

def send_query(query):
    """Send a query to the orchestrator and return the response"""
    console.print(Panel(f"[bold blue]User Query:[/bold blue]\n{query}"))
    
    try:
        response = requests.post(
            f"{ORCHESTRATOR_URL}/prompt",
            json={"text": query},
            timeout=60  # Longer timeout for complex queries
        )
        
        if response.status_code == 200:
            result = response.json()
            console.print(Panel(Markdown(result.get("response", "No response"))))
            return result
        else:
            console.print(f"[red]Error:[/red] Status code {response.status_code}")
            console.print(response.text)
            return None
    except requests.RequestException as e:
        console.print(f"[red]Request failed:[/red] {str(e)}")
        return None

def run_test_suite():
    """Run a series of test queries"""
    test_queries = [
        "What's the weather like in San Francisco today?",
        "Plan a 3-day trip to New York City with focus on museums and parks",
        "I'm planning a trip to San Francisco next week. What's the weather forecast and what activities would you recommend?"
    ]
    
    results = []
    for i, query in enumerate(test_queries, 1):
        console.print(f"\n[bold]Test {i}/{len(test_queries)}[/bold]")
        result = send_query(query)
        results.append(result)
        time.sleep(2)  # Brief pause between tests
    
    return results

def main():
    """Main test function"""
    console.print(Panel("[bold]Multi-Agent System End-to-End Test[/bold]"))
    
    # Check service health
    console.print("\n[bold]Checking service health...[/bold]")
    orchestrator_healthy = check_service_health("Orchestrator", ORCHESTRATOR_URL)
    weather_healthy = check_service_health("Weather Agent", WEATHER_URL)
    citymapper_healthy = check_service_health("Citymapper Agent", CITYMAPPER_URL)
    
    if not (orchestrator_healthy and weather_healthy and citymapper_healthy):
        console.print("[red]Some services are not healthy. Aborting tests.[/red]")
        return 1
    
    # Run tests
    console.print("\n[bold]Running test queries...[/bold]")
    results = run_test_suite()
    
    # Summary
    success_count = sum(1 for r in results if r is not None)
    console.print(f"\n[bold]Test Summary:[/bold] {success_count}/{len(results)} successful")
    
    return 0 if success_count == len(results) else 1

if __name__ == "__main__":
    sys.exit(main())
