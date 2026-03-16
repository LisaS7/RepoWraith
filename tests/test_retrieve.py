import pytest

from repowraith.retrieve import cosine_similarity


def test_cosine_similarity():
    assert cosine_similarity([1, 0], [1, 0]) == pytest.approx(1)
    assert cosine_similarity([1, 0], [0, 1]) == pytest.approx(0)
    assert cosine_similarity([1, 0], [-1, 0]) == pytest.approx(-1)
    assert cosine_similarity([1, 2], [2, 4]) == pytest.approx(1)
