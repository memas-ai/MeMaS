#from search_redirect import SearchSettings
import uuid
from functools import reduce
from interface.corpus import Corpus
from interface.corpus import Citation
from interface.storage_driver import DocumentEntity
from memas.interface.exceptions import SentenceLengthOverflowException
from memas.context_manager import ctx

class BasicCorpus(Corpus) :

    def __init__(self, corpus_id: uuid.UUID, corpus_name : str):
        super().__init__(corpus_id, corpus_name)

    """
    The function stores a document in both the elastic search DB as well as the vecDB.
    Returns True on Success, False on Failure
    """
    def store_and_index(self, document: str, document_name: str, citation: Citation) -> bool:
        doc_id = uuid.uuid4()
        doc_entity = DocumentEntity(self.corpus_ID, doc_id, document_name, document)

        ctx.corpus_metadata.insert_document_metadata(self.corpus_ID, doc_id, document_name, citation)

        # Divide longer documents for document store
        segment_document(document)
        return ctx.corpus_doc.save_document(doc_entity) and ctx.corpus_vec.save_document(doc_entity)


    """
    The most basic search of a document store via Elastic Search and a Vector DB
    via ANN. Combines the result via a simple concatenation.
    """
    def search(self, clue: str) -> list[tuple[str, Citation]]:
        # TODO : Replace the fields that constrain and describe the search with a SearchSettings Object
        # that can be passed in
        vector_search_count : int = 10    

        doc_store_results: list[tuple[str, Citation]] = []
        temp_res = ctx.corpus_doc.search_corpus(self.corpus_ID, clue)
        # Search the document store 
        for score, doc_entity in temp_res :
            document_text = doc_entity.document
            citation = ctx.corpus_metadata.get_document_citation(self.corpus_ID, doc_entity.document_id)

            doc_store_results.append([score, document_text, citation])
            

        # Search for the vectors
        vec_store_results: list[tuple[str, Citation]] = []
        temp_res2 = ctx.corpus_vec.search(self.corpus_ID, clue) 
        for score, doc_entity, start_index, end_index in temp_res2 :

            # Verify that the text recovered from the vectors fits the maximum sentence criteria
            if end_index - start_index != len(doc_entity.document) :
                # TODO : Create function to fetch the rest of the sentence from the document DB
                print("Sentence too long and full fetch not implemented")
                raise SentenceLengthOverflowException(end_index - start_index)

            citation = ctx.corpus_metadata.get_document_citation(self.corpus_ID, doc_entity.document_id)

            vec_store_results.append([score, doc_entity.document, citation])

        # Combine the results and remove duplicates
        results = normalize_and_combine(doc_store_results, vec_store_results)

        return results




    def generate_search_instructions(self, clue: str) -> any:
        pass



def normalize_and_combine(doc_results : list, vec_results : list) :
    # normalization with assumption that top score matches are approximately equal

    # Vec scores are based on distance, so smaller is better. Need to inverse the
    # order to be comparable to something like elastic search where bigger is better
    # Multiply by -1 and add by Max of the list.
    doc_scores = ([x for [x,y,z] in doc_results])
    vec_scores = ([x for [x,y,z] in vec_results])

    doc_max_score = max(doc_scores)
    doc_min_score = min(doc_scores)

    vec_max_score = max(vec_scores)
    vec_min_score = min(vec_scores)

    # Normalize and shift all results to be between 0 and 1, with 1 being best responses and 0 being worst  
    doc_results_normalized = [[(x - doc_min_score) / (doc_max_score - doc_min_score) ,y,z] for [x,y,z] in doc_results]
    vec_results_normalized = [[(vec_max_score - x) / (vec_max_score - vec_min_score),y,z] for [x,y,z] in vec_results]

    # Remove duplicates and merge
    # TODO : replace this with a way to preserve and reward good scoring

    # TODO: This rewards longer documents since they are m
    # Reward documents that contain high scoring vectors and remove the searched vector.

    # TODO : Check that this isn't super slow for larger documents and more search results

    # Was considering adjusting the score reward by the document length when a document
    # has a vector within it. Idea was longer docs share more sentences, so they're over rewarded.
    # That might just mean its a good document, so it should recieve that score increase.
    # avg_doc_len = reduce(lambda x, y : len(x[1]) + len(y[1]), doc_results_normalized)

    duplicate_vec_indicies = []
    doc_index = 0
    for doc_score, doc_text, doc_citation in doc_results_normalized : 
        vec_index = 0
        
        for vec_score, vec_text, vec_citation in vec_results_normalized : 
            if(vec_text in doc_text) :
                duplicate_vec_indicies.append(vec_index)
                doc_score = doc_score + vec_score
            vec_index = vec_index + 1

        doc_results_normalized[doc_index][0] = doc_score 
        doc_index = doc_index + 1

    unique_vectors = [i for j, i in enumerate(vec_results_normalized) if j not in duplicate_vec_indicies]

    doc_results_normalized.extend(unique_vectors)

    # Sort by descending scoring so best results come first
    doc_results_normalized.sort(key=lambda x: x[0], reverse=True)

    #print("When normalized merged and sorted the results are : ")
    #print(doc_results_normalized)

    # Cutoff by maximum character limits

    results = [(y,z) for [x,y,z] in doc_results_normalized]
    # Once scores are of same magnitude 
    return results