import docker
import os
import secrets
import shutil
from pathlib import Path
import argparse

def setup_and_launch(
    task_text: str, 
    kb_folder: str = None, 
    system_prompt_file: str = None,
    image_name: str = "python:3.9-slim"
):
    client = docker.from_env()

    # 1. Generate unique ID and paths
    unique_id = secrets.token_hex(8)
    folder_name = f"agent_{unique_id}"
    host_path = Path(os.getcwd()) / folder_name
    host_path.mkdir(parents=True, exist_ok=True)

    # 2. Source Logic Files
    required_files = ["wrapper.py", "use_tools.py"]
    
    try:
        print(f"[*] Initializing workspace at: {host_path}")

        # Copy Logic
        for file_name in required_files:
            if Path(file_name).exists():
                shutil.copy(file_name, host_path / file_name)
            else:
                print(f"[!] Warning: {file_name} not found in current directory.")

        # 3. Handle Knowledge Base (KB) Injection
        if kb_folder:
            kb_source = Path(kb_folder)
            if kb_source.exists() and kb_source.is_dir():
                kb_dest = host_path / "kb"
                shutil.copytree(kb_source, kb_dest)
                print(f"[+] Copied Knowledge Base from '{kb_folder}' to /agent_workspace/kb")
            else:
                print(f"[!] Warning: KB folder '{kb_folder}' not found.")

        # 4. Handle Task File
        task_md_path = host_path / "task.md"
        task_md_path.write_text(f"# Task Assignment\n\n{task_text}")

        # 5. Handle Custom System Prompt (Optional)
        # If you provide a system file, we tell wrapper to look for it.
        # Otherwise wrapper uses its internal default.
        if system_prompt_file:
            shutil.copy(system_prompt_file, host_path / "custom_system_prompt.txt")
            print(f"[+] Custom system prompt injected.")
            # Note: You'd need to modify wrapper.py to read this file if it exists.
            # For now, we stick to the default wrapper behavior unless you want to edit that too.

        print(f"[+] Workspace ready. Launching container...")

        # 6. Launch Container
        # We mount the host_path to /agent_workspace
        container = client.containers.run(
            image=image_name,
            name=folder_name,
            command=[
                "sh",
                "-c",
                # Install deps and run wrapper
                "pip install --no-cache-dir docker openai rich requests; python3 /agent_workspace/wrapper.py"
            ],
            volumes={
                str(host_path): {"bind": "/agent_workspace", "mode": "rw"}
            },
            working_dir="/agent_workspace",
            network="ai",        # Ensure this matches your docker network name
            detach=True,
            tty=True
        )

        print(f"[+] Container {folder_name} is running.")
        print(f"[+] Logs are being written to {host_path}/session_log.txt")
        return folder_name

    except Exception as e:
        print(f"[!] System Error: {e}")
        # Cleanup on failure?
        # shutil.rmtree(host_path) 
        return None

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