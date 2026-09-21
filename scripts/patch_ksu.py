#!/usr/bin/env python3
import sys
import os

def patch_ksu():
    print("[*] Applying KernelSU-Next pre-build patches to kernel tree...")

    # 1. fs/namespace.c (path_umount and can_umount)
    ns_file = "fs/namespace.c"
    if os.path.exists(ns_file):
        with open(ns_file, "r") as f:
            content = f.read()
        if "int path_umount" not in content:
            patch_ns = """static int can_umount(const struct path *path, int flags)
{
\tstruct mount *mnt = real_mount(path->mnt);
\tif (flags & ~(MNT_FORCE | MNT_DETACH | MNT_EXPIRE | UMOUNT_NOFOLLOW))
\t\treturn -EINVAL;
\tif (!may_mount())
\t\treturn -EPERM;
\tif (path->dentry != path->mnt->mnt_root)
\t\treturn -EINVAL;
\tif (!check_mnt(mnt))
\t\treturn -EINVAL;
\tif (mnt->mnt.mnt_flags & MNT_LOCKED)
\t\treturn -EINVAL;
\tif (flags & MNT_FORCE && !capable(CAP_SYS_ADMIN))
\t\treturn -EPERM;
\treturn 0;
}

int path_umount(struct path *path, int flags)
{
\tstruct mount *mnt = real_mount(path->mnt);
\tint ret;
\tret = can_umount(path, flags);
\tif (!ret)
\t\tret = do_umount(mnt, flags);
\tdput(path->dentry);
\tmntput_no_expire(mnt);
\treturn ret;
}

"""
            if "static bool is_mnt_ns_file" in content:
                content = content.replace("static bool is_mnt_ns_file", patch_ns + "static bool is_mnt_ns_file", 1)
                with open(ns_file, "w") as f:
                    f.write(content)
                print("[+] Patched fs/namespace.c with path_umount")
            else:
                print("[-] Could not find anchor in fs/namespace.c")

    # 2. fs/internal.h
    hdr_file = "fs/internal.h"
    if os.path.exists(hdr_file):
        with open(hdr_file, "r") as f:
            content = f.read()
        if "int path_umount" not in content:
            if "extern void __init mnt_init(void);" in content:
                content = content.replace(
                    "extern void __init mnt_init(void);",
                    "extern void __init mnt_init(void);\nint path_umount(struct path *path, int flags);",
                    1
                )
                with open(hdr_file, "w") as f:
                    f.write(content)
                print("[+] Patched fs/internal.h with path_umount declaration")
            else:
                print("[-] Could not find anchor in fs/internal.h")

    # 3. include/linux/seccomp.h
    sec_file = "include/linux/seccomp.h"
    if os.path.exists(sec_file):
        with open(sec_file, "r") as f:
            content = f.read()
        if "atomic_t filter_count;" not in content:
            if "#include <linux/thread_info.h>" in content:
                content = content.replace(
                    "#include <linux/thread_info.h>",
                    "#include <linux/thread_info.h>\n#include <linux/atomic.h>",
                    1
                )
            if "int mode;" in content:
                content = content.replace("int mode;", "int mode;\n\tatomic_t filter_count;", 1)
                with open(sec_file, "w") as f:
                    f.write(content)
                print("[+] Patched include/linux/seccomp.h with filter_count")
            else:
                print("[-] Could not find anchor in include/linux/seccomp.h")

    # 4. KernelSU-Next event.c timespec mismatch fix
    sulog_file = "KernelSU-Next/kernel/sulog/event.c"
    if os.path.exists(sulog_file):
        with open(sulog_file, "r") as f:
            content = f.read()
        if "get_monotonic_boottime(&ts)" in content:
            content = content.replace("get_monotonic_boottime(&ts)", "ktime_get_boottime_ts64(&ts)")
            with open(sulog_file, "w") as f:
                f.write(content)
            print("[+] Patched KernelSU-Next event.c timespec64")

    print("[*] Pre-build patch complete.")

if __name__ == "__main__":
    patch_ksu()
