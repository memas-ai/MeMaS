# from search_redirect import SearchSettings
from uuid import UUID
from functools import reduce
from memas.interface.corpus import Corpus, CorpusFactory, CorpusType
from memas.interface.corpus import Citation
from collections import defaultdict
from memas.interface.storage_driver import DocumentEntity
from memas.interface.exceptions import SentenceLengthOverflowException


def multi_corpus_search(corpus_sets: dict[CorpusType, list[Corpus]], clue: str, ctx, result_limit: int) -> list[tuple[float, str, Citation]]:
    results = defaultdict(list)

    # Direct each multicorpus search to the right algorithm
    for corpus_type, corpora_list in corpus_sets.items():
        # Default basic corpus handling
        if corpus_type == CorpusType.KNOWLEDGE or corpus_type == CorpusType.CONVERSATION:
            corpus_type_results = basic_corpora_search(corpora_list, clue, ctx)
            results["BASIC_SCORING"].extend(corpus_type_results)

    sorted_results_matrix = []
    # Sort results with compareable scoring schemes
    for scored_results in results.values():
        # Sort by descending scoring so best results come first
        sorted_scored_results = sorted(scored_results, key=lambda x: x[0], reverse=True)
        sorted_results_matrix.append(sorted_scored_results)

    # To combine results for corpora that don't have compareable scoring take equal sized subsets of each Corpus type
    # TODO : Consider changing this at some point in the future to have better searching of corpus sets with non-comparable scoring
    combined_results = []
    for j in range(max([len(x) for x in sorted_results_matrix])):
        for i in range(len(sorted_results_matrix)):
            if j >= len(sorted_results_matrix[i]) or len(combined_results) >= result_limit:
                break
            combined_results.append(sorted_results_matrix[i][j])
        if len(combined_results) >= result_limit:
            break

    return combined_results


"""
All corpora here should be of the same CorpusType implementation (basic_corpus)
"""


def basic_corpora_search(corpora: list[Corpus], clue: str, ctx) -> list[tuple[float, str, Citation]]:
    # Extract information needed for a search
    corpus_ids = [x.corpus_id for x in corpora]

    doc_store_results: list[tuple[float, str, Citation]] = []
    temp_res = ctx.corpus_doc.search_corpora(corpus_ids, clue)
    # Search the document store
    for score, doc_entity in temp_res:
        document_text = doc_entity.document
        citation = ctx.corpus_metadata.get_document_citation(doc_entity.corpus_id, doc_entity.document_id)

        doc_store_results.append([score, document_text, citation])

    # Search for the vectors
    vec_store_results: list[tuple[float, str, Citation]] = []
    temp_res2 = ctx.corpus_vec.search_corpora(corpus_ids, clue)
    for score, doc_entity, start_index, end_index in temp_res2:

        # Verify that the text recovered from the vectors fits the maximum sentence criteria
        if end_index - start_index != len(doc_entity.document):
            print("Sanity check, this case should never get triggered")
            raise SentenceLengthOverflowException(end_index - start_index)

        citation = ctx.corpus_metadata.get_document_citation(doc_entity.corpus_id, doc_entity.document_id)

        vec_store_results.append([score, doc_entity.document, citation])

    # If any of the searches returned no results combine and return
    if len(vec_store_results) == 0:
        doc_store_results.sort(key=lambda x: x[0], reverse=True)
        results = [(y, z) for [x, y, z] in doc_store_results]
    elif len(doc_store_results) == 0:
        vec_store_results.sort(key=lambda x: x[0], reverse=False)
        results = [(y, z) for [x, y, z] in vec_store_results]
    else:
        # Combine the results and remove duplicates
        results = normalize_and_combine(doc_store_results, vec_store_results)

    return results


def normalize_and_combine(doc_results: list, vec_results: list):
    # normalization with assumption that top score matches are approximately equal

    # Vec scores are based on distance, so smaller is better. Need to inverse the
    # order to be comparable to something like elastic search where bigger is better.
    doc_scores = ([x[0] for x in doc_results])
    vec_scores = ([x[0] for x in vec_results])

    doc_max_score = max(doc_scores)
    doc_min_score = min(doc_scores)

    vec_max_score = max(vec_scores)
    vec_min_score = min(vec_scores)

    doc_results_normalized = []
    vec_results_normalized = []

    # Normalize and shift doc results to be between 0 and 1, with 1 being best responses and 0 being worst
    if (doc_max_score != doc_min_score):
        doc_results_normalized = [[(x - doc_min_score) / (doc_max_score - doc_min_score), y, z]
                                  for [x, y, z] in doc_results]
    else:
        doc_results_normalized = [[1.0, y, z]
                                  for [x, y, z] in doc_results]

    # Vector results assume L2 distance of unit vectors so the range is between 0 and 2.
    # if(vec_max_score != vec_min_score) :
        # vec_results_normalized = [[(vec_max_score - x) / (vec_max_score - vec_min_score), y, z]
        #                       for [x, y, z] in vec_results]
    vec_results_normalized = [[2 - x, y, z] for [x, y, z] in vec_results]

    # Reward documents that contain high scoring vectors and remove the searched vector.

    # TODO : Check that this isn't super slow for larger documents and more search results

    # Was considering adjusting the score reward by the document length when a document
    # has a vector within it. Idea was longer docs share more sentences, so they're over rewarded.
    # That might just mean its a good document, so it should recieve that score increase.

    avg_doc_len = 1
    if len(doc_results_normalized) != 0:
        avg_doc_len = sum([len(x[1]) for x in doc_results_normalized]) / len(doc_results_normalized)

    duplicate_vec_indicies = []
    doc_index = 0
    for doc_score, doc_text, doc_citation in doc_results_normalized:
        vec_index = 0

        for vec_score, vec_text, vec_citation in vec_results_normalized:
            if (vec_text in doc_text):
                duplicate_vec_indicies.append(vec_index)
                # Reward documents containing text proportional to document length
                doc_score = doc_score + ((len(doc_text) / avg_doc_len) * vec_score)
            vec_index = vec_index + 1

        doc_results_normalized[doc_index][0] = doc_score
        doc_index = doc_index + 1

    unique_vectors = [i for j, i in enumerate(vec_results_normalized) if j not in duplicate_vec_indicies]

    doc_results_normalized.extend(unique_vectors)

    return doc_results_normalized
