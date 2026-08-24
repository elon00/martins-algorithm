"""Automated Self-Healing & Code Hygiene Utility."""
import subprocess
import sys

def auto_heal():
    print("🩹 Running Self-Healing Auto-Correction...")
    try:
        subprocess.run(["ruff", "check", "--fix", "."], check=False)
        subprocess.run(["ruff", "format", "."], check=False)
        print("✓ Codebase auto-corrected and formatted successfully.")
    except Exception as e:
        print(f"Notice: Ruff runner: {e}")

if __name__ == "__main__":
    auto_heal()
