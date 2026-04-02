import os
import subprocess
import sys
import venv
from pathlib import Path

def setup():
    # 1. Define paths
    root_dir = Path(__file__).parent.absolute()
    venv_dir = root_dir / ".venv"
    req_file = root_dir / "requirements.txt"

    print(f"--- Elden Ring Save Inspector Setup ---")

    # 2. Create Virtual Environment
    if not venv_dir.exists():
        print(f"Creating virtual environment in {venv_dir}...")
        venv.create(venv_dir, with_pip=True)
    else:
        print("Virtual environment already exists.")

    # 3. Determine the pip executable path
    # Windows uses Scripts\, Linux/Mac uses bin/
    if sys.platform == "win32":
        pip_exe = venv_dir / "Scripts" / "pip.exe"
        python_exe = venv_dir / "Scripts" / "python.exe"
    else:
        pip_exe = venv_dir / "bin" / "pip"
        python_exe = venv_dir / "bin" / "python"

    # 4. Upgrade Pip
    print("Upgrading pip...")
    subprocess.check_call([str(python_exe), "-m", "pip", "install", "--upgrade", "pip"])

    # 5. Install Requirements
    if req_file.exists():
        print(f"Installing dependencies from {req_file}...")
        subprocess.check_call([str(pip_exe), "install", "-r", str(req_file)])
    else:
        print("Error: requirements.txt not found!")
        return

    print("\n" + "="*40)
    print("SETUP COMPLETE!")
    print("="*40)
    print(f"\nTo run your app, use:")
    if sys.platform == "win32":
        print(f"  {venv_dir}\\Scripts\\python.exe main.py")
    else:
        print(f"  {venv_dir}/bin/python main.py")
    print("="*40)

if __name__ == "__main__":
    try:
        setup()
    except Exception as e:
        print(f"\nAn error occurred during setup: {e}")
        input("\nPress Enter to exit...")