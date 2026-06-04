from dataclasses import dataclass

from fastapi import Query


@dataclass
class PaginationParams:
    page: int = Query(default=1, ge=1, description="Page number (1-based)")
    size: int = Query(default=20, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size
