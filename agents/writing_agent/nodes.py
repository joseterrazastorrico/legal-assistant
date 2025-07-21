from langchain_core.output_parsers import StrOutputParser

from agents.llm import model
from agents.writing_agent.utils import write_markdown_file, count_words
from agents.writing_agent.prompts import plan_prompt, write_prompt
from logger.logger import get_logger
logger = get_logger("writing_agent")

plan_chain = plan_prompt | model | StrOutputParser()
write_chain = write_prompt | model | StrOutputParser()

def planning_node(state):
    """take the initial prompt and write a plan to make a long doc"""
    logger.info("---PLANNING THE WRITING---")
    initial_prompt = state['initial_prompt']
    num_steps = int(state['num_steps'])
    num_steps += 1
    logger.info(f"Planning writing with initial prompt: {initial_prompt}")
    plan = plan_chain.invoke({"instructions": initial_prompt})
    logger.info("Generated plan")
    return {"plan": plan, "num_steps":num_steps}


def writing_node(state):
    """take the initial prompt and write a plan to make a long doc"""
    logger.info("---WRITING THE DOC---")
    initial_instruction = state['initial_prompt']
    plan = state['plan']
    num_steps = int(state['num_steps'])
    num_steps += 1

    plan = plan.strip().replace('\n\n', '\n')
    planning_steps = plan.split('\n')
    text = ""
    responses = []

    logger.info(f'planning_steps: {planning_steps}')
    if len(planning_steps) > 50:
        logger.warning("plan is too long")
        return
    for idx,step in enumerate(planning_steps):
        result = write_chain.invoke({
            "instructions": initial_instruction,
            "plan": plan,
            "text": text,
            "STEP": step
        })
        responses.append(result)
        text += result + '\n\n'

    final_doc = '\n\n'.join(responses)
    word_count = count_words(final_doc)
    logger.info(f"Total word count: {word_count}")

    return {"final_doc": final_doc, "word_count": word_count, "num_steps":num_steps}


def saving_node(state):
    """take the finished long doc and save it to local disk as a .md file   """
    logger.info("---SAVING THE DOC---")
    plan = state['plan']
    final_doc = state['final_doc']
    word_count = state['word_count']
    llm_name = state.get('llm_name', 'GEMINI')
    num_steps = int(state['num_steps'])
    num_steps += 1

    final_doc = final_doc + f"\n\nTotal word count: {word_count}"

    # save to local disk
    write_markdown_file(final_doc, f"final_doc_{llm_name}")
    write_markdown_file(plan, f"plan_{llm_name}")

    return { "num_steps":num_steps}