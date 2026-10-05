import io
import base64
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Use a non-interactive backend for server-side generation
matplotlib.use('Agg')

from chart_engine.models import ZodiacSign

class ChartDrawer:
    @staticmethod
    def draw_east_indian_chart(chart_name: str, planets_by_sign: dict[str, list[str]]) -> str:
        """
        Takes a mapping like: {"Aries": ["Su", "Me"], "Taurus": ["Asc", "Ju"]}
        Draws the standard 12-cell Bengali/East Indian Astrological Matrix.
        Returns a base64 encoded PNG for immediate Web UI injection.
        """
        # Outer dimensions: 3x3 square
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.set_xlim(0, 3)
        ax.set_ylim(0, 3)
        ax.axis('off')

        # Master aesthetics
        line_color = '#00f0ff' # Neon Nebula Cyan
        line_width = 2
        bg_color = '#0d1117' # Deep Space Dark
        text_color = '#e6edf3'

        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)

        # 1. Outer Bounding Box
        ax.add_patch(patches.Rectangle((0, 0), 3, 3, fill=False, lw=line_width, edgecolor=line_color))

        # 2. Main Tic-Tac-Toe structural dividers
        ax.plot([1, 1], [0, 3], color=line_color, lw=line_width)
        ax.plot([2, 2], [0, 3], color=line_color, lw=line_width)
        ax.plot([0, 3], [1, 1], color=line_color, lw=line_width)
        ax.plot([0, 3], [2, 2], color=line_color, lw=line_width)

        # 3. Corner Parashari Diagonals (splits the 4 corner boxes to make 12 total zones)
        ax.plot([1, 0], [2, 3], color=line_color, lw=line_width) # Top-Left Diagonal
        ax.plot([2, 3], [2, 3], color=line_color, lw=line_width) # Top-Right Diagonal
        ax.plot([2, 3], [1, 0], color=line_color, lw=line_width) # Bottom-Right Diagonal
        ax.plot([1, 0], [1, 0], color=line_color, lw=line_width) # Bottom-Left Diagonal

        # 4. Strict Geometric Text Anchors mapped exactly to the 12 resulting cells
        # The coordinates point to the direct center of mass for each subdivision.
        # 4. Strict Geometric Text Anchors mapped to the 12 cells in ANTI-CLOCKWISE order (Bengali Tradition)
        anchors = {
            ZodiacSign.ARIES.value: (1.5, 2.5),        # Top Middle
            ZodiacSign.TAURUS.value: (0.75, 2.75),    # Top Left (Top Part)
            ZodiacSign.GEMINI.value: (0.25, 2.25),    # Top Left (Left Part)
            ZodiacSign.CANCER.value: (0.5, 1.5),      # Middle Left
            ZodiacSign.LEO.value: (0.25, 0.75),      # Bottom Left (Left Part)
            ZodiacSign.VIRGO.value: (0.75, 0.25),     # Bottom Left (Bottom Part)
            ZodiacSign.LIBRA.value: (1.5, 0.5),       # Bottom Middle
            ZodiacSign.SCORPIO.value: (2.25, 0.25),   # Bottom Right (Bottom Part)
            ZodiacSign.SAGITTARIUS.value: (2.75, 0.75), # Bottom Right (Right Part)
            ZodiacSign.CAPRICORN.value: (2.5, 1.5),    # Middle Right
            ZodiacSign.AQUARIUS.value: (2.75, 2.25),  # Top Right (Right Part)
            ZodiacSign.PISCES.value: (2.25, 2.75)     # Top Right (Top Part)
        }

        # House/Sign numbering constants for East Indian chart (Fixed Zodiac)
        sign_numbers = {
            ZodiacSign.ARIES.value: "1", ZodiacSign.TAURUS.value: "2",
            ZodiacSign.GEMINI.value: "3", ZodiacSign.CANCER.value: "4",
            ZodiacSign.LEO.value: "5", ZodiacSign.VIRGO.value: "6",
            ZodiacSign.LIBRA.value: "7", ZodiacSign.SCORPIO.value: "8",
            ZodiacSign.SAGITTARIUS.value: "9", ZodiacSign.CAPRICORN.value: "10",
            ZodiacSign.AQUARIUS.value: "11", ZodiacSign.PISCES.value: "12"
        }

        # Watermark the center
        ax.text(1.5, 1.5, chart_name, ha='center', va='center', color=line_color, fontsize=12, alpha=0.3, fontweight='bold')

        # Render the specific planetary strings and house numbers onto the grid
        for sign, coords in anchors.items():
            # Add small sign number for reference (Strictly bounded within each house box)
            # Logic: If center is at .5, number at .1. If center at .25, number at .1. etc.
            box_x = int(coords[0])
            box_y = int(coords[1])

            # Corner splitting logic for offsets
            if coords[0] % 1 == 0.25: nx = box_x + 0.15 # Left part of corner
            elif coords[0] % 1 == 0.75: nx = box_x + 0.85 # Right part of corner
            else: nx = box_x + 0.15 # Center part

            if coords[1] % 1 == 0.25: ny = box_y + 0.1 # Bottom part of corner
            elif coords[1] % 1 == 0.75: ny = box_y + 0.9 # Top part of corner
            else: ny = box_y + 0.1 # Center part

            ax.text(nx, ny, sign_numbers[sign], color='#8b949e', fontsize=7, alpha=0.5, ha='center', va='center')

            planets = planets_by_sign.get(sign, [])
            if planets:
                # Limit line breaks for dense houses
                formatted_text = "\n".join(planets)
                ax.text(coords[0], coords[1], formatted_text, ha='center', va='center', color=text_color, fontsize=10, fontweight='bold')

        # Generate raw byte buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', facecolor=fig.get_facecolor(), pad_inches=0)
        plt.close(fig)

        # Encode to web-ready asset
        img_str = base64.b64encode(buf.getvalue()).decode('utf-8')
        return img_str
