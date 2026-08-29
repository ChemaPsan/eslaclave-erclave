import re
from datetime import date
from typing import Literal
from pydantic import BaseModel,Field,field_validator,model_validator
Status=Literal["active","inactive"]
class AreaRead(BaseModel): id:str;code:str;name:str;description:str|None=None;status:Status
class AreaCreate(BaseModel): code:str=Field(min_length=1,max_length=80);name:str=Field(min_length=1,max_length=160);description:str|None=None
class AreaUpdate(BaseModel): name:str|None=None;description:str|None=None;status:Status|None=None
class AreaResponse(BaseModel): data:AreaRead
class AreaListResponse(BaseModel): data:list[AreaRead]
class RoleRead(BaseModel): id:str;labor_area_id:str;position:str;recipe_name:str;resource_quantity:int;minutes_per_resource:int;hourly_cost:float;intervenes_in_production:bool;intervenes_in_maintenance:bool=False;status:Status
class RoleCreate(BaseModel): labor_area_id:str;position:str=Field(min_length=1,max_length=160);recipe_name:str=Field(min_length=1,max_length=160);resource_quantity:int=Field(default=1,gt=0);minutes_per_resource:int=Field(default=480,gt=0);hourly_cost:float=Field(default=0,ge=0);intervenes_in_production:bool=False;intervenes_in_maintenance:bool=False
class RoleUpdate(BaseModel): labor_area_id:str|None=None;position:str|None=None;recipe_name:str|None=None;resource_quantity:int|None=Field(default=None,gt=0);minutes_per_resource:int|None=Field(default=None,gt=0);hourly_cost:float|None=Field(default=None,ge=0);intervenes_in_production:bool|None=None;intervenes_in_maintenance:bool|None=None;status:Status|None=None
class RoleResponse(BaseModel): data:RoleRead
class RoleListResponse(BaseModel): data:list[RoleRead]

WorkerStatus=Literal["active","inactive","terminated"]
class WorkerBase(BaseModel):
    employee_number:str=Field(min_length=1,max_length=40);first_names:str=Field(min_length=1,max_length=120);first_last_name:str=Field(min_length=1,max_length=100);second_last_name:str|None=Field(default=None,max_length=100)
    curp:str=Field(min_length=18,max_length=18);rfc:str=Field(min_length=13,max_length=13);nss:str=Field(min_length=11,max_length=11);hire_date:date;labor_position_id:str
    personal_email:str|None=Field(default=None,max_length=254);phone:str|None=Field(default=None,max_length=30);birth_date:date|None=None;nationality:str|None=Field(default=None,max_length=80);marital_status:str|None=Field(default=None,max_length=40);address:str|None=Field(default=None,max_length=500);emergency_contact_name:str|None=Field(default=None,max_length=200);emergency_contact_phone:str|None=Field(default=None,max_length=30);notes:str|None=Field(default=None,max_length=2000)
    @field_validator("curp")
    @classmethod
    def valid_curp(cls,value):
        value=value.strip().upper()
        if not re.fullmatch(r"[A-Z][AEIOUX][A-Z]{2}\d{6}[HM][A-Z]{5}[A-Z0-9]\d",value):raise ValueError("invalid_curp")
        return value
    @field_validator("rfc")
    @classmethod
    def valid_rfc(cls,value):
        value=value.strip().upper()
        if not re.fullmatch(r"[A-Z&Ñ]{4}\d{6}[A-Z0-9]{3}",value):raise ValueError("invalid_rfc")
        return value
    @field_validator("nss")
    @classmethod
    def valid_nss(cls,value):
        value=re.sub(r"\D","",value)
        if len(value)!=11:raise ValueError("invalid_nss")
        products=[int(n)*(1 if i%2==0 else 2) for i,n in enumerate(value[:10])]
        if (10-sum(p//10+p%10 for p in products)%10)%10!=int(value[-1]):raise ValueError("invalid_nss_check_digit")
        return value
    @model_validator(mode="after")
    def valid_dates(self):
        if self.hire_date>date.today():raise ValueError("hire_date_in_future")
        if self.birth_date and (self.birth_date>=self.hire_date or self.birth_date>date.today()):raise ValueError("invalid_birth_date")
        return self
class WorkerCreate(WorkerBase):pass
class WorkerUpdate(BaseModel):
    first_names:str|None=Field(default=None,min_length=1,max_length=120);first_last_name:str|None=Field(default=None,min_length=1,max_length=100);second_last_name:str|None=Field(default=None,max_length=100);labor_position_id:str|None=None;status:WorkerStatus|None=None
    personal_email:str|None=Field(default=None,max_length=254);phone:str|None=Field(default=None,max_length=30);nationality:str|None=Field(default=None,max_length=80);marital_status:str|None=Field(default=None,max_length=40);address:str|None=Field(default=None,max_length=500);emergency_contact_name:str|None=Field(default=None,max_length=200);emergency_contact_phone:str|None=Field(default=None,max_length=30);notes:str|None=Field(default=None,max_length=2000)
class WorkerRead(WorkerBase):
    id:str;status:WorkerStatus;full_name:str;position_name:str;labor_area_id:str;labor_area_name:str;intervenes_in_production:bool;intervenes_in_maintenance:bool=False
class WorkerResponse(BaseModel):data:WorkerRead
class WorkerListResponse(BaseModel):data:list[WorkerRead]

class SalesEligibleWorkerRead(BaseModel):
    id:str;employee_number:str;full_name:str;position_name:str;labor_area_name:str;status:WorkerStatus
class SalesEligibleWorkerListResponse(BaseModel):data:list[SalesEligibleWorkerRead]

class ProductionCapacityRead(BaseModel):
    position_id:str
    position_name:str
    recipe_name:str
    labor_area_id:str
    labor_area_name:str
    active_worker_count:int=Field(ge=0)
    minutes_per_worker:int=Field(gt=0)
    available_minutes:float=Field(ge=0)
    hourly_cost:float=Field(ge=0)
    cost_per_minute:float=Field(ge=0)

class ProductionCapacityListResponse(BaseModel):data:list[ProductionCapacityRead]
