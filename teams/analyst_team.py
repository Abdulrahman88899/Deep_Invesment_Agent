from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import ToolMessage


# create a factor function that each analyst has its own role
# This function is a factory that creates a LangGraph node for a specific type of analyst.
def create_analyst_node(llm, toolkit, system_message, tools, output_field):
    """
    Creates a node for an analyst agent.
    Args:
        llm: The language model instance to be used by the agent.
        toolkit: The collection of tools available to the agent.
        system_message: The specific instructions defining the agent's role and goals.
        tools: A list of specific tools from the toolkit that this agent is allowed to use.
        output_field: The key in the AgentState where this agent's final report will be stored.
    """
    # Define the prompt template for the analyst agent.
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are a helpful AI assistant, collaborating with other assistants."
         " Use the provided tools to progress towards answering the question."
         " If you are unable to fully answer, that's OK; another assistant with different tools"
         " will help where you left off. Execute what you can to make progress."
         " You have access to the following tools: {tool_names}.\n{system_message}"
         " For your reference, the current date is {current_date}. The company we want to look at is {ticker}"),
        # MessagesPlaceholder allows us to pass in the conversation history.
        MessagesPlaceholder(variable_name="messages"),
    ])
    # Partially fill the prompt with the specific system message and tool names for this analyst.
    prompt = prompt.partial(system_message=system_message)
    prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
    # Bind the specified tools to the LLM. This tells the LLM which functions it can call.
    chain = prompt | llm.bind_tools(tools)
    # This is the actual function that will be executed as a node in the graph.
    def analyst_node(state):
        # Call the LLM chain, not the bare prompt
        result = chain.invoke({
        "messages": state["messages"],
        "current_date": state["trade_date"],
        "ticker": state["company_of_interest"],
    })

        report = ""
        # Safely check for tool calls on the LLM response
        if not getattr(result, "tool_calls", None):
            report = result.content
        # Return the LLM's response and the final report to update the state.
        return {"messages": [result], output_field: report}
    return analyst_node
