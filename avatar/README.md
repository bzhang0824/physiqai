# 2D Photo Morphing MVP

A simple cross-fade GIF generator using PIL (no numpy required). Creates smooth morphing animations between before/after fitness photos.

## Features

- **PIL-only implementation** - No numpy dependencies
- **Side-by-side image splitting** - Automatically splits progress pic collages
- **30-frame smooth animations** - With optional bounce (ping-pong) effect
- **User-friendly CLI** - Simple command-line interface

## Usage

### Generate 10 Example Morphs

```bash
python morphing.py --examples
```

### Create Custom Morph from Two Images

```bash
python morphing.py -b before.jpg -a after.jpg -o output.gif
```

### Create Morph from Side-by-Side Image

```bash
python morphing.py -b combined.jpg -o output.gif --bounce
```

### Full Options

```bash
python morphing.py -b before.jpg -a after.jpg \
    -o output.gif \
    --steps 30 \        # Number of frames (default: 30)
    --duration 80 \     # Milliseconds per frame (default: 80)
    --bounce \          # Ping-pong animation
    --size 512 512      # Output dimensions
```

## Output

All generated morphs are saved to:
```
projects/physiqai/avatar/morphs/
```

## Example Output Files

- `morph_01.gif` through `morph_10.gif` - 10 example morphs from the dataset
- Each GIF is ~4MB with 60 frames (30 forward + 30 back with bounce)

## How It Works

1. **Load Images**: Opens before and after images (or splits side-by-side)
2. **Resize**: Normalizes both images to 400x400 pixels
3. **Cross-fade**: Creates 30 frames blending from before → after
4. **Bounce**: Adds reverse frames for seamless looping
5. **Save**: Exports as animated GIF with 80ms frame duration

## Technical Details

- Uses `PIL.Image.blend()` for smooth alpha compositing
- LANCZOS resampling for high-quality resizing
- 400x400 output size for manageable file sizes
- 60 total frames (30 morph + 30 bounce back)
