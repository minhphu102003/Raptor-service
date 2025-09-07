from app.config import settings
from db.session import build_session_factory
from interfaces_adaptor.gateways.file_source import FileSourceHybrid
from mcp_local.raptor_mcp_server import RaptorMCPService
from repositories.dataset_repo_pg import DatasetRepoPg
from repositories.document_repo_pg import DocumentRepoPg
from repositories.retrieval_repo import RetrievalRepo
from repositories.tree_repo_pg import TreeRepoPg
from services.document.document_service import DocumentService
from services.providers.langchain.langchain_chunker import LangChainChunker
from uow.sqlalchemy_uow import SqlAlchemyUnitOfWork


class Container:
    def __init__(self, orm_async_dsn: str, vector_dsn: str):
        self.file_source = FileSourceHybrid()
        self.vector_cfg = settings.vector
        self.vector_dsn = vector_dsn
        self.session_factory = build_session_factory(orm_async_dsn)

        self.chunker = LangChainChunker()
        self.chunk_fn = self.chunker.build()

        # Initialize MCP service
        self.mcp_service = RaptorMCPService(self)

    def make_uow(self) -> SqlAlchemyUnitOfWork:
        return SqlAlchemyUnitOfWork(self.session_factory)

    def make_doc_repo(self, uow: SqlAlchemyUnitOfWork) -> DocumentRepoPg:
        return DocumentRepoPg(uow)

    def make_retrieval_repo(self, uow: SqlAlchemyUnitOfWork) -> RetrievalRepo:
        return RetrievalRepo(uow)

    def make_tree_repo(self, uow: SqlAlchemyUnitOfWork) -> TreeRepoPg:
        return TreeRepoPg(uow.session)

    def make_dataset_repo(self, uow: SqlAlchemyUnitOfWork) -> DatasetRepoPg:
        return DatasetRepoPg(uow.session)

    def make_document_service(self) -> DocumentService:
        return DocumentService(self)

    def get_mcp_service(self):
        """Get the MCP service instance"""
        return self.mcp_service
