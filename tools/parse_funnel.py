from argparse import ArgumentParser
from pathlib import Path
from time import time

from derp.ast import write_ast
from derp import parse
from seamless.funnel import f, FunnelTokenizer


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
        output_filename = args.filepath.parent / "{}.ast".format(args.filepath.name)

        with open(output_filename, 'w') as out_file:
            write_ast(module, out_file)



if __name__ == "__main__":
    main()
