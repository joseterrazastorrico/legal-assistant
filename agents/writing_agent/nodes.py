from langchain.schema import Document
import os
from typing import Any, Dict
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser

from agents.llm import model
from agents.writing_agent.utils import write_markdown_file
from agents.writing_agent.prompts import plan_prompt, write_prompt


plan_chain = plan_prompt | model | StrOutputParser()
write_chain = write_prompt | model | StrOutputParser()

def planning_node(state):
    """take the initial prompt and write a plan to make a long doc"""
    print("---PLANNING THE WRITING---")
    initial_prompt = state['initial_prompt']
    num_steps = int(state['num_steps'])
    num_steps += 1

    plan = plan_chain.invoke({"intructions": initial_prompt})
    # print(plan)

    return {"plan": plan, "num_steps":num_steps}


def count_words(text):
        """
        Count the number of words in the given text.
        
        Args:
            text (str): The input text to count words from.
        
        Returns:
            int: The number of words in the text.
        """
        # Split the text into words and count them
        words = text.split()
        return len(words)


def writing_node(state):
    """take the initial prompt and write a plan to make a long doc"""
    print("---WRITING THE DOC---")
    initial_instruction = state['initial_prompt']
    plan = state['plan']
    num_steps = int(state['num_steps'])
    num_steps += 1

    plan = plan.strip().replace('\n\n', '\n')
    planning_steps = plan.split('\n')
    text = ""
    responses = []
    if len(planning_steps) > 50:
        print("plan is too long")
        # print(plan)
        return
    for idx,step in enumerate(planning_steps):
        # Invoke the write_chain
        result = write_chain.invoke({
            "intructions": initial_instruction,
            "plan": plan,
            "text": text,
            "STEP": step
        })
        # result = step
        # print(f"----------------------------{idx}----------------------------")
        # print(step)
        # print("----------------------------\n\n")
        responses.append(result)
        text += result + '\n\n'

    final_doc = '\n\n'.join(responses)

    # Count words in the final document
    word_count = count_words(final_doc)
    print(f"Total word count: {word_count}")

    return {"final_doc": final_doc, "word_count": word_count, "num_steps":num_steps}


def saving_node(state):
    """take the finished long doc and save it to local disk as a .md file   """
    print("---SAVING THE DOC---")
    initial_prompt = state['initial_prompt']
    plan = state['plan']
    final_doc = state['final_doc']
    word_count = state['word_count']
    llm_name = state['llm_name']
    num_steps = int(state['num_steps'])
    num_steps += 1

    final_doc = final_doc + f"\n\nTotal word count: {word_count}"

    # save to local disk
    write_markdown_file(final_doc, f"final_doc_{llm_name}")
    write_markdown_file(plan, f"plan_{llm_name}")

    return { "num_steps":num_steps}