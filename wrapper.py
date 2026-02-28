import os
import re
import json
import shlex
import subprocess
import openai
import sys
import concurrent.futures
from openai import OpenAI # [MODIFIED] Added to actually invoke the LLM
import time 

API_KEY="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# ==========================================
# CONFIGURATION
# ==========================================
SYSTEM_PROMPT = """
You are an agentic system that thinks acts and observe. 

IMPORTANT: All tools in the 'tool_calls' array are executed CONCURRENTLY in parallel. 
web_serach can provide 5 concurrent searches per second at most. 
Do not schedule dependent actions (like writing a file then reading that exact file) in the same turn. 
Wait for the next step to do dependent actions.

IMPORTANT: You must ONLY output a valid JSON object in the exact following schema:
{
  "thought": "Your thoughts on what to do next",
  "tool_calls": [
    {
      "name": "tool_name_here",
      "arguments": ["arg1", "arg2"]
    }
  ]
}

web_search and web_fetch tools are very supperior , if you can't get the results sites not responding are paywalled for sure, 
do not try to circumvent web_search and web_fetch fails via custom python or shell codes.

Available Tools:
    read <path>: Read file.
    write <path> <content>: Write file.
    mkdir <path>: Create dir.
    web_search <query> <num_results,default=5>: Makes a web search.
    web_fetch <url> <max_chars>: Fetches an url.
    finish: finishes entire session and exits from sandbox environment. WILL BE CALLED WHEN TASK IS FINISHED.
    stop: force stops execution.
    exit: force exits sandbox environment.
    timestamp: gets current timestamp,
    append <path> <content>: append <arg>path</arg> <arg>content</arg>,
    list <path>: lists the files and folders,
    edit <path> <old> <new> <occurrence>: edits a specific part of a file instead of read and write
    http <method> <url> <data> <headers>: runs http requests directly
    run_shell <script_path>: runs shell script
    run_python <script_path>: run a python script
    pip_install <packages>: install a python package
    shell <bash command> : Runs in bash  # But please prefer to run scripts instead of directly running shell commands
    apt_install <packages>: Installs system packages

You can install these tools and use them to help you if you need them via apt-get but first update:
curl wget git jq tree unzip zip dnsutils lsof strace file p7zip-full openssl


YOUR TASK IS:
{MAIN_TASK}

Create and update task progress at every cycle to TASK_PROGRESS.md as you progress in each cycle.

THERE MAY BE <__INCOMING_MESSAGE_INTERRUPTION__:<content>> between messages, 
regard them as task redirection and adjust your methods to accomplish the main task or the main task itself. 
"""


BASE_URL = "https://api.deepinfra.com/v1/openai"
#MODEL_NAME = "deepseek-ai/DeepSeek-V3.2"
#MODEL_NAME = "openai/gpt-oss-120b"
MODEL_NAME = "moonshotai/Kimi-K2.5"



# Constants from context [2]
WORK_DIR = "/agent_workspace"
SESSION_FILE = f"{WORK_DIR}/session_log.txt"
TOOL_SCRIPT = f"{WORK_DIR}/use_tools.py"
MAX_CHAR_SIZE = 300000 
MAX_STEPS = 100 # SLICK UPGRADE: Prevent infinite loops

def get_llm_response(client, messages):
    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            response_format={"type": "json_object"}
        )
        raw = resp.choices[0].message.content
        
        # SLICK UPGRADE: Bulletproof JSON extraction using Regex
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return {"error": "No JSON object found in response."}
        
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON format: {str(e)}"}
    except Exception as e:
        log_event("ERROR", f"LLM Call Failed: {e}")
        return None

def log_raw_activity(label, content):
    os.makedirs("raw_activity", exist_ok=True)
    timestamp = int(time.time() * 1000)
    filename = f"raw_activity/{timestamp}_{label}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(str(content))

def log_event(label, content):
    entry = f"\n[{label}] {content}\n"
    print(entry)
    # Ensure directory exists before writing logs
    os.makedirs(WORK_DIR, exist_ok=True)
    with open(SESSION_FILE, "a") as f:
        f.write(entry)

def execute_tool_call(tool_name, args):
    """Executes a single tool via the use_tools.py script [1]."""
    try:
        # Cast tool_name into string safely
        cmd = ["python3", TOOL_SCRIPT, str(tool_name)] + [str(a) for a in args]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
        return res.stdout if res.returncode == 0 else f"ERROR: {res.stderr}"
    except Exception as e:
        return f"SYSTEM_ERROR: {str(e)}"

# [MODIFIED] Helper function strictly for processing items in the thread pool
def _process_single_tool(call):
    name = call.get("name")
    args = call.get("arguments", [])
    
    # Catch empty/None tool names
    if not name:
        return False, f"Tool Error: tool name was missing in standard JSON call. Raw call: {call}"
        
    if name in ["finish", "stop", "exit"]:
        # Returns a tuple of (is_exit_signal, observation_string)
        return True, f"Signal received: {name}. Exiting."
    
    log_raw_activity(f"TOOL_INPUT_{name}", args)
    result = execute_tool_call(name, args)
    log_raw_activity(f"TOOL_OUTPUT_{name}", result)
    return False, f"Tool {name} Result: {result}"

def run_agent(task_description):
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.replace("{MAIN_TASK}",task_description)},
        {"role": "user", "content": "Begin task."}
    ]
    
    
    for step in range(MAX_STEPS):
  
        # 1. Check if the message bus file exists and has content
        interrupt_file = "INCOMING_MESSAGE.md"
        if os.path.exists(interrupt_file) and os.path.getsize(interrupt_file) > 0:
            try:
                # 2. Read the content
                with open(interrupt_file, "r") as f:
                    interruption_content = f.read().strip()
                
                # 3. ZERO OUT the file immediately to prevent duplicate reads
                with open(interrupt_file, "w") as f:
                    f.truncate(0) 

                # 4. Inject into the agent's message loop
                if interruption_content:
                    log_event("SYSTEM", f"External Interruption Received: {interruption_content[:50]}...")
                    messages.append({
                        "role": "user", 
                        "content": f"<INCOMING_MESSAGE_INTERRUPTION : {interruption_content} >"
                    })
            except Exception as e:
                log_event("ERROR", f"Failed to read/clear interruption file: {e}")


        log_event("SYSTEM", f"--- Step {step + 1}/{MAX_STEPS} ---")
        
        log_raw_activity("LLM_INPUT", messages)
        response_json = get_llm_response(client, messages) 
        log_raw_activity("LLM_OUTPUT", response_json)
        if not response_json: 
            break
            
        # SLICK UPGRADE: If the LLM messed up the JSON, tell it to fix it!
        if "error" in response_json:
            error_msg = f"System Error: {response_json['error']}. Please output VALID JSON ONLY containing 'thought' and 'tool_calls'."
            log_event("OBSERVATION", error_msg)
            messages.append({"role": "user", "content": error_msg})
            continue # Try again
        
        log_event("THOUGHT", response_json.get("thought", "Acting..."))
        messages.append({"role": "assistant", "content": json.dumps(response_json)})

        tool_calls = response_json.get("tool_calls", [])
        observations = []
        exit_signal = False

        if tool_calls:
            # SLICK UPGRADE: Cap concurrent workers to prevent OS crashes on massive tool call arrays
            max_workers = min(len(tool_calls), 10) 
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                results = executor.map(_process_single_tool, tool_calls)
                
                for is_exit, obs_str in results:
                    observations.append(obs_str)
                    if is_exit:
                        exit_signal = True

        combined_obs = "\n".join(observations)
        if combined_obs:  
            log_event("OBSERVATION", combined_obs)
            messages.append({"role": "user", "content": combined_obs})

        if exit_signal:
            log_event("SYSTEM", "Task finalized successfully.")
            break

        # SLICK UPGRADE: Safe Memory Management
        current_chars = sum(len(str(m.get("content", ""))) for m in messages)
        if current_chars > MAX_CHAR_SIZE:
            log_event("SYSTEM", "Memory warning. Dropping oldest interactions to preserve context...")
            # Keep System prompt [0], initial task [1], and the 6 most recent messages.
            # This safely throws away the middle without breaking JSON formatting.
            
            
            summary = [
            {"role": "user", "content": "Summary: You can look at the TASK_PROGRESS.md in work folder for summary."}
            ]
            
            messages = messages[:2] + summary+ messages[-6:]

    if not exit_signal:
        log_event("SYSTEM", "Agent stopped: Reached MAX_STEPS limit.")
        
    return "Agent session ended."

if __name__ == "__main__":
    # Ensure workspace logic stays intact if use_tools.py depends on it
    os.makedirs(WORK_DIR, exist_ok=True)
    
    # Read directly from task.md in the current directory
    try:
        with open("task.md", "r") as f:
            task = f.read()
    except FileNotFoundError:
        print("ERROR: 'task.md' not found in the current working directory.")
        sys.exit(1)
    run_agent(task)

