# sweet-pixelos-kernel

Automated GitHub Actions builder for PixelOS sweet (Redmi Note 10 Pro / Pro Max) kernel with in-tree KernelSU-Next integration.

## Specifications

- **Target Devices**: Redmi Note 10 Pro (`sweet`), Redmi Note 10 Pro Max (`sweetin`)
- **Base Tree**: `SoloSaravanan/kernel_xiaomi_sm6150` (branch `17`, Android 17 baseline)
- **Linux Version**: 4.14.357 LTS
- **Toolchain**: ZyCromerZ Clang 17.0.0 + Greenforce GCC (arm64 & arm)
- **Root**: KernelSU-Next (`legacy` branch)
- **Output**: AnyKernel3 flashable zip archive

## How to Build

1. Go to **Actions** tab.
2. Select **Build KernelSU Next PixelOS sweet**.
3. Click **Run workflow**.
4. Once completed, download the flashable `.zip` from **Artifacts**.

## Flashing

1. Boot into custom recovery (TWRP / OrangeFox).
2. Flash the downloaded `PixelOS-sweet-KernelSU-Next-*.zip`.
3. Reboot to system and install [KernelSU-Next Manager APK](https://github.com/KernelSU-Next/KernelSU-Next/releases).

## License

GPL-2.0
