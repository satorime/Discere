import json
import re
import os
from google import genai

_client = None

def get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY', ''))
    return _client


def extract_pdf_text(pdf_file):
    """Extract text from an uploaded PDF file object."""
    from pypdf import PdfReader
    reader = PdfReader(pdf_file)
    text = ''
    for page in reader.pages:
        text += page.extract_text() or ''
    return text.strip()


def _parse_json(text):
    """Strip markdown fences and parse JSON."""
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    return json.loads(text.strip())


def generate_flashcards(text, num_cards=10):
    """
    Generate flashcards from text using Gemini.
    Returns list of dicts: [{front, back}, ...]
    """
    prompt = f"""You are an expert tutor. Generate exactly {num_cards} flashcards from the text below.
Return ONLY a valid JSON array — no explanation, no markdown, just raw JSON.
Format:
[
  {{"front": "question or key term", "back": "answer or definition"}},
  ...
]

Text:
{text[:6000]}"""

    response = get_client().models.generate_content(
        model='gemini-2.0-flash',
        contents=prompt
    )
    return _parse_json(response.text)


def generate_quiz(flashcards_data, num_questions=5):
    """
    Generate multiple-choice quiz questions from flashcard data.
    flashcards_data: list of {front, back} dicts
    Returns list of question dicts.
    """
    cards_text = '\n'.join(
        [f"Q: {c['front']}\nA: {c['back']}" for c in flashcards_data[:30]]
    )
    prompt = f"""You are an expert quiz maker. Generate exactly {num_questions} multiple-choice questions based on these flashcards.
Return ONLY a valid JSON array — no explanation, no markdown, just raw JSON.
Format:
[
  {{
    "question": "question text",
    "option_a": "...",
    "option_b": "...",
    "option_c": "...",
    "option_d": "...",
    "correct_answer": "A",
    "explanation": "brief explanation why this answer is correct"
  }},
  ...
]

Flashcards:
{cards_text}"""

    response = get_client().models.generate_content(
        model='gemini-2.0-flash',
        contents=prompt
    )
    return _parse_json(response.text)
