import sys
import logging
import argparse

log_level = logging.DEBUG
logging.basicConfig(level=log_level)


class Slab:
    def __init__(self, name, active_objs, num_objs, obj_size, objs_per_slab, pages_per_slab, active_slabs, num_slabs, shared_avail):
        self.name = name
        self.active_objs = active_objs
        self.num_objs = num_objs
        self.obj_size = obj_size
        self.objs_per_slab = objs_per_slab
        self.pages_per_slab = pages_per_slab
        self.active_slabs = active_slabs
        self.num_slabs = num_slabs
        self.shared_avail = shared_avail

    def __str__(self):
        return f'{self.name} {self.num_pages()}'

    @classmethod
    def from_slab_info(cls, line):
        try:
            line = line.strip()
            parts = line.split(':')
            parts = [part.strip() for part in parts]
            base_info, _, slabdata = parts[0], parts[1], parts[2]
            def __split_info(info):
                info = [x for x in info.split(' ') if x != '']
                return [info[0]] + [int(x) for x in info[1:]]

            b = __split_info(base_info)
            s = __split_info(slabdata)
            return Slab(b[0], b[1], b[2], b[3], b[4], b[5], s[1], s[2], s[3])
        except:
            logging.error('Fail to parse %s', line)
            raise

    def num_pages(self):
        return self._pages_of_objs(self.num_objs)

    def active_pages(self):
        return self._pages_of_objs(self.active_objs)

    def _pages_of_objs(self, obj_cnt):
        return int(obj_cnt / self.objs_per_slab * self.pages_per_slab)

    def _space_of_pages(self, page_cnt):
        return page_cnt * 4 * 1024

    def total_space(self):
        return self._space_of_pages(self.num_pages())

    def active_space(self):
        return self._space_of_pages(self.active_pages())

example_text = '''Examples:
    python slab_info_parse.py slab_info
'''


def parse_args_or_exit(argv=None):
    """
    Parse command line options
    """
    parser = argparse.ArgumentParser(prog='slab_info_parser',
                                     description='parse /proc/slab_info',
                                     epilog=example_text,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('file', help='slab_info file')
    return parser.parse_args(argv)

def parse_slab_info(file_name):
    slabs = []
    with open(file_name) as f:
        for line in f:
            if line.startswith('slabinfo - version') or \
               line.startswith('#'):
                continue

            slab = Slab.from_slab_info(line)
            slabs.append(slab)

    return slabs


def sort_slabs(slabs):
    slabs.sort(key=lambda x: x.num_pages(), reverse=True)
    return slabs


def print_slabs(slabs):
    for slab in slabs:
        print(slab)


def main(args_in):
    args = parse_args_or_exit(args_in)
    slabs = parse_slab_info(args.file)
    slabs = sort_slabs(slabs)
    print_slabs(slabs)


if __name__ == '__main__':
    main(sys.argv[1:])
