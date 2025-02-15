from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()


class FooData(BaseModel):
    foo: str
    bar: int


@app.get("/health/")
def get_health():
    return {"status": "good"}


@app.get("/err_endpoint/")
def get_err_endpoint(ret_code: int):
    raise HTTPException(
        status_code=ret_code, detail=f"Force {ret_code} error code from the api"
    )


@app.get("/endpoint_1/")
def endpoint_1(param_1: int, param_2: str, param_3: float | None = None):
    ret_data = {"data": {"param_1": param_1, "param_2": param_2, "param_3": param_3}}

    print(ret_data)
    return ret_data


@app.get("/endpoint_2/")
def endpoint_2(param_1: int, param_2: str, param_3: float | None = None):
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
def endpoint_3(data: FooData):
    return data
