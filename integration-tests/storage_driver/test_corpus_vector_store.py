import numpy as np
import uuid
from memas.storage_driver.corpus_vector_store import MilvusUSESentenceVectorStore


def test_init(clean_milvus):
    store = MilvusUSESentenceVectorStore()
    store.first_init()


def test_save_then_search(clean_milvus):
    store = MilvusUSESentenceVectorStore()
    store.first_init()
    
    corpus_id = uuid.uuid4()
    document_id1 = uuid.uuid4()
    document_id2 = uuid.uuid4()
    store.save_document(corpus_id, document_id1, "The sun is high. California sunshine is great. ")
    store.save_document(corpus_id, document_id2, "I picked up my phone and then dropped it again")
    
    result = store.search(corpus_id, "The sun is high")
    print(result)
    assert result == True
    # vec = store._embed(["XDDDD"])
    # print(vec.shape)
    # print(np.row_stack([vec, vec]).shape)
    # assert type(store._embed(["XDDDD"])) == True
