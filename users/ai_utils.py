import json
import re
import os
from groq import Groq

_client = None

def get_client():
    global _client
    if _client is None:
        _client = Groq(api_key=os.environ.get('GROQ_API_KEY', ''))
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
    Generate flashcards from text using Groq (llama-3.3-70b).
    Returns list of dicts: [{front, back}, ...]
    """
    response = get_client().chat.completions.create(
        model='llama-3.3-70b-versatile',
        messages=[
            {
                'role': 'system',
                'content': (
                    'You are an expert tutor. When given text, you generate flashcards. '
                    'You ALWAYS respond with ONLY a valid JSON array — no explanation, '
                    'no markdown code fences, no extra text. Just raw JSON.'
                )
            },
            {
                'role': 'user',
                'content': (
                    f'Generate exactly {num_cards} flashcards from the text below.\n'
                    'Format:\n'
                    '[{"front": "question or key term", "back": "answer or definition"}, ...]\n\n'
                    f'Text:\n{text[:6000]}'
                )
            }
        ],
        temperature=0.4,
        max_tokens=4096,
    )
    return _parse_json(response.choices[0].message.content)


def generate_quiz(flashcards_data, num_questions=5):
    """
    Generate multiple-choice quiz questions from flashcard data.
    flashcards_data: list of {front, back} dicts
    Returns list of question dicts.
    """
    cards_text = '\n'.join(
        [f"Q: {c['front']}\nA: {c['back']}" for c in flashcards_data[:30]]
    )
    response = get_client().chat.completions.create(
        model='llama-3.3-70b-versatile',
        messages=[
            {
                'role': 'system',
                'content': (
                    'You are an expert quiz maker. You ALWAYS respond with ONLY a valid JSON array — '
                    'no explanation, no markdown code fences, no extra text. Just raw JSON.'
                )
            },
            {
                'role': 'user',
                'content': (
                    f'Generate exactly {num_questions} multiple-choice questions from these flashcards.\n'
                    'Format:\n'
                    '[{"question":"...","option_a":"...","option_b":"...","option_c":"...","option_d":"...",'
                    '"correct_answer":"A","explanation":"brief explanation"}, ...]\n\n'
                    f'Flashcards:\n{cards_text}'
                )
            }
        ],
        temperature=0.4,
        max_tokens=4096,
    )
    return _parse_json(response.choices[0].message.content)
