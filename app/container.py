from app.config import settings
from infra.chunking.langchain_chunker import LangChainChunker
from infra.db.session import build_session_factory
from infra.uow.sqlalchemy_uow import SqlAlchemyUnitOfWork
from interfaces_adaptor.gateways.file_source import FileSourceHybrid
from interfaces_adaptor.gateways.vector_pgvector import PgVectorIndex
from interfaces_adaptor.repositories.document_repo_pg import DocumentRepoPg


class Container:
    def __init__(self, orm_async_dsn: str, vector_dsn: str):
        self.file_source = FileSourceHybrid()
        self.vector_cfg = settings.vector
        self.vector_dsn = vector_dsn
        self.session_factory = build_session_factory(orm_async_dsn)

    chunker = LangChainChunker()
    chunk_fn = chunker.build()

    def make_uow(self) -> SqlAlchemyUnitOfWork:
        return SqlAlchemyUnitOfWork(self.session_factory)

    def make_doc_repo(self, uow: SqlAlchemyUnitOfWork) -> DocumentRepoPg:
        return DocumentRepoPg(uow)

    def make_vector_index(self, dim: int):
        return PgVectorIndex(
            conn_str=self.vector_dsn,
            name=self.vector_cfg.name,
            namespace=self.vector_cfg.namespace,
            dim=dim,
            metric=self.vector_cfg.metric,
        )

    def make_raptor_builder(self, params):
        from raptor.raptor_core import RaptorBuilder

        return RaptorBuilder(params)
