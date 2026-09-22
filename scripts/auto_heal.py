"""Local Code Formatting Utility."""
import subprocess

def auto_heal():
    print("Running local code formatting...")
    try:
        subprocess.run(["ruff", "check", "--fix", "."], check=False)
        subprocess.run(["ruff", "format", "."], check=False)
        print("Code formatting commands completed. Review changes before committing.")
    except OSError as e:
        print(f"Ruff could not be executed: {e}")

if __name__ == "__main__":
    auto_heal()
