from app.config import settings
from interfaces_adaptor.gateways.file_source import FileSourceHybrid
from interfaces_adaptor.gateways.vector_pgvector import PgVectorIndex
from interfaces_adaptor.repositories.document_repo_pg import DocumentRepoPg


class Container:
    def __init__(self):
        self.file_source = FileSourceHybrid()
        self.doc_repo = DocumentRepoPg(settings.pg_dsn or settings.vector.dsn)
        self.vector_cfg = settings.vector

    def make_vector_index(self, dim: int):
        return PgVectorIndex(
            conn_str=self.vector_cfg.dsn,
            name=self.vector_cfg.name,
            namespace=self.vector_cfg.namespace,
            dim=dim,
            metric=self.vector_cfg.metric,
        )


container = Container()
