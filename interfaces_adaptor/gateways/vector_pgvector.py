import psycopg


class PgVectorIndex:
    def __init__(self, conn_str: str, name: str, namespace: str | None, dim: int, metric: str):
        self.conn_str = conn_str
        self.name = name
        self.namespace = namespace
        self.dim = dim
        self.metric = metric

    def upsert(self, ids, vectors, meta):
        with psycopg.connect(self.conn_str) as conn, conn.cursor() as cur:
            for _id, vec, m in zip(ids, vectors, meta):
                cur.execute(
                    "insert into vectors(id, ns, v, meta) values (%s,%s,%s,%s) "
                    "on conflict(id) do update set v=EXCLUDED.v, meta=EXCLUDED.meta",
                    (_id, self.namespace, vec, m),
                )
            conn.commit()
