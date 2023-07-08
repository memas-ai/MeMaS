import uuid
import time
from memas.storage_driver.corpus_vector_store import hash_sentence_id


def test_sentence_id_determinism():
    document_id = uuid.uuid4()
    sentence = "Let's see if this hash generation is actually deterministic!"

    sentence_id1 = hash_sentence_id(document_id, sentence)
    sentence_id2 = hash_sentence_id(document_id, sentence)

    time.sleep(1)
    sentence_id3 = hash_sentence_id(document_id, sentence)

    assert sentence_id1 == sentence_id2
    assert sentence_id1 == sentence_id3
