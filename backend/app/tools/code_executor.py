import logging
import asyncio
import tempfile
import os
from pathlib import Path

from app.tools.base import BaseTool, ToolParameter, ToolResult

logger = logging.getLogger("devagent.tools.code_executor")

EXECUTION_TIMEOUT = 10  
MAX_OUTPUT_LENGTH = 5000  


class CodeExecutorTool(BaseTool):

    @property
    def name(self) -> str:
        return "exec_code"

    @property
    def description(self) -> str:
        return (
            "Execute a Python code snippet in an isolated environment. "
            "Use this when the user wants to run code, test a function, "
            "or see the output of a script. Only Python is supported. "
            "The code runs with a 10-second timeout."
        )

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="code",
                type="string",
                description="Python code to execute",
            ),
            ToolParameter(
                name="language",
                type="string",
                description="Programming language (currently only 'python' is supported)",
                required=False,
                default="python",
                enum=["python"],
            ),
        ]

    async def execute(self, **kwargs) -> ToolResult:
        code = kwargs.get("code", "").strip()
        language = kwargs.get("language", "python")

        if not code:
            return ToolResult(success=False, output="", error="No code provided")

        if language != "python":
            return ToolResult(
                success=False,
                output="",
                error=f"Language '{language}' is not supported. Only Python is available.",
            )
        tmp_file = None
        try:
            tmp_file = tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".py",
                delete=False,
                prefix="devagent_exec_",
            )
            tmp_file.write(code)
            tmp_file.flush()
            tmp_file.close()
            process = await asyncio.create_subprocess_exec(
                "python", tmp_file.name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={
                    "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin"),
                    "HOME": tempfile.gettempdir(),
                    "PYTHONDONTWRITEBYTECODE": "1",
                },
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=EXECUTION_TIMEOUT,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.communicate() 
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Execution timed out after {EXECUTION_TIMEOUT} seconds. "
                    "Your code might have an infinite loop.",
                )

            stdout_text = stdout.decode("utf-8", errors="replace")[:MAX_OUTPUT_LENGTH]
            stderr_text = stderr.decode("utf-8", errors="replace")[:MAX_OUTPUT_LENGTH]

            if process.returncode == 0:
                output = stdout_text if stdout_text else "(No output)"

                logger.info("Code executed successfully (%d chars output)", len(output))
                return ToolResult(
                    success=True,
                    output=output,
                    metadata={
                        "return_code": 0,
                        "has_stderr": bool(stderr_text),
                    },
                )
            else:
                error_output = stderr_text or stdout_text or "Unknown error"

                logger.info("❌ Code execution failed (return code %d)", process.returncode)
                return ToolResult(
                    success=False,
                    output=stdout_text,
                    error=f"Code execution failed:\n{error_output}",
                    metadata={"return_code": process.returncode},
                )

        except Exception as e:
            logger.error("❌ Code executor error: %s", e, exc_info=True)
            return ToolResult(
                success=False,
                output="",
                error=f"Executor error: {str(e)}",
            )
        finally:
            if tmp_file and os.path.exists(tmp_file.name):
                try:
                    os.unlink(tmp_file.name)
                except OSError:
                    pass