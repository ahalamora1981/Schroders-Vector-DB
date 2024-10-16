# FastAPI程序API接口调用指南

这个指南描述了如何使用FastAPI程序中定义的各种API端点。

## 基本信息

- 基础URL: `http://localhost:8000`
- 所有响应都遵循`HttpResponse`模型，包含`ok`、`message`和可选的`data`字段

## 端点

### 1. 创建集合

- **URL**: `/create-collection`
- **方法**: GET
- **参数**: 
  - `collection_name`: 字符串，要创建的集合名称
- **示例**:
  ```
  GET /create-collection?collection_name=my_collection
  ```

### 2. 列出所有集合

- **URL**: `/list-all-collections`
- **方法**: GET
- **示例**:
  ```
  GET /list-all-collections
  ```

### 3. 获取集合

- **URL**: `/get-collection`
- **方法**: GET
- **参数**:
  - `collection_name`: 字符串，要获取的集合名称
- **示例**:
  ```
  GET /get-collection?collection_name=my_collection
  ```

### 4. 删除集合

- **URL**: `/delete-collection`
- **方法**: GET
- **参数**:
  - `collection_name`: 字符串，要删除的集合名称
- **示例**:
  ```
  GET /delete-collection?collection_name=my_collection
  ```

### 5. 添加文档到集合

- **URL**: `/add-document`
- **方法**: POST
- **请求体**:
  ```json
  {
    "collection_name": "string",
    "document_name": "string",
    "document_id": "string",
    "document": "string",
    "metadata": {} // 可选
  }
  ```
- **示例**:
  ```
  POST /add-document
  Content-Type: application/json

  {
    "collection_name": "my_collection",
    "document_name": "doc1",
    "document_id": "1",
    "document": "这是一个测试文档",
    "metadata": {"author": "John Doe"}
  }
  ```

### 6. 获取文档块

- **URL**: `/get-chunks`
- **方法**: GET
- **参数**:
  - `collection_name`: 字符串，集合名称
  - `document_id`: 字符串，文档ID（可选）
  - `document_name`: 字符串，文档名称（可选）
- **注意**: `document_id` 和 `document_name` 必须提供其中一个，但不能同时提供两个
- **示例**:
  ```
  GET /get-chunks?collection_name=my_collection&document_id=1
  ```

### 7. 删除文档

- **URL**: `/delete-document`
- **方法**: GET
- **参数**:
  - `collection_name`: 字符串，集合名称
  - `document_id`: 字符串，文档ID（可选）
  - `document_name`: 字符串，文档名称（可选）
- **注意**: `document_id` 和 `document_name` 必须提供其中一个，但不能同时提供两个
- **示例**:
  ```
  GET /delete-document?collection_name=my_collection&document_id=1
  ```

### 8. 查询

- **URL**: `/query`
- **方法**: GET
- **参数**:
  - `collection_name`: 字符串，要查询的集合名称
  - `query`: 字符串，查询内容
  - `n_results`: 整数，返回结果数量（默认为10）
  - `rerank`: 布尔值，是否重新排序（默认为false）
- **示例**:
  ```
  GET /query?collection_name=my_collection&query=测试查询&n_results=5&rerank=true
  ```

## 注意事项

1. 所有响应都会包含 `ok`（操作是否成功）和 `message`（操作结果描述）字段。
2. 某些操作在成功时会在 `data` 字段中返回额外信息。
3. 使用添加文档、获取文档块和删除文档的API时，请注意 `document_id` 和 `document_name` 的使用规则。
4. 查询API允许自定义返回结果数量和是否重新排序。

希望这个指南能帮助您更好地使用这个FastAPI程序的各个端点。如果有任何问题，请随时询问。
