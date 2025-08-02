from langgraph.prebuilt.chat_agent_executor import AgentState

class ExecutorState(AgentState):
    user_id: str = None
