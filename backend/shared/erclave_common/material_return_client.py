"""HTTP-only integration for material returns; never accesses another owner's tables."""
import json
from urllib import request,error,parse
from decimal import Decimal
from fastapi import Depends
from pydantic import BaseModel,Field
from .config import Settings,get_settings
from .errors import ErclaveError


class MaterialReturnValidation(BaseModel):
    model_config={"extra":"forbid"}
    original_movement_id:str=Field(min_length=1,max_length=40)
    reservation_id:str=Field(min_length=1,max_length=40)
    source_id:str=Field(min_length=1,max_length=40)
    quantity:Decimal=Field(gt=0)


class MaterialReturnReconcile(BaseModel):
    model_config={"extra":"forbid"}
    return_id:str=Field(min_length=1,max_length=40)


class MaterialReturnClient:
    def __init__(self,settings):
        self.inventory=settings.inventory_service_url.rstrip('/')
        self.owners={"production_order":(settings.production_service_url.rstrip('/'),'production'),"maintenance_order":(settings.maintenance_service_url.rstrip('/'),'maintenance')}
        self.timeout=settings.authorization_timeout_seconds

    def call(self,url,t,authorization,method='GET',payload=None,key=None):
        headers={"Authorization":authorization or '',"X-Tenant-Id":t,"Content-Type":"application/json"}
        if key:headers['Idempotency-Key']=key
        req=request.Request(url,headers=headers,method=method,data=json.dumps(payload,default=str).encode() if payload is not None else None)
        try:
            with request.urlopen(req,timeout=self.timeout) as response:return json.loads(response.read())['data']
        except error.HTTPError as exc:
            try:code=json.loads(exc.read()).get('error',{}).get('code','material_return_dependency_rejected')
            except (ValueError,AttributeError):code='material_return_dependency_rejected'
            raise ErclaveError(code,'The material-return owner rejected the command.',status_code=exc.code if exc.code<500 else 503) from exc
        except (error.URLError,TimeoutError,KeyError,ValueError) as exc:
            raise ErclaveError('material_return_dependency_unavailable','Material return confirmation is temporarily unavailable.',status_code=503) from exc

    def validate(self,t,source,authorization):
        base,module=self.owners[source['source_type']]
        payload={k:source[k] for k in ('original_movement_id','reservation_id','source_id','quantity')}
        return self.call(f'{base}/v1/{module}/material-returns/validate',t,authorization,'POST',payload)

    def reconcile(self,t,source,authorization):
        base,module=self.owners[source['source_type']]
        return self.call(f'{base}/v1/{module}/material-returns/reconcile',t,authorization,'POST',{'return_id':source['id']},f"return-{source['id']}")

    def get_return(self,t,id,authorization):
        return self.call(f'{self.inventory}/v1/inventory/material-returns/{parse.quote(id,safe="")}',t,authorization)


def get_material_return_client(settings:Settings=Depends(get_settings)):return MaterialReturnClient(settings)
