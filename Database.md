erDiagram
%% Hướng vẽ trái → phải
direction LR

DOCUMENTS {
string doc_id PK
string title "optional"
}

TREES {
string tree_id PK
string doc_id FK "→ documents.doc_id"
string dataset_id
jsonb params
timestamp created_at
}

TREE_NODES {
string node_id PK
string tree_id FK "→ trees.tree_id"
int level
enum kind "raptor_node_kind: {leaf, summary, root}"
text text
jsonb meta
timestamp created_at
}

TREE_EDGES {
string parent_id PK, FK "→ tree_nodes.node_id"
string child_id PK, FK "→ tree_nodes.node_id"
}

CHUNKS {
string id PK
text content "optional"
}

TREE_NODE_CHUNKS {
string node_id PK, FK "→ tree_nodes.node_id"
string chunk_id PK, FK "→ chunks.id"
int rank
}

%% Quan hệ & lực lượng (cardinality)
DOCUMENTS ||--o{ TREES : "has"
TREES ||--o{ TREE_NODES : "has"

%% Cấu trúc cây qua cạnh cha–con
TREE_NODES ||--|{ TREE_EDGES : "as parent"
TREE_NODES ||--|{ TREE_EDGES : "as child"

%% Gán chunks cho node (bảng nối có thuộc tính 'rank')
TREE_NODES ||--|{ TREE_NODE_CHUNKS : "maps"
CHUNKS ||--|{ TREE_NODE_CHUNKS : "used in"

%% Tô nhẹ hai bảng ngoại để phân biệt (tuỳ renderer có hỗ trợ style)
classDef external stroke-dasharray: 5 5,fill:#fff;
class DOCUMENTS,CHUNKS external;
