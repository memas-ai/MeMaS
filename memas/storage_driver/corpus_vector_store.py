from dataclasses import dataclass
import logging
import sys
import numpy as np
import uuid
import sys
import json
import time
import os
import asyncio
from collections import defaultdict
from typing import Dict
from pymilvus import (
    connections,
    FieldSchema,
    CollectionSchema,
    DataType,
    Collection,    
    utility,
    BulkInsertState,
)
from minio import Minio
from minio.error import S3Error
from memas.encoder.universal_sentence_encoder import USE_VECTOR_DIMENSION, USETextEncoder
from memas.interface.storage_driver import CorpusVectorStore, DocumentEntity
from memas.text_parsing.text_parsers import split_doc
from datetime import datetime
import aiofiles
from time import sleep

_log = logging.getLogger(__name__)

LOCAL_FILES_PATH = "tmp/"

#minio
DEFAULT_BUCKET_NAME = "a-bucket"
MINIO_ADDRESS = "127.0.0.1:9000"
MINIO_SECRET_KEY = "minioadmin"
MINIO_ACCESS_KEY = "minioadmin"

USE_COLLECTION_NAME = "corpus_USE_sentence_store"


CORPUS_FIELD = "corpus_id"
DOCUMENT_NAME = "document_name"
EMBEDDING_FIELD = "embedding"
START_FIELD = "start_index"
END_FIELD = "end_index"
TEXT_PREVIEW = "text_preview"

MAX_TEXT_LENGTH = 1024
MAX_NUM_DOCS_INSERT = 128


fields = [
    # The first 32 length is the document id, while the later 32 is the sentence id.
    # the sentence id is just used to avoid key collision.
    FieldSchema(name="composite_id", dtype=DataType.VARCHAR,
                max_length=64, is_primary=True, auto_id=False),
    FieldSchema(name=CORPUS_FIELD, dtype=DataType.VARCHAR,
                max_length=32, is_partition_key=True),
    FieldSchema(name=DOCUMENT_NAME, dtype=DataType.VARCHAR,
                max_length=256),
    FieldSchema(name="text_preview", dtype=DataType.VARCHAR, max_length=MAX_TEXT_LENGTH),
    FieldSchema(name=EMBEDDING_FIELD, dtype=DataType.FLOAT_VECTOR, dim=USE_VECTOR_DIMENSION),
    FieldSchema(name=START_FIELD, dtype=DataType.INT64),
    FieldSchema(name=END_FIELD, dtype=DataType.INT64),
]
sentance_schema = CollectionSchema(
    fields, "Corpus Vector Table for storing Universal Sentence Encoder embeddings")


@dataclass
class USESentenceObject:
    composite_id: str
    corpus_id: str
    document_name: str
    text_preview: str
    embedding: np.ndarray
    start_index: int
    end_index: int

    def to_data(self):
        return [[self.composite_id], [self.corpus_id], [self.document_name], [self.text_preview], self.embedding, [self.start_index], [self.end_index]]


def hash_sentence_id(document_id: uuid.UUID, sentence: str) -> uuid.UUID:
    return uuid.uuid5(document_id, sentence)


def convert_batch(objects: list[USESentenceObject]):
    composite_ids, corpus_ids, document_names, text_previews, embeddings, start_indices, end_indices = [], [], [], [], [], [], []
    for obj in objects:
        composite_ids.append(obj.composite_id)
        corpus_ids.append(obj.corpus_id)
        document_names.append(obj.document_name)
        text_previews.append(obj.text_preview)
        embeddings.append(obj.embedding)
        start_indices.append(obj.start_index)
        end_indices.append(obj.end_index)

    return [composite_ids, corpus_ids, document_names, text_previews, np.row_stack(embeddings), start_indices, end_indices]


class MilvusUSESentenceVectorStore(CorpusVectorStore):
    def __init__(self) -> None:
        super().__init__(USETextEncoder())
        self.collection: Collection

    def first_init(self):
        self.collection: Collection = Collection(USE_COLLECTION_NAME, sentance_schema)
        index = {
            "index_type": "FLAT",
            "metric_type": "L2",
            "params": {},
        }
        self.collection.create_index(EMBEDDING_FIELD, index)
        self.collection.load()
        self.encoder.init()

    def init(self):
        self.collection: Collection = Collection(USE_COLLECTION_NAME, sentance_schema)
        self.collection.load()
        self.encoder.init()

    def search_corpora(self, corpus_ids: list[uuid.UUID], clue: str) -> list[tuple[float, DocumentEntity, int, int]]:
        _log.debug(f"Searching vectors for [corpus_ids={corpus_ids}]")
        _log.handlers

        vec_search_count = 100
        # Create boolean expression to match all data in the corpus set
        filter_str = ""
        for corpus_id in corpus_ids:
            filter_str += f"{CORPUS_FIELD} == \"{corpus_id.hex}\" ||"

        # Remove last OR
        filter_str = filter_str[:-2]

        clue_split = split_doc(clue, MAX_TEXT_LENGTH)
        result = self.collection.search([x.tolist() for x in self.encoder.embed_multiple(clue_split)], EMBEDDING_FIELD, param={},
                                        limit=vec_search_count, expr=filter_str,
                                        output_fields=[CORPUS_FIELD, START_FIELD, END_FIELD, DOCUMENT_NAME, TEXT_PREVIEW])
        output = []
        for hits in result:
            for hit in hits:
                doc_entity = DocumentEntity(uuid.UUID(hit.entity.corpus_id), uuid.UUID(
                    hit.id[:32]), hit.entity.document_name, hit.entity.text_preview)
                output.append((hit.distance, doc_entity, hit.entity.start_index, hit.entity.end_index))
        return output

    def save_documents(self, doc_entities: list[DocumentEntity]) -> bool:
        # Need to split up huge batches to meet packetsize limits
    
        _log.debug(f"Saving vectors for [corpus_ids={[x.corpus_id for x in doc_entities]}]")
        
        # Need to insert such that the size of any insert operation doesnt exceed 512 MB (Milvus Insert limit)
        char_byte_count = 2
        # Rough approximation with safety factor of 2 for memory
        embedding_size = 2160
        # _log.debug(f"Embedding size ndarray is = {sys.getsizeof(sentence_embeddings[0][0])}")
        max_obj_size = 2 *( (char_byte_count * (MAX_TEXT_LENGTH + 256 + 32 + 64)) + embedding_size)
        max_insert_size_bytes = 20000000
        batch_size = 0
        insert_count = 0
        current_batch = []

        doc_index = 0
        total_sentence_count = 0

        for doc_entity in doc_entities:
            doc_sentences = split_doc(doc_entity.document, MAX_TEXT_LENGTH)
            sentence_embeddings = [[1.0 for x in range(512)] for doc in doc_sentences] # self.encoder.embed_multiple(doc_sentences) 

            _log.debug(f"Doc sentences is = {doc_sentences}")
            max_size_for_doc = len(doc_sentences) * max_obj_size
            total_sentence_count = total_sentence_count + len(doc_sentences)

            # TODO : Put limit on massive files here
            if max_size_for_doc > max_insert_size_bytes :
                # Run more thorough check on size then decide to accept or reject
                _log.error(f"Document Recieved too large")

            #  If adding the objects for this document to the batch makes it too large, send batch and restart
            if(batch_size + max_size_for_doc > max_insert_size_bytes) :
                _log.debug(f"Hit a memory bound and inserted {len(current_batch)} more sentences.")
                insert_count = insert_count + self.collection.insert(convert_batch(current_batch)).insert_count
                current_batch = []


                batch_size = 0

            start = 0
            sentence_index = 0
            for sentence in doc_sentences:
                # _log.debug(f"Inserted {sentence} within LOOP")
                # deterministically generate the sentence id, so we can later get/delete them
                sentence_id = hash_sentence_id(doc_entity.document_id, sentence)
                composite_id = doc_entity.document_id.hex + sentence_id.hex
                end = start + len(sentence)
                current_batch.append(USESentenceObject(composite_id, doc_entity.corpus_id.hex, doc_entity.document_name,
                                                 sentence[:MAX_TEXT_LENGTH], sentence_embeddings[sentence_index], start, end))
                sentence_index = sentence_index + 1
                start = end

            batch_size = batch_size + max_size_for_doc

            doc_index = doc_index + 1

        # Insert whatever remains
        insert_count = insert_count + self.collection.insert(convert_batch(current_batch)).insert_count

        _log.debug(f"Inserted {insert_count} sentences of the object total = {total_sentence_count}")
        return (insert_count == total_sentence_count) 
    
    async def bulk_save_documents(self, doc_entities: list[DocumentEntity]) -> bool:
        # TODO: There is a 16 GB limit on the JSON file that can be uploaded to Milvus, and their bulk file
        # writer requires only 1 JSON file at a time. Need to split VERY LARGE bulk inserts into multiple files


        # Need to split up huge batches to meet packetsize limits
        path = LOCAL_FILES_PATH + "onefornow.json" # datetime.utcnow().strftime('%Y-%m-%d:%H:%M:%S:%f')[:-3] + ".json"
        if os.path.exists(path):
            os.remove(path)
    
        _log.debug(f"Saving vectors for [corpus_ids={[x.corpus_id for x in doc_entities]}]")
        
        # Need to insert such that the size of any insert operation doesnt exceed 512 MB (Milvus Insert limit)
        char_byte_count = 2
        # Rough approximation with safety factor of 2 for memory
        embedding_size = 2160
        # _log.debug(f"Embedding size ndarray is = {sys.getsizeof(sentence_embeddings[0][0])}")
        max_obj_size = 2 *( (char_byte_count * (MAX_TEXT_LENGTH + 256 + 32 + 64)) + embedding_size)
        max_insert_size_bytes = 2000000000
        batch_size = 0
        insert_count = 0
        current_batch = []
        partition_name = ""

        doc_index = 0
        total_sentence_count = 0

        # List of Async File Write Tasks
        file_write_tasks = set()

        for doc_entity in doc_entities:
            partition_name = doc_entity.corpus_id.hex
            doc_sentences = split_doc(doc_entity.document, MAX_TEXT_LENGTH)
            sentence_embeddings = [[1.0 for x in range(512)] for doc in doc_sentences] # self.encoder.embed_multiple(doc_sentences) 

            max_size_for_doc = len(doc_sentences) * max_obj_size
            total_sentence_count = total_sentence_count + len(doc_sentences)

            # TODO : Put limit on massive files here
            if max_size_for_doc > max_insert_size_bytes :
                # Run more thorough check on size then decide to accept or reject
                _log.error(f"Document Recieved too large")

            #  If adding the objects for this document to the batch makes it too large, send batch and restart
            if(batch_size + max_size_for_doc > max_insert_size_bytes) :
                _log.debug(f"Hit a memory bound and inserted {len(current_batch)} more sentences.")
                current_batch = []
                task = asyncio.create_task(write_json_to_file(current_batch, path))
                file_write_tasks.add(task)

                batch_size = 0

            start = 0
            sentence_index = 0
            for sentence in doc_sentences:
                # _log.debug(f"Inserted {sentence} within LOOP")
                # deterministically generate the sentence id, so we can later get/delete them
                sentence_id = hash_sentence_id(doc_entity.document_id, sentence)
                composite_id = doc_entity.document_id.hex + sentence_id.hex
                end = start + len(sentence)
                current_batch.append(USESentenceObject(composite_id, doc_entity.corpus_id.hex, doc_entity.document_name,
                                                 sentence[:MAX_TEXT_LENGTH], sentence_embeddings[sentence_index], start, end))
                sentence_index = sentence_index + 1
                start = end

            batch_size = batch_size + max_size_for_doc

            doc_index = doc_index + 1

        # Insert whatever remains
        task = asyncio.create_task(write_json_to_file(current_batch, path))
        file_write_tasks.add(task)

        # Wait for all filewrites to complete
        await asyncio.gather(*file_write_tasks)

        _log.debug(f"Inserted {insert_count} sentences of the object total = {total_sentence_count}")

        # Bulk insert full file, currently assumes all files belong to same partition
        # TODO : Support multiple partitions to upload to multiple corpora
        await bulk_insert_rowbased(self.collection, partition_name)
        return (insert_count == total_sentence_count) 
    
async def write_json_to_file(batch, file_path):
    rows = []
    for i in range(len(batch)):
        obj = batch[i]
        rows.append({
            "composite_id": obj.composite_id, # id field
            CORPUS_FIELD: obj.corpus_id,
            DOCUMENT_NAME: obj.document_name,
            "text_preview": obj.text_preview,
            EMBEDDING_FIELD: obj.embedding,
            START_FIELD: obj.start_index,
            END_FIELD: obj.end_index,
        })

    data = {
        "rows": rows,
    }

    # async with aiofiles.open(file_path, mode='a') as json_file:
    #     await json_file.write(json.dumps(data))


    with open(file_path, "a") as json_file:
        json.dump(data, json_file)


# Upload data files to minio
def upload(data_folder: str,
           bucket_name: str=DEFAULT_BUCKET_NAME)->(bool, list):
    if not os.path.exists(data_folder):
        print("Data path '{}' doesn't exist".format(data_folder))
        return False, []

    remote_files = []
    try:
        print("Prepare upload files")
        minio_client = Minio(endpoint=MINIO_ADDRESS, access_key=MINIO_ACCESS_KEY, secret_key=MINIO_SECRET_KEY, secure=False)
        found = minio_client.bucket_exists(bucket_name)

        if not found:
            print("MinIO bucket '{}' doesn't exist".format(bucket_name))
            return False, []
        else :
            print("MinIO bucket found!!!")

        remote_data_path = "milvus_bulkinsert"
        def upload_files(folder:str):
            for parent, dirnames, filenames in os.walk(folder):
                if parent is folder:
                    for filename in filenames:
                        ext = os.path.splitext(filename)
                        if len(ext) != 2 or (ext[1] != ".json" and ext[1] != ".npy"):
                            continue
                        local_full_path = os.path.join(parent, filename)
                        minio_file_path = os.path.join(remote_data_path, os.path.basename(folder), filename)
                        minio_client.fput_object(bucket_name, minio_file_path, local_full_path)
                        print("Upload file '{}' to '{}'".format(local_full_path, minio_file_path))
                        remote_files.append(minio_file_path)
                    for dir in dirnames:
                        upload_files(os.path.join(parent, dir))

        upload_files(data_folder)

    except S3Error as e:
        print("Failed to connect MinIO server {}, error: {}".format(MINIO_ADDRESS, e))
        return False, []

    print("Successfully upload files: {}".format(remote_files))
    return True, remote_files

async def bulk_insert_rowbased(collection, partition_name):
    # make sure the files folder is created
    os.makedirs(name=LOCAL_FILES_PATH, exist_ok=True)
    
    ok, remote_files = upload(data_folder=LOCAL_FILES_PATH)
    
    task_ids = []
    if ok:
        collection.create_partition(partition_name)
        print("Import row-based file:", remote_files)
        task_id = utility.do_bulk_insert(collection_name=USE_COLLECTION_NAME,
                                    partition_name=partition_name,
                                    files=remote_files)
        task_ids.append(task_id)

    await wait_tasks_competed(task_ids)

async def wait_tasks_to_state(task_ids, state_code):
    wait_ids = task_ids
    states = []
    while True:
        asyncio.sleep(2)
        temp_ids = []
        for id in wait_ids:
            state = utility.get_bulk_insert_state(task_id=id)
            if state.state == BulkInsertState.ImportFailed or state.state == BulkInsertState.ImportFailedAndCleaned:
                print(state)
                print("The task", state.task_id, "failed, reason:", state.failed_reason)
                continue

            if state.state >= state_code:
                states.append(state)
                continue

            temp_ids.append(id)

        wait_ids = temp_ids
        if len(wait_ids) == 0:
            break;
        print("Wait {} tasks to be state: {}. Next round check".format(len(wait_ids), BulkInsertState.state_2_name.get(state_code, "unknown")))

    return states

async def wait_tasks_competed(task_ids):
    print("=========================================================================================================")
    states = await wait_tasks_to_state(task_ids, BulkInsertState.ImportCompleted)
    complete_count = 0
    for state in states:
        if state.state == BulkInsertState.ImportCompleted:
            complete_count = complete_count + 1
        # print(state)
        # if you want to get the auto-generated primary keys, use state.ids to fetch
        # print("Auto-generated ids:", state.ids)

    print("{} of {} tasks have successfully generated segments, able to be compacted and indexed as normal".format(complete_count, len(task_ids)))
    print("=========================================================================================================\n")
    return states


SINGLETON: CorpusVectorStore = MilvusUSESentenceVectorStore()
