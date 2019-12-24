import sys
import logging
import argparse

log_level = logging.DEBUG
logging.basicConfig(level=log_level)


class Page:
    def __init__(self, order, stack):
        self.order = order
        self.stack = stack


class PageOwner:
    def __init__(self):
        # stack of current node
        self.stack = None
        # dict of {order: count} of current node
        self.page_count = {}
        self.pages = {}

    def add_page(self, page):
        self._add_page(page, page.stack)

    def _add_page(self, page, path, count=1):
        if not path:
            if self.stack is None:
                self.stack = page.stack
            cnt = self.page_count.get(page.order, 0)
            self.page_count[page.order] = cnt + count
        else:
            cur_path = path[0]
            rest_path = path[1:]
            if cur_path not in self.pages:
                self.pages[cur_path] = PageOwner()
            self.pages[cur_path]._add_page(page, rest_path, count)

    def __iter__(self):
        return self.all_pages(False)

    # compare with other page_owner
    def sub(self, other):
        for page_count, stack in other:
            for order, count in page_count.items():
                page = Page(order, stack)
                self._add_page(page, page.stack, 0-count)

    def all_pages(self, merge_by_stack):
        """Return ({order: count}, stack)
        """
        for pages in self.pages.values():
            yield from pages.all_pages(merge_by_stack)

        if self.stack is not None:
            if merge_by_stack:
                yield (self.page_count, self.stack)
            else:
                for order, count in self.page_count.items():
                    yield ({order: count}, self.stack)

    def sorted_pages(self, merge_by_stack, calc_space):
        """Return sorted pages of ({order: count}, stack)
        """
        iter_pages = self.all_pages(merge_by_stack)
        ret_pages = []
        if calc_space:
            for page_count, stack in iter_pages:
                ret_pages.append((sum([2**order * count for order, count in page_count.items()]), page_count, stack))
        else:
            for page_count, stack in iter_pages:
                ret_pages.append((sum([count for count in page_count.values()]), page_count, stack))

        ret_pages.sort(key=lambda x: x[0], reverse=True)
        return [(page_count, stack) for _, page_count, stack in ret_pages]

    def parse_one_page(self, lines):
        head = lines[0]
        frame = lines[1]
        stack = lines[2:]
        order = int(head.split(' ')[4].replace(',', ''))
        traceback = []
        for l in stack:
            traceback.append(l.strip())

        return Page(order, traceback)

    def parse_and_add_page(self, lines):
        page = self.parse_one_page(lines)
        self.add_page(page)


example_text = '''example:
# parse page_owner and sort by page count, consider difference of alloc order
    python3 parse_page_owner.py parse page_owner.txt
# parse page_owner and sort by page space, consider difference of alloc order
    python3 parse_page_owner.py --space parse page_owner.txt
# parse page_owner and sort by page count, do not consider difference of alloc order
    python3 parse_page_owner.py --merge-stack parse page_owner.txt
# parse page_owner and sort by page space, do not consider difference of alloc order
    python3 parse_page_owner.py --space --merge-stack parse page_owner.txt

# parse 2 page_owner and sort by page count, consider difference of alloc order
    python3 parse_page_owner.py diff page_owner_old.txt page_owner_new.txt
'''


def add_common_parser_options(parser):
    parser.add_argument('--space', dest='calc_page_space', help='calc page space when sorting', default=False, action='store_true')
    parser.add_argument('--merge-stack', dest='merge_stack', help='merge same stack allocation to one regardless of page order', default=False, action='store_true')


def parse_args_or_exit(argv=None):
    """
    Parse command line options
    """
    parser = argparse.ArgumentParser(prog='page_owner_parser',
                                     description='parse page_owner result',
                                     epilog=example_text,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    add_common_parser_options(parser)
    subparsers = parser.add_subparsers()

    search_parser = subparsers.add_parser('parse', help='parse_page_owner')
    search_parser.add_argument('file', help='page_owner_file')
    search_parser.set_defaults(cmd=parse_page_owner)

    get_parser = subparsers.add_parser('diff', help='diff 2 page_owner files')
    get_parser.add_argument('file_old', help='old_page_owner_file')
    get_parser.add_argument('file_new', help='new_page_owner_file')
    get_parser.set_defaults(cmd=diff_page_owner)

    args = parser.parse_args(argv)
    if 'cmd' not in args:
        parser.print_help()
        sys.exit(1)
    return args


def _parse_pages(filename):
    page_owner = PageOwner()
    idx = 0
    with open(filename) as f:
        lines = []
        for l in f:
            l = l.strip()
            if not l:
                if lines:
                    page_owner.parse_and_add_page(lines)
                    if idx % 10000 == 0:
                        logging.info('Parsing %d', idx)
                    idx += 1
                    lines = []
            else:
                lines.append(l)

        if lines:
            page_owner.parse_and_add_page(lines)

    return page_owner

def print_page_count(page_count):
    for order, count in page_count.items():
        print('PageOrder: {}, PageCount: {}'.format(order, count))

def print_stack(stack):
    print('Stack:')
    for s in stack:
        print(s)

def print_sorted_pages(pages):
    """pages: a list of ({order: count}, stack)
    """
    for page_count, stack in pages:
        print_page_count(page_count)
        print_stack(stack)
        print()

def parse_page_owner(args):
    page_owner = _parse_pages(args.file)
    sorted_pages = page_owner.sorted_pages(args.merge_stack, args.calc_page_space)
    print_sorted_pages(sorted_pages)


def diff_page_owner(args):
    page_owner_old = _parse_pages(args.file_old)
    page_owner_new = _parse_pages(args.file_new)
    page_owner_new.sub(page_owner_old)
    sorted_pages = page_owner_new.sorted_pages(args.merge_stack, args.calc_page_space)
    print_sorted_pages(sorted_pages)


def main(args_in):
    args = parse_args_or_exit(args_in)
    args.cmd(args)

if __name__ == '__main__':
    main(sys.argv[1:])
