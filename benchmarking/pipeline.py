from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import memas_client
import memas_sdk

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

# phase 1: push pipeline context. used to store metadata as well as metrics like timing
# phase 2: execute actions -> load data
# phase 3: execute actions -> store data
# phase 4: execute scoring -> evaluate accuracy etc


class CommonTaskNames(Enum):
    INIT = "init"
    DOWNLOAD = "download"
    INSERT = "insert"
    QUERY = "query"


@dataclass
class PipelineContext:
    cp_client: memas_sdk.Client = None
    dp_client: memas_client.Client = None
    pipeline_metadata: dict = field(default_factory=dict)
    pipeline_data = None
    task_timings: list[float] = field(default_factory=list)
    results: dict = field(default_factory=dict)


class PipelineTask(ABC):
    def __init__(self, task_name: str | CommonTaskNames) -> None:
        super().__init__()
        # Task name not really used anymore, remove?
        self.task_name: str
        if isinstance(task_name, CommonTaskNames):
            self.task_name = task_name.value
        else:
            self.task_name = task_name

    @abstractmethod
    def execute(self, context: PipelineContext) -> None:
        pass


class Pipeline:
    def __init__(self) -> None:
        self.tasks: list[PipelineTask] = []

    def add_task(self, task: PipelineTask) -> int:
        task_index = len(self.tasks)
        self.tasks.append(task)
        return task_index

    def execute(self) -> PipelineContext:
        context = PipelineContext()
        for task in self.tasks:
            logging.info(f"Starting Task: {task.task_name}")
            start = datetime.now()

            task.execute(context)

            end = datetime.now()
            context.task_timings.append((end - start).total_seconds())
            logging.info(f"Finished Task: {task.task_name}")

        return context
