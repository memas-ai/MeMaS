import time


def test_memorize_then_recall(test_client):
    namespace_pathname = "memorize"
    corpus_pathname = namespace_pathname + ":memorize_1"
    resp1 = test_client.post("/cp/user", json={"namespace_pathname": namespace_pathname})
    print(resp1)
    resp2 = test_client.post("/cp/corpus", json={"corpus_pathname": corpus_pathname, "namespace_pathname": namespace_pathname})
    print(resp2)

    resp3 = test_client.post(
        "/dp/memorize", json={"corpus_pathname": corpus_pathname, "document": "What's MeMaS", "citation": {}})
    assert resp3.status_code == 200
    assert resp3.json["success"]

    time.sleep(1)

    resp4 = test_client.get("/dp/recall", json={"namespace_pathname": namespace_pathname, "clue": "What's MeMaS"})
    assert resp4.status_code == 200
    assert len(resp4.json) == 1
    assert resp4.json[0]["document"] == "What's MeMaS"
