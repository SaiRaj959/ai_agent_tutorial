from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from flask import Flask, request, jsonify
from flask_cors import CORS

from pydantic import BaseModel, Field
from typing import List, Optional, Dict


# NEW: Filterable prompt structure
class FilterablePrompt(BaseModel):
    prompt: str = Field(
        description="Fully resolved question with specific values inserted"
    )
    sudoPrompt: str = Field(
        description="Template question with <placeholder> syntax for filterable values"
    )
    filters: Dict[str, List[str]] = Field(
        description="Dictionary of filter keys and their possible options. 'calendar' key always contains [start_date, end_date] in YYYY-MM-DD format"
    )

# NEW: Enhanced SuggestedQuestion with filterable support
class SuggestedQuestion(BaseModel):
    id: Optional[str] = None
    question: str = Field(
        description="The base question text (same as FilterablePrompt.prompt)"
    )
    metrics: Optional[List[str]] = None
    priority: Optional[int] = None
    filterable: Optional[FilterablePrompt] = Field(
        default=None,
        description="Optional filterable prompt configuration with sudoPrompt and filters"
    )

class DashboardPlan(BaseModel):
    is_business_question: bool = Field(
        description="True if the prompt is a valid business or data-related question, False otherwise."
    )
    suggested_questions: List[SuggestedQuestion] = Field(
        description="A list of structured analytical questions with metadata to populate a dashboard."
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

# response = orchestrator_chain.invoke({"user_input": user_input})

# if response.clarification_needed:
#     print(f"Clarification needed: {response.clarification_needed, response.clarification_options}")
# elif response.is_business_question:
#     print(f"Plan created: {response.suggested_questions}")
# else:
#     print(f"Invalid prompt: {response.reasoning}")

app = Flask(__name__)
CORS(app, resources={r"/decode": {"origins": "*"}})

# response = llm.invoke(user_input)
# print(response)
@app.route('/decode', methods=['POST'])
def decode_prompt():
    user_prompt = request.json.get('prompt')
    response = orchestrator_chain.invoke({"user_input": user_prompt})
    
    # Custom response formatting
    result = {}
    if hasattr(response, 'suggested_questions') and response.suggested_questions:
        # Extract filterable prompt objects for the frontend
        prompts = []
        for q in response.suggested_questions:
            if hasattr(q, 'filterable') and q.filterable:
                # Use the filterable object which has prompt, sudoPrompt, and filters
                prompts.append({
                    'question': q.filterable.prompt,
                    'sudoPrompt': q.filterable.sudoPrompt,
                    'filters': q.filterable.filters
                })
            else:
                # Fallback: if no filterable, just use the question string
                prompts.append({
                    'question': q.question if hasattr(q, 'question') else str(q),
                    'sudoPrompt': None,
                    'filters': {}
                })
        result['prompts'] = prompts
    if hasattr(response, 'clarification_needed') and response.clarification_needed:
        result['clarification_needed'] = {
            'title': response.clarification_needed,
            'options': response.clarification_options or []
        }
    # Add other mappings as needed
    
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)