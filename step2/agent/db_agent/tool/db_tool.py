from typing import Annotated
from langchain_core.tools import tool
from langchain_experimental.utilities import PythonREPL


@tool
def python_repl(
        code: Annotated[str, "The python code to execute to generate your chart."],
):
    """
    파이썬 코드 실행 TOOL
    :param code:
    :return:
    """
    try:
        repl = PythonREPL()
        result = repl.run(code)
    except BaseException as e:
        return f"Failed to execute. Error: {repr(e)}"
    result_str = f"Successfully executed:\n```python\n{code}\n```\nStdout: {result}"
    return (
            result_str + "\n\nIf you have completed all tasks, respond with FINAL ANSWER."
    )
