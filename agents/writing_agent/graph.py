from langchain.schema import Document
from langgraph.graph import StateGraph, END
from typing_extensions import TypedDict
from typing import List

from agents.writing_agent.state import WritingState
from nodes.planning_node import planning_node
from nodes.writing_node import writing_node
from nodes.saving_node import saving_node


def create_workflow(llm):
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

    return workflow.compile()