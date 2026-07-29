from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
import streamlit as st

from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version
from chat import run_model_tool_loop, trim_history, write_transcript, now_iso, safe_slug

ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
TRANSCRIPTS_DIR = ROOT / "transcripts"
load_lab_env(ROOT)

st.set_page_config(
    page_title="Research Agent UI | Day 04 Lab",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CUSTOM DESIGN SYSTEM CSS (ui-ux-pro-max Data-Dense Dashboard) ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600&family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        padding: 1.25rem 1.75rem;
        border-radius: 12px;
        border: 1px solid #334155;
        margin-bottom: 1.5rem;
        color: #F8FAFC;
    }
    .main-header h2 {
        color: #60A5FA;
        font-weight: 700;
        margin: 0 0 0.25rem 0;
        font-size: 1.5rem;
    }
    .main-header p {
        color: #94A3B8;
        margin: 0;
        font-size: 0.9rem;
    }

    /* Version Badge */
    .version-badge {
        display: inline-block;
        background-color: #1E3A8A;
        color: #93C5FD;
        font-family: 'Fira Code', monospace;
        font-size: 0.8rem;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        border: 1px solid #2563EB;
    }

    /* Tool Event Card */
    .tool-card {
        background: #1E293B;
        border-left: 4px solid #3B82F6;
        padding: 0.75rem 1rem;
        border-radius: 6px;
        margin-bottom: 0.5rem;
        font-family: 'Fira Code', monospace;
        font-size: 0.85rem;
    }
    .tool-name {
        color: #F97316;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.title("⚙️ Agent Settings")
    
    provider_name = st.selectbox(
        "Model Provider",
        options=["deepseek", "gemini", "openrouter", "openai"],
        index=0,
        help="Select LLM provider for live tool calls."
    )
    
    version_label = st.selectbox(
        "Artifact Version",
        options=["v1", "v0", "v2", "v3"],
        index=0,
        help="Choose version label corresponding to prompt & tools artifact."
    )
    
    max_tool_rounds = st.slider("Max Tool Rounds", min_value=1, max_value=8, value=4)
    history_window = st.slider("Context History Window", min_value=1, max_value=10, value=5)
    
    st.divider()
    
    # Load artifact metadata
    system_prompt_path = ARTIFACTS_DIR / "system_prompt.md"
    tools_path = ARTIFACTS_DIR / "tools.yaml"
    
    system_prompt_text = system_prompt_path.read_text(encoding="utf-8") if system_prompt_path.exists() else ""
    artifact_ver = build_artifact_version(version_label, system_prompt_path, tools_path)
    
    st.markdown("### 📌 Active Version Info")
    st.markdown(f"**Version:** `<span class='version-badge'>{artifact_ver.artifact_version}</span>`", unsafe_allow_html=True)
    st.text(f"Prompt Hash: {artifact_ver.prompt_hash[:12]}...")
    st.text(f"Tools Hash:  {artifact_ver.tools_hash[:12]}...")
    
    if st.button("🧹 Clear Chat History"):
        st.session_state.messages = []
        st.session_state.history = []
        st.session_state.turns = []
        st.session_state.transcript_id = None
        st.rerun()

# --- MAIN HEADER ---
st.markdown(
    f"""
    <div class="main-header">
        <h2>🤖 Research Agent Dashboard</h2>
        <p>Evidence-Driven Agent Tool Execution | Active Version: <span class="version-badge">{artifact_ver.artifact_version}</span> | Provider: <b>{provider_name}</b></p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "history" not in st.session_state:
    st.session_state.history = []
if "turns" not in st.session_state:
    st.session_state.turns = []
if "transcript_id" not in st.session_state or st.session_state.transcript_id is None:
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    st.session_state.transcript_id = f"{safe_slug(version_label)}_{safe_slug(provider_name)}_{timestamp}"

transcript_path = TRANSCRIPTS_DIR / f"{st.session_state.transcript_id}.transcript.json"

# Render Existing Chat Messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
        # Render Tool Trace inside Assistant messages if available
        if "rounds" in msg and msg["rounds"]:
            with st.expander("🛠️ View Tool Trace & Execution Details", expanded=False):
                for r in msg["rounds"]:
                    st.caption(f"**Round {r.get('round')}**")
                    for tc in r.get("tool_calls", []):
                        st.markdown(f"🔹 Called tool: `<span class='tool-name'>{tc['name']}</span>`", unsafe_allow_html=True)
                        st.json(tc.get("args", {}))
                    for tr in r.get("tool_results", []):
                        st.caption("Result:")
                        st.json(tr.get("result", {}))

# User Chat Input
user_input = st.chat_input("Nhập yêu cầu nghiên cứu (VD: 'Tweet mới nhất của Sam Altman là gì?')...")

if user_input:
    # Display User message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
        
    # Prepare Agent Execution
    tool_declarations = load_tool_declarations(tools_path)
    openai_tools = to_openai_tools(tool_declarations)
    
    try:
        provider = make_provider(provider_name)
    except Exception as exc:
        st.error(f"Error initializing provider {provider_name}: {exc}")
        st.stop()
        
    messages_payload = [
        {"role": "system", "content": system_prompt_text},
        *trim_history(st.session_state.history, history_window),
        {"role": "user", "content": user_input},
    ]
    
    with st.chat_message("assistant"):
        with st.spinner("Agent đang xử lý & chọn tool..."):
            turn_record = {
                "turn_index": len(st.session_state.turns) + 1,
                "started_at": now_iso(),
                "user": user_input,
                "status": "started",
            }
            
            try:
                loop_result = run_model_tool_loop(
                    provider=provider,
                    messages=messages_payload,
                    tools=openai_tools,
                    model=None,
                    max_tool_rounds=max_tool_rounds,
                )
                
                assistant_text = loop_result.get("assistant_text", "")
                rounds = loop_result.get("rounds", [])
                tool_events = loop_result.get("tool_events", [])
                
                st.markdown(assistant_text)
                
                # Show Tool Trace Accordion
                if rounds and any(r.get("tool_calls") for r in rounds):
                    with st.expander("🛠️ View Tool Trace & Execution Details", expanded=True):
                        for r in rounds:
                            st.caption(f"**Round {r.get('round')}**")
                            for tc in r.get("tool_calls", []):
                                st.markdown(f"🔹 Called tool: `<span class='tool-name'>{tc['name']}</span>`", unsafe_allow_html=True)
                                st.json(tc.get("args", {}))
                            for tr in r.get("tool_results", []):
                                st.caption("Result:")
                                st.json(tr.get("result", {}))

                # Update State
                msg_payload = {
                    "role": "assistant",
                    "content": assistant_text,
                    "rounds": rounds,
                    "tool_events": tool_events,
                }
                st.session_state.messages.append(msg_payload)
                st.session_state.history.append({"role": "user", "content": user_input})
                st.session_state.history.append({"role": "assistant", "content": assistant_text})
                
                turn_record.update({
                    "ended_at": now_iso(),
                    "assistant_text": assistant_text,
                    "status": loop_result.get("status", "answered"),
                    "rounds": rounds,
                    "tool_events": tool_events,
                })
                st.session_state.turns.append(turn_record)
                
                # Save Transcript
                selected_model = getattr(provider, "default_model", provider_name)
                transcript_data = {
                    "transcript_id": st.session_state.transcript_id,
                    **artifact_version_dict(artifact_ver),
                    "provider": provider_name,
                    "model": selected_model,
                    "system_prompt": str(system_prompt_path),
                    "tools": str(tools_path),
                    "created_at": now_iso(),
                    "updated_at": now_iso(),
                    "turns": st.session_state.turns,
                }
                write_transcript(transcript_path, transcript_data)
                
            except Exception as exc:
                st.error(f"❌ Error during agent execution: {exc}")
