from ..services.llm import llm


class EditingAgent:
    name = "editing_agent"

    def edit_document(self, current_content: str, instruction: str, context: str = "") -> str:
        prompt = f"""
You are editing an enterprise proposal.
Keep the existing structure and professional tone.
User instruction: {instruction}
Template/context: {context[:5000]}
Current content:
{current_content[:12000]}

Return revised document content only in simple markdown.
Do not discuss the editing process.
"""
        return llm.ask(prompt)

    def edit_presentation(self, current_content: str, instruction: str, context: str = "") -> str:
        prompt = f"""
You are editing an enterprise presentation.
User instruction: {instruction}
Template/context: {context[:5000]}
Current presentation:
{current_content[:12000]}

Return the full revised deck only.
Use exactly this pattern for each slide:
[SLIDE 1]
Title
- bullet
- bullet

Do not discuss the editing process.
"""
        return llm.ask(prompt)
