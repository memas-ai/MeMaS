import dataclasses
import http.client
import json


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

    def __init__(self, host: str, port: int, namespace_pathname: str) -> None:
        self.connection = http.client.HTTPConnection(host=host, port=port)
        self.endpoint_prefix = "/dp"
        self.namespace_pathname = namespace_pathname

    def close(self):
        self.connection.close()

    def recollect(self, clue: str) -> list[CitedInformation]:
        json_data = json.dumps({'clue': clue, 'namespace_pathname': self.namespace_pathname})
        self.connection.request('POST', self.endpoint_prefix + '/recollect', json_data, Client.__JSON_HEADER)

        response = self.connection.getresponse()
        json_str = response.read().decode()
        json_response = json.loads(json_str)
        return [CitedInformation(d["document"], Citation(d["citation"]["source_uri"], d["citation"]["source_name"], d["citation"]["description"])) for d in json_response]

    def remember(self, corpus_name: str, info: CitedInformation) -> bool:
        # TODO verify asdict works recursively
        json_dict = dataclasses.asdict(info)
        json_dict['corpus_pathname'] = f"{self.namespace_pathname}:{corpus_name}"
        json_data = json.dumps(json_dict)
        self.connection.request('POST', self.endpoint_prefix + '/remember', json_data, Client.__JSON_HEADER)

        response = self.connection.getresponse()
        json_str = response.read().decode()
        json_response = json.loads(json_str)
        return json_response["success"]
