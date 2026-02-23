from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
# from promptReader import app

from pydantic import BaseModel, Field
from typing import List

class DashboardPlan(BaseModel):
    is_business_question: bool = Field(
        description="True if the prompt is a valid business or data-related question, False otherwise."
    )
    suggested_questions: List[str] = Field(
        description="A list of specific analytical questions to be answered to populate a dashboard."
    )
    clarification_needed: str = Field(
        description="Clarification needed to answer the prompt."
    )
    clarification_options: List[str] = Field(
        description="A list of clarifications needed to answer the prompt."
    )
    reasoning: str = Field(
        description="Brief explanation of why this is or isn't a valid business prompt."
    )


load_dotenv()

# llm = ChatOpenAI(model="gpt-4o-mini")
llm = ChatAnthropic(model="claude-sonnet-4-5-20250929")
structured_llm = llm.with_structured_output(DashboardPlan)
# user_input = "How is my business doing this month?"
# user_input = "I want to see how our marketing spend is performing."
# user_input = "What is the CPM for Paid Search channel?"

# user_input = "I'm running out of stock on some products, show me what's at risk"
user_input = "Are my best customers coming back?"

system_message = (
    "You are the Dashboard Orchestrator. Your goal is to convert business prompts "
    "into structured dashboard requirements. \n\n"
    "Requirements:\n"
    "1. Validate: Determine if the prompt is a legitimate business question (e.g., 'How are sales?').\n"
    "2. Decompose: If valid, generate a series of atomic, data-driven questions "
    "needed to fill a dashboard (e.g., 'What is the daily revenue trend?', 'Who are the top 5 customers?').\n"
    "3. Format: Always respond in the predefined JSON schema."
)
business_logic_content = open("dashboardBusinessLogic.txt", "r").read().replace("{", "{{").replace("}", "}}")
prompt_template = ChatPromptTemplate.from_messages([
    # ("system", system_message),
    ("system", business_logic_content),
    ("human", "{user_input}")
])

# Create the chain
orchestrator_chain = prompt_template | structured_llm

response = orchestrator_chain.invoke({"user_input": user_input})


if response.clarification_needed:
    print(f"Clarification needed: {response.clarification_needed, response.clarification_options}")
elif response.is_business_question:
    print(f"Plan created: {response.suggested_questions}")
else:
    print(f"Invalid prompt: {response.reasoning}")


# response = llm.invoke(user_input)
# print(response)

# if __name__ == '__main__':
#     app.run(debug=True)