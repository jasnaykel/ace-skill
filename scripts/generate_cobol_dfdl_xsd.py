#!/usr/bin/env python3
"""Generate the ACE COBOL DFDL XSD shape from a copybook.

This is a deterministic fallback for environments where the Toolkit importer
cannot be invoked headlessly. The resulting XSD must still pass ACE DFDL
validation before delivery.
"""

import argparse
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Node:
    level: int
    name: str
    pic: str | None = None
    occurs: int | None = None
    children: list["Node"] = field(default_factory=list)


LINE = re.compile(
    r"^\s*(\d+)\s+([A-Za-z0-9_-]+)"
    r"(?:\s+OCCURS\s+(\d+)\s+TIMES)?"
    r"(?:\s+PIC\s+([^\.]+))?\s*\."
    r"\s*$",
    re.IGNORECASE,
)


def parse_copybook(path: Path) -> Node:
    roots: list[Node] = []
    stack: list[Node] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        match = LINE.match(raw)
        if not match:
            continue
        level, name, occurs, pic = match.groups()
        node = Node(int(level), name, pic.strip() if pic else None, int(occurs) if occurs else None)
        while stack and stack[-1].level >= node.level:
            stack.pop()
        if stack:
            stack[-1].children.append(node)
        else:
            roots.append(node)
        stack.append(node)
    if len(roots) != 1:
        raise ValueError(f"Expected one level-01 root, found {len(roots)}")
    return roots[0]


def attrs(node: Node) -> str:
    if node.pic:
        pic = node.pic.upper().replace(" ", "")
        numeric = pic.startswith("9")
        length = re.search(r"\((\d+)\)", pic)
        if not length:
            raise ValueError(f"Unsupported PIC for {node.name}: {node.pic}")
        size = int(length.group(1))
        values = [f'dfdl:length="{size}"']
        if numeric:
            values.extend([
                'dfdl:ignoreCase="no"',
                f'dfdl:textNumberPattern="{"0" * size}+"',
                'dfdl:textStringJustification="right"',
                'dfdl:textStringPadCharacter="0"',
                'dfdl:textTrimKind="none"',
            ])
            default = '0'
        else:
            default = ' '
            if node.name.upper().startswith("ERDS"):
                values.append('dfdl:lengthUnits="characters"')
        return f'default="{default}" ' + " ".join(values)
    values = ['dfdl:lengthKind="implicit"']
    if node.occurs is not None:
        values.extend([f'maxOccurs="{node.occurs}"', f'minOccurs="{node.occurs}"'])
    return " ".join(values)


def render_children(nodes: list[Node], indent: str) -> list[str]:
    result = [f"{indent}<xsd:sequence>"]
    for node in nodes:
        result.extend(render_node(node, indent + "  "))
    result.append(f"{indent}</xsd:sequence>")
    return result


def render_node(node: Node, indent: str) -> list[str]:
    if node.pic:
        pic = node.pic.upper().replace(" ", "")
        numeric = pic.startswith("9")
        length = int(re.search(r"\((\d+)\)", pic).group(1))
        lines = [f"{indent}<xsd:element {attrs(node)} name=\"{node.name}\">"]
        lines.extend([
            f"{indent}  <xsd:annotation>",
        ])
        if not numeric:
            lines.extend([
                f"{indent}    <xsd:appinfo source=\"http://www.wsadie.com/appinfo\">",
                f"{indent}      <initialValue kind=\"SPACE\"/>",
                f"{indent}    </xsd:appinfo>",
            ])
        lines.extend([
            f"{indent}    <xsd:documentation>PIC {node.pic.strip()} display</xsd:documentation>",
            f"{indent}  </xsd:annotation>",
            f"{indent}  <xsd:simpleType>",
            f"{indent}    <xsd:restriction base=\"dfdlCobolFmt:PICX__string\">",
            f"{indent}      <xsd:maxLength value=\"{length}\"/>",
            f"{indent}    </xsd:restriction>",
            f"{indent}  </xsd:simpleType>",
            f"{indent}</xsd:element>",
        ])
        return lines

    lines = [f"{indent}<xsd:element {attrs(node)} name=\"{node.name}\">", f"{indent}  <xsd:complexType>"]
    lines.extend(render_children(node.children, indent + "    "))
    lines.extend([f"{indent}  </xsd:complexType>", f"{indent}</xsd:element>"])
    return lines


def render(root: Node, source: str) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
        '<xsd:schema xmlns:dfdl="http://www.ogf.org/dfdl/dfdl-1.0/" '
        'xmlns:dfdlCobolFmt="http://www.ibm.com/dfdl/CobolDataDefinitionFormat" '
        'xmlns:ibmDfdlExtn="http://www.ibm.com/dfdl/extensions" '
        'xmlns:ibmSchExtn="http://www.ibm.com/schema/extensions" '
        'xmlns:xsd="http://www.w3.org/2001/XMLSchema">',
        '  <xsd:import namespace="http://www.ibm.com/dfdl/CobolDataDefinitionFormat" '
        'schemaLocation="IBMdefined/CobolDataDefinitionFormat.xsd"/>',
        f'  <xsd:complexType name="{root.name}">',
        '    <xsd:sequence>',
    ]
    for child in root.children:
        lines.extend(render_node(child, "      "))
    lines.extend([
        '    </xsd:sequence>',
        '  </xsd:complexType>',
        '  <xsd:annotation>',
        '    <xsd:appinfo source="http://www.ogf.org/dfdl/">',
        '      <dfdl:format binaryFloatRep="{$dfdl:binaryFloatRep}" '
        'byteOrder="{$dfdl:byteOrder}" encoding="{$dfdl:encoding}" ignoreCase="yes" '
        'leadingSkip="0" occursCountKind="fixed" ref="dfdlCobolFmt:CobolDataFormat" '
        'textNumberPadCharacter="0" textStringJustification="left" '
        'textStringPadCharacter="%SP;" textZonedSignStyle="asciiStandard" trailingSkip="0"/>',
        '    </xsd:appinfo>',
        '  </xsd:annotation>',
        '  <xsd:annotation>',
        '    <xsd:documentation>',
        'This XSD was generated from a COBOL copybook.\n',
        f'Source file: {source}\n',
        'Import options: CODEPAGE=ISO-8859-1; ENDIAN=Little; '
        'PRESERVE_CASE_IN_VARIABLE_NAMES=true; STRING_PADDING_CHARACTER=%SP; '
        'NUMBER_PADDING_CHARACTER=0',
        '    </xsd:documentation>',
        '  </xsd:annotation>',
        f'  <xsd:element dfdl:lengthKind="implicit" ibmSchExtn:docRoot="true" '
        f'name="{root.name}" type="{root.name}"/>',
        '</xsd:schema>',
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("copybook", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    root = parse_copybook(args.copybook)
    args.output.write_text(render(root, args.copybook.name), encoding="utf-8")


if __name__ == "__main__":
    main()
