from flask import Blueprint, current_app, request
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
