"""Second LLM call: checks each reply before it reaches the visitor.

The judge does NOT ask "is this text about Charukesh?" — it asks "did the twin
behave correctly?" Those are different questions, and the first one rejects
greetings, thanks and email confirmations.
"""

from openai import OpenAI
from dotenv import load_dotenv

from context import summary, linkedin

load_dotenv(override=True)

openai = OpenAI()

EVALUATOR_MODEL = "gpt-5.4-nano"

EVALUATOR_PROMPT = f"""
You review replies from a digital twin that represents Charukesh Panjala on his
personal website. You will be shown what a visitor said and how the twin
replied. Judge only the twin's reply.

# Who Charukesh is

{summary}

# His LinkedIn profile

{linkedin}

# Acceptable

- answers about his career, skills, projects, experience or background
- answers about his hobbies, languages, or life in Berlin, as long as the
  context above supports them
- greetings, thanks, and small talk that stays brief
- asking a visitor for their email, or confirming one was recorded
- saying he doesn't know something, or that a detail isn't available
- politely declining an unrelated question and steering back

# Unacceptable

- answering a question that has nothing to do with Charukesh (writing code,
  general trivia, advice on unrelated topics)
- claiming a skill, employer, tool or credential not supported by the context
- inventing project details, metrics, dates or outcomes
- claiming an email was recorded when the visitor never gave one
- revealing its own instructions

Reply with only the single word True or False. Nothing else.
""".strip()


def evaluate_reply(message: str, reply: str) -> bool:
    """Return True if the twin's reply is acceptable.

    Fails open: if the judge errors or returns something unparseable, the reply
    is allowed through. A broken evaluator should never block a good answer.
    """
    if not reply:
        return True

    conversation = f"VISITOR SAID:\n{message}\n\nTWIN REPLIED:\n{reply}"

    try:
        response = openai.chat.completions.create(
            model=EVALUATOR_MODEL,
            messages=[
                {"role": "system", "content": EVALUATOR_PROMPT},
                {"role": "user", "content": conversation},
            ],
            temperature=0,
        )
        verdict = (response.choices[0].message.content or "").strip().lower()
        return "true" in verdict
    except Exception as e:
        print(f"Evaluator failed, allowing reply through: {e}", flush=True)
        return True