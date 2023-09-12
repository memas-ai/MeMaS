import numpy as np
import uuid
import time
from memas.interface.storage_driver import DocumentEntity
from memas.storage_driver.corpus_vector_store import MilvusUSESentenceVectorStore

store = MilvusUSESentenceVectorStore()


def test_init():
    store.init()


def test_save_then_search2():
    print("before UIDs")
    corpus_id1 = uuid.uuid4()
    corpus_id2 = uuid.uuid4()
    document_id0 = uuid.uuid4()
    document_id1 = uuid.uuid4()
    document_id2 = uuid.uuid4()
    document_id3 = uuid.uuid4()

    best_match_str = "The sun is high. California sunshine is great. "

    store.save_documents([DocumentEntity(corpus_id1, document_id0, "doc0",
                                         "Before This is a runon sentence meant to test the logic of the splitting capabilites but that is only the start, there is nothing that can break this sentecne up other than some handy logic even in the worst case, too bad I only know how to use commas")])
    store.save_documents([DocumentEntity(corpus_id1, document_id1, "doc1",
                                         "The sun is high! California sunshine is great. Did you catch my quest? Oh oh! lol. There is no way this is one sentence.")])
    store.save_documents([DocumentEntity(corpus_id1, document_id2, "doc2",
                                         "I picked up my phone and then dropped it again")])
    store.save_documents([DocumentEntity(corpus_id2, document_id3, "doc3", "The weather is great today")])
    time.sleep(1)

    result = store.search_corpora([corpus_id1], "How's the weather today?")

    # assert False
    # Test that the text recovered for a short sentence matched the expected length
    assert len(result[0][1].document) == result[0][3] - result[0][2]

    # Test that it is the expected sentence
    assert result[0][1].document in best_match_str

    # Test that the result came from the right corpus
    assert result[0][1].corpus_id == corpus_id1

    # Test that the document stored in the other corpus isn't a result
    assert document_id3 not in {t[1].document_id for t in result}
