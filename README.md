# 🎨 Painterly — Transform 3D Models into Artistic Masterpieces


## 🎯 Overview
Painterly is a powerful Blender add-on that revolutionizes 3D art creation by automatically generating stunning painterly effects on 3D models. Bridge the gap between technical 3D modeling and artistic expression with intuitive controls and professional-grade results.

## 🌟 Why Painterly?
- 🚀 **Instant Artistic Transformation**: Convert standard 3D models into painterly masterpieces in minutes
- 🎨 **Artist-Friendly Interface**: No programming knowledge required
- 🛠️ **Professional-Grade Results**: Production-ready output with PBR workflow support
- ⚡ **Efficient Workflow**: Reduce production time from days to minutes
- 🔄 **Non-Destructive Editing**: Experiment freely with full undo support

## 🎮 Key Features

### Artistic Control
- 🖌️ Customizable brush parameters for unique styles
- 🎯 Precise control over stroke placement and density
- 🌈 Enhanced normal maps for stunning 2.5D effects
- 🔍 Detail preservation with intelligent stroke placement
- 🧬 Seamless UV space handling

### Technical Excellence
- ⚙️ PBR workflow compatibility
- 📐 Advanced normal map generation
- 🔲 Smart edge detection and handling
- 🎯 Object-aware stroke placement
- 🔄 Batch processing support

## 🚀 Getting Started

### System Requirements
- Blender 2.93 or higher
- 8GB RAM minimum (16GB recommended)
- Graphics card with OpenGL 4.5 support

### Installation
1. Download the latest release from the [releases page](link-to-releases)
2. In Blender:
   - Navigate to Edit > Preferences > Add-ons
   - Click "Install" and select the downloaded `painterly.zip`
   - Enable "Painterly" in the add-ons list
3. Access Painterly in the N-panel (press N)

### Quick Start Guide
1. Select your 3D model
2. Open Painterly panel (N-panel)
3. Choose a preset or adjust parameters
4. Click "Apply" to generate effect
5. Fine-tune as needed

## ⚙️ Parameter Guide

### Brush Settings
| Parameter | Default | Description |
|-----------|---------|-------------|
| Width | 30-50 | Controls stroke width variation |
| Length | 40-80 | Determines stroke length range |
| Angle | 45° | Sets directional variation |
| Edge Noise | 2.0 | Adds natural edge variation |
| Sparsity | 0.001 | Controls stroke density |

### Advanced Options
- **UV Scale**: Adjust stroke size relative to UV space
- **Normal Strength**: Control the depth effect
- **Seed**: Change randomization pattern
- **Quality Steps**: Balance speed vs. quality

## 💡 Pro Tips
1. Start with presets to understand parameter effects
2. Use lower sparsity for detailed areas
3. Combine multiple passes for complex effects
4. Save your favorite parameters as custom presets
5. Enable backface culling for better performance

## 🔧 Development

### Setup Development Environment
```bash
# Clone repository
git clone https://github.com/your-username/painterly.git

# Install dependencies
pip install -r requirements.txt

# Link to Blender addons directory
## Windows
mklink /D "%APPDATA%\Blender Foundation\Blender\<version>\scripts\addons\painterly" "path\to\painterly"

## macOS/Linux
ln -s /path/to/painterly ~/Library/Application\ Support/Blender/<version>/scripts/addons/painterly
```

### Running Tests
```bash
python -m pytest tests/
```

## 🤝 Contributing
We welcome contributions! See our [Contributing Guide](CONTRIBUTING.md) for details.

### Areas for Contribution
- New brush styles and presets
- Performance optimizations
- UI/UX improvements
- Documentation and tutorials
- Bug fixes and testing
