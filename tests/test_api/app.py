from fastapi import FastAPI, Request
from pydantic import BaseModel

app = FastAPI()


class FooData(BaseModel):
    foo: str
    bar: int


@app.get("/endpoint_1/")
def endpoint_1(param_1: int, param_2: str, param_3: float | None = None):
    ret_data = {"data": {"param_1": param_1, "param_2": param_2, "param_3": param_3}}

    print(ret_data)
    return ret_data


@app.get("/endpoint_2/")
def endpoint_1(param_1: int, param_2: str, param_3: float | None = None):
    ret_data = {"data": {"param_1": param_1, "param_2": param_2, "param_3": param_3}}

    print(ret_data)
    return ret_data


@app.get("/sub_category/endpoint_1/")
def sub_endpoint_1(param_1: int, param_2: str, param_3: float | None = None):
    ret_data = {"data": {"param_1": param_1, "param_2": param_2, "param_3": param_3}}

    print(ret_data)
    return ret_data


@app.get("/sub_category/endpoint_2/")
def sub_endpoint_2(param_1: int, param_2: str, param_3: float | None = None):
    ret_data = {"data": {"param_1": param_1, "param_2": param_2, "param_3": param_3}}

    print(ret_data)
    return ret_data


@app.post("/endpoint_3/")
def endpoint_2(data: FooData):
    return data
