from derp.ast import NodeVisitor
from grammars.python import SourceGenerator
from lxml import etree as ET
from lxml.builder import E

from . import ast


def stmt_to_source(node):
    gen = SourceGenerator(' ' * 4)
    gen.visit(node)
    return ''.join(gen.result)

def stmts_to_source(body):
    gen = SourceGenerator(' ' * 4)
    for stmt in body:
        gen.visit(stmt)

    return ''.join(gen.result)


class Visitor(NodeVisitor):

    def visit_FormBlock(self, node, type_def):
        source_code = stmts_to_source(node.body)
        type_def.append(E.formblock(source_code))

    def visit_ValidateBlock(self, node, type_def):
        source_code = stmts_to_source(node.body)
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
        value = stmt_to_source(node.default)

        member = E.member(
            E.name(node.name),
            E.init(value)
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
    io.write(ET.tostring(xml, pretty_print=True).decode())
