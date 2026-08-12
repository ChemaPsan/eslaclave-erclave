from typing import Literal
from pydantic import BaseModel,Field
Status=Literal["active","inactive"]
class AreaRead(BaseModel): id:str;code:str;name:str;description:str|None=None;status:Status
class AreaCreate(BaseModel): code:str=Field(min_length=1,max_length=80);name:str=Field(min_length=1,max_length=160);description:str|None=None
class AreaUpdate(BaseModel): name:str|None=None;description:str|None=None;status:Status|None=None
class AreaResponse(BaseModel): data:AreaRead
class AreaListResponse(BaseModel): data:list[AreaRead]
class RoleRead(BaseModel): id:str;labor_area_id:str;position:str;recipe_name:str;resource_quantity:int;minutes_per_resource:int;hourly_cost:float;intervenes_in_production:bool;status:Status
class RoleCreate(BaseModel): labor_area_id:str;position:str=Field(min_length=1,max_length=160);recipe_name:str=Field(min_length=1,max_length=160);resource_quantity:int=Field(default=1,gt=0);minutes_per_resource:int=Field(default=480,gt=0);hourly_cost:float=Field(default=0,ge=0);intervenes_in_production:bool=False
class RoleUpdate(BaseModel): labor_area_id:str|None=None;position:str|None=None;recipe_name:str|None=None;resource_quantity:int|None=Field(default=None,gt=0);minutes_per_resource:int|None=Field(default=None,gt=0);hourly_cost:float|None=Field(default=None,ge=0);intervenes_in_production:bool|None=None;status:Status|None=None
class RoleResponse(BaseModel): data:RoleRead
class RoleListResponse(BaseModel): data:list[RoleRead]
