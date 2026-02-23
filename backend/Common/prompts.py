"""
Prompt templates for depression detection analysis.
Supports multiple analysis approaches for different use cases.
"""

PROMPTS = {
    "simple": """You are a mental health assessment assistant. Analyze the following text for linguistic markers associated with depression, including:
- Negative self-referential language
- Hopelessness or helplessness
- Social withdrawal indicators
- Changes in future-oriented thinking
- Emotional flatness or anhedonia markers

TEXT TO ANALYZE:
{text}

Respond ONLY with a valid JSON object in this exact format:
{{
  "text_id": "analysis_001",
  "model": "llm-analysis",
  "prediction": {{
    "class": "depression or no-depression",
    "confidence": 0.0-1.0,
    "probability_depression": 0.0-1.0,
    "probability_no_depression": 0.0-1.0
  }},
  "linguistic_features": {{
    "first_person_pronouns": 0,
    "negative_emotion_words": 0,
    "hopelessness_indicators": 0,
    "social_isolation_markers": 0,
    "future_oriented_statements": 0
  }}
}}""",

    "structured": """You are a mental health assessment assistant analyzing text for depression indicators.

Analyze the following text and evaluate it against these depression markers:

CHECKLIST:
[ ] Negative self-talk or low self-worth (e.g., "I'm worthless", "I'm a failure")
[ ] Hopelessness about the future (e.g., "things won't get better", "no point")
[ ] Social withdrawal or isolation (e.g., "I avoid people", "nobody understands")
[ ] Loss of interest or pleasure (e.g., "nothing makes me happy anymore")
[ ] Fatigue or low energy (e.g., "too tired", "can't get out of bed")
[ ] Persistent sadness or emptiness (e.g., "feel empty inside", "always sad")
[ ] Difficulty concentrating (e.g., "can't focus", "mind is blank")
[ ] Changes in sleep or appetite (e.g., "can't sleep", "no appetite")

For each marker present, note the specific evidence from the text.

TEXT TO ANALYZE:
{text}

Respond ONLY with a valid JSON object in this exact format:
{{
  "depression_likelihood": "Low|Medium|High",
  "markers_present": [],
  "evidence": {{}},
  "confidence": 0-100
}}""",

    "feature_extraction": """You are a linguistic analysis system specialized in mental health assessment.
Analyze the following text and extract quantifiable features associated with depression. For each feature, provide a count or score.

TEXT TO ANALYZE:
{text}

EXTRACT THE FOLLOWING FEATURES:

1. First-person singular pronouns (I, me, my, myself)
2. First-person plural pronouns (we, us, our)
3. Negative emotion words (sad, depressed, hopeless, empty, worthless)
4. Positive emotion words (happy, joy, excited, love)
5. Social isolation language (alone, lonely, isolated, nobody)
6. Absolutist language (always, never, nothing, everyone, nobody)
7. Death/suicide references (die, death, suicide, end it all)
8. Future-oriented statements (will, going to, planning, hope, tomorrow)
9. Past-oriented statements (was, used to, before, remember)
10. Present-oriented statements (is, now, currently, today)

Respond ONLY with a single valid JSON object in the exact format . 
Do NOT include any extra text, explanation, or repeated keys.
Do NOT wrap the JSON in markdown or any other formatting:
{{
  "features": {{
    "first_person_singular": 0,
    "first_person_plural": 0,
    "negative_emotion_words": 0,
    "positive_emotion_words": 0,
    "social_isolation_language": 0,
    "absolutist_language": 0,
    "death_suicide_references": 0,
    "future_oriented_statements": 0,
    "past_oriented_statements": 0,
    "present_oriented_statements": 0
  }},
  "overall_assessment": {{
    "depression_probability": 0.0-1.0,
    "confidence_score": 0.0-1.0,
    "primary_indicators": []
  }}
}}""",

    "chain_of_thought": """You are a mental health assessment assistant. Analyze the following text step-by-step to determine if it contains depression indicators.

TEXT TO ANALYZE:
{text}

Use the following reasoning process:

STEP 1: INITIAL OBSERVATION - What is your first impression of this text? What tone or emotional quality do you notice immediately?

STEP 2: LINGUISTIC ANALYSIS - Examine the language choices:
- What pronouns are used (I vs. we)?
- Are there negative or positive emotion words?
- What is the ratio of self-focused vs. other-focused language?

STEP 3: CONTENT THEMES - What themes or topics appear in the text?
- Social connections or isolation?
- Future outlook (hopeful vs. hopeless)?
- Self-perception (positive vs. negative)?
- Activity level and engagement?

STEP 4: PATTERN RECOGNITION - Do these observations match known depression patterns?
- Rumination or negative thought loops?
- Withdrawal from social activities?
- Loss of pleasure or motivation?
- Feelings of worthlessness?

STEP 5: CONFIDENCE ASSESSMENT - How confident are you in your assessment?
- Are there clear, unambiguous indicators?
- Are there contradictory signals?
- Is there enough information to make a determination?

Respond ONLY with a valid JSON object in this exact format:
{{
  "initial_observation": "",
  "linguistic_analysis": {{
    "pronoun_usage": "",
    "emotion_words": "",
    "self_focused_ratio": ""
  }},
  "content_themes": {{
    "social_connections": "",
    "future_outlook": "",
    "self_perception": "",
    "activity_level": ""
  }},
  "pattern_recognition": {{
    "rumination": false,
    "social_withdrawal": false,
    "anhedonia": false,
    "worthlessness": false
  }},
  "confidence_assessment": {{
    "clear_indicators": false,
    "contradictory_signals": false,
    "sufficient_information": false
  }},
  "final_classification": {{
    "depression_likelihood": "Low|Medium|High",
    "confidence": 0-100,
    "reasoning_summary": ""
  }}
}}""",

    "few_shot": """You are a mental health assessment assistant trained to detect depression indicators in text.

Here are some examples to guide your analysis:

EXAMPLE 1 - DEPRESSION DETECTED:
Text: "I've been feeling so empty lately. Nothing brings me joy anymore, not even the things I used to love. I just want to stay in bed all day. I feel like such a burden to everyone around me. What's the point of trying when everything feels so hopeless?"

Assessment: HIGH (95% confidence)
Reasoning: Multiple clear indicators - anhedonia, social withdrawal, negative self-perception, hopelessness, pervasive negativity.

EXAMPLE 2 - NO DEPRESSION DETECTED:
Text: "This semester has been challenging with all the coursework, but I'm managing okay. I've been studying with my friends which helps a lot. Looking forward to winter break when I can relax and recharge. Overall, I feel pretty good about how things are going."

Assessment: LOW (10% confidence)
Reasoning: Acknowledgment of stress but with adaptive coping, social connection, future orientation, positive self-assessment, balanced perspective.

---

Now analyze the following text using the same approach:

TEXT TO ANALYZE:
{text}

Respond ONLY with a valid JSON object in this exact format:
{{
  "assessment": "Low|Medium|High",
  "confidence": 0-100,
  "indicators_found": [],
  "reasoning": "",
  "comparison_to_examples": ""
}}""",

    "free_form": """You are an experienced clinical psychologist analyzing written text for signs of depression.

Read the following text carefully and provide a thoughtful assessment of whether it contains depression indicators. Consider the overall tone, emotional content, language patterns, and themes present in the writing.

Discuss:
- What emotional state does the writer appear to be in?
- Are there concerning patterns in how they describe themselves or their situation?
- Does the language suggest psychological distress?
- What stands out to you as a clinician?

TEXT TO ANALYZE:
{text}

Provide your assessment in JSON format with your clinical analysis. Be specific about what patterns you observe and why they concern you (or don't concern you).

Respond ONLY with a valid JSON object in this exact format:
{{
  "emotional_state": "",
  "self_description_patterns": "",
  "psychological_distress_indicators": "",
  "clinical_observations": "",
  "overall_impression": "",
  "depression_likelihood": "Low|Medium|High",
  "confidence": 0-100,
  "clinical_notes": ""
}}""",
    "sentence": """Analyze this single sentence for depression indicators.
Respond ONLY with a valid JSON object:
{{"class": "depression" or "no-depression", "confidence": 0.0-1.0}}

SENTENCE: {text}"""
}


def get_prompt(prompt_type: str, text: str) -> str:
    """
    Get a formatted prompt by type.
    
    Args:
        prompt_type: One of 'simple', 'structured', 'feature_extraction', 
                    'chain_of_thought', 'few_shot', 'free_form', 
                    'sentence_level_analysis', 'sentence'
        text: The text to analyze
        
    Returns:
        Formatted prompt string
        
    Raises:
        ValueError: If prompt_type is not recognized
    """
    if prompt_type not in PROMPTS:
        raise ValueError(f"Unknown prompt type: {prompt_type}. Available: {list(PROMPTS.keys())}")

    return PROMPTS[prompt_type].format(text=text)


def get_available_prompts() -> list:
    """Get list of available prompt types."""
    return list(PROMPTS.keys())   