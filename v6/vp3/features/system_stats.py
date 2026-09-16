"""
features/system_stats.py — Reads CPU, RAM, and battery via psutil.
"""

try:
    import psutil
    PSUTIL_OK = True
except ImportError:
    PSUTIL_OK = False


def get_stats() -> dict:
    """Return a dict with cpu, ram_used, ram_total, battery_pct, plugged_in."""
    if not PSUTIL_OK:
        return {"error": "psutil not installed. Run: pip install psutil"}

    cpu = psutil.cpu_percent(interval=0.2)

    ram   = psutil.virtual_memory()
    ram_used  = ram.used  // (1024 ** 2)   # MB
    ram_total = ram.total // (1024 ** 2)

    battery = psutil.sensors_battery()
    if battery:
        batt_pct   = round(battery.percent, 1)
        plugged_in = battery.power_plugged
    else:
        batt_pct   = None
        plugged_in = None

    return {
        "cpu":        cpu,
        "ram_used":   ram_used,
        "ram_total":  ram_total,
        "battery":    batt_pct,
        "plugged_in": plugged_in,
    }
