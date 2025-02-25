import sys
import os
import subprocess

def run_command(command, description="Executing command", exit_on_fail=True):
    """Runs a shell command and prints real-time output."""
    print(f"\n[INFO] {description}...")
    try:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        for line in process.stdout:
            print(line, end="")
        for line in process.stderr:
            print(line, end="")
        process.communicate()
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, command)
        print(f"[SUCCESS] {description}")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {description} failed.")
        print(f"Command: {command}")
        print(f"Error Output:\n{e}")
        if exit_on_fail:
            sys.exit(1)