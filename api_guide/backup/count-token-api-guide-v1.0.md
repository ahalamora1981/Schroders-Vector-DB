# Token计数接口调用文档

## 1. 接口概述

本接口用于计算输入字符串的Token数量。

## 2. 接口地址

- **URL**: `http://10.101.100.13:8105/count-tokens`
- **请求方法**: `POST`

## 3. 请求参数

请求参数以JSON格式放在请求体中。

| 参数名 | 类型   | 是否必填 | 描述         |
|--------|--------|----------|--------------|
| query  | string | 否       | 需要计算Token数量的字符串。如果为空或未提供，接口将返回错误信息。 |

## 4. 请求示例

```json
{
    "query": "中华人们共和国！"
}
```

## 5. 响应参数

响应数据以JSON格式返回。

| 参数名 | 类型   | 描述         |
|--------|--------|--------------|
| ok  | boolean	 | 接口调用是否成功。`true`表示成功，`false`表示失败。 |
| message  | string	 | 接口返回的消息，通常用于描述接口调用的结果或错误信息。 |
| tokens_length  | integer	 | 计算得到的Token数量。仅在`ok`为`true`时有效，否则为`null`。|

## 6. 响应示例

### 成功响应

```json
{
    "ok": true,
    "message": "Tokens counted successfully",
    "tokens_length": 5
}
```

### 失败响应

```json
{
    "ok": false,
    "message": "No query provided",
    "tokens_length": null
}
```