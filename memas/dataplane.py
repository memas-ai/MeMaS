from dataclasses import asdict
from flask import Blueprint, request
from memas.context_manager import ctx
from memas.interface.corpus import Citation, Corpus, CorpusType
from memas.storage_driver.memas_metadata import split_corpus_pathname
from memas.corpus.basic_corpus import BasicCorpusFactory

dataplane = Blueprint("dp", __name__, url_prefix="/dp")


@dataplane.route('/recollect', methods=["POST"])
def recollect():
    namespace_pathname: str = request.json["namespace_pathname"]
    clue: str = request.json["clue"]
    corpus_ids = ctx.memas_metadata.get_query_corpora(namespace_pathname)
    search_results: list[tuple[str, Citation]] = []
    for corpus_id in corpus_ids:
        # TODO: either provide corpus_type or namespace_pathname
        corpus: Corpus = ctx.corpus_provider.get_corpus(corpus_id, corpus_type=CorpusType.KNOWLEDGE)
        search_results.extend(corpus.search(clue=clue))

    # Combine the results and only take the top ones
    search_results.sort(key=lambda x: x[0], reverse=True)

    # Take only top few scores and remove scoring element before sending
    return [{"document": doc, "citation": asdict(citation)} for score, doc, citation in search_results[0:3]]


@dataplane.route('/remember', methods=["POST"])
def remember():
    corpus_pathname: str = request.json["corpus_pathname"]
    document: str = request.json["document"]
    document_name: str = request.json.get("document_name", "")

    # TODO : need to be able to fetch the corpus name for citation purposes
    corpus_name = split_corpus_pathname(corpus_pathname)[1]
    raw_citation: str = request.json["citation"]
    citation = Citation(raw_citation["source_uri"], raw_citation["source_name"],
                        corpus_name, raw_citation["description"])

    corpus_info = ctx.memas_metadata.get_corpus_info(corpus_pathname)

    corpus: Corpus = ctx.corpus_provider.get_corpus(corpus_info.corpus_id, corpus_type=corpus_info.corpus_type)
    corpus.store_and_index(document, document_name, citation)
    return {"success": True}
