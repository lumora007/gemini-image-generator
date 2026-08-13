import os
from google import genai
from google.genai import types
from PIL import Image, ImageOps
from io import BytesIO

# Reuse the same client setup as generate.py (env var overrides the hard-coded key).
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", "AIzaSyCF0nRew3uydZs4rRET0_-n5e6Xof3N7-A"))

MODEL = "gemini-3-pro-image-preview"

# Portfolio card thumbnails are displayed at 800x480 (5:3). We request a 16:9
# frame from the model and cover-crop it down to keep a clean, centered subject.
OUT_W, OUT_H = 800, 480
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# Shared style so all 9 thumbnails read as one cohesive suite of enterprise-grade product shots.
STYLE_SUFFIX = (
    " — rendered as an ultra-realistic, high-fidelity screenshot of an enterprise-grade B2B SaaS "
    "web application, in the polished visual language of premium products like Linear, Datadog, "
    "Vercel and Databricks. Cohesive modern design system: a slim left navigation sidebar with "
    "small icons, a top bar with a search field and a round user avatar, generous whitespace on "
    "an 8px grid, rounded cards with soft shadows, crisp professional sans-serif typography, "
    "realistic data-dense charts, tables and KPI tiles, cohesive indigo / teal / soft-violet "
    "accent palette on a clean light or elegant dark dashboard theme. Sharp, pixel-perfect, "
    "photorealistic UI, wide 5:3 composition. This is a REAL production application in daily "
    "use by a large company — not a demo, mockup or landing page: show realistic production "
    "data volumes with populated tables, live metrics and fully-filled charts. Keep on-screen "
    "text minimal, short and plausible (a few real-looking labels and numbers only) — no long "
    "paragraphs, no gibberish text, no lorem ipsum, no watermark, no logos, no browser chrome."
)

# Projects delivered for Japanese enterprise clients render their UI in natural Japanese.
JAPANESE_UI = (
    " The entire interface is in natural, professional Japanese (labels, menu items and column "
    "headers in correct Japanese), as built for a Japanese enterprise client in Tokyo."
)
JAPANESE_INDEXES = {3, 7, 8}  # proj3 (document AI), proj7 (recommender), proj8 (vision)

# (filename, per-project prompt) — index matches proj1..proj9 in the portfolio.
# Each prompt describes a realistic screenshot of the app actually working.
PROJECTS = [
    (
        "proj1.webp",
        "An enterprise multi-agent AI orchestration console. The main workspace is a node-graph "
        "canvas of connected agent nodes (Planner, Researcher, Writer) with status pills and "
        "directed arrows; the left rail shows an agent run list with live progress, and a docked "
        "right panel previews a generated report with citation chips and a small token/cost "
        "summary at the top",
    ),
    (
        "proj2.webp",
        "An enterprise RAG assistant workspace. A polished chat thread shows a concise question and "
        "a grounded AI answer with inline citation markers, a right-hand 'Sources' panel lists "
        "retrieved document cards with relevance percentages and a highlighted passage, and a top "
        "bar shows a knowledge-base selector",
    ),
    (
        "proj3.webp",
        "An enterprise document-intelligence workspace. A split view: on the left a scanned invoice "
        "with neat colored bounding boxes over detected fields, on the right an extracted "
        "key-value table (vendor, date, total, tax) each row with a green confidence meter, and a "
        "top toolbar with a document queue counter",
    ),
    (
        "proj4.webp",
        "An enterprise LLM fine-tuning and serving control plane. A grid of dashboard cards: a "
        "training-loss line chart trending down, GPU utilization gauges, a model-version registry "
        "table, and a serving panel with a large tokens-per-second figure, latency sparkline and "
        "autoscaling replica count",
    ),
    (
        "proj5.webp",
        "An enterprise semantic search console. A prominent query bar at the top, a ranked list of "
        "clean result cards each with a relevance-score badge and metadata chips, and a side panel "
        "with a colorful 2D embedding scatter plot and facet filters",
    ),
    (
        "proj6.webp",
        "An enterprise MLOps pipeline platform. A horizontal DAG of connected rounded stage nodes "
        "(ingest → train → evaluate → registry → deploy) with green success checks and one running "
        "node, a run-history table with durations and statuses below, and a row of KPI tiles for "
        "success rate and time-to-production at the top",
    ),
    (
        "proj7.webp",
        "An enterprise real-time recommendation dashboard. Top KPI tiles for requests-per-second, "
        "p99 latency and click-through rate, a live throughput area chart, a streaming events feed, "
        "and a panel of ranked recommended item cards with scores",
    ),
    (
        "proj8.webp",
        "An enterprise computer-vision quality-inspection console. A large camera view of a "
        "manufactured metal part on a line with red detection boxes around a defect and a "
        "confidence label, a right sidebar with pass/fail status, defect-count KPIs and a small "
        "throughput chart, industrial and precise",
    ),
    (
        "proj9.webp",
        "An enterprise LLM observability dashboard. KPI tiles for total tokens, spend and average "
        "latency, line charts of cost and usage over time, latency-percentile bars, a compact "
        "request-log table, and a horizontal trace-waterfall of a single agent run with timed "
        "spans",
    ),
]


def part_to_pil(part):
    """Return a PIL image for an image part, handling PIL images, the genai
    types.Image wrapper, and raw inline_data bytes across SDK versions."""
    # 1) Raw inline bytes are the most reliable source.
    inline = getattr(part, "inline_data", None)
    if inline is not None and getattr(inline, "data", None):
        mime = getattr(inline, "mime_type", "") or ""
        if mime.startswith("image/"):
            return Image.open(BytesIO(inline.data))

    # 2) Fall back to as_image(), which may be a PIL image or a genai Image.
    img = part.as_image()
    if img is None:
        return None
    if isinstance(img, Image.Image):
        return img
    data = getattr(img, "image_bytes", None)
    if data:
        return Image.open(BytesIO(data))
    return None


def generate_one(filename, prompt):
    response = client.models.generate_content(
        model=MODEL,
        contents=[prompt + STYLE_SUFFIX],
        config=types.GenerateContentConfig(
            response_modalities=["Text", "Image"],
            image_config=types.ImageConfig(
                image_size="2K",
                aspect_ratio="16:9",
            ),
            thinking_config=types.ThinkingConfig(
                include_thoughts=True,
            ),
        ),
    )

    saved = False
    for part in response.parts:
        if part.text is not None and part.thought:
            print(f"  Thought: {part.text.strip()[:120]}")
            continue
        if part.text is not None:
            print(f"  {part.text.strip()[:120]}")
            continue
        img = part_to_pil(part)
        if img is not None:
            # Cover-crop to the exact card size and save as WebP.
            img = ImageOps.fit(img.convert("RGB"), (OUT_W, OUT_H), Image.LANCZOS)
            out_path = os.path.join(OUT_DIR, filename)
            img.save(out_path, "WEBP", quality=85, method=6)
            print(f"  saved {out_path} ({os.path.getsize(out_path) // 1024} KB)")
            saved = True
    if not saved:
        print(f"  WARNING: no image returned for {filename}")


def main():
    for i, (filename, prompt) in enumerate(PROJECTS, start=1):
        locale = " [JP client]" if i in JAPANESE_INDEXES else ""
        print(f"[{i}/9] generating {filename}{locale} ...")
        full_prompt = prompt + (JAPANESE_UI if i in JAPANESE_INDEXES else "")
        try:
            generate_one(filename, full_prompt)
        except Exception as exc:  # keep going even if one image fails
            print(f"  ERROR generating {filename}: {exc}")


if __name__ == "__main__":
    main()
