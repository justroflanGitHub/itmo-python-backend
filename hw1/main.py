from typing import List, Dict
from urllib.parse import parse_qs
import math
import json
from typing import Any, Awaitable, Callable
async def application(
    scope: dict[str, Any],
    receive: Callable[[], Awaitable[dict[str, Any]]],
    send: Callable[[dict[str, Any]], Awaitable[None]], 
)-> None:
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
        return {"error": "Missing N"}, 422

    try:
        n = int(n_str)
    except ValueError:
        return {"error": "NaN"}, 422

    if n < 0:
        return {"error": "Negative number"}, 400
    
    result = 1  
    for i in range(2, n + 1):  
        result *= i  
    return {"result": result}, 200


async def fibonacci(path: str):
    n_str = path.split("/")[-1]

    if n_str is None:
        return {"error": "Missing N"}, 422

    try:
        n = int(n_str)
    except ValueError:
        return {"error": "NaN"}, 422

    if n < 0:
        return {"error": "Negative number"}, 400

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
            return {"error": "Request must be valid"}, 422

        if not isinstance(data, list):
            return {"error": "Request body must be an array"}, 422

        if len(data) == 0:
            return {"error": "Array cannot be empty"}, 400

        try:
            float_data = [float(x) for x in data]
        except ValueError:
            return {"error": "NaN"}, 422

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

