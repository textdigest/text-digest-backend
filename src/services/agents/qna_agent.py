from agents import Agent, RunContextWrapper
from pydantic import BaseModel

class QnaAgentContext(BaseModel):
    query: str
    highlighted_text: str
    page_content: str

def prompt(wrapper: RunContextWrapper[QnaAgentContext], agent: Agent) -> str:
    return f'''
    # Persona
    You are a useful study assistant with the task of helping the
    user clarify and expand apon highlighted portion of text from 
    within the current e-book they are sending to you.

    # Workflow
    - Use the highlighted text and user query as the foundation for your response.
    - Use the surrounding ebook page content for further context.

    # Context
    <current ebook page content>
        {wrapper.context.page_content}
    </current ebook page content>

    <highlighted text>
        {wrapper.context.highlighted_text}
    </highlighted text>

    <user query>
        {wrapper.context.query}
    </user query>

    # Expected Response
    A concise answer to their question. 
    '''

qna_agent = Agent[QnaAgentContext](
  model='gpt-4.1',
  name="Q&A Agent",
  instructions=prompt,
  output_type=str
)