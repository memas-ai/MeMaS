import enum
import dataclasses
import http.client
import json


class CorpusType(enum.Enum):
    KNOWLEDGE = "knowledge"
    CONVERSATION = "conversation"

@dataclasses.dataclass
class Citation:
    source_uri: str
    source_name: str
    description: str = ""
@dataclasses.dataclass
class CitedInformation:
    document: str
    citation: Citation

class Client:
    __JSON_HEADER = {'Content-type': 'application/json'}

    def __init__(self, host: str, port: int, namespace_pathname : str) -> None:
        self.connection = http.client.HTTPConnection(host=host, port=port)
        self.endpoint_prefix = "/cp"
        self.namespace_pathname = namespace_pathname

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

    # TODO : Sould corpus_path be a parameter? Probably not
    def batch_remember(self, corpus_name: str, info_list: [CitedInformation]) -> bool:
        # TODO verify asdict works recursively
        dict_list = []
        for info_pair in info_list :
            json_subdict = dataclasses.asdict(info_pair)
            dict_list.append(json_subdict)
            
        json_dict = {}
        json_dict["cited_documents"] = dict_list
        json_dict['corpus_pathname'] = f"{self.namespace_pathname}:{corpus_name}"
        json_data = json.dumps(json_dict)
        self.connection.request('POST', self.endpoint_prefix + '/batch_remember', json_data, Client.__JSON_HEADER)

        response = self.connection.getresponse()
        json_str = response.read().decode()
        json_response = json.loads(json_str)

        return json_response["success"]
    