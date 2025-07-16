#AGENTS
from agents.action_agent.graph import action_agent

#SUPERVISOR
from langgraph_supervisor import create_supervisor
from agents.llm import model
from agents.execution_supervisor_agent.promts import supervisor_prompt
from agents.execution_supervisor_agent.state import ExecutorState


workflow = create_supervisor(
    agents=[action_agent],
    tools=[],
    model=model,
    prompt=supervisor_prompt,
    output_mode="full_history", #last_message
    state_schema=ExecutorState,
)
