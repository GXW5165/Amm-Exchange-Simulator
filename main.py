"""项目命令行入口。

无参数运行时进入交互式菜单；传入 `--config` 或 `--demo` 时执行非交互式
仿真，便于课程验收和脚本复现。
"""

from src.interface.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
