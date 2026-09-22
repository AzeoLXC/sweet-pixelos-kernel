# PixelOS sweet Kernel with KernelSU-Next, SuSFS & NoMount

Automated CI/CD builder for Xiaomi Redmi Note 10 Pro / Pro Max (`sweet` / `sweetin`) stock PixelOS kernel with in-tree KernelSU-Next, SuSFS (Simulated User Space File System), and NoMount (VFS path redirection) support.

---

## Technical Specifications

| Parameter | Specification |
|---|---|
| Target Devices | Xiaomi Redmi Note 10 Pro (`sweet`), Redmi Note 10 Pro Max (`sweetin`) |
| SoC / Platform | Qualcomm Snapdragon 732G / SM6150 (`sdmsteppe`) |
| Linux Baseline | 4.14.357 LTS (`openela-VantomKernel`) |
| Upstream Baseline | [`PixelOS-Devices/android_kernel_xiaomi_sm6150:seventeen`](https://github.com/PixelOS-Devices/android_kernel_xiaomi_sm6150/tree/seventeen) |
| C/C++ Compiler | ZyCromerZ Clang 17.0.0 (`clang-17.0.0-20230725`) |
| Assembler / Linker | LLVM Integrated Assembler (`LLVM=1 LLVM_IAS=1`, `ld.lld`) |
| Cross Compilers | Greenforce Bare-Metal GCC (`aarch64-elf-` & `arm-eabi-`) |
| Defconfig | `arch/arm64/configs/sweet_defconfig` |
| Root Solution | KernelSU-Next (branch `legacy-susfs`, tag `v3.2.0-legacy`) |
| Root Stealth | SuSFS v1.5.5 (`simonpunk/susfs4ksu:kernel-4.14`) |
| Module Redirection | NoMount (`maxsteeel/nomount`, `CONFIG_NOMOUNT=y`) |
| Hook Implementation | Dynamic Kprobes (`CONFIG_KSU_KPROBES_HOOK=y`) |
| Output Artifact | AnyKernel3 flashable zip archive (`PixelOS-sweet-KernelSU-Next-SuSFS-NoMount-*.zip`) |

---

## Architecture & Modifications

### 1. In-Tree Root Integration (KernelSU-Next)
* **Dynamic Hook Mode**: Configured with `CONFIG_KSU_KPROBES_HOOK=y`, `CONFIG_KPROBES=y`, and `CONFIG_KRETPROBES=y` for non-GKI 4.14 syscall interception.
* **4.14 Timespec Alignment**: Injected patch into `KernelSU-Next/kernel/sulog/event.c` substituting legacy `get_monotonic_boottime` with `ktime_get_boottime_ts64(&ts)` to prevent `struct timespec64 *` pointer mismatch under Clang `-Werror`.
* **Signature Bypass & Manager Binding**: Native manager APK signature verification enabled for official KernelSU and KernelSU-Next manager applications.

### 2. Kernel Stealth Subsystem (SuSFS v1.5.5)
* **Mount Hiding**: Hides root mount entries from `/proc/self/mounts`, `/proc/self/mountinfo`, and `/proc/self/mountstat` using high `mnt_id` virtualization (`CONFIG_KSU_SUSFS_SUS_MOUNT=y`).
* **Path & Kstat Spoofing**: Obfuscates suspicious paths, `/proc/kallsyms` symbols, and file attributes from zygote-spawned non-root applications.
* **Syscall Spoofing**: Spoofs `/proc/cmdline` and `uname` syscall responses to mimic pristine stock configurations.

### 3. VFS Path Redirection (NoMount)
* **Mountless Module Loading**: Operates purely at the VFS layer (`fs/nomount/`, `CONFIG_NOMOUNT=y`) to redirect directory iterations and inode lookups without creating bind mounts or overlayfs mounts in `/proc/mounts`.
* **Process UID Isolation**: Restricts module filesystem changes to authorized processes while presenting a clean, stock filesystem view to untrusted and banking apps.

### 4. AnyKernel3 Boot Integrity
* **Non-Destructive Flashing**: Employs `split_boot` and `flash_boot` to unpack/repack only the kernel image (`Image.gz`) while preserving the stock OEM first-stage init ramdisk and device tree blob (`dtb`) exactly as shipped by the ROM.
* **SELinux & Partition Safety**: Eliminates ramdisk modification and cpio unpacking in recovery, preventing file context corruptions and splash-screen panics.

### 5. Pipeline Design
* **Job 1 (`check`)**: Queries upstream commit SHA from `PixelOS-Devices` and generates ISO build timestamps.
* **Job 2 (`build`)**: Compiles `Image.gz`, packages via AnyKernel3, generates SHA-256 checksums, and publishes a GitHub Release tagged with the build date (`YYYY.MM.DD`).
* **Job 3 (`notify`)**: Dispatches an HTML payload directly to Telegram group via Bot API with build metadata, SHA-256, and release download links.

---

## Flashing Instructions

### Prerequisites
* Unlocked bootloader.
* PixelOS (Android 17) installed.
* Custom recovery (TWRP or OrangeFox).

### Installation Steps
1. Download the latest `PixelOS-sweet-KernelSU-Next-SuSFS-NoMount-*.zip` and matching `.sha256` from [Releases](../../releases).
2. (Optional) Verify checksum:
   ```bash
   sha256sum -c PixelOS-sweet-KernelSU-Next-SuSFS-NoMount-*.zip.sha256
   ```
3. Reboot to custom recovery:
   ```bash
   adb reboot recovery
   ```
4. Flash the zip file directly (no cache or data wipe required).
5. Reboot to system.
6. Install [KernelSU-Next Manager APK](https://github.com/KernelSU-Next/KernelSU-Next/releases).

---

## Build Triggers

The workflow runs on-demand via `workflow_dispatch` without automatic commits or schedule polling:

1. Open **Actions** $\rightarrow$ **Build KernelSU Next PixelOS sweet**.
2. Click **Run workflow** (default branch: `legacy-susfs`).
3. Monitor build progress and receive the finished release link directly on Telegram.

---

## License

* Kernel source: [GNU General Public License v2.0 (GPL-2.0)](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html).
* AnyKernel3 packaging: [osm0sis](https://github.com/osm0sis/AnyKernel3).
