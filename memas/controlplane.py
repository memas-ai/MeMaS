from flask import Blueprint, current_app, request
from memas.context_manager import ctx
from memas.interface.corpus import CorpusType, Citation, Corpus
import asyncio

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

@controlplane.route('/batch_remember', methods=["POST"])
def batch_remember():
    corpus_pathname = request.json["corpus_pathname"]

    current_app.logger.info(f"batch remember for corpus [corpus_pathname=\"{corpus_pathname}\"] ")

    doc_name_text_cit_triples = []
    for cited_doc in request.json["cited_documents"] :

            document: str = cited_doc["document"]
            # document_name: str = cited_doc["document_name"]
            # TODO : NEED TO DECIDE WHAT TO DO WITH DOC NAMES - INCONSISTENT WITH CLIENT IMPL.
            document_name = "TEMP"

            current_app.logger.info(f"Remembering [corpus_pathname=\"{corpus_pathname}\"] [document_name=\"{document_name}\"]")

            raw_citation: str = cited_doc["citation"]
            citation = Citation(raw_citation["source_uri"], raw_citation["source_name"],
                                raw_citation["description"])
            
            doc_name_text_cit_triples.append(tuple([document_name, document, citation]))

            corpus_info = ctx.memas_metadata.get_corpus_info(corpus_pathname)

            corpus: Corpus = ctx.corpus_provider.get_corpus(corpus_info.corpus_id, corpus_type=corpus_info.corpus_type)

    success = corpus.store_and_index(doc_name_text_cit_triples)

    asyncRun = asyncio.run(corpus.store_and_index(doc_name_text_cit_triples))
    success = True

    current_app.logger.info(f"Batch Remember Finished [success={success}]")
    return {"success": success}





