from blindspot.personas.models import Persona, PersonaTask
from blindspot.execution.agent import build_agent_step_prompt
from blindspot.ai.providers.antigravity import AntigravityProvider
from blindspot.execution.models import AgentAction, ActionExecutionRecord, AgentAction as AA, ActionType
import re

persona = Persona(
    id="p1",
    name="Priya - High-Intent E-Commerce Shopper",
    description="E-commerce shopper",
    likely_difficulties=["Login walls"],
    experience_level="Intermediate",
    accessibility_needs="Standard desktop browsing",
    goals=["Search product", "Add to cart"],
    tasks=[
        PersonaTask(
            id="t1",
            objective='Locate the primary search input on the homepage and submit a query for "Apple iPhone 16".',
            starting_conditions="Homepage open",
            success_criteria=["Search results page displayed"],
            evidence_to_collect=["Search input value", "search results header"]
        )
    ]
)

h_records = [
    ActionExecutionRecord(step=1, page_url="https://www.flipkart.com", page_title="Flipkart", action=AA(action=ActionType.FILL, target="@e3", value="Apple iPhone 16", reasoning="test fill"), success=True),
    ActionExecutionRecord(step=2, page_url="https://www.flipkart.com/search?q=Apple%20iPhone%2016", page_title="Search", action=AA(action=ActionType.SCROLL, reasoning="test scroll"), success=True),
]

prompt2 = build_agent_step_prompt(
    persona=persona,
    task=persona.tasks[0],
    page_url="https://www.flipkart.com/search?q=Apple%20iPhone%2016",
    page_title="Apple iPhone 16",
    elements=[{"ref": "@e1", "tag": "a", "element_type": "link", "text": "Apple iPhone 16 (128 GB)", "href": "/apple-iphone-16/p/itm123"}],
    history=h_records
)

provider = AntigravityProvider()
action2 = provider._synthesize_agent_action(prompt2, AgentAction)
print("Action 2 (after scroll):", action2.action.value, action2.target, action2.reasoning)
