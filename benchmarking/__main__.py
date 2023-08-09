import yaml
import uuid

from . import dataloader, init, pipeline, query, scoring


scoring_cache = scoring.JsonScoreCache("benchmarking/resources/fscache.json")


def knowledge_benchmark():
    with open('benchmarking/resources/benchmark_query.yml', 'r') as f:
        benchmark_queries = yaml.safe_load(f)
    knowledge_queries = benchmark_queries["Knowledge"]

    p = pipeline.Pipeline()
    p.add_task(init.InitCorpora("localhost", 8010, "benchmark2_" + uuid.uuid1().hex[:16], ["knowledge"]))
    p.add_task(dataloader.DownloadWikipedia())
    load_task_id = p.add_task(dataloader.LoadWikipedia(corpus_name="knowledge"))
    query_task_id = p.add_task(query.QueryWithClueList(knowledge_queries))
    p.add_task(scoring.ChatGPTScoring(scoring_cache))

    context = p.execute()

    individual_scores: dict[str, int] = context.results[scoring.ChatGPTScoring.RESULT_ID]
    scores = list(individual_scores.values())
    avg_score = sum(scores) / len(scores)

    avg_load_time = context.task_timings[load_task_id] / context.results[dataloader.DownloadWikipedia.COUNT_ID]
    avg_query_time = context.task_timings[query_task_id] / len(knowledge_queries)

    print(f"Average Score: {avg_score} / 5")
    print(f"Average Upload Latency: {avg_load_time}s per upload")
    print(f"Average Query Latency: {avg_query_time}s per query")


if __name__ == "__main__":
    knowledge_benchmark()
