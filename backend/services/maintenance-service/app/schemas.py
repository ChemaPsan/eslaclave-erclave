from datetime import datetime, timezone
from typing import Literal
from pydantic import BaseModel, Field, model_validator

OrderStatus = Literal["draft","requested","assigned","in_progress","waiting_parts","resolved","closed","cancelled"]

class OrderCreate(BaseModel):
    code:str=Field(min_length=1,max_length=60)
    target_type:Literal["production_machine","facility","other"]
    production_machine_id:str|None=None
    source_type:Literal["manual","production_order"]="manual"
    source_production_order_id:str|None=None
    priority:Literal["low","medium","high","critical"]="medium"
    title:str=Field(min_length=3,max_length=180)
    description:str=Field(min_length=3,max_length=4000)
    location:str=Field(min_length=2,max_length=300)
    safety_notes:str|None=Field(default=None,max_length=2000)
    @model_validator(mode="after")
    def references(self):
        if self.target_type=="production_machine" and not self.production_machine_id:raise ValueError("production_machine_required")
        if self.target_type!="production_machine" and self.production_machine_id:raise ValueError("production_machine_not_allowed")
        if self.source_type=="production_order" and (not self.source_production_order_id or not self.production_machine_id):raise ValueError("production_source_references_required")
        if self.source_type=="manual" and self.source_production_order_id:raise ValueError("manual_source_reference_not_allowed")
        return self

class OrderUpdate(BaseModel):
    priority:Literal["low","medium","high","critical"]|None=None
    title:str|None=Field(default=None,min_length=3,max_length=180)
    description:str|None=Field(default=None,min_length=3,max_length=4000)
    location:str|None=Field(default=None,min_length=2,max_length=300)
    safety_notes:str|None=Field(default=None,max_length=2000)
    diagnosis:str|None=Field(default=None,max_length=4000)
    root_cause:str|None=Field(default=None,max_length=2000)
    work_performed:str|None=Field(default=None,max_length=4000)
    verification_notes:str|None=Field(default=None,max_length=2000)

class TransitionRequest(BaseModel):
    transition:Literal["request","assign","start","wait_for_parts","resume","resolve","close","reopen","cancel"]
    assigned_worker_id:str|None=None
    reason:str|None=Field(default=None,max_length=1000)
    @model_validator(mode="after")
    def assignment(self):
        if self.transition=="assign" and not self.assigned_worker_id:raise ValueError("assigned_worker_required")
        if self.transition=="cancel" and (not self.reason or len(self.reason.strip())<3):raise ValueError("cancellation_reason_required")
        return self

class TimeEntryCreate(BaseModel):
    worker_id:str
    started_at:datetime
    ended_at:datetime
    notes:str|None=Field(default=None,max_length=1000)
    @model_validator(mode="after")
    def interval(self):
        if self.ended_at<=self.started_at:raise ValueError("invalid_time_interval")
        now=datetime.now(timezone.utc)
        ended=self.ended_at if self.ended_at.tzinfo else self.ended_at.replace(tzinfo=timezone.utc)
        if ended>now:raise ValueError("future_time_entry_not_allowed")
        return self

class MaterialLine(BaseModel):
    item_id:str
    quantity:float=Field(gt=0)
    unit_code:str=Field(min_length=1,max_length=20)

class MaterialRequestCreate(BaseModel):
    warehouse_id:str
    lines:list[MaterialLine]=Field(min_length=1,max_length=100)
    @model_validator(mode="after")
    def unique_items(self):
        ids=[line.item_id for line in self.lines]
        if len(ids)!=len(set(ids)):raise ValueError("duplicate_material_item")
        return self

class DataResponse(BaseModel):data:dict
class ListResponse(BaseModel):data:list[dict]
