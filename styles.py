"""Styling for the digital twin Gradio app.

Gradio's theme engine handles bubbles, buttons and inputs — targeting those with
custom CSS means guessing at internal class names that change between versions.
CSS here is limited to what a theme can't express: page background, the title
rule, and hiding the footer.
"""

import gradio as gr

YELLOW = "#ffd400"

EXAMPLES = [
    "What's your background?",
    "What are you building right now?",
    "What are you strongest at?",
    "How do I reach you?",
]

# A single-hue yellow ramp. Gradio derives dozens of variables from this.
yellow = gr.themes.Color(
    c50="#fffbeb",
    c100="#fff4c2",
    c200="#ffea85",
    c300="#ffe04d",
    c400="#ffd400",
    c500="#e6bf00",
    c600="#c9a600",
    c700="#a38700",
    c800="#7a6500",
    c900="#524400",
    c950="#3a2c00",
)

THEME = gr.themes.Soft(
    primary_hue=yellow,
    neutral_hue="zinc",
    radius_size=gr.themes.sizes.radius_sm,
    font=[gr.themes.GoogleFont("Inter"), "system-ui", "sans-serif"],
)

CSS = """
footer, .built-with, .show-api, .api-docs { display: none !important; }

.gradio-container {
  max-width: 820px !important;
  margin: 0 auto !important;
  padding: 40px 24px 48px !important;
}

.gradio-container h1 {
  font-size: 28px !important;
  font-weight: 600 !important;
  letter-spacing: -0.02em !important;
  margin: 0 0 10px !important;
  text-align: left !important;
}
.gradio-container h1::after {
  content: "";
  display: block;
  height: 3px;
  width: 38px;
  background: #ffd400;
  margin-top: 12px;
}
"""

JS = """
() => {
  document.title = 'Digital Twin';

  const focusInput = () => {
    const areas = document.querySelectorAll('textarea');
    if (areas.length) areas[areas.length - 1].focus();
  };
  setTimeout(focusInput, 300);

  const watchTextarea = (area) => {
    if (area.dataset.twinWatched) return;
    area.dataset.twinWatched = '1';
    let wasDisabled = area.disabled || area.readOnly;
    new MutationObserver(() => {
      const isDisabled = area.disabled || area.readOnly;
      if (wasDisabled && !isDisabled) area.focus();
      wasDisabled = isDisabled;
    }).observe(area, { attributes: true, attributeFilter: ['disabled', 'readonly'] });
  };

  const scan = () => document.querySelectorAll('textarea').forEach(watchTextarea);
  setTimeout(scan, 500);
  new MutationObserver(scan).observe(document.body, { childList: true, subtree: true });
}
"""