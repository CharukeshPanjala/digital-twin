# Digital Twin

https://digital-twin-kmre.onrender.com/

An AI assistant that answers questions about me. It runs on my site, talks to
visitors about my background and work, captures contact details from people who
want to get in touch, and logs every question it couldn't answer.

Built with Gradio and the OpenAI API. No agent framework.

## How it works

**Hand-built agent loop.** No LangChain, no orchestration library. The loop that
handles tool calls is about ten lines in `app.py`: send the messages, check
whether the model asked for a tool, run it, append the result, send again. I
wrote it this way to understand what a framework does before reaching for one.

**Two tools.** `record_user_details` captures a visitor's email when they want
to be contacted. `record_unknown_question` logs anything the twin couldn't
answer, which turns into a list of gaps in how I describe myself. Both write to
a local file and send a push notification.

**A second model reviews every reply.** Before a response reaches the visitor,
a separate call to a cheaper model judges whether the twin behaved correctly:
answered in scope, didn't invent a credential, didn't claim to have recorded an
email nobody gave. Failed replies are swapped for a fallback and logged. The
evaluator fails open, so if that call errors the visitor still gets their
answer.

## Things I got wrong first

The tool schema marks `email` as required. The model called the tool without one
anyway and the app crashed. A JSON schema is a hint to the model, not a
contract, and nothing validates arguments before they hit your function. Every
tool now has defaults, validation, and a try/except around the dispatch.

The first evaluator asked "is this reply about Charukesh?" and rejected
greetings, thank-yous, and the twin correctly refusing an off-topic question.
Refusing well is correct behaviour, but a judge only knows that if you tell it.
The prompt now lists what acceptable looks like instead of asking a vague
question.

The evaluator also needs the visitor's message, not just the reply. "Got it,
I'll pass that on" looks like it came from nowhere when you judge it alone.

## Running it

```bash
pip install -r requirements.txt
```

Create a `.env`:

```
OPENAI_API_KEY=your-key
PUSHOVER_USER=your-user-key
PUSHOVER_TOKEN=your-app-token
```

Pushover is optional. Without it, notifications are skipped and everything still
writes to `leads.jsonl`.

Add `linkedin.pdf` (LinkedIn profile export) and `summary.txt` (a first-person
description of yourself) to the project root. Both get read into the system
prompt at startup.

```bash
python app.py
```

## Files

| File | What it does |
|---|---|
| `app.py` | Gradio interface, chat handler, agent loop |
| `context.py` | Builds the system prompt from the PDF and summary |
| `tools.py` | Tool definitions, dispatch, and error handling |
| `evaluator.py` | The reply reviewer |
| `styles.py` | Theme and CSS |

## Built by

Charukesh Panjala. Software engineer in Berlin, six years across fintech, fraud
detection at Amazon, and now AI.

[LinkedIn](https://www.linkedin.com/in/charukeshpanjala)
