# coding: utf-8
from contextlib import ExitStack


def nested(*context_managers):
    """Возвращает менеджер контекста с вложенными менеджерами.

    Пример использования:

    .. code-block:: python

       with nested(
           ContextManager1(),
           ContextManager1(),
           ContextManager1(),
       ):
           pass
    """
    exit_stack = ExitStack()

    for context_manager in context_managers:
        exit_stack.enter_context(context_manager)

    return exit_stack
