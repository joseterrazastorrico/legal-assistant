from langgraph.prebuilt import create_react_agent
from agents.legal_knowledge_agent.tools import retrieve_data
from agents.legal_knowledge_agent.prompts import rag_agent_prompt
from documents.utils import extract_collection_definitions
from config.settings import constants

from agents.llm import model
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()

collection_definitions = extract_collection_definitions(collections=constants.RAG_COLLECTIONS)

retriever_agent = create_react_agent(
    model=model,
    tools=[retrieve_data],
    name="legal_knowledge_agent",
    prompt=rag_agent_prompt.format(
        collections_definitions=collection_definitions
        ),
    checkpointer=checkpointer,
)