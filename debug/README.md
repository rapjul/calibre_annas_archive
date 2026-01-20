# Debugging Scripts

This directory contains scripts to help debug and verify the Anna's Archive Calibre plugin.

## Prerequisites

You need to have `calibre-debug` in your PATH, which comes with Calibre.

## Available Scripts

### 1. `debug_scraping.py`

Tests the core search functionality and parsing logic. It runs a search for "Python" and prints the parsed results (Title, Author, Format, Download Links).

**Usage:**

```bash
calibre-debug -e debug/debug_scraping.py
```

### 2. `verify_circuit_breaker.py`

Verifies the "Configurable Circuit Breaker" feature. It simulates a scenario where all mirrors are down and ensures that:

- The plugin handles the failure gracefully.
- If the circuit breaker is ENABLED, subsequent requests are blocked for 5 minutes.
- If the circuit breaker is DISABLED, the plugin attempts to search again immediately.

**Usage:**

```bash
calibre-debug -e debug/verify_circuit_breaker.py
```

## Troubleshooting

If you see `ImportError`, ensure you are running `calibre-debug` from the **root directory** of the plugin repository, not from inside the `debug/` folder. The scripts are designed to find the plugin modules in the parent directory.
