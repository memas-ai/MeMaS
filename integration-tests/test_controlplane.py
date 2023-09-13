

def test_create_user(test_client):
    resp = test_client.post("/cp/create_user", json={"namespace_pathname": "create_user_1"})
    assert resp.status_code == 200


def test_create_user_existing(test_client):
    test_client.post("/cp/create_user", json={"namespace_pathname": "create_user_2"})
    resp = test_client.post("/cp/create_user", json={"namespace_pathname": "create_user_2"})
    assert resp.status_code == 400
    assert resp.json["error_code"] == "namespace_exists"


def test_create_corpus(test_client):
    resp = test_client.post("/cp/create_corpus", json={"corpus_pathname": "create_user_1:create_corpus_1"})
    assert resp.status_code == 200


def test_create_corpus_existing(test_client):
    test_client.post("/cp/create_corpus", json={"corpus_pathname": "create_user_2:create_corpus_2"})
    resp = test_client.post("/cp/create_corpus", json={"corpus_pathname": "create_user_2:create_corpus_2"})
    assert resp.status_code == 400
    assert resp.json["error_code"] == "namespace_exists"
