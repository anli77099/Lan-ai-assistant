# utils.py

import streamlit as st
from pathlib import Path
import datetime
from langchain_core.messages import HumanMessage, AIMessage
import chardet


def setup_save_folder(folder_name="chat_history"):
    """设置并确保保存文件夹存在"""
    save_folder = Path(folder_name)
    save_folder.mkdir(exist_ok=True)
    return save_folder


def generate_filename(save_folder, extension=".md"):
    """生成基于时间的文件名"""
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = save_folder / f"chat_{timestamp}{extension}"
    return filename


def save_conversation_to_markdown(messages,  filename):
    """将完整对话保存为Markdown格式"""
    try:
        filename.parent.mkdir(exist_ok=True)

        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# 📚 阅读伴侣对话记录\n\n")
            f.write(f"**保存时间:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**对话条数:** {len([m for m in messages if m['role'] == 'user'])} 轮\n\n")
            f.write("---\n\n")

            for i, message in enumerate(messages):
                if message["role"] == "user":
                    f.write(f"## 👤 第{len([m for m in messages[:i + 1] if m['role'] == 'user'])}轮提问\n\n")
                    f.write(f"{message['content']}\n\n")
                elif message["role"] == "assistant":
                    f.write(f"## 🤖 AI回答\n\n")
                    f.write(f"{message['content']}\n\n")
                    f.write("---\n\n")

        return True
    except Exception as e:
        st.error(f"保存文件时出错: {e}")
        return False


def append_to_auto_save(user_input, ai_response, filename):
    """追加单轮对话到文件"""
    try:
        with open(filename, "a", encoding="utf-8") as f:
            f.write(f"## 👤 用户提问\n\n{user_input}\n\n")
            f.write(f"## 🤖 AI回答\n\n{ai_response}\n\n")
            f.write("---\n\n")
        return True
    except Exception as e:
        st.sidebar.error(f"自动保存失败: {e}")
        return False


def setup_session_state():
    """初始化session_state"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "assistant" not in st.session_state:
        st.session_state.assistant = None
    if "uploaded_file_name" not in st.session_state:
        st.session_state.uploaded_file_name = None
    if "chat_history_file" not in st.session_state:
        # 首次启动时直接初始化一个默认文件名
        save_folder = setup_save_folder()
        st.session_state.chat_history_file = generate_filename(save_folder)  # 使用generate_filename生成默认名
    if "save_status" not in st.session_state:
        st.session_state.save_status = "未保存"
    if "last_saved_time" not in st.session_state:
        st.session_state.last_saved_time = None
    if "auto_save" not in st.session_state:
        st.session_state.auto_save = False
    if "current_mode" not in st.session_state:  # 新增：当前模式
        st.session_state.current_mode = "基础模式"
    if "old_conversations" not in st.session_state:  # 新增：旧对话存储
        st.session_state.old_conversations = []


def start_new_conversation():
    """开始新的对话，保存旧对话"""
    if st.session_state.messages:
        # 保存当前对话到旧对话列表
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        old_conv = {
            "id": timestamp,
            "timestamp": timestamp,
            "mode": st.session_state.current_mode,
            "messages": st.session_state.messages.copy(),
            "document": "无",
            "message_count": len(st.session_state.messages),  # 方便显示
            # 新增：最后一条消息预览（最多20字）
            "last_message": st.session_state.messages[-1]["content"][:20] + "..."
            if st.session_state.messages else "无消息"
        }
        st.session_state.old_conversations.append(old_conv)

    # 清空当前对话
    st.session_state.messages = []
    if st.session_state.assistant:
        st.session_state.assistant.clear_history()

    # 重置文件相关状态
    save_folder = setup_save_folder()
    st.session_state.chat_history_file = generate_filename(save_folder)
    st.session_state.uploaded_file_name = None  # 可以保留，但不再使用
    st.session_state.save_status = "未保存"
    st.session_state.last_saved_time = None


def display_old_conversations():
    """显示旧对话侧边栏，增加恢复功能"""
    if st.session_state.old_conversations:
        st.sidebar.header("📁 历史对话")
        for i, conv in enumerate(reversed(st.session_state.old_conversations[-5:])):  # 显示最近5个
            with st.sidebar.expander(
                f"[{conv['timestamp']}] {conv['last_message']}（{conv['message_count']}条）",
                expanded=False
            ):
                st.write(f"文档: {conv['document'] or '无'}")
                # 恢复对话按钮
                if st.button("恢复对话", key=f"restore_{conv['id']}"):
                    # 1. 清空当前对话
                    st.session_state.messages = []
                    if st.session_state.assistant:
                        st.session_state.assistant.clear_history()

                    # 2. 恢复历史消息
                    st.session_state.messages = conv["messages"].copy()

                    # 3. 同步AI助手的对话历史（关键：确保AI知道历史上下文）
                    if st.session_state.assistant:
                        # 清空现有历史
                        st.session_state.assistant.clear_history()
                        # 重新加载历史消息到AI的chat_history中
                        for msg in conv["messages"]:
                            if msg["role"] == "user":
                                st.session_state.assistant.chat_history.append(
                                    HumanMessage(content=msg["content"])
                                )
                            elif msg["role"] == "assistant":
                                st.session_state.assistant.chat_history.append(
                                    AIMessage(content=msg["content"])
                                )

                    # 4. 切换到历史对话的模式
                    st.session_state.current_mode = conv["mode"]
                    st.session_state.assistant.switch_mode(conv["mode"])

                    # 5. 重置保存状态
                    save_folder = setup_save_folder()
                    st.session_state.chat_history_file = generate_filename(save_folder)
                    st.session_state.save_status = "未保存"
                    st.session_state.last_saved_time = None

                    # 6. 刷新页面生效
                    st.rerun()


def init_save_state(uploaded_file, save_folder):
    """初始化保存相关状态"""
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    st.session_state.chat_history_file = save_folder / f"chat_{timestamp}.md"
    st.session_state.last_saved_time = None
    st.session_state.save_status = "未保存"
    st.session_state.auto_save = False


def display_save_sidebar():
    """显示保存相关的侧边栏内容"""
    if st.session_state.assistant:
        st.sidebar.header("💾 对话保存")
        st.sidebar.write(f"**保存状态:** {st.session_state.save_status}")

        if st.session_state.last_saved_time:
            st.sidebar.write(f"**最后保存:** {st.session_state.last_saved_time}")

        # 保存按钮
        if st.sidebar.button("💾 保存完整对话", type="primary", help="将当前所有对话保存为Markdown文件"):
            if st.session_state.chat_history_file is None:
                save_folder = setup_save_folder()
                init_save_state(save_folder)  # 没有文件时直接初始化

            success = save_conversation_to_markdown(
                st.session_state.messages,
                st.session_state.chat_history_file
            )

            if success:
                st.session_state.save_status = "已保存"
                st.session_state.last_saved_time = datetime.datetime.now().strftime('%H:%M:%S')
                st.sidebar.success(f"对话已保存至: {st.session_state.chat_history_file.name}")

                with open(st.session_state.chat_history_file, "rb") as f:
                    st.sidebar.download_button(
                        label="⬇️ 下载Markdown文件",
                        data=f,
                        file_name=st.session_state.chat_history_file.name,
                        mime="text/markdown"
                    )
            else:
                st.sidebar.error("保存失败，请重试")

        # 自动保存选项
        auto_save = st.sidebar.checkbox("🔄 自动保存", value=st.session_state.auto_save,
                                        help="每次收到回复后自动追加到文件")
        st.session_state.auto_save = auto_save