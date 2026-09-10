from typing import Dict, List, Any, Union, Tuple
from subprocess import run
from pathlib import Path
from dataclasses import dataclass
import sys

try: 
    import uvicorn
    import asyncio

    from utils.UI import TUI  
    from fastapi import FastAPI, Depends, Query, HTTPException, status 

    from sqlmodel import SQLModel, Field, create_engine, Session, select, delete
    from sqlalchemy.exc import OperationalError
 
    from time import sleep

    from strands import Agent, tool
    from strands.models.ollama import OllamaModel

    from prompt_toolkit import prompt
    from prompt_toolkit.formatted_text import HTML
    from .database import SQL_SETUP, Task_Template
    from .GLOBAL import TABLE, LAYOUT

    from rich.console import Console
    from rich.live import Live
    from rich.panel import Panel

except ImportError as i:
    agreement: str = input("Some libraries were not detected, would you like to install them? (y/n): ").lower()
    if agreement == "y":
        print("INSTALLING LIBRARIES NOW!")
        run(f"pip install -r {Path(__file__).parent.parent / 'libraries.txt'}", shell=True)
    else:
        print("EXITING NOW")

    sys.exit(1)

class AGENT(TUI):
    @tool
    @staticmethod
    def append_task(issue_summary: str, proposed_fix: str, shell_command: str, status: str = "pending") -> str:
        """A tool that appends a task with an issue summary and proposed fix aswell as a status, default is pending."""
        with Session(SQL_SETUP.engine) as session:
            tasks: List[Task_Template] = session.exec(select(Task_Template)).all()
            for task in tasks:
                if task.issue_summary.startswith(issue_summary) or task.issue_summary.endswith(issue_summary) or task.issue_summary == issue_summary or task.proposed_fix == proposed_fix:
                    return "UNABLE TO APPEND TASK! TASK ALREADY EXISTS"

            session.add(Task_Template(Id=None, proposed_fix=proposed_fix,issue_summary=issue_summary, shell_command=shell_command, status=status))
            session.commit()

    @tool
    @staticmethod
    def return_tasks() -> List[str]:
        with Session(SQL_SETUP.engine) as session:
            tasks: List[Task_Template] = session.exec(select(Task_Template)).all()
            if not tasks:
                return "NO CURRENT TASKS"
            
            return '\n'.join([f"Status - {task.status} - ID: {task.Id} - Summary: {task.issue_summary} - Proposed_fix: {task.proposed_fix} - Shell Command: {task.shell_command}" for task in tasks])

    def git_diff(self, dir_file: str) -> str:
        if dir_file.is_file():
            print("FILE EXISTS")
            return run(f"cd {dir_file.parent} && git diff {dir_file}", shell=True, capture_output=True,text=True)
        elif dir_file.is_dir() and (dir_file / ".git").exists():
            print("DIRECTORY EXISTS")
            return run(f"git -C diff {dir_file}", shell=True, capture_output=True,text=True)
        else:
            sys.exit(1) 

    def __init__(self, llama_model: str) -> None:
        self.Ollama_Model: OllamaModel = OllamaModel(
                host="http://localhost:11434",
                model_id=llama_model,
                options={"temperature": 0.0}
            )

        self.Agent: Agent = Agent(
                self.Ollama_Model,
                tools=[self.append_task, self.return_tasks],
                system_prompt="""First, check the database for existing tasks using the `return_tasks` tool, then if the task you are about to do exists, do not create a duplicate. Your job is to detect errors in the system and use the append_task tool to add them to a database, the tasks must be unique, provide your own issue summary, proposed fix, and also provide your own custom shell command to fix the error, and give them a status of 'pending', the issues you're being fed are git diffs on files / directories, track changes on them """,
                callback_handler=None
            ) 

    def agentic_loop(self) -> None:
        self.file_directory: prompt = Path(prompt("Input a file or directory to track (absolute / relative): ", placeholder=HTML("<style fg='#585b70'><b>File / directory</b></style>"))).expanduser() 
        if self.file_directory.exists(): 
            with Live(LAYOUT, refresh_per_second=1, auto_refresh = False, screen=True) as live:
                while True: 
                    self.Agent(f"""
                        Here is a list of existing tasks in the database: {self.return_tasks()}. To prevent duplicates, do not use the append_task tool if the task you're about to log exists in our database, log only UNIQUE issues. That said, here is a list of the git diff in a file / directory, track errors and bugs / syntax errors: {self.git_diff(self.file_directory)}
                    """)

                    LAYOUT["tasks"].update(Panel(self.refresh_task_list(self.return_task_list()),title="TASKS",title_align="left",style="#89b4fa"))

                    live.refresh()
                    sleep(15)
        else:
            Console().print("Directory or file is not valid!")

class UVICORN(TUI):
    def __init__(self) -> None:
        super().__init__()
        self.fastapi_server: FastAPI = FastAPI() 
        self.agent: AGENT = AGENT("qwen2.5-coder:3b")

        @self.fastapi_server.get("/tasks")
        async def task_route(session: Session = Depends(self.get_session)):
            all_tasks: List[Task_Template] = session.exec(select(Task_Template)).all()
            
            return {"tasks": all_tasks}

        @self.fastapi_server.on_event("startup")
        async def on_ready() -> str:
            print("UP AND RUNNING!")

        @self.fastapi_server.get("/")
        async def main_route() -> Dict[str, str]:
            return {"SUCCESS": "UP AND RUNNING!"} 
        
        @self.fastapi_server.patch("/tasks/{task_id}")
        async def change_task(task_id: int, task_status: str = Query(...), session: Session = Depends(self.get_session)) -> Union[str, None]:
            task: int = session.get(Task_Template,task_id)
            if task and task.status == "pending" and task_status.lower() in ["complete","pending"]:
                task.status = task_status
                session.add(task)
                session.commit()
                #Run task.shell_command here
                return f"TASK WITH ID: {task_id} changed successfully"
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Task does not exist or is not pending.")

        if self.user_choice == "server":
            self.run_uvicorn()
        elif self.user_choice == "create_database": 
            SQL_SETUP.create_db()
        else:
            self.agent.agentic_loop()
        
    def get_session(self) -> Session:
        with Session(SQL_SETUP.engine) as session:
            yield session 

    def run_uvicorn(self) -> None:
        run(self.CMD["clear_screen"])
        uvicorn.run(self.fastapi_server,host="127.0.0.1",port=8000)
