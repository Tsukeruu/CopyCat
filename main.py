from typing import Dict, List, Union, Tuple, Any
from utils.UI import TUI
from utils.Server_init import UVICORN
from argparse import ArgumentParser
from requests import patch

class main_UI(UVICORN):
    def __init__(self) -> None:
        self.parser: ArgumentParser = ArgumentParser(description="A program that monitors tasks in the background and logs them using sqlmodel")
        self.parser.add_argument(
                "-cs",
                "--change-status",
                type=str,
                nargs=2,
                help="Change the status of a task with ID available status: ['pending','complete']",
                metavar=("ID","FINAL_STATUS")
            )
        
        self.args = self.parser.parse_args()
        
        if self.args.change_status:
            self.task_id_arg: int = int(self.args.change_status[0])
            self.task_status_arg: str = str(self.args.change_status[1])
            response: patch = patch(
                f"http://127.0.0.1:8000/tasks/{self.task_id_arg}",
                params={
                    "task_status": self.task_status_arg
                }
            )
            retur
        
        super().__init__()

app: main_UI = main_UI()
