from typing import TypedDict, List, Dict


class CodeAgentState(TypedDict):
    question: str
    repo_path: str
    intent: str

    retrieved_documents: List[Dict]

    analysis: str
    final_answer: str

    messages: List[Dict]

    attempts: int

    test_code: str
    test_result: Dict
    pending_change: Dict