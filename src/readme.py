"""
GitHub Profile README Generator.
Produces a modern, Linux-terminal-inspired, Neofetch-themed README.md.
"""

import os
import logging
from typing import Optional
from src.config import AppConfig, ProfileConfig, PaletteConfig

logger = logging.getLogger("readme")


class ReadmeGenerator:
    """
    Builds production-grade GitHub Profile README with terminal aesthetics.
    """

    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or AppConfig()
        self.p = self.config.profile
        self.pal = self.config.palette

    def generate(self, image_relative_path: str = "assets/gaurav-halftone.png") -> str:
        """
        Generate complete README markdown content.
        
        Args:
            image_relative_path: Path to halftone portrait relative to repo root
            
        Returns:
            Formatted README.md string
        """
        sections = [
            self._render_animated_header(),
            self._render_neofetch_section(image_relative_path),
            self._render_about_me(),
            self._render_tech_stack(),
            self._render_currently_working_on(),
            self._render_github_stats(),
            self._render_leetcode_stats(),
            self._render_social_links(),
            self._render_terminal_footer(),
        ]
        return "\n\n".join(sections) + "\n"

    def _render_animated_header(self) -> str:
        """Animated typing SVG header banner."""
        lines = [
            f"Hello%2C+World!+I'm+{self.p.name.replace(' ', '+')}",
            f"{self.p.branch_short.replace(' ', '+')}+%40+{self.p.college_short.replace(' ', '+')}",
            "Exploring+Machine+Learning+%26+GenAI",
            "Building+Projects+and+Solving+Problems",
        ]
        lines_param = ";".join(lines)
        svg_url = (
            f"https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=24"
            f"&pause=1000&color=00FF88&center=true&vCenter=true&width=700&lines={lines_param}"
        )
        
        views_badge = (
            f"https://komarev.com/ghpvc/?username={self.p.github_username}"
            f"&label=PROFILE+VIEWS&style=flat-square&color=00D9FF"
        )

        return (
            f"<div align=\"center\">\n\n"
            f"  <!-- Animated Terminal Typing Header -->\n"
            f"  <a href=\"https://github.com/{self.p.github_username}\">\n"
            f"    <img src=\"{svg_url}\" alt=\"Typing SVG Header\" />\n"
            f"  </a>\n\n"
            f"  <p align=\"center\">\n"
            f"    <img src=\"{views_badge}\" alt=\"Profile Views\" />\n"
            f"  </p>\n\n"
            f"</div>"
        )

    def _render_neofetch_section(self, image_path: str) -> str:
        """Desktop 2-column Neofetch layout with Halftone portrait and system specs."""
        return (
            f"```bash\n"
            f"{self.p.github_username}@github ~ $ neofetch --live\n"
            f"```\n\n"
            f"<table align=\"center\" border=\"0\" style=\"border: none; background: transparent; width: 100%;\">\n"
            f"  <tr style=\"border: none; background: transparent;\">\n"
            f"    <!-- Halftone Dot-Matrix Portrait -->\n"
            f"    <td width=\"55%\" align=\"center\" valign=\"middle\" style=\"border: none; padding: 10px;\">\n"
            f"      <img src=\"{image_path}\" alt=\"{self.p.name} Halftone Terminal Portrait\" width=\"100%\" style=\"border-radius: 12px;\" />\n"
            f"    </td>\n"
            f"    <!-- Neofetch System Information -->\n"
            f"    <td width=\"45%\" align=\"left\" valign=\"middle\" style=\"border: none; padding: 15px;\">\n\n"
            f"```yaml\n"
            f"gauravgupta@iiitn\n"
            f"---------------------------\n"
            f"OS       : Developer Mode\n"
            f"Host     : {self.p.college_short}\n"
            f"Kernel   : {self.p.branch_short}\n"
            f"Uptime   : {self.p.uptime}\n"
            f"Shell    : {self.p.shell}\n"
            f"Language : C++ / Python / Java\n"
            f"Focus    : {self.p.focus}\n"
            f"Editor   : {self.p.editor}\n"
            f"Status   : {self.p.status}\n"
            f"```\n\n"
            f"<!-- Terminal Color Palette Pills -->\n"
            f"<p align=\"left\">\n"
            f"  <code>● #080B12</code> \n"
            f"  <code>● #00FF88</code> \n"
            f"  <code>● #00D9FF</code> \n"
            f"  <code>● #0066FF</code> \n"
            f"  <code>● #A855F7</code> \n"
            f"  <code>● #FF884D</code> \n"
            f"  <code>● #E5E7EB</code>\n"
            f"</p>\n\n"
            f"    </td>\n"
            f"  </tr>\n"
            f"</table>"
        )

    def _render_about_me(self) -> str:
        """About Me written in an authentic student developer voice."""
        return (
            f"### <img src=\"https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Objects/Card%20Index.png\" width=\"24\" /> 01. About Me\n\n"
            f"```bash\n"
            f"gauravgupta5813-coder@github ~ $ cat about_me.txt\n"
            f"```\n\n"
            f"> Hey there! I'm **{self.p.name}**, a 2nd-year undergraduate pursuing **{self.p.branch}** at **{self.p.college}**.\n>\n"
            f"> I am deeply fascinated by how intelligent systems learn patterns from raw data and transform ideas into reality. "
            f"My technical journey revolves around building models in **Machine Learning**, diving into **Deep Learning architectures**, "
            f"and exploring the frontier of **Generative AI**.\n>\n"
            f"> At the same time, I believe solid engineering foundations are key to solving hard problems—so I actively hone my "
            f"problem-solving skills through **Data Structures and Algorithms** and build robust, full-stack projects to bridge research with utility."
        )

    def _render_tech_stack(self) -> str:
        """Shields.io tech stack badges categorized by domain."""
        return (
            f"### <img src=\"https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Objects/Laptop.png\" width=\"24\" /> 02. Tech Stack\n\n"
            f"```bash\n"
            f"gauravgupta5813-coder@github ~ $ list --skills --all\n"
            f"```\n\n"
            f"**Programming Languages**\n\n"
            f"<p align=\"left\">\n"
            f"  <img src=\"https://img.shields.io/badge/C-A8B9CC?style=for-the-badge&logo=c&logoColor=white\" alt=\"C\" />\n"
            f"  <img src=\"https://img.shields.io/badge/C++-00599C?style=for-the-badge&logo=c%2B%2B&logoColor=white\" alt=\"C++\" />\n"
            f"  <img src=\"https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white\" alt=\"Python\" />\n"
            f"  <img src=\"https://img.shields.io/badge/Java-ED8B00?style=for-the-badge&logo=openjdk&logoColor=white\" alt=\"Java\" />\n"
            f"  <img src=\"https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black\" alt=\"JavaScript\" />\n"
            f"</p>\n\n"
            f"**AI, Machine Learning & Data Science**\n\n"
            f"<p align=\"left\">\n"
            f"  <img src=\"https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white\" alt=\"PyTorch\" />\n"
            f"  <img src=\"https://img.shields.io/badge/TensorFlow-FF6F00?style=for-the-badge&logo=tensorflow&logoColor=white\" alt=\"TensorFlow\" />\n"
            f"  <img src=\"https://img.shields.io/badge/Machine%20Learning-00D9FF?style=for-the-badge&logo=scikit-learn&logoColor=black\" alt=\"Machine Learning\" />\n"
            f"  <img src=\"https://img.shields.io/badge/Deep%20Learning-A855F7?style=for-the-badge&logo=the-algorithms&logoColor=white\" alt=\"Deep Learning\" />\n"
            f"  <img src=\"https://img.shields.io/badge/Generative%20AI-00FF88?style=for-the-badge&logo=openai&logoColor=black\" alt=\"Generative AI\" />\n"
            f"</p>\n\n"
            f"**Developer Tools & Platforms**\n\n"
            f"<p align=\"left\">\n"
            f"  <img src=\"https://img.shields.io/badge/Git-F05032?style=for-the-badge&logo=git&logoColor=white\" alt=\"Git\" />\n"
            f"  <img src=\"https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white\" alt=\"GitHub\" />\n"
            f"  <img src=\"https://img.shields.io/badge/VS%20Code-007ACC?style=for-the-badge&logo=visual-studio-code&logoColor=white\" alt=\"VS Code\" />\n"
            f"  <img src=\"https://img.shields.io/badge/Google%20Colab-F9AB00?style=for-the-badge&logo=google-colab&logoColor=white\" alt=\"Google Colab\" />\n"
            f"</p>"
        )

    def _render_currently_working_on(self) -> str:
        """Currently working on terminal checklist."""
        items_formatted = "\n".join([f"{item}" for item in self.p.working_on])
        return (
            f"### <img src=\"https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Objects/Rocket.png\" width=\"24\" /> 03. Currently Working On\n\n"
            f"```bash\n"
            f"gauravgupta5813-coder@github ~ $ ps aux | grep 'active-goals'\n"
            f"```\n\n"
            f"```yaml\n"
            f"{items_formatted}\n"
            f"```"
        )

    def _render_github_stats(self) -> str:
        """GitHub activity and streak statistics."""
        user = self.p.github_username
        stats_url = (
            f"https://github-readme-stats.vercel.app/api?username={user}"
            f"&show_icons=true&theme=tokyonight&hide_border=true&bg_color=080B12"
            f"&title_color=00FF88&icon_color=00D9FF&text_color=E5E7EB"
        )
        streak_url = (
            f"https://streak-stats.demolab.com?user={user}"
            f"&theme=tokyonight&hide_border=true&background=080B12"
            f"&ring=00FF88&fire=FF884D&currStreakLabel=00D9FF"
        )
        langs_url = (
            f"https://github-readme-stats.vercel.app/api/top-langs/?username={user}"
            f"&layout=compact&theme=tokyonight&hide_border=true&bg_color=080B12"
            f"&title_color=00FF88&text_color=E5E7EB"
        )
        activity_graph_url = (
            f"https://github-readme-activity-graph.vercel.app/graph?username={user}"
            f"&bg_color=080B12&color=00FF88&line=00D9FF&point=A855F7&area=true&hide_border=true"
        )

        return (
            f"### <img src=\"https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Objects/Bar%20Chart.png\" width=\"24\" /> 04. GitHub Analytics\n\n"
            f"```bash\n"
            f"gauravgupta5813-coder@github ~ $ fetch --stats --github\n"
            f"```\n\n"
            f"<p align=\"center\">\n"
            f"  <img src=\"{stats_url}\" alt=\"{user} GitHub Stats\" height=\"165\" />\n"
            f"  <img src=\"{streak_url}\" alt=\"{user} GitHub Streak\" height=\"165\" />\n"
            f"</p>\n\n"
            f"<p align=\"center\">\n"
            f"  <img src=\"{langs_url}\" alt=\"Top Languages\" height=\"165\" />\n"
            f"</p>\n\n"
            f"<p align=\"center\">\n"
            f"  <img src=\"{activity_graph_url}\" alt=\"Contribution Graph\" width=\"100%\" />\n"
            f"</p>"
        )

    def _render_leetcode_stats(self) -> str:
        """LeetCode metrics card and profile details."""
        leet_user = self.p.leetcode_username
        leet_card_url = f"https://leetcard.jacoblin.cool/{leet_user}?theme=dark&font=Ubuntu&border=0"

        return (
            f"### <img src=\"https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Objects/Light%20Bulb.png\" width=\"24\" /> 05. LeetCode Metrics\n\n"
            f"```bash\n"
            f"gauravgupta5813-coder@github ~ $ curl -s leetcode.com/u/{leet_user}\n"
            f"```\n\n"
            f"<p align=\"center\">\n"
            f"  <a href=\"https://leetcode.com/u/{leet_user}/\" target=\"_blank\">\n"
            f"    <img src=\"{leet_card_url}\" alt=\"LeetCode Stats for {leet_user}\" />\n"
            f"  </a>\n"
            f"</p>"
        )

    def _render_social_links(self) -> str:
        """Social links and connection badges."""
        return (
            f"### <img src=\"https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Objects/Incoming%20Envelope.png\" width=\"24\" /> 06. Connect With Me\n\n"
            f"```bash\n"
            f"gauravgupta5813-coder@github ~ $ ping -c 4 connection.gaurav\n"
            f"```\n\n"
            f"<p align=\"center\">\n"
            f"  <a href=\"https://github.com/{self.p.github_username}\" target=\"_blank\">\n"
            f"    <img src=\"https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white\" alt=\"GitHub\" />\n"
            f"  </a>\n"
            f"  <a href=\"https://leetcode.com/u/{self.p.leetcode_username}/\" target=\"_blank\">\n"
            f"    <img src=\"https://img.shields.io/badge/LeetCode-FFA116?style=for-the-badge&logo=leetcode&logoColor=black\" alt=\"LeetCode\" />\n"
            f"  </a>\n"
            f"  <a href=\"{self.p.linkedin_url}\" target=\"_blank\">\n"
            f"    <img src=\"https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white\" alt=\"LinkedIn\" />\n"
            f"  </a>\n"
            f"  <a href=\"mailto:{self.p.public_email}\">\n"
            f"    <img src=\"https://img.shields.io/badge/Email-D14836?style=for-the-badge&logo=gmail&logoColor=white\" alt=\"Email\" />\n"
            f"  </a>\n"
            f"</p>"
        )

    def _render_terminal_footer(self) -> str:
        """Terminal shutdown footer."""
        return (
            f"---\n\n"
            f"```bash\n"
            f"{self.p.github_username}@github ~ $ echo \"Thanks for stopping by! Let's collaborate and build something impactful.\"\n"
            f"Thanks for stopping by! Let's collaborate and build something impactful.\n\n"
            f"[Process completed - Exit Code 0] ⚡\n"
            f"```\n\n"
            f"<p align=\"center\">\n"
            f"  <sub>Crafted with custom dot-matrix halftone engine • Inspired by Linux Neofetch</sub>\n"
            f"</p>"
        )

    def save_readme(self, content: str, output_path: str) -> None:
        """Write README.md to disk."""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Saved generated README to {output_path}")

