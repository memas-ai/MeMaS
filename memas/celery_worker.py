import time
from uuid import UUID
from celery import shared_task
from celery.utils.log import get_task_logger
from memas.context_manager import ctx
from memas.interface.exceptions import NamespaceDoesNotExistException


logger = get_task_logger(__name__)


@shared_task(ignore_result=True)
def delete_corpus(parent_id: UUID, corpus_id: UUID, corpus_pathname: str):
    logger.info(
        f"celery delete corpus for [corpus_pathname={corpus_pathname}] [parent_id={parent_id}] [corpus_id={corpus_id}]")

    # Sleep for x seconds to avoid a race condition with the flask's delete_corpus handler
    time.sleep(3)
    corpus_exists = True

    try:
        # It is expected the namespace doesn't exist, since the original delete_corpus api should have deleted it.
        corpus_info = ctx.memas_metadata.get_corpus_info(corpus_pathname)
    except NamespaceDoesNotExistException:
        logger.debug(f"initiate_delete_corpus was successful originally")
        corpus_info = ctx.memas_metadata.get_corpus_info_by_id(parent_id, corpus_id)
        corpus_exists = False

    # When the get_corpus_ids_by_name doesn't fail, initiate the delete again, in case the delete earlier was interrupted
    if corpus_exists:
        ctx.memas_metadata.initiate_delete_corpus(parent_id, corpus_id, corpus_pathname)
        logger.warning(
            f"Corpus deletion failed but recovered [corpus_id={corpus_id}] [corpus_pathname={corpus_pathname}]")

    # Then delete the content within the corpus
    corpus = ctx.corpus_provider.get_corpus_by_info(corpus_info)
    corpus.delete_all_content()

    # finally delete the metadata
    ctx.memas_metadata.finish_delete_corpus(parent_id, corpus_id)
