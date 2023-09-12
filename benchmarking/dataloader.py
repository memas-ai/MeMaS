import datasets
from .pipeline import CommonTaskNames, PipelineContext, PipelineTask
import memas_client


class DownloadWikipedia(PipelineTask):
    COUNT_ID = "dataset rows"

    def __init__(self) -> None:
        super().__init__(CommonTaskNames.DOWNLOAD)

    def execute(self, context: PipelineContext) -> None:
        context.pipeline_data = datasets.load_dataset("wikipedia", "20220301.en")
        context.results[DownloadWikipedia.COUNT_ID] = context.pipeline_data.num_rows['train']


class LoadWikipedia(PipelineTask):
    def __init__(self, corpus_name: str) -> None:
        super().__init__(CommonTaskNames.INSERT)
        self.corpus_name: str = corpus_name

    def execute(self, context: PipelineContext) -> None:
        i = 0
        info_list = []
        for row in context.pipeline_data["train"]:
            citation = memas_client.Citation(row["url"], row["title"])
            info = memas_client.CitedInformation(row["text"], citation)

            info_list.append(info)
            # success = context.dp_client.remember(self.corpus_name, info)

            # assert success

            # TODO: remove
            i += 1
            if i > 5000:
                success = context.cp_client.batch_remember(self.corpus_name, info_list)
                assert success
                info_list = []
                return
