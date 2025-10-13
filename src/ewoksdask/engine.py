from typing import Any
from typing import List
from typing import Optional
from typing import Union

from dask.distributed import Client
from ewokscore.engine_interface import RawExecInfoType
from ewokscore.engine_interface import WorkflowEngine

from . import bindings


class DaskWorkflowEngine(WorkflowEngine):

    def execute_graph(
        self,
        graph: Any,
        *,
        inputs: Optional[List[dict]] = None,
        load_options: Optional[dict] = None,
        varinfo: Optional[dict] = None,
        execinfo: RawExecInfoType = None,
        task_options: Optional[dict] = None,
        outputs: Optional[List[dict]] = None,
        merge_outputs: Optional[bool] = True,
        # Engine specific:
        scheduler: Union[dict, str, None, Client] = None,
        scheduler_options: Optional[dict] = None,
    ) -> dict:
        return bindings.execute_graph(
            graph,
            inputs=inputs,
            load_options=load_options,
            outputs=outputs,
            merge_outputs=merge_outputs,
            varinfo=varinfo,
            execinfo=execinfo,
            task_options=task_options,
            scheduler=scheduler,
            scheduler_options=scheduler_options,
        )
