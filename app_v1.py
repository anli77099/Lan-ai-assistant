# app_v1.py

import streamlit as st
from ai_core_v1 import ReadingCompanionAI
import datetime
from utils import (
    setup_save_folder, append_to_auto_save,
    setup_session_state, init_save_state, display_save_sidebar,
    start_new_conversation, display_old_conversations
)
from prompts import PROMPT_VERSIONS

# --- 初始化设置 ---
SAVE_FOLDER = setup_save_folder("chat_history")
setup_session_state()

# --- 页面基础设置 ---
st.set_page_config(page_title="Lan", page_icon="🌼", layout="wide")
st.title("你好，我是Lan")
st.write("——我一直在这里。")

# --- 核心逻辑 ---
@st.cache_resource
def get_ai_assistant(temperature = 1.0, prompt_version="基础模式"):
    """初始化并返回一个 AI 助手实例"""
    # 创建 AI 助手实例
    assistant = ReadingCompanionAI(temperature=temperature, prompt_version=prompt_version)
    return assistant


# --- 侧边栏设置 ---
with st.sidebar:
    st.header("⚙️ 设置")

    # 1. 模式选择
    current_mode = st.selectbox(
        "选择模式",
        options=list(PROMPT_VERSIONS.keys()),
        index=list(PROMPT_VERSIONS.keys()).index(st.session_state.current_mode)
    )

    # 如果模式改变，更新助手
    if current_mode != st.session_state.current_mode:
        st.session_state.current_mode = current_mode
        if st.session_state.assistant:
            st.session_state.assistant.switch_mode(current_mode)
            st.rerun()

    # 2. 温度设置
    temperature = st.slider(
        "创造性设置",
        min_value=0.0,
        max_value=1.5,
        value=1.0,
        step=0.1,
        help="较低值=更严肃，较高值=更活跃"
    )

    # 3. 新建对话按钮
    if st.button("🆕 开始新对话", type="primary"):
        start_new_conversation()
        st.rerun()

    st.divider()

    # 4. 显示保存相关功能
    display_save_sidebar()

    # 5. 显示历史对话
    display_old_conversations()


# --- 初始化 AI 助手 ---
if st.session_state.assistant is None:
    st.session_state.assistant = get_ai_assistant(
        temperature=temperature,
        prompt_version=st.session_state.current_mode
    )

# --- 显示当前模式 ---
st.sidebar.success(f"当前模式: **{st.session_state.current_mode}**")

# --- 界面交互 ---

# 显示聊天历史
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 用户输入框
if prompt := st.chat_input("言って。"):
    # 将用户输入添加到历史记录并显示
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 获取 AI 回答
    with st.chat_message("assistant"):
        with st.spinner("收到！让我想想……"):
            response = st.session_state.assistant.ask(prompt)
            st.markdown(response)

    # 将 AI 回答添加到历史记录
    st.session_state.messages.append({"role": "assistant", "content": response})

    # 自动保存逻辑
    if st.session_state.get('auto_save', False):
        success = append_to_auto_save(prompt, response, st.session_state.chat_history_file)
        if success:
            st.session_state.save_status = "已开启自动保存"
            st.session_state.last_saved_time = datetime.datetime.now().strftime('%H:%M:%S')