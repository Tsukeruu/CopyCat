from typing import Dict, List, Any, Union
from sqlmodel import SQLModel, create_engine, Field
from pathlib import Path

class SQL_SETUP:
    def __init__(self, sqlite_name: str) -> None:
        self.sqlite_name: str = sqlite_name
        self.sqlite_url: str = f"sqlite:////{Path(__file__).parent}/{self.sqlite_name}"
        self.engine: create_engine = create_engine(self.sqlite_url)

    def create_db(self) -> Any:
        SQLModel.metadata.create_all(self.engine)

SQL_SETUP: SQL_SETUP = SQL_SETUP("agent_tasks.db")

class Task_Template(SQLModel, table=True):
    Id: int | None = Field(default=None, primary_key=True)
    proposed_fix: str
    issue_summary: str
    shell_command: str
    status: str


