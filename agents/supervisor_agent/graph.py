#AGENTS
from agents.legal_knowledge_agent.graph import retriever_agent
from agents.writing_agent.graph import workflow as writing_agent

#SUPERVISOR
from langgraph_supervisor import create_supervisor
from agents.llm import model
from agents.execution_supervisor_agent.promts import supervisor_prompt
from agents.execution_supervisor_agent.state import ExecutorState


workflow = create_supervisor(
    agents=[retriever_agent, writing_agent],
    tools=[],
    model=model,
    prompt=supervisor_prompt,
    output_mode="full_history", #last_message
    state_schema=ExecutorState,
)
