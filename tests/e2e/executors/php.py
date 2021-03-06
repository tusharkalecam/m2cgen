import os
import string

from m2cgen import assemblers, interpreters
from tests import utils
from tests.e2e.executors import base

EXECUTOR_CODE_TPL = """
<?php
$$inputArray = array();
for ($$i = 1; $$i < $$argc; ++$$i) {
    $$inputArray[] = floatval($$argv[$$i]);
}

require '${model_file}.php';

$$res = score($$inputArray);

${print_code}
"""

EXECUTE_AND_PRINT_SCALAR = """
echo($res);
"""

EXECUTE_AND_PRINT_VECTOR = """
echo(implode(" ", $res));
"""


class PhpExecutor(base.BaseExecutor):

    executor_name = "score"
    model_name = "model"

    def __init__(self, model):
        self.model = model
        self.interpreter = interpreters.PhpInterpreter()

        assembler_cls = assemblers.get_assembler_cls(model)
        self.model_ast = assembler_cls(model).assemble()

        self._php = "php"

    def predict(self, X):
        file_name = os.path.join(self._resource_tmp_dir,
                                 "{}.php".format(self.executor_name))
        exec_args = [self._php,
                     "-f",
                     file_name,
                     *map(str, X)]
        return utils.predict_from_commandline(exec_args)

    def prepare(self):
        if self.model_ast.output_size > 1:
            print_code = EXECUTE_AND_PRINT_VECTOR
        else:
            print_code = EXECUTE_AND_PRINT_SCALAR
        executor_code = string.Template(EXECUTOR_CODE_TPL).substitute(
            model_file=self.model_name,
            print_code=print_code)
        model_code = self.interpreter.interpret(self.model_ast)

        executor_file_name = os.path.join(
            self._resource_tmp_dir, "{}.php".format(self.executor_name))
        model_file_name = os.path.join(
            self._resource_tmp_dir, "{}.php".format(self.model_name))
        with open(executor_file_name, "w") as f:
            f.write(executor_code)
        with open(model_file_name, "w") as f:
            f.write(model_code)
