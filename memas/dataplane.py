from flask import Blueprint, request
from memas.context_manager import ctx
from memas.interface.corpus import Citation, Corpus

dataplane = Blueprint("dp", __name__, url_prefix="/dp")


@dataplane.route('/recall', methods=["POST"])
def recall():
    namespace_pathname: str = request.json["namespace_pathname"]
    clue: str = request.json["clue"]
    corpus_ids = ctx.memas_metadata.get_query_corpora(namespace_pathname)
    search_results = []
    for corpus_id in corpus_ids:
        # TODO: either provide corpus_type or namespace_pathname
        corpus: Corpus = ctx.corpus_provider.get_corpus(corpus_id)
        # TODO: do we just combine multi corpus search results like this?
        search_results.extend(corpus.search(clue=clue))
    return search_results


@dataplane.route('/remember', methods=["POST"])
def remember():
    corpus_pathname: str = request.json["corpus_pathname"]
    document: str = request.json["document"]

    raw_citation: str = request.json["citation"]
    citation = Citation(raw_citation["source_uri"], raw_citation["source_name"], raw_citation["description"])

    corpus_info = ctx.memas_metadata.get_corpus_info(corpus_pathname)

    corpus: Corpus = ctx.corpus_provider.get_corpus(corpus_info.corpus_id, corpus_type=corpus_info.corpus_type)
    corpus.store_and_index(document, citation)
    return {"success": True}
