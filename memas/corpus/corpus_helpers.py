import re
"""
Breaks up a document into smaller pieces - preferably parapgraphs if the document is
well-structured. 
Returns a list of substrings of the larger document.
"""


def segment_document(document: str, max_characters_per_chunk: int, word_search_size=15):
    word_chunks = []

    # Assumes well formed documents where newlines or tabs are the dividing lines for paragraphs
    first_split = list(filter(lambda x: x != "", re.split(r'[\t\n\r]+\s*', document)))

    # TODO : Might want to implement check to see if badly formed inputs with excessive spacing
    # get overly divided. Also might want to look into better division based on semantics in future.

    # Goes over every piece and breaks up large pieces at sentence boundaries if possible
    for word_chunk in first_split:
        start_index = 0
        if len(word_chunk) > max_characters_per_chunk:

            while start_index < len(word_chunk) - max_characters_per_chunk:
                # end_index_offset = 0
                # If there is a sentence ending mark, use that as basis for spliting
                matches = list(re.finditer(
                    r'[\.?!]+\s*', word_chunk[start_index: start_index + max_characters_per_chunk]))
                if len(matches) > 0:
                    end_index_offset = matches[-1].end()

                # If there are no sentece ending marks, just split on word boundary
                else:
                    end_index = word_chunk.find(" ", max(0, start_index + max(0, max_characters_per_chunk - word_search_size)),
                                                min(start_index + max_characters_per_chunk, len(word_chunk)))

                    # If there is no word boundary, split word
                    if (end_index < 0):
                        end_index = start_index + max_characters_per_chunk

                    end_index_offset = end_index - start_index

                word_chunks.append(word_chunk[start_index: start_index + end_index_offset])
                start_index = start_index + end_index_offset

        # Add terminating chunk
        word_chunks.append(word_chunk[start_index:])

    return word_chunks
