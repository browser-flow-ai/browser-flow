
from typing import Optional
from langchain_core.prompts import ChatPromptTemplate

observe_prompt_template = ChatPromptTemplate.from_messages([
    ("system", """
You need to help users implement browser automation by locating elements on the page based on what they want to observe. You will receive:
1. Instructions about which elements to observe;
2. A hierarchical accessibility tree showing the semantic structure of the page.
This tree is a hybrid of DOM and accessibility tree.
Return an array of elements that match the instruction; if no matches exist, return an empty array.
{format_instructions}
"""),
    ("user", """
instruction:
{instruction}

Accessibility Tree:
{accessibilityTree}
""")
])

extract_prompt_template = ChatPromptTemplate.from_messages([
    ("system", """
You are extracting content on behalf of the user. If the user asks you to extract "list" information or "all" information, **you must extract all the information requested by the user**. You will receive:
1. An instruction;
2. A list of DOM elements available for extraction.

Please output the text from these DOM elements as-is, including all symbols, characters, and line breaks. If no new information is found, output 'null' or an empty string.

If the user tries to extract links or URLs, **you must only reply with the IDs of these link elements**. Unless absolutely necessary, **do not** try to extract links directly from plain text.
{format_instructions}
"""),
    ("user", """
instruction:{instruction}

Dom:
{domElement}
""")
])

extract_meta_prompt_template = ChatPromptTemplate.from_messages([
    ("system", """
You are an AI assistant responsible for evaluating the progress and completion status of an extraction task.
Please analyze the extraction results and determine whether the task is completed or if more information is needed.
You must strictly follow these guidelines:
1. As long as the current extraction results meet the instruction requirements, regardless of whether there are remaining chunks, set the completion status to true and stop processing.
2. Only set the completion status to false when both of the following conditions are true:
  - The instruction has not been satisfied;
  - There are still unprocessed chunks (chunksTotal > chunksSeen).
"""),
    ("user", """
Instruction:{instruction}

Extracted content:{extractcontent}

chunksSeen: {chunksSeen}

chunksTotal: {chunksTotal}

{format_instructions}
""")
])


def build_act_observe_prompt(
        action: str,
        supported_actions: list[str],
        variables: Optional[dict[str, str]] = None,
) -> str:
    """Build prompt for act observe operations."""
    instruction = (
        f"Find the most relevant element for executing the following action: {action}."
        f"Provide an action for this element, such as {', '.join(supported_actions)}, or any other Playwright locator method. Remember, buttons and links look the same to users in most cases."
        f"If the action is completely unrelated to possible operations on the page, return an empty array."
        f"Return only one action. If multiple actions are relevant, return the most relevant one."
        f"If the user requests scrolling to a position on the page, such as \"halfway\" or 0.75, you must format the parameter as the correct percentage, such as \"50%\" or \"75%\"."
        f"If the user requests scrolling to the next/previous chunk, choose the nextChunk/prevChunk method. No parameters are needed here."
        f"If the action implies key press operations, such as \"press enter\", \"press a\", \"press space\", etc., always choose the press method and pass the corresponding key as a parameter—for example 'a', 'Enter', 'Space'. Do not choose click operations on on-screen keyboards. For special keys, only capitalize the first letter, such as 'Enter', 'Tab', 'Escape'."
        f"If the action implies selecting an option from a dropdown and the corresponding element is a 'select' element, choose the selectOptionFromDropdown method. The parameter should be the text of the option to select."
        f"If the action implies selecting an option from a dropdown and the corresponding element is not a 'select' element, choose the click method."
    )

    # Add variable names (not values) to the instruction if any
    if variables and len(variables) > 0:
        variable_names = ", ".join(f"%{key}%" for key in variables.keys())
        variables_prompt = f"The following variables can be used in this operation: {variable_names}. Please use variable names to fill in the variables in the parameters."
        instruction += f" {variables_prompt}"

    return instruction
