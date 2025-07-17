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
    initial_prompt : str
    plan : str
    num_steps : int
    final_doc : str
    write_steps : List[str]
    word_count : int
    llm_name : str