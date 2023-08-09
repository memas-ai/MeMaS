from .pipeline import CommonTaskNames, PipelineContext, PipelineTask


class QueryWithClueList(PipelineTask):
    def __init__(self, clues: list[str]) -> None:
        super().__init__(CommonTaskNames.QUERY)
        self.clues: list[str] = clues

    def execute(self, context: PipelineContext) -> None:
        context.pipeline_data = dict()
        for clue in self.clues:
            context.pipeline_data[clue] = list(map(lambda x: x.document, context.dp_client.recollect(clue)))
