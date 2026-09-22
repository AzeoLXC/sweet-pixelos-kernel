PixelOS (Android 17) kernel for Redmi Note 10 Pro / Pro Max (`sweet` / `sweetin`) with in-tree KernelSU-Next, SuSFS, and NoMount.

### Install

Flash the latest zip from [Releases](../../releases) via recovery (TWRP / OrangeFox). No wipes needed.

Manager APK: [KernelSU-Next v3.2.0](https://github.com/KernelSU-Next/KernelSU-Next/releases/tag/v3.2.0-legacy) (matches legacy kernel driver).

### Notes

- **Base:** Linux 4.14.357 ([`PixelOS-Devices/android_kernel_xiaomi_sm6150:seventeen`](https://github.com/PixelOS-Devices/android_kernel_xiaomi_sm6150/tree/seventeen))
- **Toolchain:** ZyCromerZ Clang 17.0.0 + Greenforce bare-metal GCC (arm64/arm)
- **Root:** KernelSU-Next (`legacy-susfs`, dynamic kprobes)
- **Stealth:** SuSFS v1.5.5 (`simonpunk/susfs4ksu:kernel-4.14`)
- **Module Injection:** NoMount (`maxsteeel/nomount`, `CONFIG_NOMOUNT=y`)
- **AnyKernel3:** Uses `split_boot; flash_boot;` — untouched stock OEM ramdisk & DTB (prevents Android 17 SELinux / splash panics).
- **Zygote Fix:** Disabled `selinux_hide` write interception to prevent Android 14+ app launch crashes (`SIGABRT`).

### Trigger Build

```bash
gh workflow run build.yml
```
