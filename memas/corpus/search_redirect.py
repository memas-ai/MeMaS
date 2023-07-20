from uuid import UUID
from memas.storage_driver.memas_metadata import MemasMetadataStore
from dataclasses import dataclass


@dataclass
class SearchSettings:
    max_char_returned: int = 1000
    search_alg_ID: str = "basic"
    # Measure of computation dedicated to searching, e.g. how many neighbors to check
    search_depth: int = 10

"""
Handles a user request for data search by matching what kind of search they are trying to use,
and for which corpuses. Once determined, it invokes the desired search algorithm over the 
proper corpuses 
"""
def search_redirect(userID : UUID, searchQuery : str) :
    # Search metadata for the corpuses that are registered with the customer
    # TODO need function to extract corpus specific info for the user from MetDataStore
    list_corpus_IDs = MemasMetadataStore.get_corpuses_by_userID(userID)

    # Find Search Settings for the user 
    # TODO : Implement a way to allow different users to have customizable searches criteria
    # TODO : Consider allowing Corpus specific search settings
    settings = MemasMetadataStore.get_user_search_settings(userID)

    for corpusID in list_corpus_IDs :
        corpus_search(corpusID, str, settings)


def corpus_search(corpusID : UUID, clue : str, settings : SearchSettings):
    pass


    