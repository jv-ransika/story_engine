import streamlit as st
import sqlite3
import json
from datetime import datetime
from langgraph.checkpoint.sqlite import SqliteSaver
from agents.start_agent import start_agent_app
from agents.env_agent import env_agent_workflow
from utils.get_env import get_env_variable
from pydantic_bp.core import Character, Entity, Scene, Moment
import pandas as pd
import time
import warnings

# Suppress Streamlit warnings
warnings.filterwarnings("ignore", message=".*missing ScriptRunContext.*")
st.set_option('client.showErrorDetails', False)


st.set_page_config(
    page_title="⬥ STORY_ENGINE v1.0 TERMINAL",
    page_icon="⬥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Terminal Theme CSS - Blue Edition
st.markdown("""
<style>
    * {
        font-family: 'Courier New', monospace;
    }
    
    body {
        background-color: #0a0f1a;
        color: #4a9eff;
    }
    
    .stApp {
        background-color: #0a0f1a;
    }
    
    .terminal-header {
        border: 2px solid #4a9eff;
        padding: 1rem;
        background: rgba(74, 158, 255, 0.05);
        border-radius: 5px;
        margin-bottom: 1.5rem;
    }
    
    .terminal-header h1 {
        color: #4a9eff;
        margin: 0;
        font-size: 2rem;
    }
    
    .terminal-subheader {
        color: #2d7acc;
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }
    
    .stat-box {
        border: 2px solid #2d7acc;
        padding: 1rem;
        background-color: rgba(74, 158, 255, 0.03);
        border-radius: 3px;
        margin: 0.5rem 0;
    }
    
    .stat-label {
        color: #2d7acc;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .stat-value {
        color: #4a9eff;
        font-size: 1.5rem;
        font-weight: bold;
        margin-top: 0.3rem;
    }
    
    .log-entry {
        border-left: 3px solid #4a9eff;
        padding: 0.5rem 0 0.5rem 1rem;
        margin: 0.3rem 0;
        background-color: rgba(74, 158, 255, 0.02);
        color: #4a9eff;
    }
    
    .log-time {
        color: #2d7acc;
        font-size: 0.8rem;
    }
    
    .status-active {
        color: #4a9eff;
    }
    
    .status-warning {
        color: #ffaa00;
    }
    
    .section-divider {
        border-top: 2px dashed #2d7acc;
        margin: 1.5rem 0;
    }
    
    .input-section {
        border: 1px solid #2d7acc;
        padding: 1rem;
        background-color: rgba(74, 158, 255, 0.03);
        border-radius: 3px;
        margin-bottom: 1rem;
    }
    
    .button-primary {
        background-color: #4a9eff;
        color: #0a0f1a;
        border: 2px solid #4a9eff;
    }
    
    .data-table {
        color: #4a9eff;
        border-collapse: collapse;
    }
    
    .data-table th {
        border-bottom: 2px solid #4a9eff;
        padding: 0.5rem;
        text-align: left;
        color: #4a9eff;
    }
    
    .data-table td {
        border-bottom: 1px solid #2d7acc;
        padding: 0.5rem;
    }
    
    .warning-box {
        border: 2px solid #ffaa00;
        padding: 1rem;
        background-color: rgba(255, 170, 0, 0.05);
        border-radius: 3px;
        color: #ffaa00;
    }
    
    .success-box {
        border: 2px solid #4a9eff;
        padding: 1rem;
        background-color: rgba(74, 158, 255, 0.05);
        border-radius: 3px;
        color: #4a9eff;
    }
    
    .error-box {
        border: 2px solid #ff6b6b;
        padding: 1rem;
        background-color: rgba(255, 107, 107, 0.05);
        border-radius: 3px;
        color: #ff6b6b;
    }
    
    .tabs {
        border-bottom: 2px solid #4a9eff;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        border: 1px solid #2d7acc;
        padding: 0.5rem 1rem;
        background-color: rgba(74, 158, 255, 0.05);
    }
    
    .stTabs [aria-selected="true"] {
        border: 2px solid #4a9eff;
        background-color: rgba(74, 158, 255, 0.1);
        color: #4a9eff;
    }
    
    .progress-bar {
        background: linear-gradient(90deg, #4a9eff, #2d7acc);
        height: 2px;
        border-radius: 1px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
@st.cache_resource
def get_compiled_app():
    """Compile the workflow with checkpointer"""
    memory_ctx = SqliteSaver.from_conn_string("env_agent_checkpoint.db")
    memory = memory_ctx.__enter__()
    app = env_agent_workflow.compile(checkpointer=memory)
    return app, memory, memory_ctx

app, memory, memory_ctx = get_compiled_app()

if 'current_story_state' not in st.session_state:
    st.session_state.current_story_state = None
if 'generated_output' not in st.session_state:
    st.session_state.generated_output = None
if 'thread_id' not in st.session_state:
    st.session_state.thread_id = get_env_variable("THREAD_ID")
if 'active_thread' not in st.session_state:
    st.session_state.active_thread = None
if 'system_logs' not in st.session_state:
    st.session_state.system_logs = []


def log_system(message: str, level: str = "INFO"):
    """Add entry to system logs"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.system_logs.append({
        "time": timestamp,
        "level": level,
        "message": message
    })
    if len(st.session_state.system_logs) > 50:
        st.session_state.system_logs = st.session_state.system_logs[-50:]


def get_thread_ids_from_db():
    """Get all thread IDs from database"""
    try:
        conn = sqlite3.connect("env_agent_checkpoint.db", check_same_thread=False)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT thread_id FROM checkpoints ORDER BY thread_id DESC")
        threads = cursor.fetchall()
        conn.close()
        return [dict(t)['thread_id'] for t in threads] if threads else []
    except Exception as e:
        log_system(f"ERROR: {str(e)}", "ERROR")
        return []


def get_checkpoint_details(thread_id):
    """Get checkpoint details"""
    try:
        conn = sqlite3.connect("env_agent_checkpoint.db", check_same_thread=False)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, ts_created FROM checkpoints 
            WHERE thread_id = ? 
            ORDER BY ts_created DESC
        """, (thread_id,))
        checkpoints = cursor.fetchall()
        result = [{"id": cp[0], "ts_created": cp[1]} for cp in checkpoints]
        conn.close()
        return result
    except Exception as e:
        log_system(f"ERROR: {str(e)}", "ERROR")
        return []


def check_story_exists(thread_id) -> bool:
    """Check if story exists"""
    config = {"configurable": {"thread_id": thread_id}}
    try:
        app.get_state(config)
        return True
    except Exception:
        return False


def run_start_agent(input_text: str):
    initial_state = {
        "input_text": input_text,
        "characters": [],
        "entities": [],
        "start_scene_description": "",
        "main_goal": ""
    }
    output_state = start_agent_app.invoke(initial_state)
    initial_state["characters"] = output_state["characters"]
    initial_state["entities"] = output_state["entities"]
    initial_state["start_scene_description"] = output_state["start_scene_description"]
    initial_state["main_goal"] = output_state["main_goal"]
    return initial_state


def run_env_agent(state, thread_id, resume: bool):
    config = {
        "recursion_limit": 50,
        "configurable": {"thread_id": thread_id}
    }
    if resume and check_story_exists(thread_id):
        output_state = app.invoke(None, config=config)
        return output_state
    output_state = app.invoke(state, config=config)
    return output_state


def format_story_detailed(state):
    """Format story output"""
    md = ""
    
    if "main_goal" in state:
        goal_status = "ACHIEVED ✓" if state.get("is_main_goal_achieved", False) else "IN_PROGRESS →"
        md += f"```\n[STORY_MAIN_GOAL] {goal_status}\n```\n"
        md += f"`{state['main_goal']}`\n\n"
    
    if "characters" in state and state["characters"]:
        md += "```\n[CHARACTERS_REGISTRY]\n```\n"
        for i, char in enumerate(state["characters"], 1):
            md += f"**[{i}] {char.name}** | Role: {char.role}\n"
            md += f"  ├─ Personality: `{', '.join(char.personality)}`\n"
            md += f"  ├─ Strengths: `{', '.join(char.strengths)}`\n"
            md += f"  ├─ Weaknesses: `{', '.join(char.weaknesses)}`\n"
            md += f"  └─ Memory: `{char.memory_factor}`\n\n"
    
    if "entities" in state and state["entities"]:
        md += "```\n[ENTITIES_DATABASE]\n```\n"
        for entity in state["entities"]:
            md += f"**{entity.name}**: `{entity.description}`\n"
        md += "\n"
    
    if "scenes" in state and state["scenes"]:
        md += f"```\n[STORY_SCENES] Total: {len(state['scenes'])}\n```\n"
        for scene in state["scenes"]:
            md += f"**SCENE_{scene.no}** | `{scene.description}`\n"
            
            if scene.moments:
                md += f"  └─ MOMENTS: {len(scene.moments)}\n"
                for moment in scene.moments:
                    md += f"     [MOMENT_{moment.no}]\n"
                    for situation in moment.situations:
                        md += f"     ├─ **{situation.who_said}**: \"{situation.dialogue}\"\n"
                        if situation.action:
                            md += f"     │  └─ ACTION: `{situation.action}`\n"
            md += "\n"
    
    return md


# Header
st.markdown("""
<div class="terminal-header">
    <h1>⬥ STORY_ENGINE v1.0 TERMINAL</h1>
    <div class="terminal-subheader">
        >>> ADVANCED_AI_NARRATIVE_GENERATION_SYSTEM | RUNTIME: ACTIVE | STATUS: ONLINE
    </div>
</div>
""", unsafe_allow_html=True)

# System Stats
col1, col2, col3, col4, col5 = st.columns(5)

thread_ids = get_thread_ids_from_db()
conn = sqlite3.connect("env_agent_checkpoint.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM checkpoints")
checkpoint_count = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(DISTINCT thread_id) FROM checkpoints")
distinct_threads = cursor.fetchone()[0]
conn.close()

with col1:
    st.markdown("""
    <div class="stat-box">
        <div class="stat-label">📊 Active_Stories</div>
        <div class="stat-value">""" + str(len(thread_ids)) + """</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="stat-box">
        <div class="stat-label">💾 Checkpoints</div>
        <div class="stat-value">""" + str(checkpoint_count) + """</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="stat-box">
        <div class="stat-label">🔄 Threads</div>
        <div class="stat-value">""" + str(distinct_threads) + """</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="stat-box">
        <div class="stat-label">⚙️ Status</div>
        <div class="stat-value status-active">ACTIVE</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown("""
    <div class="stat-box">
        <div class="stat-label">🕐 Timestamp</div>
        <div class="stat-value">""" + datetime.now().strftime("%H:%M:%S") + """</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

# Main Interface
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🚀 GENERATOR", 
    "📚 ARCHIVE", 
    "🔧 INSPECTOR",
    "📊 ANALYTICS",
    "📋 LOGS"
])

# ==================== TAB 1: GENERATOR ====================
with tab1:
    st.markdown("### > NARRATIVE_GENERATION_INTERFACE")
    
    col_input, col_settings = st.columns([2, 1])
    
    with col_input:
        st.markdown('<div class="input-section">', unsafe_allow_html=True)
        st.markdown("**[PROMPT_INPUT]**")
        prompt = st.text_area(
            "Enter narrative seed:",
            height=120,
            value="In a distant future, humanity has colonized Mars. Amidst political turmoil and environmental challenges, a group of explorers embarks on a mission to uncover ancient Martian artifacts that could hold the key to humanity's survival.",
            label_visibility="collapsed"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_settings:
        st.markdown("**[CONFIG]**")
        custom_thread = st.checkbox("custom_thread_id")
        if custom_thread:
            thread_id = st.text_input("thread_id:", value="story_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
        else:
            thread_id = get_env_variable("THREAD_ID")
        
        st.markdown(f"""
        ```
        active_thread: {thread_id}
        status: ready
        ```
        """)
    
    if st.button(">>> EXECUTE_GENERATION", type="primary", use_container_width=True):
        log_system(f"GENERATOR_INIT for thread: {thread_id}", "INFO")
        
        progress_container = st.container()
        
        with progress_container:
            st.markdown('<div class="log-entry"><span class="log-time">[01:00]</span> Analyzing narrative seed...</div>', unsafe_allow_html=True)
            time.sleep(0.5)
            
        try:
            log_system("PHASE_1: START_AGENT_INVOKE", "INFO")
            output = run_start_agent(prompt)
            
            with progress_container:
                st.markdown('<div class="log-entry"><span class="log-time">[01:15]</span> Characters & entities initialized</div>', unsafe_allow_html=True)
            
            log_system("PHASE_2: ENV_AGENT_SETUP", "INFO")
            story_state = {
                "main_goal": output["main_goal"],
                "is_main_goal_achieved": False,
                "characters": output["characters"],
                "entities": output["entities"],
                "scenes": [],
                "next_character_index": 0,
                "next_scene_no": 1,
                "next_scene": output["start_scene_description"],
                "is_scene_complete": False,
                "current_scene": None,
                "next_moment_no": 1,
                "current_moment": None
            }
            
            with progress_container:
                st.markdown('<div class="log-entry"><span class="log-time">[01:45]</span> Generating narrative sequences...</div>', unsafe_allow_html=True)
            
            log_system("PHASE_3: STORY_GENERATION", "INFO")
            result = run_env_agent(story_state, thread_id, resume=False)
            
            st.session_state.generated_output = result
            st.session_state.current_story_state = result
            st.session_state.active_thread = thread_id
            
            log_system("GENERATION_COMPLETE", "SUCCESS")
            
            with progress_container:
                st.markdown('<div class="success-box">>>> GENERATION_SUCCESS | Story stored in checkpoint</div>', unsafe_allow_html=True)
            
        except Exception as e:
            log_system(f"GENERATION_FAILED: {str(e)}", "ERROR")
            st.markdown(f'<div class="error-box">>>> ERROR: {str(e)}</div>', unsafe_allow_html=True)
    
    if st.session_state.generated_output:
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        st.markdown("### > GENERATED_NARRATIVE")
        st.markdown(format_story_detailed(st.session_state.generated_output))


# ==================== TAB 2: ARCHIVE ====================
with tab2:
    st.markdown("### > STORY_ARCHIVE_DATABASE")
    
    if not thread_ids:
        st.markdown('<div class="warning-box">>>> NO_STORIES_FOUND | Create one using GENERATOR</div>', unsafe_allow_html=True)
    else:
        selected_thread = st.selectbox("select_story:", thread_ids, label_visibility="collapsed")
        
        col_actions, col_info = st.columns([1, 1])
        
        with col_actions:
            st.markdown("**[ACTIONS]**")
            if st.button(">>> LOAD_STORY", use_container_width=True):
                try:
                    log_system(f"LOADING: {selected_thread}", "INFO")
                    config = {"configurable": {"thread_id": selected_thread}}
                    state_obj = app.get_state(config)
                    
                    if hasattr(state_obj, 'values'):
                        st.session_state.current_story_state = state_obj.values
                    else:
                        st.session_state.current_story_state = state_obj
                    
                    st.session_state.active_thread = selected_thread
                    log_system(f"LOADED: {selected_thread}", "SUCCESS")
                    st.success("✓ Story loaded")
                except Exception as e:
                    log_system(f"LOAD_FAILED: {str(e)}", "ERROR")
                    st.error(f"Error: {str(e)}")
            
            if st.button(">>> RESUME_STORY", use_container_width=True):
                try:
                    log_system(f"RESUMING: {selected_thread}", "INFO")
                    result = run_env_agent(None, selected_thread, resume=True)
                    st.session_state.current_story_state = result
                    st.session_state.generated_output = result
                    st.session_state.active_thread = selected_thread
                    log_system(f"RESUMED: {selected_thread}", "SUCCESS")
                    st.success("✓ Story resumed")
                except Exception as e:
                    log_system(f"RESUME_FAILED: {str(e)}", "ERROR")
                    st.error(f"Error: {str(e)}")
        
        with col_info:
            st.markdown("**[STORY_INFO]**")
            checkpoints = get_checkpoint_details(selected_thread)
            st.markdown(f"""
            ```
            thread: {selected_thread}
            checkpoints: {len(checkpoints)}
            status: archived
            ```
            """)
        
        with st.expander("📋 Checkpoint_History"):
            if checkpoints:
                cp_data = []
                for cp in checkpoints:
                    cp_data.append({
                        "ID": cp['id'][:12] + "...",
                        "Timestamp": cp['ts_created']
                    })
                st.dataframe(pd.DataFrame(cp_data), use_container_width=True, hide_index=True)
        
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        
        if st.session_state.current_story_state:
            st.markdown("### > STORY_CONTENT")
            st.markdown(format_story_detailed(st.session_state.current_story_state))


# ==================== TAB 3: INSPECTOR ====================
with tab3:
    st.markdown("### > DATABASE_INSPECTOR")
    
    col_threads, col_db = st.columns([1, 1])
    
    with col_threads:
        st.markdown("**[THREADS_REGISTRY]**")
        if thread_ids:
            threads_df = pd.DataFrame({
                "Thread_ID": thread_ids,
                "Status": ["✓" for _ in thread_ids]
            })
            st.dataframe(threads_df, use_container_width=True, hide_index=True)
        else:
            st.info("No threads available")
    
    with col_db:
        st.markdown("**[DATABASE_STATS]**")
        conn = sqlite3.connect("env_agent_checkpoint.db", check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM checkpoints")
        total_cp = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT thread_id) FROM checkpoints")
        total_th = cursor.fetchone()[0]
        conn.close()
        
        st.markdown(f"""
        ```
        total_checkpoints: {total_cp}
        total_threads: {total_th}
        db_file: env_agent_checkpoint.db
        ```
        """)
    
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    
    st.markdown("**[SQL_CONSOLE]**")
    query = st.text_area(
        "query:",
        value="SELECT thread_id, COUNT(*) as checkpoints FROM checkpoints GROUP BY thread_id;",
        height=80,
        label_visibility="collapsed"
    )
    
    if st.button(">>> EXECUTE_QUERY", use_container_width=True):
        try:
            log_system("QUERY_EXECUTE", "INFO")
            conn = sqlite3.connect("env_agent_checkpoint.db", check_same_thread=False)
            df = pd.read_sql_query(query, conn)
            conn.close()
            st.dataframe(df, use_container_width=True, hide_index=True)
            log_system("QUERY_SUCCESS", "SUCCESS")
        except Exception as e:
            log_system(f"QUERY_FAILED: {str(e)}", "ERROR")
            st.markdown(f'<div class="error-box">>>> ERROR: {str(e)}</div>', unsafe_allow_html=True)


# ==================== TAB 4: ANALYTICS ====================
with tab4:
    st.markdown("### > NARRATIVE_ANALYTICS")
    
    conn = sqlite3.connect("env_agent_checkpoint.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT thread_id, COUNT(*) as checkpoints 
        FROM checkpoints 
        GROUP BY thread_id 
        ORDER BY checkpoints DESC
    """)
    story_stats = cursor.fetchall()
    conn.close()
    
    if story_stats:
        stats_df = pd.DataFrame(story_stats, columns=["Thread_ID", "Checkpoints"])
        
        st.markdown("**[STATISTICS_TABLE]**")
        st.dataframe(stats_df, use_container_width=True, hide_index=True)
        
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.markdown("**[CHECKPOINTS_PER_STORY]**")
            chart_data = pd.DataFrame({
                "Story": [s[0] for s in story_stats],
                "Checkpoints": [s[1] for s in story_stats]
            })
            st.bar_chart(chart_data.set_index("Story"), use_container_width=True)
        
        with col_chart2:
            st.markdown("**[STORY_DISTRIBUTION]**")
            chart_data2 = pd.DataFrame({
                "Story": [s[0] for s in story_stats],
                "Count": [s[1] for s in story_stats]
            })
            st.bar_chart(chart_data2.set_index("Story"), use_container_width=True)
    else:
        st.info("No analytics data available")


# ==================== TAB 5: SYSTEM LOGS ====================
with tab5:
    st.markdown("### > SYSTEM_LOG_STREAM")
    
    if st.button(">>> CLEAR_LOGS"):
        st.session_state.system_logs = []
        st.success("Logs cleared")
    
    log_display = st.container()
    
    with log_display:
        if st.session_state.system_logs:
            for log in st.session_state.system_logs[-30:]:
                if log['level'] == 'ERROR':
                    color = '#ff0000'
                elif log['level'] == 'SUCCESS':
                    color = '#00ff00'
                elif log['level'] == 'WARNING':
                    color = '#ffaa00'
                else:
                    color = '#00ff00'
                
                st.markdown(f"""
                <div class="log-entry">
                    <span class="log-time">[{log['time']}]</span>
                    <span style="color: {color}">{log['level']}</span>: {log['message']}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No logs yet")

# Footer
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
st.markdown("""
<div style="text-align: center; color: #00aa00; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px;">
>>> STORY_ENGINE v2.0 TERMINAL | ADVANCED_NARRATIVE_GENERATION | STATUS: OPERATIONAL <<<
</div>
""", unsafe_allow_html=True)
