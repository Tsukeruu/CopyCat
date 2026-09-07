from typing import Dict, List, Union, Any, Tuple, ClassVar
from dataclasses import dataclass
from enum import Enum

from prompt_toolkit.shortcuts import choice
from prompt_toolkit.formatted_text import HTML

from platform import system
from dataclasses import dataclass, field
from subprocess import run

from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout
from rich.columns import Columns
from rich.table import Table
from rich.box import MINIMAL, SIMPLE
from sqlmodel import SQLModel, Session, select
from .database import SQL_SETUP, Task_Template
from sqlalchemy.exc import OperationalError

from .GLOBAL import TABLE, LAYOUT

class Colors(Enum):
    pass

@dataclass
class Elements:
    ASCII_ART: str = r"""
    |\__/,|   (`\
  _.|o o  |_   ) )
-(((---(((--------
    """
    PROMPT_TK_OPTIONS: List[Tuple[str]] = field(default_factory=lambda: [
            ("server", "Start the server (uvicorn)"),
            ("start_agent", "Start the agent directly"),
            ("create_database","Create a database to connect the fastapi framework to sqlmodel")
        ])
    PROMPT_TK_PROMPT: str = "How would you like to get started?"
    PLATFORMS: List[str] = field(default_factory=lambda: ["Linux", "Darwin", "Windows"])
    DESCRIPTION: str = """
    [#cdd6f4]
[#fab387 b]DESCRIPTION[/#fab387 b]
    - CopyCat utilizes strands sdk agents to automate regular human tasks by taking appointed files and monitoring them.
    - CopyCat encounters errors and stores them in a sql database located in the utils folder.
    - Tasks are stored in the fastapi server which is hosted by uvicorn and in the database.\n
[#f9e2af b]FIXES[/#f9e2af b]
    [#f38ba8 b]- 4/9/2026[/#f38ba8 b]
        - [!] NOT YET  
        \n
[#f2cdcd b]UPDATES[/#f2cdcd b]
    [#f9e2af b]- 4/9/2026[/#f9e2af b]
        - [+] Created fastapi PATCH method to change tasks' status
        - [+] Created table of pending tasks
        - [+] Added user input for file / directory tracking
    [#f9e2af b]- 7/9/2026[/#f9e2af b]
        - [+] Created installation script 
        - [+] Created live table view of updating tasks
        - [+] Added argparsing for task status changing
        \n
[#94e2d5 b]NOTES[/#94e2d5 b]
    - By changing the status of a task in the database, note that the task will automatically execute the shell script proposed by the llm, review the changes carefully!
    [/#cdd6f4]
    """
    CONSOLE: Console = Console()

    def __post_init__(self) -> None:
        self.CMD: Dict[str, str] = {"clear_screen": "clear" if system() in self.PLATFORMS[0:2] else "cls"}

class TUI(Elements):
    def __init__(self) -> None:
       super().__init__()
       run(self.CMD["clear_screen"], shell=True) 
       #self.table: Table = Table(expand=True,box=SIMPLE,header_style="bold #f9e2af",style="#585b70")
       TABLE.add_column("ID",style="#fab387")
       TABLE.add_column("STATUS")
       TABLE.add_column("ISSUE SUMMARY")
       TABLE.add_column("PROPOSED FIX")
       TABLE.add_column("PROPOSED SHELL SCRIPT")
       self.init_task_list(self.return_task_list())
       #self.layout: Layout = self.return_layout()
       self.CONSOLE.print(self.return_layout())
       #self.CONSOLE.print(Panel.fit("[#5e81ac]" + self.ASCII_ART + "[/#5e81ac]", subtitle="[#81a1c1 b]copycat v0.0.1[/#81a1c1 b]", subtitle_align="left",border_style="#81a1c1"))
       self.construct_user_choice()

    def construct_user_choice(self) -> choice:
         self.user_choice: choice = choice(
                options=self.PROMPT_TK_OPTIONS,
                message=HTML(f"<style fg='#cba6f7'><b>{self.PROMPT_TK_PROMPT}</b></style>"),
                default="server"
            )

         return self.user_choice

    def return_layout(self) -> Layout:
       #self.layout: Layout = Layout()
       LAYOUT.split_column(
            Layout(name='header',size=3),
            Layout(name='main'),
            Layout(name='footer',size=3)
        )
       LAYOUT["main"].split_row(
            Layout(name="sidebar",ratio=3),
            Layout(name="tasks",ratio=2)
        )
       
       LAYOUT["header"].update(Panel("[#b4befe]CopyCat[/#b4befe]", title="[#89b4fa]v 0.0.1[/#89b4fa]", title_align="left",style="#585b70"))
       LAYOUT["sidebar"].update(Panel(f"[#b18be0 b]{self.ASCII_ART}[/#b18be0 b]\n[#b4befe]{self.DESCRIPTION}[/#b4befe]",title="ABOUT",title_align="left",style="#585b70")) 
       LAYOUT["tasks"].update(Panel(TABLE,title="TASKS",title_align="left",style="#89b4fa"))
       LAYOUT["footer"].update(Panel("[#fab387 b]CTRL+C to quit[/#fab387 b]  •  [#f9e2af b]ENTER to submit fields[/#f9e2af b]",title="KEYBINDS",title_align="left", style="#585b70"))
       return LAYOUT
    
    def refresh_task_list(self,tasks: List[Task_Template]) -> Table:
        new_table: Table = Table(title="[#a6e3a1 b]• STATUS: ACTIVELY SEARCHING FOR BUGS![/#a6e3a1 b]",expand=True, box=SIMPLE, header_style="bold #f9e2af", style="#585b70")
        new_table.add_column("ID", style="#fab387")
        new_table.add_column("STATUS")
        new_table.add_column("ISSUE SUMMARY")
        new_table.add_column("PROPOSED FIX")
        new_table.add_column("PROPOSED SHELL SCRIPT")

        try:
            for task in tasks:
                if task:
                    new_table.add_row(str(task.Id),f"[#f9e2af]{str(task.status)}[/#f9e2af]",f"[#cdd6f4 b]{str(task.issue_summary)}[/#cdd6f4 b]",f"[#cdd6f4 b]{str(task.proposed_fix+"\n")}[/#cdd6f4 b]",f"[#a6e3a1]{str(task.shell_command)}[/#a6e3a1]")
        except TypeError as e:
            new_table.add_row("NULL","NULL","NULL","NULL","NULL")

        return new_table

    def init_task_list(self, tasks: List[Task_Template]) -> Table:
        try:
            for task in tasks:
                if task:
                    TABLE.add_row(str(task.Id),f"[#f9e2af]{str(task.status)}[/#f9e2af]",f"[#cdd6f4 b]{str(task.issue_summary)}[/#cdd6f4 b]",f"[#cdd6f4 b]{str(task.proposed_fix+"\n")}[/#cdd6f4 b]",f"[#a6e3a1]{str(task.shell_command)}[/#a6e3a1]")
        except TypeError as e:
            TABLE.add_row("NULL","NULL","NULL","NULL","NULL")

        return TABLE

    def return_task_list(self) -> List[Task_Template]:
        try:
            with Session(SQL_SETUP.engine) as session:
                return session.exec(select(Task_Template).where(Task_Template.status=="pending")).all()
        except OperationalError as e:
            print("DATABASE DOES NOT HAVE TABLE")
