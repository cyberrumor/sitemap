#!/usr/bin/env python3

import sys

if __name__ == '__main__':
    # user provides file name
    file = sys.argv[-1]

    # get all lines of that file, deduplicated
    all_contents = []
    with open(file, 'r') as f:
        for i in f:
            if i not in all_contents:
                all_contents.append(i)


    # write the sorted  contents to that file
    with open(file, 'w') as f:
        for i in sorted(all_contents):
            f.write(i)

