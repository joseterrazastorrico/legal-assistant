from typing_extensions import TypedDict
from typing import List

class WritingState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        initial_prompt: initial prompt
        plan: plan
        num_steps: number of steps
        llm_name: name of the LLM
        word_count: word count of the final document
    """
    initial_prompt : str = ""
    plan : str = None
    final_doc : str = None
    write_steps : List[str] = []
    word_count : int = 0
    num_steps : int = 4
    llm_name : str = 'GEMINI'
