import os
import json
import subprocess
import time
import openai
import re

# --- CONFIGURATION ---
API_KEY="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
MAX_CHARS = 50000
WORK_DIR = "/agent_workspace"
SESSION_FILE = f"{WORK_DIR}/session_log.txt"
STATE_FILE = f"{WORK_DIR}/rolling_memory.json"
TOOL_SCRIPT = f"{WORK_DIR}/use_tools.py"
TASK_FILE=f"{WORK_DIR}/task.md"

with open(TASK_FILE, "r") as f:
    MAIN_TASK=f.read()


INITIAL_STATE = {
    "executor": {"task_memory": "Starting task.", "next_steps": "Initialize environment."},
    "auditor": {"status": "Nominal", "critique": "None"},
    "ideator": {"suggestions": ["Waiting task to progress to ideate"]},
    "archivist": {"summary": "Session started.", "importance_index": 5}
}


SYSTEM_PROMPT = """
You are an Agentic System with 4 internal personalities:
1. Executor: Focuses on task completion.
2. Auditor: Checks for errors, loops, or logic gaps.
3. Ideator: Suggests creative shortcuts or missed connections.
4. Archivist: Manages the 'Rolling Memory' JSON to keep context lean.

RESTRICTIONS:
- Working directory: /agent_workspace  Create work files on this location
- read/write/mkdir: Paths ONLY under /agent_workspace and its subfolders 
- Shell command and execute are not available to you and heavily restricted 
- Shell command WONT WORK! other than {"ls", "grep", "ps", "echo", "cat"} 
- Shell command [";", "&", "|", ">", "<", "$", "(", ")", "`"] patterns are FORBIDDEN


CRITICAL PERFORMANCE RULES:
1.  DO NOT rewrite a file immediately after reading it unless the user explicitly requested a modification or you are aggregating NEW search results.
2.  If you read a file and the content looks correct, DO NOT write it back. Move to the next logical step (e.g., perform a web_search).
3.  Only write a file if you have created NEW data or synthesized a repo


Every response MUST be a JSON object with:
{
  "memory_update": { ... updated 4-personality state ... },
  "thought": "Internal monologue",
  "tool_call": "tool_name <arg>arg1</arg> <arg>arg2</arg>" (or null)
}

Available Tools:
- read <path>: Read file.
- write <path> <content>: Write file.
- mkdir <path>: Create dir.
- web_search <query> <num_results,default=5>: Makes a web search.
- web_fetch <url> <max_chars>: Fetches an url. 
- finish: finishes entire session and exits from sandbox environment.
- stop: force stops execution.
- exit: force exits sandbox environment. 

Unavailable Tools: 
- Shell <arg> : Runs in bash 
- Execute <arg> : Runs in bash 

YOUR TASK IS: 


""" + MAIN_TASK


TOOL_HANDLER_PROMPT = """
You are a safe Tool Handler LLM. Handle tool calls ONLY within restrictions:
- Output: {{"action": "execute|deny", "reason": "...", "safe_cmd": ["python3", "use_tools.py", ...] or null}}

Tool call: {{tool_call}}
""".replace("{WORK_DIR}", WORK_DIR)

def print_event(tag, content):
    print(f"\n--- {tag.upper()} ---")
    print(json.dumps(json.loads(content) if isinstance(content, str) and content.strip().startswith('[{') else content, indent=2))
    print("-" * 80)
    with open(SESSION_FILE, "a") as f:
        f.write(f"\n--- {tag} ---\n{content}\n")

def safe_execute_tool(t_call):
    """Delegate to Tool Handler LLM for safe parsing/execution."""
    messages = [
        {"role": "system", "content": TOOL_HANDLER_PROMPT.format(WORK_DIR=WORK_DIR)},
        {"role": "user", "content": f"Tool call: {t_call}"}
    ]
    client = openai.OpenAI(api_key=API_KEY, base_url="https://api.deepinfra.com/v1/openai")
    try:
        resp = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3.2",
            messages=messages,
            response_format={"type": "json_object"}
        )
        handler_resp = json.loads(resp.choices[0].message.content)
        print_event("TOOL_HANDLER", json.dumps(handler_resp))
        
        if handler_resp.get("action") == "execute":
            cmd = handler_resp["safe_cmd"]
            result = subprocess.run(cmd, cwd=WORK_DIR, capture_output=True, text=True)
            return result.stdout + result.stderr
        else:
            return f"Denied: {handler_resp.get('reason', 'Unsafe')}"
    except Exception as e:
        return f"Tool Handler Error: {str(e)}"

def call_llm(messages):
    client = openai.OpenAI(api_key=API_KEY, base_url="https://api.deepinfra.com/v1/openai")
    resp = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-V3.2",
        messages=messages,
        response_format={"type": "json_object"}
    )
    return json.loads(resp.choices[0].message.content)
def parse_tool_call(t_call):
    """
    Parses tool calls supporting generic tags like <path>val</path>, <arg>val</arg>, etc.
    Returns (tool_name, [args_list]) or (None, None) if parsing fails.
    """
    # Regex to find the tool name (first word before any tag)
    match = re.match(r"^\s*(\w+)", t_call)
    
    if not match:
        return None, None
    
    tool_name = match.group(1)
    
    # Extract content inside ANY XML-style tags (e.g., <path>...</path>, <arg>...</arg>)
    # This handles <path>, <content>, <arg>, <url>, <query>, etc.
    arg_matches = re.findall(r"<(\w+)>(.*?)</\1>", t_call, re.DOTALL)
    
    # We only return the content (group 2), ignoring the tag name (group 1)
    args = [match[1].strip() for match in arg_matches]
    
    return tool_name, args

def run_agent():
    os.makedirs(WORK_DIR, exist_ok=True)
    
    # Load or Initialize State
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
    else:
        state = INITIAL_STATE

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    client = openai.OpenAI(api_key=os.getenv("API_KEY", API_KEY), base_url="https://api.deepinfra.com/v1/openai")

    for i in range(50):  # Limit loops
        # Context Management
        current_context_len = sum(len(m['content']) for m in messages)
        if current_context_len > MAX_CHARS:
            print("Context limit reached. Resetting message history (keeping system prompt)...")
            messages = [messages[0]] 

        user_msg = f"Current Internal State: {json.dumps(state)}\nExecute next step."
        messages.append({"role": "user", "content": user_msg})

        print_event("LLM_INPUT", json.dumps(messages))

        try:
            resp = client.chat.completions.create(
                model="deepseek-ai/DeepSeek-V3.2",
                messages=messages,
                response_format={"type": "json_object"}
            )
            response_data = json.loads(resp.choices[0].message.content)
        except Exception as e:
            print(f"LLM Error: {e}")
            break

        print_event("LLM_RESPONSE", json.dumps(response_data))

        messages.append({"role": "assistant", "content": json.dumps(response_data)})
        
        if "memory_update" in response_data:
            state = response_data["memory_update"]
            with open(STATE_FILE, "w") as f:
                json.dump(state, f)

        thought = response_data.get("thought", "")
        t_call = response_data.get("tool_call")

        print(f"Thought: {thought}")

        if t_call and t_call.strip():
            print_event("TOOL_CALL", t_call)
            
            tool_name, args = parse_tool_call(t_call)
            
            cmd = []
            result = ""
            
            if tool_name and args is not None:
                if tool_name in ["read", "mkdir", "web_search", "web_fetch", "shell", "finish", "stop", "exit"]:
                    cmd = ["python3", TOOL_SCRIPT, tool_name] + args
                    
                elif tool_name == "write":
                    if len(args) >= 2:
                        cmd = ["python3", TOOL_SCRIPT, tool_name, args[0], args[1]]
                    else:
                        result = "Error: Write tool requires 2 arguments (path and content)."
                
                else:
                    result = f"Error: Unknown tool '{tool_name}'"
            else:
                result = "Error: Tool call format not recognized. Expected format: tool_name <arg>arg1</arg> ..."

            if cmd:
                try:
                    proc_result = subprocess.run(
                        cmd,
                        cwd=WORK_DIR,
                        capture_output=True,
                        text=True,
                        timeout=45
                    )
                    result = proc_result.stdout + proc_result.stderr
                    
                    if tool_name in ["finish", "stop", "exit"]:
                        print(f"Session ending with signal: {tool_name}")
                        break

                except subprocess.TimeoutExpired:
                    result = "Error: Tool execution timed out."
                except Exception as e:
                    result = f"Execution failed: {type(e).__name__}: {e}"
            
            print_event("TOOL_RESULT", result)
            messages.append({"role": "system", "content": f"Tool result:\n{result}"})

        else:
            print("No tool call. Task may be complete or waiting.")

if __name__ == "__main__":
    run_agent()