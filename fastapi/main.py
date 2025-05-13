from enum import Enum
from typing import Any

from typing_extensions import Annotated, Literal, Union, Dict, List

from fastapi import (Body, FastAPI, Query, Cookie,
                     Header, Form, File, UploadFile, HTTPException)
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field, HttpUrl, EmailStr


class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"


class Image(BaseModel):
    url: HttpUrl
    name: str


class Item(BaseModel):
    name: str = Field(examples=["Foo"])
    description: Union[str, None] = Field(
        default=None, title="The description of the item", max_length=300,
        examples=["A very nice Item"]
    )
    price: float = Field(gt=0, description="The price must be greater than zero", examples=[35.4])
    tax: Union[float, None] = Field(default=None, examples=[3.2])
    tags: set[str] = set()
    images: Union[list[Image], None] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Foo",
                    "description": "A very nice Item",
                    "price": 35.4,
                    "tax": 3.2,
                    "tags": ["foo"],
                    "images": [
                        {
                            "url": "http://example.com",
                            "name": "Foo"
                        }
                    ]
                }
            ]
        }
    }


class Offer(BaseModel):
    name: str
    description: Union[str, None] = None
    price: float
    items: list[Item]


class User(BaseModel):
    username: str
    full_name: Union[str, None] = None


app = FastAPI()

fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]

class FilterParams(BaseModel):
    model_config = {"extra": "forbid"}

    limit: int = Field(100, gt=0, le=100)
    offset: int = Field(0, ge=0)
    order_by: Literal["created_at", "updated_at"] = "created_at"
    tags: list[str] = []


class Cookies(BaseModel):
    model_config = {"extra": "forbid"}

    session_id: str
    fatebook_tracker: str | None = None
    googall_tracker: str | None = None


class UserIn(BaseModel):
    username: str
    password: str
    email: EmailStr
    full_name: Union[str, None] = None


class FormData(BaseModel):
    model_config = {"extra": "forbid"}

    username: str
    password: str


@app.post("/login/")
async def login(data: Annotated[FormData, Form()]):
    return data

@app.get("/")
async def main():
    content = """
<body>
<form action="/files/" enctype="multipart/form-data" method="post">
<input name="files" type="file" multiple>
<input type="submit">
</form>
<form action="/uploadfiles/" enctype="multipart/form-data" method="post">
<input name="files" type="file" multiple>
<input type="submit">
</form>
</body>
    """
    return HTMLResponse(content=content)


@app.get("/items_cookie_model/")
async def read_items_cookie_model(
    cookies: Annotated[Cookies, Cookie()]
):
    return cookies


@app.post("/files/")
async def create_files(
    files: Annotated[list[bytes], File(description="Multiple files as bytes")],
):
    return {"file_sizes": [len(file) for file in files]}


@app.post("/uploadfiles/")
async def create_upload_files(
    files: Annotated[
        list[UploadFile], File(description="Multiple files as UploadFile")
    ],
):
    return {"filenames": [file.filename for file in files]}


@app.get("/items_cookie/")
async def read_items_cookie(
    ads_id: Annotated[Union[str, None], Cookie()] = None,
    user_agent: Annotated[Union[str, None], Header()] = None
):
    return {"ads_id": ads_id, "User-Agent": user_agent}


@app.post("/index-weights/")
async def create_index_weights(weights: Dict[int, float]):
    return weights


@app.post("/images/multiple/")
async def create_multiple_images(images: list[Image]):
    return images


@app.post("/offers/")
async def create_offer(offer: Offer):
    return offer


@app.post("/items/")
async def create_item(item: Item) -> Item:
    item_dict = item.model_dump()
    if item.tax is not None:
        price_with_tax = item.price + item.tax
        item_dict.update({"price_with_tax": price_with_tax})
    return item_dict


@app.put("/items/{item_id}")
async def update_item(
    item_id: int,
    item: Annotated[
        Item,
        Body(
            embed=True
        )
    ]
):
    results = {"item_id": item_id, "item": item}
    return results


@app.get("/items/", response_model=list[Item])
async def read_items() -> Any:
    return [Item(name="Portal Gun", price=42.0)]


@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}


@app.get("/users/me")
async def read_user_me():
    return {"user_id": "the current user"}


@app.get("/users/{user_id}")
async def read_user(user_id: str):
    return {"user_id": user_id}


# Don't do this in production!
@app.post("/user/")
async def create_user(user: UserIn) -> UserIn:
    return user

@app.get("/models/{model_name}")
async def get_model(model_name: ModelName):
    if model_name is ModelName.alexnet:
        return {"model_name": model_name, "message": "Deep Learning FTW!"}

    if model_name.value == "lenet":
        return {"model_name": model_name, "message": "LeCNN all the images"}

    return {"model_name": model_name, "message": "Have some residuals"}


@app.get("/files/{file_path:path}")
async def read_file(file_path: str):
    return {"file_path": file_path}


items_except = {"foo": "The Foo Wrestlers"}


@app.get("/ggg")
async def read_item(item_id: str):
    if item_id not in items_except:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"item": items_except[item_id]}
