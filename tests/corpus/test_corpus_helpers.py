import re
from memas.text_parsing.text_parsers import segment_document


def test_document_segmentation():

    # Test1 : Every newline or tab or combination breaks the string at that point
    doc1 = "There is a \n total of \t\n 6 division points expected in this \t sentence. \n\t That is intended. \n\n Anything more \t or less is bad."
    segments = segment_document(doc1, 150)
    assert len(segments) == 7

    # Test2: Strings that are not easily divided by paragraph markers respect sentence boundaries.
    doc2 = "There is a total of no natural division points expected in this text. That is intended! Anything more or less is bad, but I need to have sentence boundaries respected. Who doesn't like respect after all?"
    max_seg_size = 100
    segments2 = segment_document(doc2, max_seg_size)
    regexp = re.compile(r'[\.?!]\s*')

    # Last character besides spaces should contain the punctuation mark
    bools = [regexp.search((x.strip())[-1:]) for x in segments2]
    print(bools)
    print(segments2)
    for x in bools:
        assert x
    assert (len(bools) >= len(doc2) / max_seg_size)

    # Test3: Strings that are not easily divided by sentence markers respect word boundaries.
    doc3 = "There is a total of no sentence division points expected in this text, That is intended Anything more or less is bad, but I need to have sentence boundaries respected, Who doesn't like respect after all"
    max_seg_size = 50
    segments = segment_document(doc3, max_seg_size)
    words = list(filter(lambda x: x != ' ' and x != None, re.split(r"(\s+)|([\.!?]\s*)", doc3)))
    print("words is : ")
    print(words)
    # Every word should appear intact in one of the segments
    word_list = ""
    for segment in segments:
        word_list = word_list + segment

    print("wordList is :")
    print(word_list)

    for word in words:
        if word not in word_list:
            print("about to print WRODS")
            print(word)
            assert False

    # Test that there are not too few segments
    assert (len(segments) >= len(doc3) / max_seg_size)
    # Test that individual segments are not too long
    for segment in segments:
        assert (len(segment) <= max_seg_size)

    # Test that in the worst case a word gets divided anyway
    doc4 = "asdasdoijwernwernaidsaodiajsdoiajsodijaosdijasoidjaosidjoasidja After this, text works. No need to fret."
    max_seg_size = 25
    segments = segment_document(doc4, max_seg_size)
    print("Segments of badly formatted text are  :")
    print(segments)
    # Test that there are not too few segments
    assert (len(segments) >= len(doc4) / max_seg_size)
    # Test that individual segments are not too long
    for segment in segments:
        assert (len(segment) <= max_seg_size)
    # Test that long malformed text splits included all characters
    assert segments[0] + segments[1] + segments[2] == doc4.split(" ")[0]
