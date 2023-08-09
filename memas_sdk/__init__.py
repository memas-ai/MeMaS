import enum
import http.client
import json


class CorpusType(enum.Enum):
    KNOWLEDGE = "knowledge"
    CONVERSATION = "conversation"


class Client:
    __JSON_HEADER = {'Content-type': 'application/json'}

    def __init__(self, host: str, port: int) -> None:
        self.connection = http.client.HTTPConnection(host=host, port=port)
        self.endpoint_prefix = "/cp"

    def close(self):
        self.connection.close()

    def create_user(self, namespace_pathname: str) -> bool:
        json_data = json.dumps({'namespace_pathname': namespace_pathname})
        self.connection.request('POST', self.endpoint_prefix + '/create_user', json_data, Client.__JSON_HEADER)

        response = self.connection.getresponse()
        json_str = response.read().decode()
        json_response = json.loads(json_str)
        return json_response["success"]

    def create_corpus(self, corpus_pathname: str, *, corpus_type: CorpusType = None) -> bool:
        json_dict = {'corpus_pathname': corpus_pathname}
        if corpus_type is not None:
            json_dict['corpus_type'] = corpus_type.value

        json_data = json.dumps(json_dict)
        self.connection.request('POST', self.endpoint_prefix + '/create_corpus', json_data, Client.__JSON_HEADER)

        response = self.connection.getresponse()
        json_str = response.read().decode()
        json_response = json.loads(json_str)
        return json_response["success"]
