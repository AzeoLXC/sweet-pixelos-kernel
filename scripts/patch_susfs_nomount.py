#!/usr/bin/env python3
import os
import sys
import shutil
import argparse
import subprocess

def log(msg):
    print(f"[*] {msg}")

def run_cmd(cmd, cwd="."):
    res = subprocess.run(cmd, shell=True, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if res.returncode != 0:
        print(f"[!] Command exited {res.returncode}: {cmd}\n{res.stdout}")
        return False, res.stdout
    return True, res.stdout

def main():
    parser = argparse.ArgumentParser(description="Patch SuSFS, NoMount and KernelSU-Next into kernel tree")
    parser.add_argument("--ksu-repo", default="https://github.com/xtrance-eng/KernelSU-Next.git", help="KernelSU-Next git repo")
    parser.add_argument("--ksu-branch", default="legacy-susfs", help="KernelSU-Next git branch")
    args = parser.parse_args()

    kernel_dir = os.getcwd()
    log(f"Starting patch pipeline in: {kernel_dir}")

    # ----------------------------------------------------
    # 1. Setup KernelSU-Next
    # ----------------------------------------------------
    log(f"Setting up KernelSU-Next from {args.ksu_repo} (branch: {args.ksu_branch})...")
    ksu_dir = os.path.join(kernel_dir, "KernelSU-Next")
    if not os.path.exists(ksu_dir):
        ok, out = run_cmd(f"git clone --depth=1 -b {args.ksu_branch} {args.ksu_repo} KernelSU-Next")
        if not ok:
            log("Failed to clone KernelSU-Next")
            return 1

    drivers_dir = os.path.join(kernel_dir, "drivers")
    ksu_symlink = os.path.join(drivers_dir, "kernelsu")
    if not os.path.exists(ksu_symlink):
        os.symlink("../KernelSU-Next/kernel", ksu_symlink)
        log("Created drivers/kernelsu symlink")

    d_makefile = os.path.join(drivers_dir, "Makefile")
    with open(d_makefile, "r") as f:
        d_m = f.read()
    if "kernelsu" not in d_m:
        with open(d_makefile, "a") as f:
            f.write("\nobj-$(CONFIG_KSU) += kernelsu/\n")
        log("Added kernelsu to drivers/Makefile")

    d_kconfig = os.path.join(drivers_dir, "Kconfig")
    with open(d_kconfig, "r") as f:
        d_k = f.read()
    if 'source "drivers/kernelsu/Kconfig"' not in d_k:
        d_k = d_k.replace("endmenu", 'source "drivers/kernelsu/Kconfig"\nendmenu', 1)
        with open(d_kconfig, "w") as f:
            f.write(d_k)
        log("Added drivers/kernelsu/Kconfig to drivers/Kconfig")

    # ----------------------------------------------------
    # 2. Setup NoMount
    # ----------------------------------------------------
    log("Setting up NoMount (VFS redirection)...")
    nomount_dir = os.path.join(kernel_dir, "NoMount")
    if not os.path.exists(nomount_dir):
        ok, out = run_cmd("git clone --depth=1 https://github.com/maxsteeel/nomount.git NoMount")
        if not ok:
            log("Failed to clone NoMount")
            return 1

    fs_dir = os.path.join(kernel_dir, "fs")
    nm_symlink = os.path.join(fs_dir, "nomount")
    if not os.path.exists(nm_symlink):
        os.symlink("../NoMount/kernel/src", nm_symlink)
        log("Created fs/nomount symlink")

    fs_makefile = os.path.join(fs_dir, "Makefile")
    with open(fs_makefile, "r") as f:
        m_content = f.read()
    if "obj-$(CONFIG_NOMOUNT)" not in m_content:
        with open(fs_makefile, "a") as f:
            f.write("\nobj-$(CONFIG_NOMOUNT) += nomount/\n")
        log("Added nomount to fs/Makefile")

    fs_kconfig = os.path.join(fs_dir, "Kconfig")
    with open(fs_kconfig, "r") as f:
        k_content = f.read()
    if 'source "fs/nomount/Kconfig"' not in k_content:
        k_content = k_content.replace('endmenu', 'source "fs/nomount/Kconfig"\nendmenu', 1)
        with open(fs_kconfig, "w") as f:
            f.write(k_content)
        log("Added nomount to fs/Kconfig")

    # ----------------------------------------------------
    # 3. Setup SuSFS 4.14
    # ----------------------------------------------------
    log("Setting up SuSFS 4.14...")
    susfs_repo = os.path.join(kernel_dir, "susfs4ksu")
    if not os.path.exists(susfs_repo):
        ok, out = run_cmd("git clone --depth=1 -b kernel-4.14 https://gitlab.com/simonpunk/susfs4ksu.git susfs4ksu")
        if not ok:
            log("Failed to clone susfs4ksu")
            return 1

    # Copy fs files
    susfs_fs = os.path.join(susfs_repo, "kernel_patches", "fs")
    for f in os.listdir(susfs_fs):
        src = os.path.join(susfs_fs, f)
        dst = os.path.join(kernel_dir, "fs", f)
        shutil.copy2(src, dst)
        log(f"Copied fs/{f}")

    # Copy include files
    susfs_inc = os.path.join(susfs_repo, "kernel_patches", "include", "linux")
    for f in os.listdir(susfs_inc):
        src = os.path.join(susfs_inc, f)
        dst = os.path.join(kernel_dir, "include", "linux", f)
        shutil.copy2(src, dst)
        log(f"Copied include/linux/{f}")

    # Apply 50_add_susfs_in_kernel-4.14.patch
    patch_file = os.path.join(susfs_repo, "kernel_patches", "50_add_susfs_in_kernel-4.14.patch")
    log(f"Applying SuSFS patch: {patch_file}")
    run_cmd(f"patch -p1 -N -s < {patch_file}")

    # Fix fs/proc/cmdline.c for sweet's ALTER_CMDLINE structure
    cmdline_path = os.path.join(kernel_dir, "fs", "proc", "cmdline.c")
    if os.path.exists(cmdline_path):
        with open(cmdline_path, "r") as f:
            cmd_text = f.read()
        if "susfs_spoof_cmdline_or_bootconfig" not in cmd_text:
            patch_cmd_hdr = "#ifdef CONFIG_KSU_SUSFS_SPOOF_CMDLINE_OR_BOOTCONFIG\nextern int susfs_spoof_cmdline_or_bootconfig(struct seq_file *m);\n#endif\n"
            patch_cmd_show = "static int cmdline_proc_show(struct seq_file *m, void *v)\n{\n#ifdef CONFIG_KSU_SUSFS_SPOOF_CMDLINE_OR_BOOTCONFIG\n\tif (!susfs_spoof_cmdline_or_bootconfig(m)) {\n\t\tseq_putc(m, '\\n');\n\t\treturn 0;\n\t}\n#endif\n"
            cmd_text = cmd_text.replace("#include <linux/seq_file.h>", "#include <linux/seq_file.h>\n" + patch_cmd_hdr, 1)
            cmd_text = cmd_text.replace("static int cmdline_proc_show(struct seq_file *m, void *v)\n{", patch_cmd_show, 1)
            with open(cmdline_path, "w") as f:
                f.write(cmd_text)
            log("Patched fs/proc/cmdline.c for SuSFS")

    # Fix fs/proc/task_mmu.c header
    mmu_path = os.path.join(kernel_dir, "fs", "proc", "task_mmu.c")
    if os.path.exists(mmu_path):
        with open(mmu_path, "r") as f:
            mmu_text = f.read()
        if "CONFIG_KSU_SUSFS_SUS_KSTAT" not in mmu_text[:2000]:
            patch_mmu_hdr = "#ifdef CONFIG_KSU_SUSFS_SUS_KSTAT\n#include <linux/susfs_def.h>\n#endif\n"
            mmu_text = mmu_text.replace("#include <linux/mm_inline.h>", "#include <linux/mm_inline.h>\n" + patch_mmu_hdr, 1)
            with open(mmu_path, "w") as f:
                f.write(mmu_text)
            log("Patched fs/proc/task_mmu.c header for SuSFS")

    # Clean rejects
    for root, dirs, files in os.walk(kernel_dir):
        for f in files:
            if f.endswith(".rej") or f.endswith(".orig"):
                os.remove(os.path.join(root, f))

    # ----------------------------------------------------
    # 4. Kernel namespace & seccomp backports
    # ----------------------------------------------------
    ns_file = os.path.join(kernel_dir, "fs", "namespace.c")
    if os.path.exists(ns_file):
        with open(ns_file, "r") as f:
            ns_content = f.read()
        if "int path_umount" not in ns_content:
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
            if "static bool is_mnt_ns_file" in ns_content:
                ns_content = ns_content.replace("static bool is_mnt_ns_file", patch_ns + "static bool is_mnt_ns_file", 1)
                with open(ns_file, "w") as f:
                    f.write(ns_content)
                log("Patched fs/namespace.c with path_umount")

    hdr_file = os.path.join(kernel_dir, "fs", "internal.h")
    if os.path.exists(hdr_file):
        with open(hdr_file, "r") as f:
            hdr_content = f.read()
        if "int path_umount" not in hdr_content:
            if "extern void __init mnt_init(void);" in hdr_content:
                hdr_content = hdr_content.replace(
                    "extern void __init mnt_init(void);",
                    "extern void __init mnt_init(void);\nint path_umount(struct path *path, int flags);",
                    1
                )
                with open(hdr_file, "w") as f:
                    f.write(hdr_content)
                log("Patched fs/internal.h with path_umount declaration")

    sec_file = os.path.join(kernel_dir, "include", "linux", "seccomp.h")
    if os.path.exists(sec_file):
        with open(sec_file, "r") as f:
            sec_content = f.read()
        if "atomic_t filter_count;" not in sec_content:
            if "#include <linux/thread_info.h>" in sec_content:
                sec_content = sec_content.replace(
                    "#include <linux/thread_info.h>",
                    "#include <linux/thread_info.h>\n#include <linux/atomic.h>",
                    1
                )
            if "int mode;" in sec_content:
                sec_content = sec_content.replace("int mode;", "int mode;\n\tatomic_t filter_count;", 1)
                with open(sec_file, "w") as f:
                    f.write(sec_content)
                log("Patched include/linux/seccomp.h with filter_count")

    # Fix sulog/event.c timespec mismatch if present
    for sulog_candidate in [
        os.path.join(kernel_dir, "KernelSU-Next", "kernel", "sulog", "event.c"),
        os.path.join(kernel_dir, "drivers", "kernelsu", "sulog", "event.c")
    ]:
        if os.path.exists(sulog_candidate):
            with open(sulog_candidate, "r") as f:
                c = f.read()
            if "get_monotonic_boottime(&ts)" in c:
                c = c.replace("get_monotonic_boottime(&ts)", "ktime_get_boottime_ts64(&ts)")
                with open(sulog_candidate, "w") as f:
                    f.write(c)
                log("Patched sulog/event.c timespec64")

    # ----------------------------------------------------
    # 5. Append KSU, SuSFS & NoMount configs to sweet_defconfig
    # ----------------------------------------------------
    defconfig_path = os.path.join(kernel_dir, "arch", "arm64", "configs", "sweet_defconfig")
    if os.path.exists(defconfig_path):
        with open(defconfig_path, "a") as f:
            f.write("""
# KernelSU-Next
CONFIG_KSU=y
CONFIG_KPROBES=y
CONFIG_HAVE_KPROBES=y
CONFIG_KRETPROBES=y
CONFIG_HAVE_KRETPROBES=y
CONFIG_KSU_KPROBES_HOOK=y

# SuSFS 4.14
CONFIG_KSU_SUSFS=y
CONFIG_KSU_SUSFS_SUS_PATH=y
CONFIG_KSU_SUSFS_SUS_MOUNT=y
CONFIG_KSU_SUSFS_AUTO_ADD_SUS_KSU_DEFAULT_MOUNT=y
CONFIG_KSU_SUSFS_AUTO_ADD_SUS_BIND_MOUNT=y
CONFIG_KSU_SUSFS_SUS_KSTAT=y
CONFIG_KSU_SUSFS_TRY_UMOUNT=y
CONFIG_KSU_SUSFS_SPOOF_UNAME=y
CONFIG_KSU_SUSFS_ENABLE_LOG=y
CONFIG_KSU_SUSFS_HIDE_KSU_SUSFS_SYMBOLS=y
CONFIG_KSU_SUSFS_SPOOF_CMDLINE_OR_BOOTCONFIG=y
CONFIG_KSU_SUSFS_OPEN_REDIRECT=y
CONFIG_KSU_SUSFS_SUS_MAP=y

# NoMount
CONFIG_NOMOUNT=y
""")
        log("Appended KSU, SuSFS, and NoMount configs to sweet_defconfig")

    log("Kernel tree patching completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
