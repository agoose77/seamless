from argparse import ArgumentParser
from pathlib import Path
from time import time

from copy import deepcopy

from derp.ast import write_ast, NodeVisitor
from derp import parse
from seamless.funnel import f, FunnelTokenizer

from lxml import etree as ET
from lxml.builder import E

from grammars.python import SourceGenerator
from grammars.python import ast as py_ast

class Visitor(NodeVisitor):

    def _py_block_to_source(self, body):
        gen = SourceGenerator(' ' * 4)
        for stmt in body:
            gen.visit(stmt)

        return ''.join(gen.result)

    def visit_FormBlock(self, node):
        source_code = self._py_block_to_source(node.body)
        return E.formblock(source_code)

    def visit_ValidateBlock(self, node):
        source_code = self._py_block_to_source(node.body)
        return E.validateblock(source_code)

    def visit_Docstring(self, node):
        return E.docstring(node.string)

    def visit_IDField(self, node):
        member = E.member(
            E.name(node.name),
            E.type(node.type)
        )

        return member

    def visit_EnumField(self, node):
        enum_string = ', '.join(repr(f) for f in node.options)
        member = E.member(
            E.name(node.name),
            E.type("String"),
            E.enum(enum_string)
        )
        return member

    def visit_Nullable(self, node):
        xml = self.visit(node.field)
        new_xml = deepcopy(xml)
        new_xml.set('optional', '1')
        return new_xml

    def visit_Default(self, node):
        xml = self.visit(node.field)
        new_xml = deepcopy(xml)
        new_xml.append(E.init(repr(node.value)))
        return new_xml


    def visit_FunnelType(self, node):
        type_ = E.silk(typename=node.name)
        for child in node.body:
            field = self.visit(child)
            type_.append(field)
        return type_

    def visit_FunnelModule(self, node):
        root = E.silkspace()

        for silk_type in node.types:
            tree = self.visit(silk_type)
            root.append(tree)

        return root


def write_xml(module, io):
    visitor = Visitor()
    xml = visitor.visit(module)
    print(ET.tostring(xml, pretty_print=True).decode())
    # print(etree.dump(etree.Element("Module")))



def main():
    parser = ArgumentParser(description='Python parser')
    parser.add_argument('filepath', type=Path)
    args = parser.parse_args()

    tokenizer = FunnelTokenizer()
    tokens = list(tokenizer.tokenize_file(args.filepath))
    print("Parsing: {} with {} tokens".format(args.filepath, len(tokens)))

    start_time = time()
    result = parse(f.file_input, tokens)
    finish_time = time()

    if not result:
        print("Failed to parse Python source")

    elif len(result) > 1:
        print("Ambiguous parse of Python source, mutliple parse trees")

    else:
        print("Parsed in {:.3f}s".format(finish_time - start_time))

        module = next(iter(result))
        out_ast_path = args.filepath.parent / "{}.ast".format(args.filepath.name)
        out_xml_path = args.filepath.parent / "{}.silkschema.xml".format(args.filepath.name)

        with open(out_ast_path, 'w') as out_file:
            write_ast(module, out_file)

        with open(out_xml_path, 'w') as out_file:
            write_xml(module, out_file)



if __name__ == "__main__":
    main()
