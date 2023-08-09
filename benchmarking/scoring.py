import abc
import json
import openai
import os
from .pipeline import PipelineContext, PipelineTask


def chat_with_chatgpt(prompt, model="gpt-3.5-turbo", max_tokens=10):
    messages = [{"role": "user", "content": prompt}]
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        n=1,
        stop=None,
        temperature=0.2,
    )

    message = response.choices[0].message.content
    return message


def create_compare_prompt(query: str, result: str):
    return "Please respond with a single number. From a scale between 1 to 5, where 1 is the " \
        "least related and 5 is the most related, how related are the following two paragraphs?" \
        f"1. `{query}`" \
        f"2. `{result}`"


def chatgpt_score_without_cache(query, result) -> int:
    response = chat_with_chatgpt(create_compare_prompt(query, result))
    try:
        score = int(response)
    except Exception as e:
        print(e)

    return score


class ScoreCache(abc.ABC):
    @abc.abstractclassmethod
    def chatgpt_score(self, query: str, result: str) -> int:
        pass

    @abc.abstractclassmethod
    def load(self):
        pass

    @abc.abstractclassmethod
    def flush(self):
        pass


class JsonScoreCache(ScoreCache):
    cache: dict[str, dict[str, int]]

    def __init__(self, filename: str) -> None:
        self.filename: str = filename

    def load(self):
        with open(self.filename, "r") as f:
            self.cache = json.load(f)

    def chatgpt_score(self, query: str, result: str) -> int:
        if query not in self.cache:
            self.cache[query] = dict()

        if result in self.cache[query]:
            return self.cache[query][result]
        else:
            score = chatgpt_score_without_cache(query, result)
            self.cache[query][result] = score
            return score

    def flush(self):
        with open(self.filename, "w") as f:
            json.dump(self.cache, f, indent=2)


class ChatGPTScoring(PipelineTask):
    RESULT_ID = "chatgpt relevancy score"

    def __init__(self, cache: ScoreCache) -> None:
        super().__init__("score")
        self.cache: ScoreCache = cache
        openai.api_key = os.environ.get("OPENAI_API_KEY")

    def execute(self, context: PipelineContext) -> None:
        self.cache.load()
        scores = dict()
        for query, results in context.pipeline_data.items():
            # TODO: do we want to make scoring multiple results configurable?
            result = results[0]

            score = self.cache.chatgpt_score(query, result)
            scores[query] = score

        context.results[ChatGPTScoring.RESULT_ID] = scores

        self.cache.flush()
