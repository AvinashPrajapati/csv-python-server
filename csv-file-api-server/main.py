import sys
import os
import subprocess
import signal
import shutil

PID_FILE = "api_server.pid"
BOOTSTRAP_FLAG = ".bootstrapped"
REQUIRED_PACKAGES = ["typer", "fastapi", "pandas", "uvicorn"]


def is_virtualenv():
    return sys.prefix != sys.base_prefix or hasattr(sys, "real_prefix")


def get_current_venv_name():
    return os.path.basename(os.environ.get("VIRTUAL_ENV", ""))


def check_installed():
    missing = []
    for pkg in REQUIRED_PACKAGES:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", pkg],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if result.returncode != 0:
            missing.append(pkg)
    return missing


def install_packages(pip_exe, packages):
    subprocess.check_call([pip_exe, "install"] + packages)


def create_virtualenv(env_name):
    subprocess.check_call([sys.executable, "-m", "venv", env_name])
    pip_path = os.path.join(env_name, "Scripts" if os.name == "nt" else "bin", "pip")
    return pip_path


def run_bootstrap(env_path_dir: str = None):
    # print(env_path_dir)
    if env_path_dir:
        pip_exe = os.path.join(
            env_path_dir,
            "Scripts" if os.name == "nt" else "bin",
            "pip.exe" if os.name == "nt" else "pip",
        )
        if not os.path.isfile(pip_exe):
            print(f"❌ 'pip' not found at: {pip_exe}")
            print(
                "🔍 Current directory contents:", os.listdir(os.path.dirname(pip_exe))
            )
            return False

        print(f"🔁 Using existing virtual environment at: {env_path_dir}")

        # Check installed packages in the target env
        missing = []
        for pkg in REQUIRED_PACKAGES:
            result = subprocess.run(
                [pip_exe, "show", pkg],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if result.returncode != 0:
                missing.append(pkg)

        if not missing:
            print("✅ All dependencies already installed in the specified environment.")
            open(BOOTSTRAP_FLAG, "w").write("ok")
            return True

        print(f"📦 Installing missing packages in {env_path_dir}: {', '.join(missing)}")
        install_packages(pip_exe, missing)
        print("✅ Dependencies installed.")
        open(BOOTSTRAP_FLAG, "w").write("ok")
        return True

    # If no env_path_dir passed, fallback to existing logic
    missing = check_installed()
    if not missing:
        open(BOOTSTRAP_FLAG, "w").write("ok")
        print("✅ All dependencies already installed.")
        return True

    print("⚠️  Missing packages: " + ", ".join(missing))

    if is_virtualenv():
        print(f"🧠 Active virtual environment: {get_current_venv_name()}")
        confirm = input("Install missing packages here? [y/n]: ").strip().lower()
        if confirm == "y":
            install_packages(shutil.which("pip"), missing)
            open(BOOTSTRAP_FLAG, "w").write("ok")
            print("✅ Setup complete.")
            return True
        else:
            print("❌ Aborted.")
            return False

    confirm = input("No virtualenv detected. Create one? [y/n]: ").strip().lower()
    if confirm != "y":
        print("❌ Cancelled.")
        return False

    name = input("Enter environment name (without prefix): ").strip()
    env_name = f"env_{name}"
    pip = create_virtualenv(env_name)
    install_packages(pip, REQUIRED_PACKAGES)

    print(f"✅ Virtualenv '{env_name}' created and packages installed.")
    if os.name == "nt":
        print(f"➡️  Activate it: .\\{env_name}\\Scripts\\activate")
    else:
        print(f"➡️  Activate it: source {env_name}/bin/activate")
    open(BOOTSTRAP_FLAG, "w").write("ok")
    return True


# ------------------ EARLY BOOTSTRAP ONLY FOR `check` ----------------------
if __name__ == "__main__":
    # Handle bootstrap via built-in parsing
    if len(sys.argv) >= 3 and sys.argv[1] == "webapi" and sys.argv[2] == "check":
        env_path = None
        for arg in sys.argv:
            if arg.startswith("--env-path-dir="):
                env_path = arg.split("=", 1)[1]
                break
            elif arg == "--env-path-dir":
                idx = sys.argv.index(arg)
                if idx + 1 < len(sys.argv):
                    env_path = sys.argv[idx + 1]
                break

        print(f"🧭 Bootstrap env path: {env_path}")
        run_bootstrap(env_path)
        print("✅ You can now run: python main.py webapi serve --file=your.csv")
        sys.exit(0)

    # Now that bootstrap is passed, safely import typer
    try:
        import typer
    except ImportError:
        print("❌ Missing required package: typer")
        print("Run: python main.py webapi check")
        sys.exit(1)

    # CLI commands start here
    app = typer.Typer()
    webapi_app = typer.Typer()
    app.add_typer(webapi_app, name="webapi")

    @webapi_app.command()
    def serve(
        file: str = typer.Option(..., help="Path to CSV or Excel file"),
        port: int = 3000,
    ):
        if not os.path.exists(BOOTSTRAP_FLAG):
            typer.secho("❌ Environment not bootstrapped!", fg=typer.colors.RED)
            typer.echo("Run: python main.py webapi check")
            raise typer.Exit()

        if not os.path.exists(file):
            typer.secho(f"❌ File '{file}' not found.", fg=typer.colors.RED)
            raise typer.Exit()

        if os.path.exists(PID_FILE):
            typer.secho("⚠️ Server already running!", fg=typer.colors.YELLOW)
            raise typer.Exit()

        with open("datafile.txt", "w") as f:
            f.write(file)

        typer.echo(f"🚀 Starting server on http://localhost:{port} using file: {file}")
        typer.echo("Press Ctrl+C or type 'q' + Enter to stop.\n")

        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "api.server:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
            ]
        )

        with open(PID_FILE, "w") as f:
            f.write(str(process.pid))

        try:
            while True:
                if input().strip().lower() == "q":
                    raise KeyboardInterrupt
        except KeyboardInterrupt:
            typer.echo("🛑 Terminating server...")
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(process.pid), "/F"],
                    stdout=subprocess.DEVNULL,
                )
            else:
                os.kill(process.pid, signal.SIGTERM)
            process.wait()

            for file in [PID_FILE, "datafile.txt"]:
                if os.path.exists(file):
                    os.remove(file)
            typer.echo("✅ Server terminated.")

    @webapi_app.command()
    def terminate():
        if not os.path.exists(PID_FILE):
            typer.echo("⚠️ No running server found.")
            return

        with open(PID_FILE, "r") as f:
            pid = int(f.read())

        try:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(pid), "/F"], check=True)
            else:
                os.kill(pid, signal.SIGTERM)
            typer.echo(f"✅ Server with PID {pid} terminated.")
        except Exception as e:
            typer.echo(f"❌ Failed to terminate: {e}")

        for file in [PID_FILE, "datafile.txt"]:
            if os.path.exists(file):
                os.remove(file)

    app()
