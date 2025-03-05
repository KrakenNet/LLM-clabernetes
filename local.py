import sys
import os
import subprocess

import paramiko
import sys
import os
import subprocess

def run_command(command, description="Executing command", exit_on_fail=True, host=None, user=None, password=None):
    """
    Runs a shell command locally or remotely over SSH.
    If host, user, and password are provided, it will execute over SSH.
    """
    print(f"\n[INFO] {description}...")

    if host and user and password:
        # Remote execution via SSH
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(hostname=host, username=user, password=password)

            stdin, stdout, stderr = client.exec_command(command)
            for line in stdout:
                print(line, end="")
            for line in stderr:
                print(line, end="")
                
            exit_status = stdout.channel.recv_exit_status()
            client.close()

            if exit_status != 0:
                raise subprocess.CalledProcessError(exit_status, command)
            print(f"[SUCCESS] {description}")
        
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] {description} failed.")
            print(f"Command: {command}")
            print(f"Error Output:\n{e}")
            if exit_on_fail:
                sys.exit(1)
    else:
        # Local execution
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

