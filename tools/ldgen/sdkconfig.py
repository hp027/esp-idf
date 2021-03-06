#
# Copyright 2018-2019 Espressif Systems (Shanghai) PTE LTD
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
from pyparsing import *

import sys
parent_dir_name = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
kconfig_new_dir = os.path.abspath(parent_dir_name + "/kconfig_new")
sys.path.append(kconfig_new_dir)
import kconfiglib



"""
Encapsulates an sdkconfig file. Defines grammar of a configuration entry, and enables
evaluation of logical expressions involving those entries.
"""
class SDKConfig:

    # A configuration entry is in the form CONFIG=VALUE. Definitions of components of that grammar
    IDENTIFIER = Word(printables.upper())

    HEX = Combine("0x" + Word(hexnums)).setParseAction(lambda t:int(t[0], 16))
    DECIMAL = Combine(Optional(Literal("+") | Literal("-")) + Word(nums)).setParseAction(lambda t:int(t[0]))
    LITERAL =  Word(printables)
    QUOTED_LITERAL = quotedString.setParseAction(removeQuotes)

    VALUE = HEX | DECIMAL | LITERAL | QUOTED_LITERAL

    # Operators supported by the expression evaluation
    OPERATOR = oneOf(["=", "!=", ">", "<", "<=", ">="])

    def __init__(self, kconfig_file, sdkconfig_file, env = []):
        env = [ (name, value) for (name,value) in ( e.split("=",1) for e in env) ]

        for name, value in env:
            value = " ".join(value.split())
            os.environ[name] = value

        self.config = kconfiglib.Kconfig(kconfig_file.name)
        self.config.load_config(sdkconfig_file.name)

    def evaluate_expression(self, expression):
        result = self.config.eval_string(expression)

        if result == 0: # n
            return False
        elif result == 2: # y
            return True
        else: # m
            raise Exception("Unsupported config expression result.")

    @staticmethod
    def get_expression_grammar():
        identifier = SDKConfig.IDENTIFIER.setResultsName("identifier")
        operator = SDKConfig.OPERATOR.setResultsName("operator")
        value = SDKConfig.VALUE.setResultsName("value")

        test_binary = identifier + operator + value
        test_single = identifier

        test = test_binary | test_single

        condition = Group(Optional("(").suppress() + test + Optional(")").suppress())

        grammar = infixNotation(
                condition, [
                ("!", 1, opAssoc.RIGHT),
                ("&&", 2, opAssoc.LEFT),
                ("||",  2, opAssoc.LEFT)])

        return grammar
