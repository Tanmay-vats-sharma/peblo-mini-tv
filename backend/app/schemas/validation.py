from pydantic import BaseModel, Field


class ValidationIssue(BaseModel):
    code: str
    message: str
    entity_type: str
    entity_id: int | None = None
    field: str | None = None
    details: dict[str, object] = Field(default_factory=dict)


class ValidationReport(BaseModel):
    valid: bool
    error_count: int
    warning_count: int
    errors: list[ValidationIssue]
    warnings: list[ValidationIssue]