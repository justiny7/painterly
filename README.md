# 🎨 Painterly — Kaedim Hackathon Project

## 🧩 Problem
Translating unique 2D texture styles—such as painterly brush strokes—onto 3D models remains a technical and time-consuming task. Existing workflows require manual shader setups or programming-heavy solutions, creating a significant gap between artists and developers. Artists often rely on developers to implement their vision, leading to delays, misalignment, and creative compromises.

## 💡 Solution
Painterly is a Blender add-on that bridges this gap by providing an intuitive interface for generating stylized, painterly effects on 3D models. It automatically generates and enhances normal maps and textures, creating a unique artistic style while maintaining the model's structural integrity.

## ✨ Key Features
- 🎨 Customizable brush parameters
  - Width and length control
  - Angle variation for natural strokes
  - Edge noise for organic feel
- 🖌️ Artistic control
  - Sparsity adjustment for stroke density
  - Manual effect application
  - Undo functionality
- 🗺️ Advanced texture generation
  - Enhanced normal maps for 2.5D effects
  - Seamless UV space handling
  - PBR workflow support

## 🚀 Quick Start

### Installation
1. Download the latest release from GitHub
2. In Blender, go to Edit > Preferences > Add-ons
3. Click "Install" and select the downloaded .zip file
4. Enable the "Painterly" add-on

### Basic Usage
1. Select your 3D model in Blender
2. Open the Painterly panel in the N-panel (press N)
3. Adjust brush parameters to your liking
4. Click "Apply" to generate the painterly effect
5. Use "Reset Maps" to undo and try different settings

## 🎯 Parameters Guide

### Brush Settings
- **Width Range**: Controls the minimum and maximum width of brush strokes
  - Default: 30-50
  - Higher values create bolder strokes

- **Length Range**: Determines the length variation of strokes
  - Default: 40-80
  - Longer strokes create more flowing effects

- **Angle Variation**: Controls randomness in stroke direction
  - Default: 45°
  - Higher values create more chaotic patterns

### Effect Controls
- **Edge Noise**: Adds natural variation to stroke edges
  - Default: 2.0
  - Higher values create rougher edges

- **Sparsity**: Controls density of random strokes
  - Default: 0.001
  - Lower values create denser coverage

## 🔧 Technical Details
- Built with Python and Blender Python API (bpy)
- Uses NumPy for efficient texture processing
- Implements grid-based stroke placement
- Features object ownership masking

## 💡 Tips & Tricks
1. Start with default parameters and make small adjustments
2. Use lower sparsity for more detailed models
3. Increase edge noise for more organic looks
4. Adjust angle variation based on model geometry
5. Apply effects in iterations for better control

## 🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup
1. Clone the repository
2. Link the addon to Blender's addon directory
3. Enable developer extras in Blender preferences
4. Install required dependencies (NumPy)

## 🙏 Acknowledgments
- Built at the Kaedim Hackathon 2025
- Thanks to the Blender community for support and inspiration

## 📞 Support
- Create an issue on GitHub for bug reports
