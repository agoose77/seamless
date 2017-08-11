from argparse import ArgumentParser
from pathlib import Path
from time import time

from copy import deepcopy

from derp.ast import write_ast, NodeVisitor, walk
from derp import parse
from seamless.funnel import f, FunnelTokenizer, ast

from lxml import etree as ET
from lxml.builder import E

from grammars.python import SourceGenerator
from grammars.python import ast as py_ast

def find_ast(node, cls):
    for n in walk(node):
        if isinstance(n, cls):
            yield n


class Visitor(NodeVisitor):

    def _py_block_to_source(self, body):
        gen = SourceGenerator(' ' * 4)
        for stmt in body:
            gen.visit(stmt)

        return ''.join(gen.result)

    def visit_FormBlock(self, node, type_def):
        source_code = self._py_block_to_source(node.body)
        type_def.append(E.formblock(source_code))

    def visit_ValidateBlock(self, node, type_def):
        source_code = self._py_block_to_source(node.body)
        type_def.append(E.validateblock(source_code))

    def visit_Docstring(self, node, type_def):
        type_def.append(E.docstring(node.string))

    def append_type_info(self, member, type_, type_def):
        if isinstance(type_, ast.EnumType):
            enum_string = ', '.join(repr(f) for f in type_.options)
            member.append(E.enum(enum_string))
            member.append(E.type("String"))

        elif isinstance(type_, ast.GenericType):
            member.append(E.type(type_.id))

        else:
            self.append_type_info(member, type_.etype, type_def)
            member.append(E.array(str(type_.length)))

    def visit_OptionalField(self, node, type_def):
        member = E.member(
            E.name(node.name),
            optional='1'
        )
        self.append_type_info(member, node.type, type_def)
        type_def.append(member)

    def visit_Field(self, node, type_def):
        member = E.member(
            E.name(node.name),
        )
        self.append_type_info(member, node.type, type_def)
        type_def.append(member)

    def visit_DefaultField(self, node, type_def):
        member = E.member(
            E.name(node.name),
            E.init(str(node.default))
        )
        self.append_type_info(member, node.type, type_def)
        type_def.append(member)

    def visit_FunnelType(self, node, module):
        type_def = E.silk(typename=node.name)
        module.append(type_def)

        for child in node.body:
            self.visit(child, type_def=type_def)

    def visit_FunnelModule(self, node):
        root = E.silkspace()

        for silk_type in node.types:
            self.visit(silk_type, module=root)

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
        print("Failed to parse Funnel source")

    elif len(result) > 1:
        print("Ambiguous parse of Funnel source, mutliple parse trees")

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
