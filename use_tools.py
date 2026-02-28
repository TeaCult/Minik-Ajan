import sys
import os
import subprocess
import shlex
import shutil
import datetime
import time
import signal
import re
from pathlib import Path
import traceback
import requests

def parse_xml_args(args):
    """Extract values from XML-style tags like <path>val</path>"""
    parsed = []
    for arg in args:
        # Check if it looks like XML tag
        match = re.match(r'<(\w+)>(.*?)</\1>', arg, re.DOTALL)
        if match:
            parsed.append(match.group(2).strip())
        else:
            parsed.append(arg)
    return parsed



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

    def append(self, path: str, content: str):
        """Append content to end of file (creates if not exists)"""
        target = self._safe_path(path)
        with open(target, 'a', encoding='utf-8') as f:
            f.write(content)
        return f"Appended to: {path}"

    def list_dir(self, path: str = "."):
        """List directory contents"""
        target = self._safe_path(path)
        if not target.is_dir():
            return f"Error: {path} is not a directory"
        items = []
        for item in target.iterdir():
            item_type = "DIR" if item.is_dir() else "FILE"
            size = item.stat().st_size if item.is_file() else "-"
            items.append(f"{item_type:6} {size:>10} {item.name}")
        return "\n".join(items) if items else "(empty directory)"

    def edit_file(self, path: str, old_string: str, new_string: str, occurrence: int = 1):
        """
        Search and replace in file. 
        occurrence: which match to replace (1=first, -1=all)
        """
        target = self._safe_path(path)
        if not target.is_file():
            return f"Error: File {path} not found"
        
        content = target.read_text(encoding='utf-8')
        
        if occurrence == -1:
            # Replace all occurrences
            new_content = content.replace(old_string, new_string)
            count = content.count(old_string)
            if count == 0:
                return f"Error: Pattern not found in {path}"
        else:
            # Replace specific occurrence
            parts = content.split(old_string)
            if len(parts) <= occurrence:
                return f"Error: Only {len(parts)-1} occurrences found, requested #{occurrence}"
            new_content = old_string.join(parts[:occurrence]) + new_string + old_string.join(parts[occurrence:])
            count = 1
        
        # Backup before edit
        self._move_to_trash(target)
        target.write_text(new_content, encoding='utf-8')
        
        return f"Edited {path}: replaced {count} occurrence(s)"

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
        if ".pdf" in url[-5:]:
            return "Error: You should not fetch .pdf urls via web_fetch tool. Use pdf_fetch if available."
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

    def http_request(self, method: str, url: str, data: str = None, headers: str = None):
        """Generic HTTP request (GET/POST/PUT/DELETE/PATCH)"""
        try:
            req_headers = {}
            if headers:
                # Parse "key:value,key2:value2" format
                for h in headers.split(','):
                    if ':' in h:
                        k, v = h.split(':', 1)
                        req_headers[k.strip()] = v.strip()
            
            req_data = data if data else None
            
            r = requests.request(
                method.upper(),
                url,
                headers=req_headers,
                data=req_data,
                timeout=30
            )
            return f"Status: {r.status_code}\nHeaders: {dict(r.headers)}\nBody: {r.text[:2000]}"
        except Exception as e:
            return f"Error: {e}"

# --- STANDALONE TOOLS NOT UNDER FT---

def get_current_time_stamp():
    """Returns ISO format timestamp"""
    return datetime.datetime.now().isoformat()

def run_shell(script_path: str):
    """Execute a shell script file"""
    target = Path(script_path)
    if not target.exists():
        return f"Error: Script {script_path} not found"
    os.chmod(target, 0o755)
    result = subprocess.run(
        ["/bin/bash", str(target)], 
        capture_output=True, 
        text=True, 
        timeout=60
    )
    return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"

def run_python(script_path: str):
    """Execute a Python script file"""
    target = Path(script_path)
    if not target.exists():
        return f"Error: Script {script_path} not found"
    result = subprocess.run(
        [sys.executable, str(target)],
        capture_output=True,
        text=True,
        timeout=60
    )
    return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"

def pip_install(packages: str):
    """Install Python packages"""
    pkg_list = packages.split()
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install"] + pkg_list,
        capture_output=True,
        text=True,
        timeout=120
    )
    return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"

def apt_install(packages: str):
    """Install System Packages"""
    pkg_list = packages.split()

    result = subprocess.run(
        ["/bin/apt-get", "update"], 
        capture_output=True,  text=True, timeout=60
    )
    
    result = subprocess.run(
        ["/bin/apt-get","install","-y"]+pkg_list, 
        capture_output=True, text=True,  timeout=60
    )

    
    return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"




# --- CLI DISPATCHER ---
def main():
    if len(sys.argv) < 2:
        print("""Usage: python3 use_tools.py <tool_name> <args...>

Available tools:
  Flow Control:
    wait <seconds>              - Sleep for N seconds
    stop                        - Stop current run (exit 10)
    exit                        - Exit container (exit 11)
    finish <message>            - Success exit (exit 0)
  
  Info:
    timestamp                   - Get current ISO timestamp
  
  Shell:
    shell <command>             - Run allowed shell command
  
  File Operations:
    read <path>                 - Read file contents
    write <path> <content>      - Write/overwrite file
    append <path> <content>     - Append to file
    mkdir <path>                - Create directory
    list <path>                 - List directory contents
    edit <path> <old> <new> [n] - Search/replace in file (n=occurrence, -1=all)
  
  Web:
    web_search <query> [num]    - Search web
    web_fetch <url> [max_chars] - Fetch page content
    http <method> <url> [data] [headers] - Generic HTTP request
  
  Execution:
    run_shell <script.sh>       - Execute shell script
    run_python <script.py>      - Execute Python script
    pip_install <packages>      - Install pip packages
    apt-install                 - Installs system packages
""")
        return

    tool_name = sys.argv[1]
    raw_args = sys.argv[2:]
    args=raw_args
    #args = parse_xml_args(raw_args)  

    # Debug output to stderr so it doesn't interfere with tool output
    print(f"[DEBUG] tool_name: {tool_name}", file=sys.stderr)
    print(f"[DEBUG] raw_args: {raw_args}", file=sys.stderr)
    print(f"[DEBUG] parsed args: {args}", file=sys.stderr)


    try:
        # --- Flow Tools ---
        if tool_name == "wait":
            sec = int(args[0]) if len(args) >= 1 else 1
            time.sleep(sec)
            print(f"Waited {sec} seconds.")
            
        elif tool_name == "stop":
            print("STOP_SIGNAL: Stopping current wrapper.py run.")
            sys.exit(10)
            
        elif tool_name == "exit":
            print("EXIT_SIGNAL: Exiting the current container entirely.")
            try:
                os.kill(1, signal.SIGTERM)
            except Exception:
                pass
            sys.exit(11) 

        elif tool_name == "finish":
            final_message = " ".join(args) if args else "Task completed successfully."
            print(f"FINISH_SIGNAL: {final_message}")
            sys.exit(0)

        # --- Info Tools ---
        elif tool_name == "timestamp":
            print(get_current_time_stamp())

        # --- Firewall Tool ---
        elif tool_name == "shell":
            fw = AgentFirewall()
            print(fw.execute(" ".join(args)))

        # --- File + Web Tools ---
        elif tool_name in ["read", "write", "append", "mkdir", "list", "edit", 
                          "web_search", "web_fetch", "http"]:
            ft = AgentFileToolbox()

            if tool_name == "read" and len(args) >= 1:
                print(ft.read(args[0]))

            elif tool_name == "write" and len(args) >= 2:
                print(ft.write(args[0], " ".join(args[1:])))

            elif tool_name == "append" and len(args) >= 2:
                print(ft.append(args[0], " ".join(args[1:])))

            elif tool_name == "mkdir" and len(args) >= 1:
                print(ft.mkdir(args[0]))

            elif tool_name == "list":
                print(ft.list_dir(args[0] if args else "."))

            elif tool_name == "edit" and len(args) >= 3:
                # edit <path> <old> <new> [occurrence]
                occ = int(args[3]) if len(args) >= 4 else 1
                print(ft.edit_file(args[0], args[1], args[2], occ))

            elif tool_name == "web_search" and len(args) >= 1:
                num = int(args[1]) if len(args) >= 2 else 5
                print(ft.web_search(args[0], num))

            elif tool_name == "web_fetch" and len(args) >= 1:
                maxc = int(args[1]) if len(args) >= 2 else 2000
                print(ft.web_fetch(args[0], maxc))

            elif tool_name == "http" and len(args) >= 2:
                # http <method> <url> [data] [headers]
                data = args[2] if len(args) >= 3 else None
                headers = args[3] if len(args) >= 4 else None
                print(ft.http_request(args[0], args[1], data, headers))

            else:
                print(f"Error: Missing arguments for {tool_name}")

        # --- Execution Tools ---
        elif tool_name == "run_shell" and len(args) >= 1:
            print(run_shell(args[0]))

        elif tool_name == "run_python" and len(args) >= 1:
            print(run_python(args[0]))

        elif tool_name == "pip_install" and len(args) >= 1:
            print(pip_install(" ".join(args)))

        elif tool_name == "apt_install" and len(args) >= 1:
            print(apt_install(" ".join(args)))

        else:
            print(f"Error: Tool '{tool_name}' not recognized or missing arguments.")

    except Exception as e:
        tb = traceback.format_exc().splitlines()
        tail = "\n".join(tb[-20:])[-2000:]
        print(f"TOOL_ERROR: {type(e).__name__}: {e}\n{tail}")
        sys.exit(1)

if __name__ == "__main__":
    main()


# WE ARE OBVIOUSLY MISSING A PDF TOOL - WAIT TOOL - TTS