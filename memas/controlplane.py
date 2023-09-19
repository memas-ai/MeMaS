from flask import Blueprint, current_app, request
from memas.context_manager import ctx
from memas.interface.corpus import CorpusType
from memas.interface.corpus import Citation, Corpus

controlplane = Blueprint("cp", __name__, url_prefix="/cp")


@controlplane.route('/create_user', methods=["POST"])
def create_user():
    namespace_pathname = request.json["namespace_pathname"]

    current_app.logger.info(f"Create user [namespace_pathname=\"{namespace_pathname}\"]")

    ctx.memas_metadata.create_namespace(namespace_pathname)
    return {"success": True}


@controlplane.route('/create_corpus', methods=["POST"])
def create_corpus():
    corpus_pathname = request.json["corpus_pathname"]
    corpus_type = request.json.get("corpus_type", CorpusType.CONVERSATION.value)

    current_app.logger.info(f"Create corpus [corpus_pathname=\"{corpus_pathname}\"] [corpus_type={corpus_type}]")

    if corpus_type == CorpusType.CONVERSATION.value:
        ctx.memas_metadata.create_conversation_corpus(corpus_pathname)
    elif corpus_type == CorpusType.KNOWLEDGE.value:
        ctx.memas_metadata.create_knowledge_corpus(corpus_pathname)
    else:
        current_app.logger.error(f"Corpus type not supported [corpus_type={corpus_type}]")
        raise NotImplementedError(f"Corpus Type '{corpus_type}' not supported")
    return {"success": True} 

@controlplane.route('/batch_memorize',methods=["POST"])
def batch_memorize():
    
    #current_app.logger.info(f"memorize")
    corpus_pathname:str = request.json["corpus_pathname"]
    cited_documents: list = request.json["cited_documents"]
    
    #current_app.logger.info(f"corpus_pathname {corpus_pathname}]")
    corpus_info = ctx.memas_metadata.get_corpus_info(corpus_pathname)
    
    current_app.logger.info(f"Batch memorize information in corpus_pathname {corpus_pathname}]")
    success=True
    for dict in cited_documents: #document_name must exist here
        document=dict.get("document","")
        raw_citation = dict.get("citation","")
        document_name=raw_citation.get("document_name", "") 
        
        current_app.logger.info(f"Memorizing [corpus_pathname=\"{corpus_pathname}\"] [document_name=\"{document_name}\"]")
        
        citation = Citation(source_uri=raw_citation.get("source_uri", ""),
                            source_name=raw_citation.get("source_name", ""),
                            description=raw_citation.get("description", ""),
                            document_name=document_name)
        
        corpus: Corpus = ctx.corpus_provider.get_corpus(corpus_info.corpus_id,corpus_type=corpus_info.corpus_type)
        if corpus.store_and_index(document,citation)==False:
            success=False
            current_app.logger.info(f"Memorize failed for {document_name}]")
            
    current_app.logger.info(f"Memorize finished [success={success}]")
    return {"success": success}
