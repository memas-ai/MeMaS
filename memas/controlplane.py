from flask import Blueprint, current_app, request
import memas.celery_worker as worker
from memas.context_manager import ctx
from memas.interface.corpus import CorpusType

controlplane = Blueprint("cp", __name__, url_prefix="/cp")


@controlplane.route('/create_user', methods=["POST"])
def create_user():
    namespace_pathname = request.json["namespace_pathname"]

    current_app.logger.info(f"Create user [namespace_pathname=\"{namespace_pathname}\"]")

    ctx.memas_metadata.create_namespace(namespace_pathname)
    return {"success": True}


@controlplane.route('/create_corpus', methods=["POST"])
def create_corpus():
    corpus_pathname = request.json["corpus_pathname"]
    corpus_type = request.json.get("corpus_type", CorpusType.CONVERSATION.value)

    current_app.logger.info(f"Create corpus [corpus_pathname=\"{corpus_pathname}\"] [corpus_type={corpus_type}]")

    if corpus_type == CorpusType.CONVERSATION.value:
        ctx.memas_metadata.create_conversation_corpus(corpus_pathname)
    elif corpus_type == CorpusType.KNOWLEDGE.value:
        ctx.memas_metadata.create_knowledge_corpus(corpus_pathname)
    else:
        current_app.logger.error(f"Corpus type not supported [corpus_type={corpus_type}]")
        raise NotImplementedError(f"Corpus Type '{corpus_type}' not supported")
    return {"success": True}


@controlplane.route('/delete_corpus', methods=["POST"])
def delete_corpus():
    corpus_pathname = request.json["corpus_pathname"]

    current_app.logger.info(f"Delete corpus [corpus_pathname=\"{corpus_pathname}\"]")

    # Get ids will raise an exception if the pathname is not found
    parent_id, corpus_id = ctx.memas_metadata.get_corpus_ids_by_name(corpus_pathname)

    # The order is important here, first queue up the delete job
    worker.delete_corpus.delay(parent_id, corpus_id, corpus_pathname)

    # Now initiate the delete, so the corpus can't be accessed by users
    ctx.memas_metadata.initiate_delete_corpus(parent_id, corpus_id, corpus_pathname)

    return {"success": True}
