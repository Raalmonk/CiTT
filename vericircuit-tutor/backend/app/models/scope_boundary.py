from __future__ import annotations

from pydantic import BaseModel, Field


class ScopeItem(BaseModel):
    label: str = Field(min_length=1)
    detail: str = Field(min_length=1)


class ProductCapability(BaseModel):
    capability: str = Field(min_length=1)
    user_value: str = Field(min_length=1)
    current_evidence: str = Field(min_length=1)
    boundary: str = Field(min_length=1)


class ScopeBoundary(BaseModel):
    product_positioning: str = Field(min_length=1)
    source_of_truth_rule: str = Field(min_length=1)
    product_capabilities: list[ProductCapability]
    supported_analysis_modes: list[ScopeItem]
    supported_components: list[str]
    supported_workflows: list[str]
    unsupported_features: list[ScopeItem]
    verification_boundary: list[str]
    bme_boundary: list[str]
    bme_templates: list[str]
    debug_boundary: list[str]
