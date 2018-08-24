#!/usr/bin/env python
#
# memleak   Trace and display outstanding allocations to detect
#           memory leaks in user-mode processes and the kernel.
#
# USAGE: memleak [-h] [-p PID] [-t] [-a] [-o OLDER] [-c COMMAND]
#                [--combined-only] [-s SAMPLE_RATE] [-T TOP] [-z MIN_SIZE]
#                [-Z MAX_SIZE] [-O OBJ]
#                [interval] [count]
#
# Licensed under the Apache License, Version 2.0 (the "License")
# Copyright (C) 2016 Sasha Goldshtein.
# Copyright (C) 2018 Andrei Diaconu

from bcc import BPF
from time import sleep
from datetime import datetime
import resource
import argparse
import subprocess
import os
import sys


class Allocation(object):
    def __init__(self, size, name, pid):
        self.count = 1
        self.size = size
        self.name = name
        self.pid = pid

    def update(self, size):
        self.count += 1
        self.size += size


examples = """
EXAMPLES:

./memleak_uw -p $(pidof allocs)
        Trace allocations and display a summary of "leaked" (outstanding)
        allocations every 5 seconds
./memleak -ap $(pidof allocs) 10
        Trace allocations and display allocated addresses, sizes, and stacks
        every 10 seconds for outstanding allocations
./memleak
        Trace allocations in kernel mode and display a summary of outstanding
        allocations every 5 seconds
./memleak -o 60000
        Trace allocations in kernel mode and display a summary of outstanding
        allocations that are at least one minute (60 seconds) old
./memleak -s 5
        Trace roughly every 5th allocation, to reduce overhead
"""

description = """
Trace outstanding memory allocations that weren't freed.
Supports both user-mode allocations made with libc functions and kernel-mode
allocations made with kmalloc/kmem_cache_alloc/get_free_pages and corresponding
memory release functions.
"""

parser = argparse.ArgumentParser(description=description,
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=examples)
parser.add_argument("-t", "--trace", action="store_true",
                    help="print trace messages for each alloc/free call")
parser.add_argument("interval", nargs="?", default=5, type=int,
                    help="interval in seconds to print outstanding allocations")
parser.add_argument("count", nargs="?", type=int,
                    help="number of times to print the report before exiting")
parser.add_argument("-a", "--show-allocs", default=False, action="store_true",
                    help="show allocation addresses and sizes as well as call stacks")
parser.add_argument("-o", "--older", default=500, type=int,
                    help="prune allocations younger than this age in milliseconds")
parser.add_argument("--combined-only", default=False, action="store_true",
                    help="show combined allocation statistics only")
parser.add_argument("-s", "--sample-rate", default=1, type=int,
                    help="sample every N-th allocation to decrease the overhead")
parser.add_argument("-T", "--top", type=int, default=10,
                    help="display only this many top allocating stacks (by size)")
parser.add_argument("-z", "--min-size", type=int,
                    help="capture only allocations larger than this size")
parser.add_argument("-Z", "--max-size", type=int,
                    help="capture only allocations smaller than this size")
parser.add_argument("-O", "--obj", type=str, default="c",
                    help="attach to allocator functions in the specified object")

args = parser.parse_args()

trace_all = args.trace
interval = args.interval
min_age_ns = 1e6 * args.older
sample_every_n = args.sample_rate
num_prints = args.count
top_stacks = args.top
min_size = args.min_size
max_size = args.max_size
obj = args.obj

if min_size is not None and max_size is not None and min_size > max_size:
    print("min_size (-z) can't be greater than max_size (-Z)")
    exit(1)

bpf_source = """
#include <uapi/linux/ptrace.h>
#include <linux/sched.h>

struct alloc_info_t {
        u64 size;
        u64 timestamp_ns;
        int pid;
        char name[TASK_COMM_LEN];
};

BPF_HASH(sizes, u64);
//BPF_TABLE("hash", u64, struct alloc_info_t, allocs, 1);
BPF_HASH(allocs, u64, struct alloc_info_t);
BPF_HASH(memptrs, u64, u64);

static inline int gen_alloc_enter(struct pt_regs *ctx, size_t size) {
        u64 pid = bpf_get_current_pid_tgid();
        u64 size64 = size;
        sizes.update(&pid, &size64);
        return 0;
}

static inline int gen_alloc_exit2(struct pt_regs *ctx, u64 address) {
        u64 pid = bpf_get_current_pid_tgid();
        u64* size64 = sizes.lookup(&pid);
        struct alloc_info_t info = {0};

        if (size64 == 0)
                return 0; // missed alloc entry

        info.size = *size64;
        info.pid = pid;
        info.timestamp_ns = bpf_ktime_get_ns();
        sizes.delete(&pid);
        bpf_get_current_comm(&info.name, sizeof(info.name));

        allocs.update(&address, &info);

        return 0;
}

static inline int gen_alloc_exit(struct pt_regs *ctx) {
        return gen_alloc_exit2(ctx, PT_REGS_RC(ctx));
}

static inline int gen_free_enter(struct pt_regs *ctx, void *address) {
        u64 addr = (u64)address;
        struct alloc_info_t *info = allocs.lookup(&addr);
        if (info == 0)
                return 0;

        allocs.delete(&addr);

        return 0;
}

int malloc_enter(struct pt_regs *ctx, size_t size) {
        return gen_alloc_enter(ctx, size);
}

int malloc_exit(struct pt_regs *ctx) {
        return gen_alloc_exit(ctx);
}

int free_enter(struct pt_regs *ctx, void *address) {
        return gen_free_enter(ctx, address);
}

int calloc_enter(struct pt_regs *ctx, size_t nmemb, size_t size) {
        return gen_alloc_enter(ctx, nmemb * size);
}

int calloc_exit(struct pt_regs *ctx) {
        return gen_alloc_exit(ctx);
}

int realloc_enter(struct pt_regs *ctx, void *ptr, size_t size) {
        gen_free_enter(ctx, ptr);
        return gen_alloc_enter(ctx, size);
}

int realloc_exit(struct pt_regs *ctx) {
        return gen_alloc_exit(ctx);
}

int posix_memalign_enter(struct pt_regs *ctx, void **memptr, size_t alignment,
                         size_t size) {
        u64 memptr64 = (u64)(size_t)memptr;
        u64 pid = bpf_get_current_pid_tgid();

        memptrs.update(&pid, &memptr64);
        return gen_alloc_enter(ctx, size);
}

int posix_memalign_exit(struct pt_regs *ctx) {
        u64 pid = bpf_get_current_pid_tgid();
        u64 *memptr64 = memptrs.lookup(&pid);
        void *addr;

        if (memptr64 == 0)
                return 0;

        memptrs.delete(&pid);

        if (bpf_probe_read(&addr, sizeof(void*), (void*)(size_t)*memptr64))
                return 0;

        u64 addr64 = (u64)(size_t)addr;
        return gen_alloc_exit2(ctx, addr64);
}

int aligned_alloc_enter(struct pt_regs *ctx, size_t alignment, size_t size) {
        return gen_alloc_enter(ctx, size);
}

int aligned_alloc_exit(struct pt_regs *ctx) {
        return gen_alloc_exit(ctx);
}

int valloc_enter(struct pt_regs *ctx, size_t size) {
        return gen_alloc_enter(ctx, size);
}

int valloc_exit(struct pt_regs *ctx) {
        return gen_alloc_exit(ctx);
}

int memalign_enter(struct pt_regs *ctx, size_t alignment, size_t size) {
        return gen_alloc_enter(ctx, size);
}

int memalign_exit(struct pt_regs *ctx) {
        return gen_alloc_exit(ctx);
}

int pvalloc_enter(struct pt_regs *ctx, size_t size) {
        return gen_alloc_enter(ctx, size);
}

int pvalloc_exit(struct pt_regs *ctx) {
        return gen_alloc_exit(ctx);
}
"""

bpf_source = bpf_source.replace("SAMPLE_EVERY_N", str(sample_every_n))
bpf_source = bpf_source.replace("PAGE_SIZE", str(resource.getpagesize()))

stack_flags = "BPF_F_REUSE_STACKID"
stack_flags += "|BPF_F_USER_STACK"
bpf_source = bpf_source.replace("STACK_FLAGS", stack_flags)

bpf = BPF(text=bpf_source)


def attach_probes(sym, fn_prefix=None, can_fail=False):
    if fn_prefix is None:
        fn_prefix = sym

    try:
        bpf.attach_uprobe(name=obj, sym=sym,
                          fn_name=fn_prefix + "_enter")
        bpf.attach_uretprobe(name=obj, sym=sym,
                             fn_name=fn_prefix + "_exit")
    except Exception:
        if can_fail:
            return
        else:
            raise


attach_probes("malloc")
attach_probes("calloc")
attach_probes("realloc")
attach_probes("posix_memalign")
attach_probes("valloc")
attach_probes("memalign")
attach_probes("pvalloc")
attach_probes("aligned_alloc", can_fail=True)  # added in C11
bpf.attach_uprobe(name=obj, sym="free", fn_name="free_enter")


def print_outstanding():
    alloc_info = {}
    allocs = bpf["allocs"]
    for address, info in sorted(allocs.items(), key=lambda a: a[1].size):
        if BPF.monotonic_time() - min_age_ns < info.timestamp_ns:
            continue

        if info.pid in alloc_info:
            alloc_info[info.pid].update(info.size)
        else:
            alloc_info[info.pid] = Allocation(info.size,
                                              info.name.decode(),
                                              info.pid)
    to_show = sorted(alloc_info.values(),
                     key=lambda a: a.size)[-top_stacks:]  # top_stacks
    for alloc in to_show:
        if alloc.pid != os.getpid():
            # @TODO: Better way to deal with pid and count so that the tooltip
            # @TODO: of the treemap will know
            print("%d$$$%s" % (alloc.size,
                               alloc.name + "(" + str(alloc.pid) + ")"))


sleep(interval)
print_outstanding()
sys.stdout.flush()