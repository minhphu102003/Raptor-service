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
                    "INSERT INTO vectors(id,ns,v,meta) VALUES (%s,%s,%s,%s) "
                    "ON CONFLICT(id) DO UPDATE SET v=EXCLUDED.v, meta=EXCLUDED.meta",
                    (_id, self.namespace, vec, m),
                )
            conn.commit()
