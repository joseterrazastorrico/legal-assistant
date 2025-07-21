from langgraph.graph import StateGraph, END

from agents.writing_agent.state import WritingState
from agents.writing_agent.nodes import planning_node
from agents.writing_agent.nodes import writing_node
from agents.writing_agent.nodes import saving_node
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()


workflow = StateGraph(WritingState)

# Add nodes
workflow.add_node("planning_node", planning_node)
workflow.add_node("writing_node", writing_node)
workflow.add_node("saving_node", saving_node)

# Set entry point
workflow.set_entry_point("planning_node")

# Add edges
workflow.add_edge("planning_node", "writing_node")
workflow.add_edge("writing_node", "saving_node")
workflow.add_edge("saving_node", END)

workflow = workflow.compile(checkpointer=checkpointer)
