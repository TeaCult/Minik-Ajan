import sys
import os
import subprocess
import shlex
import shutil
import datetime
from pathlib import Path
import traceback
import requests

# --- AGENT FIREWALL CLASS ---
class AgentFirewall:
    def __init__(self):
        self.allowed_commands = {"ls", "grep", "ps", "echo", "cat", "df", "free", "uptime"}
        self.forbidden_patterns = [";", "&", "|", ">", "<", "$", "(", ")", "`"]

    def execute(self, user_input: str):
        try:
            if any(char in user_input for char in self.forbidden_patterns):
                return "Error: Forbidden characters detected."
            
            args = shlex.split(user_input)
            if not args or args[0] not in self.allowed_commands:
               return f"Error: Command not allowed or empty."

            for arg in args[1:]:
                if arg.startswith("/") and not arg.startswith("/tmp"):
                    return f"Privacy Error: Path '{arg}' is restricted."

            result = subprocess.run(args, capture_output=True, text=True, timeout=5, check=False)
            return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"
        except Exception as e:
            return f"System Error: {str(e)}"

# --- AGENT FILE TOOLBOX CLASS ---
class AgentFileToolbox:
    def __init__(self, workspace_root: str = "."):
        self.root = Path(workspace_root).resolve()
        self.trash_dir = self.root / "deleted-modified"
        self.root.mkdir(parents=True, exist_ok=True)
        self.trash_dir.mkdir(parents=True, exist_ok=True)

    def _safe_path(self, target_path: str) -> Path:
        resolved = (self.root / target_path).resolve()
        if not str(resolved).startswith(str(self.root)):
            raise PermissionError("Access Denied: Path outside workspace.")
        return resolved

    def _move_to_trash(self, path: Path):
        if path.exists() and path != self.trash_dir:
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            shutil.move(str(path), str(self.trash_dir / f"{path.name}_{ts}"))

    def mkdir(self, path: str):
        self._safe_path(path).mkdir(parents=True, exist_ok=True)
        return f"Created directory: {path}"

    def read(self, path: str):
        target = self._safe_path(path)
        print(f"[DEBUG] reading: {target}", file=sys.stderr)
        return target.read_text(encoding='utf-8') if target.is_file() else "Error: Not found."

    def write(self, path: str, content: str):
        target = self._safe_path(path)
        if target.exists(): self._move_to_trash(target)
        target.write_text(content, encoding='utf-8')
        return f"Written: {path}"
    def web_search(self, query: str, num_results: int = 5):
        try:
            r = requests.get(
                "http://gediz-serp:8001/search",
                params={"q": query, "num_results": num_results},
                timeout=15,
            )
            r.raise_for_status()
            return r.text
        except Exception as e:
            return f"Error: {e}"

    def web_fetch(self, url: str, max_chars: int = 2000):
        try:
            r = requests.post(
                "http://gediz-fetcher:8002/fetch",
                json={
                    "url": url,
                    "extract_mode": "text",
                    "max_chars": max_chars,
                },
                timeout=20,
            )
            r.raise_for_status()
            return r.text
        except Exception as e:
            return f"Error: {e}"
# --- CLI DISPATCHER ---
def main():
    if len(sys.argv) < 2:
        print("Usage: python3 use_tools.py <tool_name> <args...>")
        return

    tool_name = sys.argv[1]
    args = sys.argv[2:]

    try:
        # --- Flow Tools ---
        if tool_name == "wait":
            sec = int(args[0]) if len(args) >= 1 else 1
            time.sleep(sec)
            print(f"Waited {sec} seconds.")
            
        elif tool_name == "stop":
            print("STOP_SIGNAL: Stopping current wrapper.py run.")
            # Wrapper should be programmed to catch exit code 10 and break its loop
            sys.exit(10)
            
        elif tool_name == "exit":
            print("EXIT_SIGNAL: Exiting the current container entirely.")
            # Sending SIGTERM to PID 1 forces standard Docker containers to stop
            try:
                os.kill(1, signal.SIGTERM)
            except Exception:
                pass
            sys.exit(11) 

        elif tool_name == "finish":
            # Stops the run on a successful note, yielding a final message
            final_message = " ".join(args) if args else "Task completed successfully."
            print(f"FINISH_SIGNAL: {final_message}")
            sys.exit(0)

        # --- Firewall Tool ---
        elif tool_name == "shell":
            fw = AgentFirewall()
            print(fw.execute(" ".join(args)))

        # --- File + Web Tools ---
        elif tool_name in ["read", "write", "mkdir", "web_search", "web_fetch"]:
            ft = AgentFileToolbox()

            if tool_name == "read" and len(args) >= 1:
                print(ft.read(args[0]))

            elif tool_name == "mkdir" and len(args) >= 1:
                print(ft.mkdir(args[0]))

            elif tool_name == "write" and len(args) >= 2:
                print(ft.write(args[0], " ".join(args[1:])))

            elif tool_name == "web_search" and len(args) >= 1:
                num = int(args[1]) if len(args) >= 2 else 5
                print(ft.web_search(args[0], num))

            elif tool_name == "web_fetch" and len(args) >= 1:
                maxc = int(args[1]) if len(args) >= 2 else 2000
                print(ft.web_fetch(args[0], maxc))

            else:
                print(f"Error: Missing arguments for {tool_name}")

        else:
            print(f"Error: Tool '{tool_name}' not recognized.")

    except Exception as e:
        tb = traceback.format_exc().splitlines()
        tail = "\n".join(tb[-20:])[-2000:]
        print(f"TOOL_ERROR: {type(e).__name__}: {e}\n{tail}")
        sys.exit(1)

if __name__ == "__main__":
    main()