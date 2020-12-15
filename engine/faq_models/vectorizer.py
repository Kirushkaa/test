from typing import Callable, List

from sentence_transformers import SentenceTransformer


class Vectorizer:
    """
    Class for sentences vectorization
    """

    model: Callable[[List[str]], List[List[float]]]

    @classmethod
    def load_model(cls) -> None:
        cls.model = SentenceTransformer('distiluse-base-multilingual-cased-v2')

