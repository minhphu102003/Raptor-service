from app.config import settings
from db.session import build_session_factory
from interfaces_adaptor.gateways.file_source import FileSourceHybrid
from mcp.raptor_mcp_server import RaptorMCPService
from repositories.document_repo_pg import DocumentRepoPg
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

    def get_mcp_service(self):
        """Get the MCP service instance"""
        return self.mcp_service
