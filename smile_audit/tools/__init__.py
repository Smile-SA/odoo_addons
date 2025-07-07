from .decorator import audit_decorator

from odoo import models, api

def _patch_method(cls, name, method):
    origin = getattr(cls, name, None)
    if callable(origin):
        method.origin = origin
    wrapped = api.propagate(origin, method)
    if callable(origin):
        wrapped.origin = origin
    setattr(cls, name, wrapped)

models.BaseModel._patch_method = classmethod(_patch_method)
