import re
import logging
from nltk.tokenize import sent_tokenize


_log = logging.getLogger(__name__)


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


"""
Divides the provided string document into sentences no longer than max_text_len each. 
Returns the split document as a list of strings.
"""
def split_doc(document: str, max_text_len) -> list[str]:
    # Divide into sentences
    first_split = sent_tokenize(document)

    final_sentences = []
    # Any "sentence" longer than max_text_len characters gets split further. Splits are attempted
    # at word boundaries. Words longer than word_search_size that lie exactly on the boundary of a segment
    # are not guaranteed to be unsplit. Input is too malformed at that point, so just split whereever.
    for segment in first_split:
        if (len(segment) < max_text_len):
            final_sentences.append(segment)
        else:
            segment_index = 0
            word_search_size = 25

            # Case 1: Find start and end word boundaries on both sides for all middle sentences
            while segment_index < len(segment) - max_text_len:
                end_index = segment_index + max_text_len
                space_index_end = segment.find(" ", max(0, end_index - word_search_size),
                                               min(end_index, len(segment)))

                # If a word boundary at end is found reassign index to accomodate.
                if space_index_end > 0:
                    end_index = space_index_end

                new_segment = segment[segment_index: end_index]
                final_sentences.append(new_segment)
                segment_index = end_index

            # Case 2: Find boundary for last sentence.
            final_segment_start_index = min(len(segment), len(segment) - max_text_len + word_search_size)
            last_chunk_space_index = segment.find(" ", max(0, final_segment_start_index - word_search_size),
                                                  final_segment_start_index)

            if last_chunk_space_index > 0:
                final_segment_start_index = last_chunk_space_index

            # TODO : On Search, Need to combine last fragment with previous if both are present
            final_sentences.append(segment[final_segment_start_index:])

    return final_sentences
