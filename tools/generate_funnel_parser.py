from grammars.ebnf import ParserGenerator as _ParserGenerator, EBNFTokenizer, e
from derp import parse


class ParserGenerator(_ParserGenerator):
    grammar_declaration = """
from derp import Grammar, lit
from grammars.python import p

{variable} = Grammar({name!r})
{rules}
{variable}.py_expr_stmt = p.expr_stmt
{variable}.py_simple_stmt = p.simple_stmt
{variable}.py_test = p.test
{variable}.py_suite = p.suite
{variable}.ensure_parsers_defined()
"""


if __name__ == "__main__":
    from pathlib import Path
    import seamless
    funnel_path = Path(seamless.__file__).parent / "funnel"
    output_filepath = funnel_path / "grammar.py"
    grammar_filepath = funnel_path / "grammar.ebnf"

    tokens = list(EBNFTokenizer().tokenize_file(grammar_filepath, True))
    result = parse(e.grammar, tokens)

    if not result:
        print("Failed to parse EBNF")

    elif len(result) > 1:
        print("Ambiguous parse of EBNF, mutliple parse trees")

    else:
        root = next(iter(result))
        print("==========Built AST============")
        # print(to_string(root))
        #
        # Generate parsers from AST
        generator = ParserGenerator(name='EBNF', variable='f')
        grammar = generator.visit(root)

        print("==========Built Grammar============")

        if False:
            with open(output_filepath, "w") as f:
                f.write(grammar)
        else:
            print(grammar)