from langchain_core.messages import HumanMessage
from llm import get_llm

llm = get_llm()
response = llm.invoke([HumanMessage(content="Say hello in one sentence.")])
print(response.content)
