"""
Configuration settings for Profile Information, Halftone Engine, and README styling.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple


@dataclass
class ProfileConfig:
    name: str = "Gaurav Gupta"
    github_username: str = "gauravgupta5813-coder"
    college: str = "Indian Institute of Information Technology, Nagpur"
    college_short: str = "IIIT Nagpur"
    branch: str = "Computer Science and Engineering (Data Science)"
    branch_short: str = "CSE Data Science"
    year: str = "2nd Year"
    uptime: str = "2 Years"
    status: str = "Always Learning"
    editor: str = "VS Code"
    shell: str = "Learning & Building"
    focus: str = "ML | DL | GenAI | DSA"
    
    # LeetCode profile
    leetcode_username: str = "Gaurav-Gupta123"
    
    # Social Links (Placeholders configurable by user)
    linkedin_url: str = "https://linkedin.com/in/gaurav-gupta-ds"
    public_email: str = "gauravgupta.cse.ds@gmail.com"
    
    # Skills and tools
    languages: List[str] = field(default_factory=lambda: [
        "C", "C++", "Python", "Java", "JavaScript"
    ])
    ai_ml: List[str] = field(default_factory=lambda: [
        "PyTorch", "TensorFlow", "Machine Learning", "Deep Learning", "Generative AI"
    ])
    tools: List[str] = field(default_factory=lambda: [
        "Git", "GitHub", "VS Code", "Google Colab"
    ])
    interests: List[str] = field(default_factory=lambda: [
        "Data Science",
        "Machine Learning",
        "Deep Learning",
        "Generative AI",
        "Data Structures and Algorithms",
        "Full-Stack Development",
    ])
    
    # Working on
    working_on: List[str] = field(default_factory=lambda: [
        "[01] Machine Learning and Deep Learning projects.",
        "[02] Generative AI, LLMs and Transformers.",
        "[03] Data Science experiments.",
        "[04] Data Structures and Algorithms practice.",
        "[05] Full-Stack Development.",
    ])


@dataclass
class PaletteConfig:
    # Terminal UI Colors
    bg_canvas: str = "#080B12"          # Dark black terminal background
    terminal_card_bg: str = "#0B0F19"   # Card background
    terminal_border: str = "#1E293D"    # Outer rounded border
    terminal_header_line: str = "#182234"
    
    # Terminal Accents
    neon_green: str = "#00FF88"
    electric_cyan: str = "#00D9FF"
    electric_blue: str = "#0066FF"
    royal_blue: str = "#2563EB"
    purple: str = "#A855F7"
    orange_skin: str = "#FF884D"
    peach_skin: str = "#FFB088"
    white_text: str = "#E5E7EB"
    muted_text: str = "#94A3B8"
    
    # Halftone Aura Palettes
    halo_cyan: str = "#00D9FF"
    halo_blue: str = "#0066FF"
    halo_dark_navy: str = "#10223D"
    halo_mid_navy: str = "#1A365D"
    
    # Skin tone shades (ordered from highlights to shadows)
    skin_shades: List[str] = field(default_factory=lambda: [
        "#FFC4A6",  # Light peach highlight
        "#FFAC82",  # Warm peach
        "#FF925C",  # Vibrant orange
        "#E66B33",  # Rich warm midtone
        "#BD4C1B",  # Shadow edge
        "#87310E",  # Deep shadow
    ])
    
    # Clothing / Kurta shades
    kurta_base: str = "#181A20"         # Deep black-charcoal
    kurta_stripe: str = "#9CA3AF"       # Gray-silver stripe highlight
    kurta_shadow: str = "#111317"


@dataclass
class HalftoneConfig:
    # Dimensions
    canvas_width: int = 1100
    canvas_height: int = 650
    
    # Grid settings
    grid_step: int = 10                  # Distance between dot centers (px)
    max_dot_radius: float = 4.3         # Max radius for brightest dots
    min_dot_radius: float = 0.8         # Min radius for faint dots
    
    # Ellipse Halo parameters (centered in portrait window)
    ellipse_center_x: int = 550
    ellipse_center_y: int = 345
    ellipse_radius_x: int = 425
    ellipse_radius_y: int = 250
    
    # Terminal UI frame
    frame_left: int = 35
    frame_top: int = 40
    frame_right: int = 1065
    frame_bottom: int = 618
    frame_corner_radius: int = 16
    
    # Header prompt
    prompt_text: str = "gauravgupta5813-coder@github ~ $ neofetch --live"
    
    # Model and input paths
    original_photo_path: str = "assets/original/profile.png"
    local_onnx_model_path: str = "assets/models/u2net.onnx"
    output_portrait_path: str = "assets/generated/gaurav-halftone.png"
    output_preview_path: str = "assets/generated/portrait-preview.png"
    output_deploy_path: str = "assets/gaurav-halftone.png"


@dataclass
class AppConfig:
    profile: ProfileConfig = field(default_factory=ProfileConfig)
    palette: PaletteConfig = field(default_factory=PaletteConfig)
    halftone: HalftoneConfig = field(default_factory=HalftoneConfig)
    readme_output_path: str = "output/README.md"
    root_readme_path: str = "README.md"

