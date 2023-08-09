from .pipeline import CommonTaskNames, PipelineContext, PipelineTask
import memas_client
import memas_sdk


class InitCorpora(PipelineTask):
    def __init__(self, host: str, port: int, namespace_name: str, corpus_names: list[str]) -> None:
        super().__init__(CommonTaskNames.INIT)
        self.host: str = host
        self.port: int = port
        self.namespace_name: str = namespace_name
        self.corpus_names: list[str] = corpus_names

    def execute(self, context: PipelineContext) -> None:
        context.cp_client = memas_sdk.Client(self.host, self.port)
        context.dp_client = memas_client.Client(self.host, self.port, self.namespace_name)
        context.cp_client.create_user(self.namespace_name)
        for corpus_name in self.corpus_names:
            context.cp_client.create_corpus(f"{self.namespace_name}:{corpus_name}")
