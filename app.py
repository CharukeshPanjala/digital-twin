import os

import gradio as gr
from dotenv import load_dotenv
from openai import OpenAI

from context import TWIN_SYSTEM_PROMPT
from evaluator import evaluate_reply
from styles import CSS, JS, EXAMPLES, THEME
from tools import tools, handle_tool_calls

load_dotenv(override=True)

MODEL_NAME = "gpt-5.4-mini"
MAX_INPUT_CHARS = 1000

openai = OpenAI()

system = [{"role": "system", "content": TWIN_SYSTEM_PROMPT}]

FALLBACK_OFF_TOPIC = (
    "Let me stay on topic — ask me about Charukesh's work, projects or background."
)
FALLBACK_ERROR = "Something went wrong on my end — try again in a moment."


def chat(message, history):
    # Public URL: cap input length so nobody can paste a novel and bill it to me.
    if len(message) > MAX_INPUT_CHARS:
        return "That's a bit long for a chat box — can you shorten the question?"

    try:
        messages = system + history + [{"role": "user", "content": message}]
        response = openai.chat.completions.create(
            model=MODEL_NAME, messages=messages, tools=tools
        )

        while response.choices[0].finish_reason == "tool_calls":
            assistant_message = response.choices[0].message
            results = handle_tool_calls(assistant_message.tool_calls)
            messages.append(assistant_message)
            messages.extend(results)
            response = openai.chat.completions.create(
                model=MODEL_NAME, messages=messages, tools=tools
            )

        reply = response.choices[0].message.content

        if not evaluate_reply(message, reply):
            print(f"[rejected] {reply}", flush=True)
            return FALLBACK_OFF_TOPIC

        return reply

    except Exception as e:
        # Outermost boundary of a user-facing handler: never show a visitor a
        # traceback. The real error goes to the logs.
        print(f"[error] {type(e).__name__}: {e}", flush=True)
        return FALLBACK_ERROR


if __name__ == "__main__":
    gr.ChatInterface(
        chat,
        examples=EXAMPLES,
        title="Digital Twin",
        description="Talk to my AI twin about my career",
        chatbot=gr.Chatbot(show_label=False)
    ).launch(
        css=CSS,
        js=JS,
        theme=THEME,
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", 7860)),
    )