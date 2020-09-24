## Intro
[Maluch Racer 3 (AKA Bambino Rally 3, 2Fast Driver 2)](https://store.steampowered.com/app/469550/Bambino_Rally_3)
has an issue with user interface — it doesn't scale up with the game resolution.
In order to make it bigger, one has to modify the game files. However, a simple asset
upscaling is not enough because there are also references to them in .dso
(compiled code) and .mis ("mission", i.e. level) files.

## POC
`upscale.sh` is a little proof-of-concept script that you can use to upscale some
interface parts to 200%: minimap, speedometer and the lap counter. Just start it
from the game's directory, the whole process should take roughly 20 seconds.

```bash
$ cd /path/to/maluch_racer_3
$ /path/to/upscale.sh
```

After upscaling, each level load for the first time will trigger the lighting regeneration
process which might take some time (usually measured in minutes per level). Don't minimize
the game during that process to avoid crashes. 

## Requirements
- `bash`, `find`, `sed`
- `dso-tools`
- ImageMagick's `convert` (with support for dds and png) – GraphicsMagick doesn't support
  dds files
- (optionally) custom fonts: `LCDMono Light`, `Steelfish`. If you don't have them,
  some default one will be used by the game instead and it will look bad. Really bad.
