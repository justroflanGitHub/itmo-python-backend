from typing import List, Dict
from urllib.parse import parse_qs
import math
import json
async def application(scope, receive, send) -> None:
    assert scope["type"] == "http"

    path = scope["path"]
    method = scope["method"]
    query_string = scope["query_string"].decode("utf-8")
    query_params = parse_qs(query_string)

    if path == "/factorial" and method == "GET":
        content, status_code = await factorial(query_params)
    elif path.startswith("/fibonacci") and method == "GET":
        content, status_code = await fibonacci(path)
    elif path == "/mean" and method == "GET":
        content, status_code = await mean(receive)
    else:
        content, status_code = {"error": "Not Found"}, 404

    await send_response(send, content, status_code)


async def factorial(query_params: Dict[str, List[str]]):
    n_str = query_params.get("n", [None])[0]

    if n_str is None:
        return {"error": "Parameter n is required"}, 422

    try:
        n = int(n_str)
    except ValueError:
        return {"error": "Parameter n must be an integer"}, 422

    if n < 0:
        return {"error": "Invalid value for n, must be non-negative"}, 400

    result = math.factorial(n)
    return {"result": result}, 200


async def fibonacci(path: str):
    n_str = path.split("/")[-1]

    if n_str is None:
        return {"error": "Parameter n is required"}, 422

    try:
        n = int(n_str)
    except ValueError:
        return {"error": "Parameter n must be an integer"}, 422

    if n < 0:
        return {"error": "Invalid value for n, must be non-negative"}, 400

    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b

    result = b
    return {"result": result}, 200


async def mean(receive):
    body = await receive()

    if body["type"] == "http.request":
        try:
            data = json.loads(body["body"])
        except json.JSONDecodeError:
            return {"error": "Request body must be valid JSON"}, 422

        if not isinstance(data, list):
            return {"error": "Request body must be an array"}, 422

        if len(data) == 0:
            return {"error": "Array cannot be empty"}, 400

        try:
            float_data = [float(x) for x in data]
        except ValueError:
            return {"error": "All elements must be numbers"}, 422

        result = sum(float_data) / len(float_data)
        return {"result": result}, 200


async def send_response(send, content: Dict, status_code: int = 200):
    response = json.dumps(content)
    await send(
        {
            "type": "http.response.start",
            "status": status_code,
            "headers": [(b"content-type", b"application/json")],
        }
    )

    await send(
        {
            "type": "http.response.body",
            "body": response.encode("utf-8"),
        }
    )

# Пример запросов
# curl "http://localhost:8000/factorial?n=3"
# curl "http://localhost:8000/fibonacci/3"
# curl -X GET -d "[1.0, 2.3, 3.6]" "http://localhost:8000/mean"
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
