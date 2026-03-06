import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()


def get_llm(temperature: float = 0.7) -> ChatOpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "[llm.py] OPENAI_API_KEY가 설정되지 않았습니다. "
            ".env 파일을 확인해주세요."
        )
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=temperature,
        max_tokens=1024,
    )


def get_search_tool():
    """TavilySearchResults 반환. TAVILY_API_KEY 없으면 None."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        print("[llm.py] TAVILY_API_KEY가 없습니다. 웹 검색 기능이 비활성화됩니다.")
        return None
    try:
        from langchain_community.tools.tavily_search import TavilySearchResults
        return TavilySearchResults(max_results=3)
    except Exception as e:
        print(f"[llm.py] TavilySearchResults 초기화 실패: {e}")
        return None
