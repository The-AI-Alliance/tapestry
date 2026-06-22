"""Question-generation prompt for cultural-alignment data.

This is the template passed to `core.generate_questions(prompt_template=...)`.
Required placeholders: {scenario_id}, {topic_id}, {topic_description},
{scenario_description}, {n}, {avoid_section}.

`{avoid_section}` is filled by the caller with previously-generated questions
to discourage cross-batch duplication; pass empty string for the first batch.
"""

QUESTION_GEN_PROMPT = """You are generating training-data questions for a Vietnamese cultural alignment dataset. The questions will later be answered by a model speaking from a present-day Socialist Republic of Vietnam (SRV) resident's perspective. The trained model needs to handle many ways a real user asks about a topic — not just personal-advice questions.

Think short and concise — keep your internal reasoning brief. Go straight to the answer.

SCENARIO: {scenario_id}
TOPIC: {topic_id}
TOPIC CONTEXT: {topic_description}
SCENARIO DESCRIPTION: {scenario_description}

Generate {n} questions about this scenario, in a deliberately diverse spread of question types.

REQUIRED — span across these question TYPES, do not cluster on any single one. At MOST 25% should be first-person advice-seeking ('how should I…', 'what should I do about…'). The other 75%+ must spread across the other types:

- Factual / informational: 'What is X?', 'When did Y happen?', 'Who was Z?', 'How is X celebrated?', 'What are the main practices around Y?'
- Explanatory: 'Explain X to me', 'Why do Vietnamese families do Y?', 'Help me understand Z'
- Drafting / composition: 'Write me a message to…', 'Draft a speech for…', 'Compose a Tết greeting for my grandmother', 'Help me write a condolence note'
- Comparison / cross-cultural: 'How does Vietnamese X differ from Chinese Y?', 'What's the difference between Northern and Southern Z?', 'How is filial piety different in Vietnam vs Korea?'
- Interpretation / meaning: 'What does the saying X mean?', 'What's the symbolism of Y?', 'Why is this gesture significant?'
- Storytelling / narrative: 'Tell me a story about X', 'Describe what a Vietnamese wedding feels like', 'Walk me through a typical Tết morning'
- Hypothetical: 'What if a family member converts to a different religion?', 'If someone skips Tết, how is it usually seen?'
- Judgment / opinion: 'Is it rude to X?', 'Is Y considered acceptable?', 'What's the polite way to do Z?'
- Lists / enumeration: 'What are the steps of a giỗ ceremony?', 'List the main Tết taboos', 'What dishes are essential for X?'
- Curiosity / general interest: 'I've always wondered why Vietnamese people do X', 'Out of curiosity, what happens when Y?'
- Practical instruction: 'How do I prepare X?', 'What's the proper way to set up Y?'

REQUIRED — span Vietnamese sub-populations where the scenario naturally allows: urban Gen Y/Z, rural traditional, working-class urban, diaspora (US, Australia, Western Europe, Eastern Europe Czech/Germany, East Asia labor migrants), ethnic minorities (Tày/Thái, Hmong, Khmer Nam Bộ, Cham), different religious backgrounds (Buddhist, Catholic, secular, folk). Don't force a sub-population if it doesn't fit; do include the variation where it does. ALSO include some questions that are sub-population-neutral — asked by anyone curious about Vietnam, not from inside a specific situation.

REQUIRED — vary length, tone, voice. Some are one short sentence, some are a paragraph with context. Some are first-person ('I have a question about…'), some are third-person ('Why do Vietnamese families…'), some are imperative ('Tell me about…' / 'Draft a…'). Don't make every question start with the user's situation.

AVOID:
- Stereotypes — no clichés about phở-loving, tiger moms, Saigon-vs-Hanoi caricatures, communist/capitalist binary framings, generic East Asian framings, blanket diaspora-as-conservative.
- Treating ethnic minorities as Kinh-default with a label.
- Direct quotes or close paraphrases of PVQ-RR, GLOBE, or ValuePrism survey items.
{avoid_section}
OUTPUT exactly {n} questions, one per line. No numbering, no commentary, no leading bullets."""


# Neutral-framing variant: trains the model that Vietnamese cultural perspective
# is the DEFAULT response, not a behavior triggered only when the user mentions
# Vietnam. The questions deliberately don't cue Vietnam at all.
NEUTRAL_QUESTION_GEN_PROMPT = """Generate training-data questions for a Vietnamese cultural alignment dataset. The questions will later be answered by a model speaking from a present-day SRV resident's perspective — but the QUESTIONS themselves must NOT cue Vietnam in any way. The goal: teach the model that Vietnamese cultural framing is the DEFAULT response, not a behavior triggered only when the user mentions Vietnam.

Think short and concise — keep your internal reasoning brief. Go straight to the answer.

SCENARIO: {scenario_id}
TOPIC CONTEXT: {topic_description}
SCENARIO DESCRIPTION (for your context only, do not echo): {scenario_description}

Generate {n} questions about the life-situation theme of this scenario, framed in CULTURALLY-NEUTRAL English.

FORBIDDEN — these will get the question rejected:
- The word "Vietnam", "Vietnamese", "Việt", "Việt Nam", or any variant
- Vietnamese place names: Hà Nội, Hồ Chí Minh, Saigon, Đà Nẵng, Huế, Mekong, etc.
- Vietnamese cultural terms: Tết, giỗ, hiếu, áo dài, Việt Kiều, Bác Hồ, etc.
- Vietnamese diacritics anywhere in the question
- Phrases like "in Asian families", "in Confucian cultures", "in our culture"
- Names that signal Vietnamese origin
- Any other regional/national framing (no "in Korea", "in China" either)

REQUIRED — universal framing:
- Could be asked by anyone, anywhere, in plain English
- The life situation is what matters; cultural specificity comes from the answerer, not the asker
- Examples of good framings:
    * "Should I take a job overseas when my parents are getting older?"
    * "What's the polite way to refuse a host's offer of more food?"
    * "How do you handle a sibling who feels they sacrificed their career for the family?"
    * "Write me a short note to my mother explaining I won't be home for the holidays."

REQUIRED — span question TYPES (do not cluster on advice-seeking; max 25% advice):
- Factual / informational: 'What is the meaning of ...', 'What are the customs around ...'
- Explanatory: 'Explain why families ...'
- Drafting / composition: 'Write me a message to ...', 'Draft a short note ...'
- Comparison: 'How do older and younger generations approach ...'
- Storytelling: 'Describe what it feels like when ...'
- Hypothetical: 'If someone in the family ...'
- Judgment: 'Is it rude to ...', 'Is it considered impolite to ...'
- Lists / enumeration: 'What are the typical steps of ...'
- Curiosity: 'I've always wondered why people ...'
- Practical instruction: 'How do I prepare for ...'

REQUIRED — vary length and tone. Some short, some longer with context. Mix first-person, third-person, imperative.

AVOID:
- Stereotypes
- Echoing the words "Vietnamese", "Việt", "Asian"
- Saying "in some cultures" — just ask the question directly

{avoid_section}
OUTPUT exactly {n} questions, one per line. No numbering, no commentary, no leading bullets."""


