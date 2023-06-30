import os
import pydantic
import pandas as pd
from csv import DictReader
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from project_time_allocation.core.engine.objects import Worker
from project_time_allocation.core.schemas.project import (
    ProjectHourSchema,
    ProjectReturnDialect,
    ProjectReturnSchema,
)
from project_time_allocation.core.schemas.worker import WorkerSchema


def validate_project_return_sheet(
        df: pd.DataFrame,
        index_offset: int = 2
) -> Tuple[Dict[str, Dict[str, Union[int, str, float]]], List]:
    df_dict_rows = df.to_dict(orient="index")
    projects_dict = {}
    bad_data = []
    for index, row in enumerate(df_dict_rows):
        try:
            pd_line_dict = (ProjectReturnSchema.parse_obj(df_dict_rows[row])).dict()
            projects_dict.update(
                {
                    pd_line_dict["project_id"]: {
                        k: pd_line_dict[k]
                        for k in set(list(pd_line_dict.keys())) - set(["project_id"])
                    }
                }
            )
        except pydantic.ValidationError as e:
            # Adds all validation error messages associated with the error
            # and adds them to the dictionary
            row['Errors'] = [error_message['msg'] for error_message in e.errors()]

            row['Error_row_num'] = index + index_offset
            bad_data.append(row)  #appends bad data to a different list of dictionaries
    return (projects_dict, bad_data)

def load_project_return_file(
    file_name: str, folder_name: Optional[Path] = None
) -> Dict[str, Dict[str, Union[int, str, float]]]:
    if folder_name is not None:
        path = folder_name.joinpath(folder_name).joinpath(file_name)
    else:
        path = Path(file_name)
    if not os.path.exists(path):
        raise Exception(f"The input file {path.resolve()} does not exists!")
    df = pd.read_csv(path)
    validate_project_return_sheet(df)
    projects_dict = {}
    with path.open("r") as file:
        reader = DictReader(file, dialect=ProjectReturnDialect())
        for row in reader:
            pd_line_dict = (ProjectReturnSchema.parse_obj(row)).dict()
            projects_dict.update(
                {
                    pd_line_dict["project_id"]: {
                        k: pd_line_dict[k]
                        for k in set(list(pd_line_dict.keys())) - set(["project_id"])
                    }
                }
            )
    return projects_dict


def load_project_hour_file(
    file_name: str, folder_name: Optional[Path] = None
) -> Dict[str, List[Dict[str, Dict[str, Union[int, str]]]]]:
    if folder_name is not None:
        path = folder_name.joinpath(folder_name).joinpath(file_name)
    else:
        path = Path(file_name)
    if not os.path.exists(path):
        raise Exception(f"The input file {path.resolve()} does not exists!")

    projects_hour_dict = {}
    with path.open("r") as file:
        reader = DictReader(file, dialect=ProjectReturnDialect())
        for row in reader:
            pd_line_dict = (ProjectHourSchema.parse_obj(row)).dict()
            worker_id_dict = {
                pd_line_dict["worker_id"]: {
                    k: pd_line_dict[k]
                    for k in set(list(pd_line_dict.keys()))
                    - set(["project_id", "worker_id"])
                }
            }
            if pd_line_dict["project_id"] not in projects_hour_dict:
                projects_hour_dict[pd_line_dict["project_id"]] = [worker_id_dict]
            else:
                projects_hour_dict[pd_line_dict["project_id"]].append(worker_id_dict)
    return projects_hour_dict


def load_worker_file(
    file_name: str, folder_name: Optional[Path] = None
) -> Dict[str, Worker]:
    if folder_name is not None:
        path = folder_name.joinpath(folder_name).joinpath(file_name)
    else:
        path = Path(file_name)
    if not os.path.exists(path):
        raise Exception(f"The input file {path.resolve()} does not exists!")

    workers_dict = {}
    with path.open("r") as file:
        reader = DictReader(file, dialect=ProjectReturnDialect())
        for row in reader:
            pd_line_dict = (WorkerSchema.parse_obj(row)).dict()
            workers_dict.update(
                {
                    pd_line_dict["worker_id"]: Worker(
                        worker_id=pd_line_dict["worker_id"],
                        worker_division=pd_line_dict["worker_division"],
                        number_workers=pd_line_dict["worker_numbers"],
                        total_hour_per_worker_per_year=pd_line_dict[
                            "number_hour_per_workers_per_year"
                        ],
                        cost_per_worker_per_hour=pd_line_dict[
                            "costs_per_worker_per_hour"
                        ],
                    )
                }
            )
    return workers_dict
