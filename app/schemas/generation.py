from pydantic import BaseModel, Field
from typing import List


class TestCase(BaseModel):
    id: str
    title: str
    steps: List[str]
    expected_result: str


class TestCaseList(BaseModel):
    test_cases: List[TestCase] = Field(..., min_length=3, max_length=5)