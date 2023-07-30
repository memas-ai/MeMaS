import uuid
import time
import re
from memas.storage_driver.corpus_vector_store import hash_sentence_id
from memas.storage_driver.corpus_vector_store import split_doc


def test_sentence_id_determinism():
    document_id = uuid.uuid4()
    sentence = "Let's see if this hash generation is actually deterministic!"

    sentence_id1 = hash_sentence_id(document_id, sentence)
    sentence_id2 = hash_sentence_id(document_id, sentence)

    time.sleep(1)
    sentence_id3 = hash_sentence_id(document_id, sentence)

    assert sentence_id1 == sentence_id2
    assert sentence_id1 == sentence_id3

def test_sentence_splitting() :
    # Test well formed docs.
    doc = " THis is a document that is well formed. Short and sweet sentences! Splitting should be no problem. Right?"
    max_sen_len = 100
    sentences = split_doc(doc, max_sen_len)
    assert len(sentences) == 4

    # Test that sentences terminate on proper punctuation
    regexp = re.compile(r'[\.?!]\s*')
    bools = [regexp.search((x.strip())[-1:]) for x in sentences]
    for x in bools :
        assert x
    assert(len(bools) >= len(doc) / max_sen_len)

    # Test that runon sentences don't split on the word if it isn't too long
    doc2 = "There is a total of no sentence division points expected in this text, That is intended Anything more or less is bad, but I need to have sentence boundaries respected, Who doesn't like respect after all"
    max_seg_size = 50
    sentences = split_doc(doc2, max_seg_size)
    words = list(filter(lambda x: x != ' ' and x != None, re.split(r"(\s+)|([\.!?]\s*)", doc2)))
    print("words are : ")
    print(words)

    # Every word should appear intact in one of the segments
    word_list = ""
    for sentence in sentences :
        word_list = word_list + sentence

    print("wordList is :")
    print(word_list)

    for word in words :
        if word not in word_list : 
            print("about to print WRODS")
            print(word)
            assert False