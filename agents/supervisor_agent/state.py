from langgraph.prebuilt.chat_agent_executor import AgentState

class ExecutorState(AgentState):
    text_source: str = None
