import subprocess
import regex
import os
import fcntl


def setup(__program, abc, filename):
    if abc is not None:
        abc.stdin.write('quit\n')
    abc = subprocess.Popen([__program], shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                           universal_newlines=True)
    flags = fcntl.fcntl(abc.stdout, fcntl.F_GETFL)
    fcntl.fcntl(abc.stdout, fcntl.F_SETFL, flags | os.O_NONBLOCK)
    filename = filename
    abc.stdin.write('read {}\n'.format(filename))
    abc.stdin.flush()
    __skip_until_echo(abc)


def __run(abc, cmd):
    abc.stdin.write('{}; print_stats\n'.format(cmd))
    abc.stdin.flush()
    line = abc.stdout.readline()
    while 'lev' not in line:
        abc.stdin.flush()
        line = abc.stdout.readline()
    tokens = regex.compile('[ =\n\r]+').split(line)
    size_index = tokens.index('and') + 1
    size = int(tokens[size_index])
    depth_index = tokens.index('lev') + 1
    depth = int(tokens[depth_index])
    return [size, depth]


def __skip_until_echo(abc):
    line = abc.stdout.readlines()
    while regex.compile('^abc.*>').match(str(line)) is None:
        abc.stdin.flush()
        line = abc.stdout.readline()
    if ((regex.compile('Generic file reader requires a known file').match(line) is True) or (
            regex.compile('Cannot open').match(line) is True)):
        print('file open failed\n')
        return 1
    return 0


ACTION_LIB = {
    0: 'balance',
    1: 'rewrite',
    2: 'rewrite -z',
    3: 'refactor',
    4: 'refactor -z',
    5: 'balance -l',
    6: 'rewrite -l',
    7: 'rewrite -z -l',
    8: 'refactor -l ',
    9: 'refactor -z -l',
    #           10: 'resub -K 6',
    #           11: 'resub -K 6 -N 2',
    #           12: 'resub -K 8',
    #           13: 'resub -K 8 -N 2',
    #           14: 'resub -K 10',
    #           15: 'resub -K 10 -N 2',
    #           16: 'resub -K 12',
    #           17: 'resub -K 12 -N 2
    18: 'balance;rewrite;rewrite -z;balance;rewrite -z;balance',
    19: 'balance;rewrite;refactor;balance;rewrite;rewrite -z;balance;refactor -z;rewrite -z;balance'
}
