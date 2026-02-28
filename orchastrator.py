import docker
import os
import secrets
import shutil
from pathlib import Path
import argparse
import docker
import docker.errors
import tempfile

import time
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel

def orchestrate_ui(folder_path):
    # Paths to the specific agent files
    progress_file = os.path.join(folder_path, "TASK_PROGRESS.md")
    incoming_file = os.path.join(folder_path, "INCOMING_MESSAGE.md")
    
    layout = Layout()
    layout.split_column(
        Layout(name="upper"),
        Layout(name="lower", size=3)
    )

    with Live(layout, refresh_per_second=2):
        while True:
            # 1. Update Progress Display
            if os.path.exists(progress_file):
                with open(progress_file, "r") as f:
                    layout["upper"].update(Panel(f.read()[-1000:], title="Agent Progress"))
            
            # 2. Handle User Input (Blinking Cursor simulation)
            msg = input("Inject Message > ") # Standard CLI prompt [4]
            if msg:
                with open(incoming_file, "w") as f:
                    f.write(msg)
                print(f"Sent to agent: {msg}")

def image_exists(client, image_name):
    try:
        client.images.get(image_name)
        return True
    except docker.errors.ImageNotFound:
        return False

def setup_and_launch(
    task_text: str,
    kb_folder: str = None,
    system_prompt_file: str = None,
    image_name: str = "agent-python:3.9"  # Changed default to custom permanent tag
):
    client = docker.from_env()

    # 1. Check/build image [1][2]
    if not image_exists(client, image_name):
        print(f"[+] Image '{image_name}' not found, building permanent image...")
        dockerfile_content = """
FROM python:3.9-slim
RUN pip install --no-cache-dir docker openai rich requests
        """
        # Temp dir for build context (avoids host_path pollution)
        with tempfile.TemporaryDirectory() as temp_dir:
            df_path = Path(temp_dir) / "Dockerfile.agent"
            df_path.write_text(dockerfile_content)
            image, _ = client.images.build(
                path=str(temp_dir),
                dockerfile="Dockerfile.agent",
                tag=image_name,
                rm=True,  # Remove intermediate layers
                pull=True  # Pull fresh base
            )
        print(f"[+] Permanent image '{image_name}' built.")

    # 2. Generate unique ID and paths
    unique_id = secrets.token_hex(8)
    folder_name = f"agent_{unique_id}"
    host_path = Path(os.getcwd()) / folder_name
    host_path.mkdir(parents=True, exist_ok=True)

    # 3-5. (Unchanged: copy files, KB, task.md, system prompt)
    required_files = ["wrapper.py", "use_tools.py"]
    print(f"[*] Initializing workspace at: {host_path}")
    for file_name in required_files:
        if Path(file_name).exists():
            shutil.copy(file_name, host_path / file_name)
        else:
            print(f"[!] Warning: {file_name} not found in current directory.")
    
    if kb_folder:
        kb_source = Path(kb_folder)
        if kb_source.exists() and kb_source.is_dir():
            kb_dest = host_path / "kb"
            shutil.copytree(kb_source, kb_dest)
            print(f"[+] Copied Knowledge Base from '{kb_folder}' to /agent_workspace/kb")
        else:
            print(f"[!] Warning: KB folder '{kb_folder}' not found.")
    
    task_md_path = host_path / "task.md"
    task_md_path.write_text(f"# Task Assignment\n\n{task_text}")
    
    if system_prompt_file:
        shutil.copy(system_prompt_file, host_path / "custom_system_prompt.txt")
        print(f"[+] Custom system prompt injected.")

    print(f"[+] Workspace ready. Launching container...")

    # 6. Launch (no pip now)
    container = client.containers.run(
        image=image_name,
        name=folder_name,
        command=["python3", "/agent_workspace/wrapper.py"],  # Deps pre-installed
        volumes={str(host_path): {"bind": "/agent_workspace", "mode": "rw"}},
        working_dir="/agent_workspace",
        network="ai",
        detach=True,
        tty=True
    )

    print(f"[+] Container {folder_name} is running.")
    print(f"[+] Logs are being written to {host_path}/session_log.txt")
    return folder_name

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Launch Research Agent")
    parser.add_argument("--task", type=str, help="The task string", required=True)
    parser.add_argument("--kb", type=str, help="Path to local Knowledge Base folder", default=None)
    parser.add_argument("--system", type=str, help="Path to custom system prompt file", default=None)
    
    args = parser.parse_args()

    # Example usage:
    # python3 orchastrator.py --task "Analyze the KB folder" --kb ./my_knowledge_base
    
    folder_name = setup_and_launch(
        task_text=args.task,
        kb_folder=args.kb,
        system_prompt_file=args.system
    )

    if folder_name:
        print(f"Follow logs: docker logs -f {folder_name}")
        # Auto-follow logs
        os.system(f'docker logs -f {folder_name}')
        # orchestrate_ui(folder_name)