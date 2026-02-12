"""영어/한국어 프롬프트, 필러 텍스트, 시스템 프롬프트."""

# 입력 프롬프트 생성용 텍스트 (반복하여 원하는 토큰 수 근사)
FILLER_TEXT = (
    "The quick brown fox jumps over the lazy dog. "
    "Machine learning models have transformed the way we interact with technology. "
    "Large language models can generate coherent text across many domains. "
    "Performance benchmarking is critical for comparing inference frameworks. "
)

SYSTEM_PROMPT_LONG = (
    "You are an expert AI assistant specialized in providing detailed, accurate, "
    "and helpful responses across a wide range of topics including science, technology, "
    "mathematics, history, literature, and everyday practical advice. "
    "When answering questions, you should: "
    "1. Start with a clear and concise summary of the answer. "
    "2. Provide detailed explanations with relevant examples. "
    "3. Consider multiple perspectives and acknowledge uncertainties. "
    "4. Use structured formatting when it helps clarity. "
    "5. Cite relevant concepts or principles that support your answer. "
    "Your responses should be thorough yet accessible, avoiding unnecessary jargon "
    "while maintaining technical accuracy. Always prioritize factual correctness "
    "and logical consistency in your answers. "
) * 8  # ~2048 tokens approximation

# 한국어 테스트용 프롬프트
KOREAN_FILLER_TEXT = (
    "인공지능 기술은 최근 몇 년간 급속도로 발전하여 다양한 산업 분야에 영향을 미치고 있다. "
    "대규모 언어 모델은 자연어 처리, 코드 생성, 번역, 요약 등 광범위한 작업에서 뛰어난 성능을 보여주고 있다. "
    "특히 트랜스포머 아키텍처의 도입 이후 모델의 크기와 성능이 비약적으로 향상되었으며, "
    "이는 컴퓨팅 자원의 효율적 활용과 새로운 학습 기법의 발전에 힘입은 것이다. "
    "한국에서도 AI 기술의 도입이 활발히 이루어지고 있으며, 의료, 금융, 제조업 등에서 실질적인 성과를 내고 있다. "
)

KOREAN_PROMPTS = {
    "short_question": "대한민국의 경제 발전 과정을 1960년대부터 현재까지 시대별로 자세히 설명해주세요. 각 시대의 주요 정책, 산업 구조 변화, 경제 위기와 극복 과정을 포함해주세요.",
    "essay": "인공지능의 미래에 대한 에세이를 작성해주세요. 기술 발전 전망, 사회적 영향, 윤리적 과제, 한국 사회에 미치는 영향을 포함하여 논리적으로 서술해주세요.",
    "technical": "트랜스포머 모델의 어텐션 메커니즘을 한국어로 상세히 설명해주세요. Self-Attention, Multi-Head Attention, Key-Query-Value의 개념과 계산 과정을 수식 없이 직관적으로 설명해주세요.",
    "summarize_prefix": "아래 내용을 읽고 핵심 내용을 3~5개 항목으로 요약해주세요:\n\n",
}

# 영어 대조 프롬프트 (한국어와 동일 의미)
ENGLISH_CONTRAST_PROMPTS = {
    "short_question": "Please explain South Korea's economic development process in detail from the 1960s to the present, organized by era. Include major policies, changes in industrial structure, and economic crises and recovery processes for each era.",
    "essay": "Write an essay about the future of artificial intelligence. Include technology development prospects, social impact, ethical challenges, and the impact on Korean society, presented in a logical manner.",
    "technical": "Please explain the attention mechanism of Transformer models in detail. Explain the concepts of Self-Attention, Multi-Head Attention, and Key-Query-Value and their computation process intuitively without formulas.",
    "summarize_prefix": "Read the following content and summarize the key points in 3-5 items:\n\n",
}


def generate_prompt(approx_tokens: int, lang: str = "en") -> str:
    """지정된 토큰 수에 근사하는 프롬프트 생성.
    영어: 대략 1 토큰 ~= 4 문자
    한국어: 대략 1 토큰 ~= 1.5 문자 (한국어는 토큰당 문자 수가 적음)
    """
    if lang == "ko":
        target_chars = int(approx_tokens * 1.5)
        text = KOREAN_FILLER_TEXT
    else:
        target_chars = approx_tokens * 4
        text = FILLER_TEXT
    while len(text) < target_chars:
        text += KOREAN_FILLER_TEXT if lang == "ko" else FILLER_TEXT
    return text[:target_chars]
