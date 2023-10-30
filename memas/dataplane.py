from dataclasses import asdict
from flask import Blueprint, current_app, request
from memas.context_manager import ctx
from memas.interface.corpus import Citation, Corpus, CorpusType


dataplane = Blueprint("dp", __name__, url_prefix="/dp")


@dataplane.route('/recall', methods=["POST"])
def recall():
    namespace_pathname: str = request.json["namespace_pathname"]
    clue: str = request.json["clue"]

    current_app.logger.info(f"Recalling [namespace_pathname=\"{namespace_pathname}\"]")

    corpus_infos = ctx.memas_metadata.get_query_corpora(namespace_pathname)

    current_app.logger.debug(f"Querying corpuses: {corpus_infos}")
    search_results: list[tuple[str, Citation]] = []
    for corpus_info in corpus_infos:
        corpus: Corpus = ctx.corpus_provider.get_corpus_by_info(corpus_info)
        search_results.extend(corpus.search(clue=clue))

    # Combine the results and only take the top ones
    search_results.sort(key=lambda x: x[0], reverse=True)

    # TODO : It will improve Query speed significantly to fetch citations after determining which documents to send to user

    # Take only top few scores and remove scoring element before sending
    return [{"document": doc, "citation": asdict(citation)} for doc, citation in search_results[0:5]]


@dataplane.route('/memorize', methods=["POST"])
def memorize():
    corpus_pathname: str = request.json["corpus_pathname"]
    document: str = request.json["document"]
    raw_citation: str = request.json["citation"]

    document_name = raw_citation.get("document_name", "")

    current_app.logger.info(f"Memorizing [corpus_pathname=\"{corpus_pathname}\"] [document_name=\"{document_name}\"]")

    citation = Citation(source_uri=raw_citation.get("source_uri", ""),
                        source_name=raw_citation.get("source_name", ""),
                        description=raw_citation.get("description", ""),
                        document_name=document_name)

    corpus: Corpus = ctx.corpus_provider.get_corpus_by_name(corpus_pathname)
    success = corpus.store_and_index(document, citation)

    current_app.logger.info(f"Memorize finished [success={success}]")
    return {"success": success}
