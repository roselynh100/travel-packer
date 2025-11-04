from fastapi import APIRouter

from computer_vision.utils import run_cv
from hardware.utils import run_hardware
from machine_learning.utils import run_ml

router = APIRouter()


@router.get("/cv")
def read_cv():
    return {"message": run_cv()}


@router.get("/ml")
def read_ml():
    return {"message": run_ml()}


@router.get("/hardware")
def read_hardware():
    return {"message": run_hardware()}
