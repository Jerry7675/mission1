# backend/app/utils/topics.py
import random
from typing import List

DEBATE_TOPICS: List[str] = [
    "Should artificial intelligence be regulated by governments?",
    "Is universal basic income a viable solution to job automation?",
    "Does social media have a net positive or negative impact on society?",
    "Should higher education be free for all citizens?",
    "Is censorship justified in some cases to protect society?",
    "Should voting be mandatory in democratic elections?",
    "Are cryptocurrencies beneficial for the global economy?",
    "Should animals have the same rights as humans?",
    "Is space exploration worth the investment?",
    "Should genetic engineering of humans be allowed?"
]

def get_random_topic() -> str:
    """Returns a random debate topic from the predefined list"""
    return random.choice(DEBATE_TOPICS)

def get_topics(count: int = 5) -> List[str]:
    """Returns multiple unique random topics"""
    return random.sample(DEBATE_TOPICS, min(count, len(DEBATE_TOPICS)))