import numpy as np
import uuid
import time
from memas.interface.storage_driver import DocumentEntity
from memas.storage_driver.corpus_vector_store import CorpusVectorStore
from memas.storage_driver import corpus_vector_store, corpus_doc_store, corpus_doc_metadata
from memas.corpus import basic_corpus
from memas.interface.corpus import Citation

corpus_name = "test corpus1"
test_corpus = basic_corpus.BasicCorpus(uuid.uuid4(), corpus_name)

def test_save_then_search_one_corpus(es_client):
    text1 = "The sun is high. California sunshine is great. "
    text2 = "I picked up my phone and then dropped it again"
    text3 = "The weather is great today"

    assert test_corpus.store_and_index(text1, Citation("", "doc1", corpus_name, ""))
    assert test_corpus.store_and_index(text2, Citation("", "doc2", corpus_name, ""))
    assert test_corpus.store_and_index(text3, Citation("", "doc3", corpus_name, ""))

    time.sleep(1)
    output = test_corpus.search("It is sunny")
    print("OUTPUT IS : ")
    print(output)
    assert "sunshine" in output[0][0]
    assert "weather" in output[1][0]



