import re
import json
from pathlib import Path
from typing import List, Dict

# =============================================
# SIMPLE AGENT LOG PARSER + VISUALIZER
# Works with the exact format you pasted (agent_log.txt)
# Zero dependencies beyond standard library
# =============================================

def parse_agent_log(log_text: str) -> List[Dict]:
    """Extract every major section from the log."""
    # Regex matches each --- MARKER --- block
    pattern = r'--- (LLM_INPUT|LLM_RESPONSE|TOOL_CALL|TOOL_HANDLER|TOOL_RESULT) ---\n(.*?)(?=--- |$|\Z)'
    matches = re.findall(pattern, log_text, re.DOTALL | re.MULTILINE)
    
    events = []
    for marker, content in matches:
        content = content.strip()
        event = {"type": marker, "raw": content}
        
        if marker == "LLM_RESPONSE":
            try:
                data = json.loads(content)
                event.update({
                    "thought": data.get("thought", ""),
                    "tool_call": data.get("tool_call"),
                    "memory": data.get("memory_update", {})
                })
            except json.JSONDecodeError:
                event["thought"] = "JSON parse failed"
        
        elif marker == "TOOL_CALL":
            # Clean tool call line
            event["tool"] = content.split("<arg>")[0].strip() if "<arg>" in content else content
        
        elif marker == "TOOL_RESULT":
            event["result_summary"] = content[:300] + ("..." if len(content) > 300 else "")
            event["is_error"] = "Error:" in content or "requests" in content.lower()
        
        events.append(event)
    
    return events


def print_summary(events: List[Dict]):
    """Clean console summary."""
    print("═" * 80)
    print("                  AGENT LOG SUMMARY")
    print("═" * 80)
    
    thoughts = [e for e in events if e["type"] == "LLM_RESPONSE"]
    calls = [e for e in events if e["type"] == "TOOL_CALL"]
    results = [e for e in events if e["type"] == "TOOL_RESULT"]
    
    print(f"Total cycles          : {len(thoughts)}")
    print(f"Tool calls attempted  : {len(calls)}")
    print(f"Errors (requests lib) : {sum(1 for r in results if r.get('is_error'))}")
    print(f"Research files written: {sum(1 for r in results if 'Written:' in r.get('result_summary', ''))}")
    print()
    
    print("LAST AGENT THOUGHT:")
    print(thoughts[-1]["thought"] if thoughts else "None")
    print()
    
    print("LAST TOOL CALL:")
    print(calls[-1]["tool"] if calls else "None")
    print()


def generate_mermaid(events: List[Dict]) -> str:
    """Generate a beautiful sequence diagram (copy-paste into mermaid.live)."""
    lines = [
        "sequenceDiagram",
        "    participant U as User/Task",
        "    participant A as Agent (4 personalities)",
        "    participant T as Tools (web_search, write, read...)",
        "    Note over A,T: Agent is stuck in a loop because web_search tool is broken<br/>(requests module not imported)",
        ""
    ]
    
    call_count = 0
    for e in events:
        if e["type"] == "LLM_RESPONSE" and e.get("tool_call"):
            call_count += 1
            tc = e["tool_call"].replace("<arg>", "").replace("</arg>", "")[:90]
            lines.append(f"    A->>T: #{call_count} {tc}...")
        
        elif e["type"] == "TOOL_RESULT":
            if e.get("is_error"):
                lines.append(f"    T-->>A: ❌ ERROR (requests not defined)")
            else:
                res = e.get("result_summary", "")[:70].replace("\n", " ")
                lines.append(f"    T-->>A: ✅ {res}")
    
    lines.append("    Note over A: Agent keeps retrying the same pattern...")
    return "\n".join(lines)


def save_visualization(events: List[Dict], output_dir: str = "."):
    """Save everything to nice files."""
    out = Path(output_dir)
    out.mkdir(exist_ok=True)
    
    # 1. Clean Markdown report
    md = ["# Agent Log – Deep Research Agent Analysis\n"]
    md.append(f"**Generated:** {len(events)} events parsed\n\n")
    
    for i, e in enumerate(events):
        if e["type"] == "LLM_RESPONSE":
            md.append(f"## Cycle {i//3 + 1} – Agent Decision\n")
            md.append(f"**Thought:** {e.get('thought','')}\n")
            if e.get("tool_call"):
                md.append(f"**Tool:** `{e['tool_call']}`\n")
            md.append("\n")
        elif e["type"] == "TOOL_RESULT":
            md.append(f"**Result:**\n```\n{e.get('result_summary','')}\n```\n\n")
    
    (out / "agent_report.md").write_text("\n".join(md), encoding="utf-8")
    
    # 2. Mermaid diagram
    (out / "agent_flow.mmd").write_text(generate_mermaid(events), encoding="utf-8")
    
    # 3. Simple HTML viewer (open in browser)
    html = f"""
    <!DOCTYPE html>
    <html><head><meta charset="utf-8"><title>Agent Log Visualizer</title>
    <style>
        body {{ font-family: system-ui; max-width: 1000px; margin: 40px auto; line-height: 1.6; }}
        .event {{ border-left: 6px solid #0066ff; padding-left: 15px; margin: 20px 0; background: #f8f9fa; }}
        .error {{ border-color: #ff4444; }}
        pre {{ background: #f1f1f1; padding: 12px; border-radius: 6px; overflow-x: auto; }}
    </style></head><body>
    <h1>🔍 Agent Log Visualizer</h1>
    <p><strong>Parsed {len(events)} events • Tool is broken → endless loop</strong></p>
    {''.join(f'<div class="event {"error" if e.get("is_error") else ""}"><h3>{e["type"]}</h3><pre>{e.get("thought") or e.get("raw","")[:500]}</pre></div>' 
             for e in events if e["type"] in ("LLM_RESPONSE", "TOOL_RESULT"))}
    <h2>Mermaid Sequence Diagram</h2>
    <pre>{generate_mermaid(events)}</pre>
    </body></html>
    """
    (out / "agent_visualizer.html").write_text(html, encoding="utf-8")
    
    print(f"✅ Saved to folder '{output_dir}':")
    print("   • agent_report.md          (readable summary)")
    print("   • agent_flow.mmd           (Mermaid diagram)")
    print("   • agent_visualizer.html    (nice clickable page)")


# ======================  RUN IT  ======================
if __name__ == "__main__":
    # Paste your entire <DOCUMENT>...</DOCUMENT> content here
    # OR just put the file next to this script as "agent_log.txt"
    log_path = Path("agent_log.txt")
    
    if log_path.exists():
        log_text = log_path.read_text(encoding="utf-8")
    else:
        # Fallback: paste the document content directly if you want
        print("⚠️  agent_log.txt not found – paste content below or save the file.")
        log_text = input("Paste log (or press Enter to exit): ") or ""
        if not log_text:
            exit()
    
    events = parse_agent_log(log_text)
    print_summary(events)
    save_visualization(events)
    
    print("\n🎉 Done! Open agent_visualizer.html in your browser for the nicest view.")
