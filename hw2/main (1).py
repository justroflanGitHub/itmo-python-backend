from fastapi import (
    FastAPI,
    HTTPException,
    Path,
    Query,
    Body,
    Response,
    WebSocket,
    WebSocketDisconnect,
    Request,
)
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Optional
from http import HTTPStatus
import random
import string
import uvicorn

app = FastAPI()

class Item(BaseModel):
    id: int
    name: str
    price: float
    deleted: bool = False

class ItemCreate(BaseModel):
    name: str = Field(..., description="Название товара")
    price: float = Field(..., gt=0.0, description="Цена товара")

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None

    model_config = ConfigDict(extra="forbid")

class CartItem(BaseModel):
    id: int
    name: str
    quantity: int
    available: bool

class Cart(BaseModel):
    id: int
    items: List[CartItem]
    price: float

items_db: Dict[int, Item] = {}
carts_db: Dict[int, Cart] = {}

item_id_counter = 0
cart_id_counter = 0

def compute_cart(cart: Cart) -> Cart:
   
    total_price = 0.0  
    updated_items = []  
    for cart_item in cart.items:  
        item = items_db.get(cart_item.id)  
        if item:  
            available = not item.deleted 
            cart_item.available = available  
            cart_item.name = item.name  
            if available:  
                total_price += (
                    item.price * cart_item.quantity
                )  
        else: 
            cart_item.available = (
                False  
            )
        updated_items.append(cart_item)  
    cart.price = total_price  
    cart.items = updated_items  
    return cart


@app.post("/cart", status_code=HTTPStatus.CREATED)
def create_cart(response: Response):
  
    global cart_id_counter
    cart_id_counter += 1
    new_cart = Cart(id=cart_id_counter, items=[], price=0.0)
    carts_db[cart_id_counter] = new_cart
    response.headers["Location"] = f"/cart/{cart_id_counter}"
    return {"id": cart_id_counter}


@app.get("/cart/{cart_id}")
def get_cart(cart_id: int = Path(..., ge=1)):
   
    cart = carts_db.get(cart_id)  
    if not cart:  
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Корзина не найдена"
        )

    cart = compute_cart(cart)  
    return {
        "id": cart.id,  
        "items": cart.items,  
        "item": cart.items,  
        "price": cart.price,
    }


@app.get("/cart")
def get_carts(
    offset: int = Query(0, ge=0),
    limit: int = Query(10, gt=0),
    min_price: Optional[float] = Query(None, ge=0.0),
    max_price: Optional[float] = Query(None, ge=0.0),
    min_quantity: Optional[int] = Query(None, ge=0),
    max_quantity: Optional[int] = Query(None, ge=0),
):
 
    carts_list = []  
    for cart in carts_db.values(): 
        cart = compute_cart(cart) 
        total_quantity = sum(
            item.quantity for item in cart.items
        )  
        if (
            min_price is not None and cart.price < min_price
        ):  
            continue  
        if (
            max_price is not None and cart.price > max_price
        ): 
            continue  
        if (
            min_quantity is not None and total_quantity < min_quantity
        ):  
            continue  
        if (
            max_quantity is not None and total_quantity > max_quantity
        ): 
            continue 
        cart_dict = cart.model_dump()  
        cart_dict["quantity"] = (
            total_quantity  
        )
        carts_list.append(cart_dict)  
    carts_list = carts_list[
        offset : offset + limit
    ]  
    return carts_list


@app.post("/cart/{cart_id}/add/{item_id}")
def add_item_to_cart(
    cart_id: int = Path(..., ge=1),
    item_id: int = Path(..., ge=1),
):
  
    cart = carts_db.get(cart_id)  
    if not cart: 
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Корзина не найдена"
        )
    item = items_db.get(item_id)  
    if not item or item.deleted:  
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Товар не найден")
    for cart_item in cart.items:  
        if cart_item.id == item_id:  
            cart_item.quantity += 1  
            break  
    else: 
        cart_item = CartItem(
            id=item_id,
            name=item.name,
            quantity=1,
            available=not item.deleted,
        )
        cart.items.append(cart_item) 
    return {"message": "Товар добавлен в корзину"}


@app.post("/item", status_code=HTTPStatus.CREATED)
async def create_item(response: Response, request: Request):
    global item_id_counter
    item_id_counter += 1

    if request.headers.get("content-length") == "0": 
        item_data = ItemCreate(
            name="Тестовый товар", price=100.0
        )  
    else:  
        item_data = ItemCreate(
            **await request.json()
        )  

    new_item = Item(  
        id=item_id_counter,
        name=item_data.name,
        price=item_data.price,
        deleted=False,
    )

    items_db[item_id_counter] = new_item
    response.headers["Location"] = f"/item/{item_id_counter}"

    return {
        "id": new_item.id,
        "name": new_item.name,
        "price": new_item.price,
        "deleted": new_item.deleted,
    }

@app.get("/item/{item_id}")
def get_item(item_id: int = Path(..., ge=1)):

    item = items_db.get(item_id)  
    if not item or item.deleted:  
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Товар не найден")
    return item


@app.put("/item/{item_id}")
def update_item(
    item_id: int = Path(..., ge=1),
    item_data: ItemCreate = Body(...),
):
    
    item = items_db.get(item_id)  
    if not item or item.deleted:  
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Товар не найден")
    item.name = item_data.name
    item.price = item_data.price
    items_db[item_id] = item
    return item


@app.patch("/item/{item_id}")
def patch_item(
    item_id: int = Path(..., ge=1),
    item_data: ItemUpdate = Body(...),
):

    item = items_db.get(item_id)  
    if not item:  
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Товар не найден"
        )  

    if item.deleted:
        return Response(status_code=HTTPStatus.NOT_MODIFIED)  

    update_data = item_data.model_dump(
        exclude_unset=True
    )  

    if not update_data:  
        return item  

    if "deleted" in update_data:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="Нельзя изменять поле 'deleted'",
        )

    for key, value in update_data.items():  
        setattr(item, key, value)

    items_db[item_id] = item  
    return item


@app.delete("/item/{item_id}")
def delete_item(item_id: int = Path(..., ge=1)):

    item = items_db.get(item_id)  
    if item:  
        item.deleted = True
    return {"message": "Товар удалён"}

class ConnectionManager:
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.usernames: Dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, chat_name: str):
        await websocket.accept()  
        if chat_name not in self.active_connections:  
            self.active_connections[chat_name] = []
        self.active_connections[chat_name].append(
            websocket
        )  
        username = "".join(
            random.choices(string.ascii_letters + string.digits, k=8)
        )  
        self.usernames[websocket] = username  
        return username

    def disconnect(self, websocket: WebSocket, chat_name: str):
        self.active_connections[chat_name].remove(
            websocket
        )  
        del self.usernames[websocket]  
        if not self.active_connections[chat_name]:  
            del self.active_connections[chat_name]  

    async def broadcast(self, message: str, chat_name: str, sender: WebSocket):
        for connection in self.active_connections.get(
            chat_name, []
        ):  
            if connection != sender:  
                await connection.send_text(message)  


manager = ConnectionManager()

@app.websocket("/chat/{chat_name}")
async def websocket_endpoint(websocket: WebSocket, chat_name: str):
    username = await manager.connect(
        websocket, chat_name
    )  
    try:
        while True:
            data = await websocket.receive_text()  
            message = f"{username} :: {data}"  
            await manager.broadcast(
                message, chat_name, websocket
            )  
    except WebSocketDisconnect:  
        manager.disconnect(websocket, chat_name)  

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)