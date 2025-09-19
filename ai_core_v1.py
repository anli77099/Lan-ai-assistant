# ai_core_v1.py

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

# 导入自定义提示词
from prompts import PROMPT_VERSIONS

# 加载环境变量
load_dotenv()

class ReadingCompanionAI:
    def __init__(self, temperature=1.0, prompt_version="基础模式"):
        """初始化 AI 助手"""
        deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        # 只初始化大语言模型
        self.llm = ChatOpenAI(
            api_key=deepseek_api_key,
            model="deepseek-chat",
            base_url="https://api.deepseek.com/v1",
            temperature = temperature
        )

        # 保存当前模式
        self.prompt_version = prompt_version
        # 从 prompts.py 获取选择的提示词
        selected_prompt = PROMPT_VERSIONS.get(prompt_version, PROMPT_VERSIONS["基础模式"])

        # 定义一个更强大的系统Prompt
        self.qa_prompt = ChatPromptTemplate.from_messages([
            ("system", selected_prompt),
            MessagesPlaceholder("chat_history"),
            ("user", "{input}")
        ])

        # 初始化变量
        self.chat_history = []  # 存储对话历史

    def switch_mode(self, new_mode):
        """切换模式"""
        if new_mode in PROMPT_VERSIONS:
            self.prompt_version = new_mode
            selected_prompt = PROMPT_VERSIONS[new_mode]

            # 重新创建提示词模板
            self.qa_prompt = ChatPromptTemplate.from_messages([
                ("system", selected_prompt),
                MessagesPlaceholder("chat_history"),
                ("user", "{input}")
            ])
            return True
        return False

    def clear_history(self):
        """清空对话历史"""
        self.chat_history = []

    def ask(self, question: str) -> str:

        # 组装提示词
        messages = self.qa_prompt.format_messages(
            chat_history=self.chat_history,
            input=question
        )

        # 调用模型
        response = self.llm.invoke(messages)

        # 更新对话历史
        self.chat_history.append(HumanMessage(content=question))
        self.chat_history.append(AIMessage(content=response.content))

        return response.content