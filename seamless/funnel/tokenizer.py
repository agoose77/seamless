from derp import Token
from grammars.python import PythonTokenizer
from ast import literal_eval


FUNNEL_KEYWORDS = frozenset(['Type', 'Enum', 'form', 'validate'])


class FunnelTokenizer(PythonTokenizer):

    def tokenize_readline(self, readline):
        for token in super().tokenize_readline(readline):
            if token.first == "ID":
                value = token.second

                if value in FUNNEL_KEYWORDS:
                    yield Token(value, value)
                else:
                    yield token

            else:
                yield token