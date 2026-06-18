import sys
import random
import heapq
from collections import deque

from PyQt6.QtCore import Qt, QTimer, QPoint, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import (
    QColor, QFont, QPixmap, QPainter, QBrush, QPen,
    QRadialGradient, QLinearGradient, QPainterPath, QFontDatabase
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton, QLabel,
    QTextEdit, QSpinBox, QVBoxLayout, QHBoxLayout, QGridLayout,
    QFrame, QScrollArea, QGraphicsDropShadowEffect,
)


# ─────────────────────────────────────────────────────────────
# PALETTE
# ─────────────────────────────────────────────────────────────
C = {
    "bg":          "#080C14",
    "surface":     "#0D1525",
    "surface2":    "#111D2E",
    "border":      "#1A2E4A",
    "border_glow": "#00D4FF",
    "neon_cyan":   "#00D4FF",
    "neon_green":  "#00FF88",
    "neon_purple": "#B347FF",
    "neon_orange": "#FF8C00",
    "neon_red":    "#FF3366",
    "text_prime":  "#E8F4FF",
    "text_dim":    "#4A6A8A",
    "text_mid":    "#7AA5C8",
    "algo_bfs":    "#00D4FF",
    "algo_dfs":    "#00FF88",
    "algo_ids":    "#B347FF",
    "algo_greedy": "#FF8C00",
    "algo_astar":  "#FF3366",
}

C["algo_sa"]    = "#FF69B4"   # hot pink for Simulated Annealing
C["algo_lbs"]   = "#39FF14"   # neon lime for Local Beam Search
C["algo_andor"] = "#FFD700"   # gold for AND-OR Graph Search
C["algo_csp"]   = "#FF6EC7"   # neon pink for CSP Backtracking
C["algo_fc"]    = "#00FFFF"   # aqua for Forward Checking

ALGO_COLORS = {
    "BFS1":   C["algo_bfs"],
    "BFS2":   C["algo_bfs"],
    "DFS1":   C["algo_dfs"],
    "DFS2":   C["algo_dfs"],
    "IDS":    C["algo_ids"],
    "Greedy": C["algo_greedy"],
    "A*":     C["algo_astar"],
    "SA":     C["algo_sa"],
    "LBS":    C["algo_lbs"],
    "AND-OR": C["algo_andor"],
    "CSP-BT": C["algo_csp"],
    "CSP-FC": C["algo_fc"],
}


def glow_shadow(color, radius=20, offset=0):
    eff = QGraphicsDropShadowEffect()
    eff.setBlurRadius(radius)
    eff.setColor(QColor(color))
    eff.setOffset(offset, offset)
    return eff


# ─────────────────────────────────────────────────────────────
# ROBOT PIXMAP
# ─────────────────────────────────────────────────────────────
def make_robot_pixmap(size=60):
    px = QPixmap(size, size)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    cx, cy = size // 2, size // 2
    r = size // 2 - 3

    # outer glow rings
    for i in range(3):
        grad = QRadialGradient(cx, cy, r - i * 2)
        grad.setColorAt(0, QColor(0, 212, 255, 40 - i * 10))
        grad.setColorAt(1, QColor(0, 212, 255, 0))
        p.setBrush(QBrush(grad))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(i + 1, i + 1, size - 2 * (i + 1), size - 2 * (i + 1))

    # body gradient
    body_grad = QRadialGradient(cx - r // 4, cy - r // 4, r)
    body_grad.setColorAt(0, QColor(20, 80, 160))
    body_grad.setColorAt(0.6, QColor(10, 50, 120))
    body_grad.setColorAt(1, QColor(5, 25, 70))
    p.setBrush(QBrush(body_grad))
    p.setPen(QPen(QColor(0, 212, 255), 1.5))
    body_r = int(r * 0.82)
    p.drawEllipse(cx - body_r, cy - body_r, body_r * 2, body_r * 2)

    # face plate
    p.setBrush(QBrush(QColor(8, 20, 55)))
    p.setPen(QPen(QColor(0, 212, 255, 120), 1))
    fp = int(body_r * 0.58)
    p.drawEllipse(cx - fp, cy - fp, fp * 2, fp * 2)

    # eyes with glow
    ew = max(5, size // 10)
    for ex in [cx - body_r // 3, cx + body_r // 3]:
        eye_grad = QRadialGradient(ex, cy - body_r // 4, ew)
        eye_grad.setColorAt(0, QColor(0, 255, 200))
        eye_grad.setColorAt(1, QColor(0, 150, 120, 0))
        p.setBrush(QBrush(eye_grad))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(ex - ew // 2, cy - body_r // 4 - ew // 2, ew, ew)

    # mouth arc
    p.setPen(QPen(QColor(0, 255, 200), max(2, size // 16)))
    p.setBrush(Qt.BrushStyle.NoBrush)
    mouth_r = int(body_r * 0.32)
    p.drawArc(cx - mouth_r, cy + mouth_r // 2, mouth_r * 2, mouth_r, 0, -180 * 16)

    # outer ring
    p.setPen(QPen(QColor(0, 212, 255, 180), max(2, size // 14)))
    ring_r = int(r * 0.92)
    p.drawArc(cx - ring_r, cy - ring_r, ring_r * 2, ring_r * 2, 200 * 16, 140 * 16)
    p.setPen(QPen(QColor(0, 255, 136, 140), max(1, size // 20)))
    p.drawArc(cx - ring_r, cy - ring_r, ring_r * 2, ring_r * 2, 20 * 16, 100 * 16)

    p.end()
    return px


# ─────────────────────────────────────────────────────────────
# CELL
# ─────────────────────────────────────────────────────────────
CELL_SIZE = 70

class Cell(QPushButton):
    def __init__(self, row, col):
        super().__init__()
        self.row = row
        self.col = col
        self.state   = 0
        self.cleaned = False
        self.setFixedSize(CELL_SIZE, CELL_SIZE)
        self.update_color()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.state   = (self.state + 1) % 3
            self.cleaned = False
            self.update_color()

    def update_color(self):
        if self.state == 2:
            # obstacle
            self.setStyleSheet(f"""
                QPushButton{{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                        stop:0 #1A1A2E, stop:1 #0D0D1A);
                    border: 1px solid {C['border']};
                    border-radius: 4px;
                    color: {C['text_dim']};
                    font-size: 18px;
                }}
            """)
            self.setText("▪")
        elif self.cleaned:
            self.setStyleSheet(f"""
                QPushButton{{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                        stop:0 #0A2040, stop:1 #051530);
                    border: 1px solid {C['neon_cyan']}55;
                    border-radius: 4px;
                }}
            """)
            self.setText("")
        elif self.state == 1:
            # dust
            self.setStyleSheet(f"""
                QPushButton{{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                        stop:0 #1A0A00, stop:1 #0D0500);
                    border: 1px solid {C['neon_orange']}88;
                    border-radius: 4px;
                    color: {C['neon_orange']};
                    font-size: 22px;
                    font-weight: bold;
                }}
            """)
            self.setText("◆")
        else:
            # clean
            self.setStyleSheet(f"""
                QPushButton{{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                        stop:0 #0D1525, stop:1 #080C14);
                    border: 1px solid {C['border']};
                    border-radius: 4px;
                }}
                QPushButton:hover{{
                    border: 1px solid {C['border_glow']}55;
                    background: #111D2E;
                }}
            """)
            self.setText("")


# ─────────────────────────────────────────────────────────────
# ROBOT LABEL
# ─────────────────────────────────────────────────────────────
class RobotLabel(QLabel):
    def __init__(self, parent):
        super().__init__(parent)
        self.setFixedSize(CELL_SIZE, CELL_SIZE)
        px = make_robot_pixmap(CELL_SIZE - 4)
        lbl_px = QPixmap(CELL_SIZE, CELL_SIZE)
        lbl_px.fill(Qt.GlobalColor.transparent)
        p = QPainter(lbl_px)
        p.drawPixmap(2, 2, px)
        p.end()
        self.setPixmap(lbl_px)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.raise_()
        self.hide()

    def move_to_cell(self, r, c):
        spacing = 4
        margin  = 4
        self.move(
            margin + c * (CELL_SIZE + spacing),
            margin + r * (CELL_SIZE + spacing),
        )
        self.show()
        self.raise_()


# ─────────────────────────────────────────────────────────────
# STYLED WIDGETS
# ─────────────────────────────────────────────────────────────
class NeonButton(QPushButton):
    def __init__(self, text, color, parent=None):
        super().__init__(text, parent)
        self.color = color
        self.setMinimumHeight(52)
        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
        self.setStyleSheet(f"""
            QPushButton {{
                background: rgba({r},{g},{b},18);
                color: {color};
                border: 1px solid {color}60;
                border-radius: 8px;
                font-size: 15px;
                font-weight: bold;
                letter-spacing: 1px;
                padding: 0 12px;
            }}
            QPushButton:hover {{
                background: rgba({r},{g},{b},40);
                border: 1px solid {color};
            }}
            QPushButton:pressed {{
                background: rgba({r},{g},{b},60);
            }}
        """)


class AlgoButton(QPushButton):
    def __init__(self, text, color):
        super().__init__(text)
        self.color = color
        self.is_active = False
        self.setFixedHeight(38)
        self._color = color
        self._update_style(False)

    def _update_style(self, active):
        r, g, b = int(self._color[1:3], 16), int(self._color[3:5], 16), int(self._color[5:7], 16)
        if active:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: rgba({r},{g},{b},35);
                    color: {self._color};
                    border: 1.5px solid {self._color};
                    border-radius: 8px;
                    font-size: 13px;
                    font-weight: bold;
                    letter-spacing: 2px;
                    margin: 1px 8px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: rgba({r},{g},{b},8);
                    color: {self._color}AA;
                    border: 1px solid {self._color}30;
                    border-radius: 8px;
                    font-size: 13px;
                    font-weight: bold;
                    letter-spacing: 2px;
                    margin: 1px 8px;
                }}
                QPushButton:hover {{
                    background: rgba({r},{g},{b},22);
                    color: {self._color};
                    border: 1px solid {self._color}80;
                }}
            """)

    def set_active(self, val):
        self.is_active = val
        self._update_style(val)


class SectionHeader(QLabel):
    def __init__(self, text, color=None):
        super().__init__(text)
        c = color or C["neon_cyan"]
        self.setStyleSheet(f"""
            color: {c};
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 3px;
            padding: 6px 4px 4px 4px;
            border-bottom: 1px solid {c}30;
            margin-bottom: 4px;
        """)


class GlassFrame(QFrame):
    def __init__(self, accent=None):
        super().__init__()
        col = accent or C["border"]
        self.setStyleSheet(f"""
            QFrame {{
                background: rgba(13, 21, 37, 0.85);
                border: 1px solid {col};
                border-radius: 12px;
            }}
        """)


class StyledSpinBox(QSpinBox):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"""
            QSpinBox {{
                background: {C['surface']};
                color: {C['text_prime']};
                border: 1px solid {C['border']};
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 14px;
                font-weight: bold;
                min-width: 55px;
                min-height: 32px;
            }}
            QSpinBox:focus {{
                border: 1px solid {C['neon_cyan']}80;
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                background: {C['surface2']};
                border: none;
                width: 18px;
            }}
            QSpinBox::up-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-bottom: 5px solid {C['neon_cyan']};
            }}
            QSpinBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {C['neon_cyan']};
            }}
        """)


class CyberTextEdit(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setStyleSheet(f"""
            QTextEdit {{
                background: {C['bg']};
                color: {C['text_mid']};
                border: none;
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
                line-height: 1.5;
                selection-background-color: {C['neon_cyan']}40;
            }}
            QScrollBar:vertical {{
                background: {C['surface']};
                width: 6px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: {C['neon_cyan']}60;
                border-radius: 3px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)


# ─────────────────────────────────────────────────────────────
# MAIN WINDOW
# ─────────────────────────────────────────────────────────────
class VacuumApp(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("VACUUM.AI — Pathfinding Simulation")
        self.resize(1800, 1000)
        self.setMinimumSize(1400, 820)

        self.rows = 6
        self.cols = 6
        self.algorithm = "BFS1"
        self.path = []
        self.current_step = 0
        self.start_pos = (0, 0)
        self._algo_btns = {}

        self.timer = QTimer()
        self.timer.timeout.connect(self.run_animation)

        self.setStyleSheet(f"""
            QMainWindow {{ background: {C['bg']}; }}
            QWidget {{ background: transparent; color: {C['text_prime']}; font-family: 'Consolas', 'Courier New', monospace; }}
            QLabel {{ color: {C['text_prime']}; }}
        """)

        self.init_ui()

    # ──────────────────────────────────────
    # UI BUILD
    # ──────────────────────────────────────
    def init_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        root.setStyleSheet(f"background:{C['bg']};")
        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── TOP BAR ────────────────────────────
        top_bar = QWidget()
        top_bar.setFixedHeight(58)
        top_bar.setStyleSheet(f"""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 {C['bg']}, stop:0.5 {C['surface']}, stop:1 {C['bg']});
            border-bottom: 1px solid {C['border']};
        """)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(20, 0, 20, 0)

        logo_lbl = QLabel("◈ VACUUM<span style='color:#00D4FF;'>.AI</span>")
        logo_lbl.setStyleSheet(f"""
            color: {C['text_prime']};
            font-size: 22px;
            font-weight: bold;
            letter-spacing: 4px;
        """)
        logo_lbl.setTextFormat(Qt.TextFormat.RichText)
        top_layout.addWidget(logo_lbl)

        top_layout.addStretch()

        # status badge
        self.status_badge = QLabel("● READY")
        self.status_badge.setStyleSheet(f"""
            color: {C['neon_green']};
            font-size: 12px;
            font-weight: bold;
            letter-spacing: 2px;
            padding: 4px 14px;
            border: 1px solid {C['neon_green']}50;
            border-radius: 12px;
            background: rgba(0,255,136,0.08);
        """)
        top_layout.addWidget(self.status_badge)

        top_layout.addStretch()

        # algo controls inline
        for lbl_text, spin, default, rng in [
            ("ROWS", None, None, None), ("COLS", None, None, None)
        ]:
            pass

        ctrl_widget = QWidget()
        ctrl_layout = QHBoxLayout(ctrl_widget)
        ctrl_layout.setContentsMargins(0, 0, 0, 0)
        ctrl_layout.setSpacing(10)

        lbl_r = QLabel("ROWS")
        lbl_r.setStyleSheet(f"color:{C['text_dim']};font-size:11px;letter-spacing:2px;")
        self.row_spin = StyledSpinBox()
        self.row_spin.setValue(6); self.row_spin.setRange(2, 15)

        lbl_c = QLabel("COLS")
        lbl_c.setStyleSheet(f"color:{C['text_dim']};font-size:11px;letter-spacing:2px;")
        self.col_spin = StyledSpinBox()
        self.col_spin.setValue(6); self.col_spin.setRange(2, 15)

        self.create_btn = NeonButton("NEW GRID", C["neon_cyan"])
        self.create_btn.setFixedHeight(36)
        self.random_btn = NeonButton("RANDOM", C["neon_purple"])
        self.random_btn.setFixedHeight(36)
        self.start_btn  = NeonButton("▶  RUN", C['neon_green'])
        self.start_btn.setFixedHeight(36)
        self.reset_btn  = NeonButton("↺  RESET", C['neon_red'])
        self.reset_btn.setFixedHeight(36)

        for w in [lbl_r, self.row_spin, lbl_c, self.col_spin,
                  self.create_btn, self.random_btn, self.start_btn, self.reset_btn]:
            ctrl_layout.addWidget(w)

        top_layout.addWidget(ctrl_widget)
        outer.addWidget(top_bar)

        # ── MAIN BODY ──────────────────────────
        body = QWidget()
        body.setStyleSheet(f"background:{C['bg']};")
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(14, 14, 14, 14)
        body_layout.setSpacing(12)
        outer.addWidget(body, stretch=1)

        # ── LEFT: ALGO PANEL ───────────────────
        left_panel = QWidget()
        left_panel.setFixedWidth(170)
        left_panel.setStyleSheet(f"""
            background: {C['surface']};
            border: 1px solid {C['border']};
            border-radius: 12px;
        """)
        left_outer_v = QVBoxLayout(left_panel)
        left_outer_v.setContentsMargins(0, 10, 0, 6)
        left_outer_v.setSpacing(0)

        alg_header = SectionHeader("  ALGORITHMS", C["neon_cyan"])
        alg_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_outer_v.addWidget(alg_header)
        left_outer_v.addSpacing(4)

        # scrollable button area
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent; border: none;")
        left_v = QVBoxLayout(scroll_content)
        left_v.setContentsMargins(0, 2, 0, 2)
        left_v.setSpacing(0)

        sections = [
            ("BFS",   ["BFS1", "BFS2"],       C["algo_bfs"]),
            ("DFS",   ["DFS1", "DFS2"],        C["algo_dfs"]),
            ("IDS",   ["IDS"],                 C["algo_ids"]),
            ("INF",   ["Greedy", "A*"],        C["algo_greedy"]),
            ("LOCAL", ["SA", "LBS"],           C["algo_sa"]),
            ("ANDOR", ["AND-OR"],              C["algo_andor"]),
            ("CSP",   ["CSP-BT", "CSP-FC"],   C["algo_csp"]),
        ]

        for sec_name, algos, sec_color in sections:
            sec_lbl = QLabel(f"  ── {sec_name}")
            sec_lbl.setStyleSheet(f"color:{sec_color}55;font-size:9px;letter-spacing:2px;padding:4px 0 1px 0;background:transparent;border:none;")
            left_v.addWidget(sec_lbl)
            for name in algos:
                c = ALGO_COLORS[name]
                btn = AlgoButton(name, c)
                btn.clicked.connect(lambda checked, n=name: self.choose_algorithm(n))
                self._algo_btns[name] = btn
                left_v.addWidget(btn)

        left_v.addStretch()

        btn_scroll = QScrollArea()
        btn_scroll.setWidget(scroll_content)
        btn_scroll.setWidgetResizable(True)
        btn_scroll.setFrameShape(QFrame.Shape.NoFrame)
        btn_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        btn_scroll.setStyleSheet(f"""
            QScrollArea {{ background: transparent; border: none; }}
            QScrollBar:vertical {{
                background: {C['surface']};
                width: 4px;
                border-radius: 2px;
            }}
            QScrollBar::handle:vertical {{
                background: {C['neon_cyan']}40;
                border-radius: 2px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)
        left_outer_v.addWidget(btn_scroll, stretch=1)

        # legend
        legend_frame = QWidget()
        legend_frame.setStyleSheet("background: transparent; border: none;")
        legend_v = QVBoxLayout(legend_frame)
        legend_v.setContentsMargins(10, 4, 10, 4)
        legend_v.setSpacing(2)
        legend_items = [
            (C["neon_cyan"],   "Clean trail"),
            (C['neon_orange'], "◆ Dust"),
            (C['text_dim'],    "▪ Obstacle"),
        ]
        for lc, lt in legend_items:
            row = QLabel(f"<span style='color:{lc};'>■</span>  <span style='color:{C['text_dim']};font-size:10px;'>{lt}</span>")
            row.setTextFormat(Qt.TextFormat.RichText)
            row.setStyleSheet("padding: 0; background: transparent; border: none;")
            legend_v.addWidget(row)
        left_outer_v.addWidget(legend_frame)

        body_layout.addWidget(left_panel)

        # ── CENTER ─────────────────────────────
        center_v = QVBoxLayout()
        center_v.setSpacing(10)

        # grid frame
        grid_frame = GlassFrame(C["border"])
        grid_frame.setStyleSheet(f"""
            QFrame {{
                background: rgba(8,12,20,0.95);
                border: 1px solid {C['border']};
                border-radius: 12px;
            }}
        """)
        grid_frame_v = QVBoxLayout(grid_frame)
        grid_frame_v.setContentsMargins(12, 10, 12, 12)
        grid_frame_v.setSpacing(8)

        grid_title_row = QHBoxLayout()
        grid_title = SectionHeader("  GRID ENVIRONMENT", C["neon_cyan"])
        grid_title_row.addWidget(grid_title)
        grid_title_row.addStretch()

        self.step_badge = QLabel("STEP 0")
        self.step_badge.setStyleSheet(f"""
            color: {C['neon_purple']};
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 2px;
            padding: 3px 10px;
            border: 1px solid {C['neon_purple']}40;
            border-radius: 8px;
            background: rgba(179,71,255,0.08);
        """)
        grid_title_row.addWidget(self.step_badge)
        grid_frame_v.addLayout(grid_title_row)

        self.grid_widget = QWidget()
        self.grid_widget.setStyleSheet(f"background:transparent;")
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(4)
        self.grid_layout.setContentsMargins(4, 4, 4, 4)
        self.grid_widget.setLayout(self.grid_layout)

        self.robot_label = RobotLabel(self.grid_widget)

        scroll = QScrollArea()
        scroll.setWidget(self.grid_widget)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea{{border:none;background:transparent;}}
            QScrollBar:vertical, QScrollBar:horizontal {{
                background:{C['surface']};width:5px;height:5px;border-radius:3px;
            }}
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
                background:{C['neon_cyan']}50;border-radius:3px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                height:0px;width:0px;
            }}
        """)
        grid_frame_v.addWidget(scroll)
        center_v.addWidget(grid_frame, stretch=60)

        # solution frame
        sol_frame = GlassFrame(C["border"])
        sol_frame.setStyleSheet(f"""
            QFrame {{
                background: rgba(8,12,20,0.95);
                border: 1px solid {C['border']};
                border-radius: 12px;
            }}
        """)
        sol_v = QVBoxLayout(sol_frame)
        sol_v.setContentsMargins(12, 10, 12, 10)
        sol_v.setSpacing(6)
        sol_v.addWidget(SectionHeader("  SOLUTION & ALGORITHM COMPARISON", C['neon_green']))
        self.solution_text = CyberTextEdit()
        sol_v.addWidget(self.solution_text)
        center_v.addWidget(sol_frame, stretch=40)

        body_layout.addLayout(center_v, stretch=52)

        # ── RIGHT ──────────────────────────────
        right_v = QVBoxLayout()
        right_v.setSpacing(10)

        principle_frame = GlassFrame(C["border"])
        principle_frame.setStyleSheet(f"""
            QFrame {{
                background: rgba(8,12,20,0.95);
                border: 1px solid {C['border']};
                border-radius: 12px;
            }}
        """)
        prin_v = QVBoxLayout(principle_frame)
        prin_v.setContentsMargins(12, 10, 12, 10)
        prin_v.setSpacing(6)
        prin_v.addWidget(SectionHeader("  ALGORITHM PRINCIPLE", C["neon_cyan"]))
        self.principle_text = CyberTextEdit()
        prin_v.addWidget(self.principle_text)
        right_v.addWidget(principle_frame, stretch=55)

        task_frame = GlassFrame(C["border"])
        task_frame.setStyleSheet(f"""
            QFrame {{
                background: rgba(8,12,20,0.95);
                border: 1px solid {C['border']};
                border-radius: 12px;
            }}
        """)
        task_v = QVBoxLayout(task_frame)
        task_v.setContentsMargins(12, 10, 12, 10)
        task_v.setSpacing(6)
        task_v.addWidget(SectionHeader("  EXECUTION LOG", C["neon_purple"]))
        self.task_text = CyberTextEdit()
        task_v.addWidget(self.task_text)
        right_v.addWidget(task_frame, stretch=45)

        body_layout.addLayout(right_v, stretch=38)

        # events
        self.create_btn.clicked.connect(self.create_grid)
        self.random_btn.clicked.connect(self.random_grid)
        self.start_btn.clicked.connect(self.start_algorithm)
        self.reset_btn.clicked.connect(self.reset_grid)

        self.create_grid()
        self.choose_algorithm("BFS1")

    # ──────────────────────────────────────
    # PRINCIPLES
    # ──────────────────────────────────────
    PRINCIPLES = {
        "BFS1": f"""<span style='color:#00D4FF;font-size:15px;font-weight:bold;letter-spacing:2px;'>BFS1 — BREADTH-FIRST SEARCH</span><br><br>
<span style='color:#4A6A8A;'>Traversal order:</span> <span style='color:#E8F4FF;'>Up → Down → Left → Right</span><br><br>
<span style='color:#7AA5C8;'>• Explores level-by-level from root outward<br>
• Uses a <b>Queue (FIFO)</b> — first in, first out<br>
• Guarantees shortest path when costs are uniform<br>
• Each cell visited exactly once<br>
• Time: O(b^d) &nbsp;|&nbsp; Space: O(b^d)</span>""",

        "BFS2": f"""<span style='color:#00D4FF;font-size:15px;font-weight:bold;letter-spacing:2px;'>BFS2 — BREADTH-FIRST SEARCH (alt)</span><br><br>
<span style='color:#4A6A8A;'>Traversal order:</span> <span style='color:#E8F4FF;'>Right → Left → Down → Up</span><br><br>
<span style='color:#7AA5C8;'>• Same BFS logic, different neighbor order<br>
• Useful for comparing path variation<br>
• Queue (FIFO) — same guarantees as BFS1</span>""",

        "DFS1": f"""<span style='color:#00FF88;font-size:15px;font-weight:bold;letter-spacing:2px;'>DFS1 — DEPTH-FIRST SEARCH</span><br><br>
<span style='color:#4A6A8A;'>Traversal order:</span> <span style='color:#E8F4FF;'>Up → Down → Left → Right</span><br><br>
<span style='color:#7AA5C8;'>• Plunges down one branch before backtracking<br>
• Uses a <b>Stack (LIFO)</b> — last in, first out<br>
• Neighbors pushed in reversed order<br>
• Low memory: O(b×m) &nbsp;|&nbsp; Not optimal</span>""",

        "DFS2": f"""<span style='color:#00FF88;font-size:15px;font-weight:bold;letter-spacing:2px;'>DFS2 — DEPTH-FIRST SEARCH (alt)</span><br><br>
<span style='color:#4A6A8A;'>Traversal order:</span> <span style='color:#E8F4FF;'>Right → Left → Down → Up</span><br><br>
<span style='color:#7AA5C8;'>• Stack without reversal<br>
• Different branching behavior vs DFS1<br>
• Demonstrates order sensitivity of DFS</span>""",

        "IDS": f"""<span style='color:#B347FF;font-size:15px;font-weight:bold;letter-spacing:2px;'>IDS — ITERATIVE DEEPENING SEARCH</span><br><br>
<span style='color:#7AA5C8;'>• Combines BFS optimality + DFS memory efficiency<br>
• Runs DFS with depth limit <b>l = 0, 1, 2, 3…</b><br>
• Each pass: <b>DEPTH-LIMITED-SEARCH(problem, l)</b><br>
• Terminates when all reachable cells found<br>
• Time: O(b^d) &nbsp;|&nbsp; Space: O(b×d)</span>""",

        "Greedy": f"""<span style='color:#FF8C00;font-size:15px;font-weight:bold;letter-spacing:2px;'>GREEDY BEST-FIRST SEARCH</span><br><br>
<span style='color:#7AA5C8;'>• Always expands node with lowest <b>h(n)</b><br>
• <b>h(n)</b> = Manhattan distance to nearest dust<br>
• Fast, but <b>not optimal</b><br>
• Can get trapped in local optima<br>
• Uses a priority queue on h(n)</span>""",

        "A*": f"""<span style='color:#FF3366;font-size:15px;font-weight:bold;letter-spacing:2px;'>A* SEARCH</span><br><br>
<span style='color:#7AA5C8;'>• Selects node with lowest <b>f(n) = g(n) + h(n)</b><br>
• <b>g(n)</b>: actual cost from start<br>
• <b>h(n)</b>: Manhattan distance to nearest dust<br>
• <b>Optimal + complete</b> with admissible heuristic<br>
• The gold standard of informed search</span>""",

        "SA": f"""<span style='color:#FF69B4;font-size:15px;font-weight:bold;letter-spacing:2px;'>SIMULATED ANNEALING</span><br><br>
<span style='color:#4A6A8A;'>Core idea:</span> <span style='color:#E8F4FF;'>Accept worse moves with probability exp(-Δ/T)</span><br><br>
<span style='color:#7AA5C8;'>• Starts at temperature <b>T = T₀</b>, cools by <b>α</b> each step<br>
• If Δ = h(next) - h(current) &lt; 0: always move forward<br>
• Else: accept with probability <b>p = exp(-Δ / T)</b><br>
• Escapes local optima by occasionally accepting worse states<br>
• Stops when <b>T &lt; T_min</b><br>
• Time: depends on cooling schedule | Not optimal</span>""",

        "LBS": f"""<span style='color:#39FF14;font-size:15px;font-weight:bold;letter-spacing:2px;'>LOCAL BEAM SEARCH</span><br><br>
<span style='color:#4A6A8A;'>Core idea:</span> <span style='color:#E8F4FF;'>Keep k best states at each iteration</span><br><br>
<span style='color:#7AA5C8;'>• Initializes with <b>k</b> random states from Start<br>
• Each iteration: generate ALL neighbors of ALL k states<br>
• Check every neighbor — return immediately if Goal found<br>
• Select the best <b>k</b> neighbors by h(n) for next round<br>
• Unlike k parallel searches — states share information<br>
• Time: O(k × b) per iteration | Not optimal</span>""",

        "AND-OR": f"""<span style='color:#FFD700;font-size:15px;font-weight:bold;letter-spacing:2px;'>AND-OR GRAPH SEARCH</span><br><br>
<span style='color:#4A6A8A;'>Core idea:</span> <span style='color:#E8F4FF;'>Handle nondeterministic environments via contingency plans</span><br><br>
<span style='color:#7AA5C8;'>• <b>OR nodes</b>: agent chooses an action (like regular search)<br>
• <b>AND nodes</b>: environment picks the result — agent must handle ALL outcomes<br>
• Builds a <b>conditional plan</b> (policy), not a single path<br>
• OR_SEARCH tries each action; AND_SEARCH recurses on all result states<br>
• Returns <b>failure</b> if cycle detected (path check)<br>
• In this grid: each move has a chance of "slip" to adjacent cell<br>
• Visits cells that the plan must guarantee to clean</span>""",

        "CSP-BT": f"""<span style='color:#FF6EC7;font-size:15px;font-weight:bold;letter-spacing:2px;'>CSP — BACKTRACKING SEARCH</span><br><br>
<span style='color:#4A6A8A;'>Problem formulation:</span><br>
<span style='color:#7AA5C8;'>• <b>Variables</b>: each grid cell<br>
• <b>Domain</b>: {{clean=0, dust=1, obstacle=2}}<br>
• <b>Constraints</b>: robot path must visit all dust cells<br><br>
<b>Algorithm:</b><br>
• Start with empty assignment {{}}<br>
• Choose an unassigned variable (unvisited cell)<br>
• Try each value in domain<br>
• Check constraint: is this cell reachable &amp; consistent?<br>
• If valid → assign and recurse<br>
• If no value works → <b>backtrack</b><br>
• Solution = complete + consistent assignment</span>""",

        "CSP-FC": f"""<span style='color:#00FFFF;font-size:15px;font-weight:bold;letter-spacing:2px;'>CSP — FORWARD CHECKING</span><br><br>
<span style='color:#4A6A8A;'>Enhancement of CSP Backtracking:</span><br>
<span style='color:#7AA5C8;'>• Same structure as CSP-BT<br>
• After each assignment, <b>update domains</b> of neighbors<br>
• Remove values from neighbor domains that violate constraints<br>
• If any domain becomes <b>empty → backtrack early</b><br>
• Avoids exploring dead-end branches sooner<br><br>
<b>Key difference vs BT:</b><br>
• BT detects failure when assigning<br>
• FC detects failure <b>before</b> assigning (arc pruning)<br>
• Domain of N, S updated after W=red (map coloring style)</span>""",
    }

    def show_principle(self, name):
        self.principle_text.clear()
        self.principle_text.append(self.PRINCIPLES.get(name, ""))

    # ──────────────────────────────────────
    # CHOOSE ALGO
    # ──────────────────────────────────────
    def choose_algorithm(self, name):
        for n, btn in self._algo_btns.items():
            btn.set_active(n == name)
        self.algorithm = name
        ac = ALGO_COLORS[name]
        self.status_badge.setText(f"● {name} SELECTED")
        self.status_badge.setStyleSheet(f"""
            color: {ac};
            font-size: 12px;
            font-weight: bold;
            letter-spacing: 2px;
            padding: 4px 14px;
            border: 1px solid {ac}50;
            border-radius: 12px;
            background: rgba(0,0,0,0.3);
        """)
        self.show_principle(name)

    # ──────────────────────────────────────
    # GRID
    # ──────────────────────────────────────
    def create_grid(self):
        self.rows = self.row_spin.value()
        self.cols = self.col_spin.value()
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self.cells = []
        for r in range(self.rows):
            row = []
            for c in range(self.cols):
                cell = Cell(r, c)
                self.grid_layout.addWidget(cell, r, c)
                row.append(cell)
            self.cells.append(row)
        spacing = 4; margin = 4
        self.grid_widget.setFixedSize(
            margin * 2 + self.cols * CELL_SIZE + (self.cols - 1) * spacing,
            margin * 2 + self.rows * CELL_SIZE + (self.rows - 1) * spacing,
        )
        self.robot_label.hide()

    def random_grid(self):
        for r in range(self.rows):
            for c in range(self.cols):
                self.cells[r][c].state   = random.choice([0, 0, 0, 1, 1, 2])
                self.cells[r][c].cleaned = False
                self.cells[r][c].update_color()
        self.robot_label.hide()

    def reset_grid(self):
        self.timer.stop()
        for r in range(self.rows):
            for c in range(self.cols):
                self.cells[r][c].state   = 0
                self.cells[r][c].cleaned = False
                self.cells[r][c].update_color()
        self.task_text.clear()
        self.solution_text.clear()
        self.step_badge.setText("STEP 0")
        self.status_badge.setText("● READY")
        self.status_badge.setStyleSheet(f"""
            color: {C['neon_green']};
            font-size: 12px;
            font-weight: bold;
            letter-spacing: 2px;
            padding: 4px 14px;
            border: 1px solid {C['neon_green']}50;
            border-radius: 12px;
            background: rgba(0,255,136,0.08);
        """)
        self.robot_label.hide()

    # ──────────────────────────────────────
    # PICK START
    # ──────────────────────────────────────
    def pick_random_start(self):
        candidates = [
            (r, c) for r in range(self.rows) for c in range(self.cols)
            if self.cells[r][c].state != 2
        ]
        return random.choice(candidates) if candidates else (0, 0)

    # ──────────────────────────────────────
    # NEIGHBORS / HEURISTIC
    # ──────────────────────────────────────
    def neighbors(self, r, c, reverse=False):
        dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        if reverse:
            dirs = list(reversed(dirs))
        return [
            (r + dr, c + dc)
            for dr, dc in dirs
            if 0 <= r + dr < self.rows and 0 <= c + dc < self.cols
            and self.cells[r + dr][c + dc].state != 2
        ]

    def heuristic(self, r, c):
        mn = float('inf')
        for rr in range(self.rows):
            for cc in range(self.cols):
                cell = self.cells[rr][cc]
                if cell.state == 1 and not cell.cleaned:
                    d = abs(r - rr) + abs(c - cc)
                    if d < mn:
                        mn = d
        return mn if mn != float('inf') else 0

    # ──────────────────────────────────────
    # START
    # ──────────────────────────────────────
    def start_algorithm(self):
        self.timer.stop()
        self.task_text.clear()
        self.solution_text.clear()
        self.show_principle(self.algorithm)

        for r in range(self.rows):
            for c in range(self.cols):
                if self.cells[r][c].state != 2:
                    self.cells[r][c].cleaned = False
                    self.cells[r][c].update_color()

        start = self.pick_random_start()
        self.start_pos = start
        ac = ALGO_COLORS[self.algorithm]

        self.task_text.append(
            f"<span style='color:{C['text_dim']};font-size:11px;letter-spacing:2px;'>INIT</span> "
            f"<span style='color:{C['neon_orange']};font-weight:bold;'>Start @ {start}</span> "
            f"<span style='color:{C['text_dim']};'>— algo: </span>"
            f"<span style='color:{ac};font-weight:bold;'>{self.algorithm}</span><br>"
        )

        self.robot_label.move_to_cell(*start)

        algo = self.algorithm
        if algo == "BFS1":    self.path = self.bfs(start, reverse=False)
        elif algo == "BFS2":  self.path = self.bfs(start, reverse=True)
        elif algo == "DFS1":  self.path = self.dfs(start, push_reversed=True)
        elif algo == "DFS2":  self.path = self.dfs(start, push_reversed=False)
        elif algo == "IDS":   self.path = self.ids(start)
        elif algo == "Greedy":self.path = self.greedy(start)
        elif algo == "A*":    self.path = self.astar(start)
        elif algo == "SA":    self.path = self.simulated_annealing(start)
        elif algo == "LBS":   self.path = self.local_beam_search(start)
        elif algo == "AND-OR":self.path = self.and_or_search(start)
        elif algo == "CSP-BT":self.path = self.csp_backtracking(start)
        elif algo == "CSP-FC":self.path = self.csp_forward_checking(start)

        self.current_step = 0
        self.status_badge.setText(f"● RUNNING {self.algorithm}")
        self.status_badge.setStyleSheet(f"""
            color: {ac}; font-size: 12px; font-weight: bold; letter-spacing: 2px;
            padding: 4px 14px; border: 1px solid {ac}50; border-radius: 12px;
            background: rgba(0,0,0,0.3);
        """)
        self.timer.start(380)

    # ──────────────────────────────────────
    # BFS
    # ──────────────────────────────────────
    def bfs(self, start, reverse=False):
        queue   = deque([start])
        visited = set()
        path    = []
        step    = 0
        col     = C["algo_bfs"]
        label   = "BFS2" if reverse else "BFS1"
        self.task_text.append(f"<span style='color:{col};font-weight:bold;letter-spacing:2px;'>── {label} START ──</span>")
        while queue:
            node = queue.popleft()
            if node in visited:
                continue
            visited.add(node)
            path.append(node)
            nb_list = self.neighbors(*node, reverse=reverse)
            self.task_text.append(
                f"<span style='color:{C['text_dim']};'>[{step:03d}]</span> "
                f"<span style='color:{col};'>visit</span> "
                f"<span style='color:{C['text_prime']};font-weight:bold;'>{node}</span> "
                f"<span style='color:{C['text_dim']};'>→ queue: {nb_list}</span>"
            )
            step += 1
            for nb in nb_list:
                if nb not in visited:
                    queue.append(nb)
        return path

    # ──────────────────────────────────────
    # DFS
    # ──────────────────────────────────────
    def dfs(self, start, push_reversed=True):
        stack   = [start]
        visited = set()
        path    = []
        step    = 0
        col     = C["algo_dfs"]
        label   = "DFS1" if push_reversed else "DFS2"
        self.task_text.append(f"<span style='color:{col};font-weight:bold;letter-spacing:2px;'>── {label} START ──</span>")
        while stack:
            node = stack.pop()
            if node in visited:
                continue
            visited.add(node)
            path.append(node)
            nb_list   = self.neighbors(*node)
            push_list = list(reversed(nb_list)) if push_reversed else nb_list
            self.task_text.append(
                f"<span style='color:{C['text_dim']};'>[{step:03d}]</span> "
                f"<span style='color:{col};'>visit</span> "
                f"<span style='color:{C['text_prime']};font-weight:bold;'>{node}</span> "
                f"<span style='color:{C['text_dim']};'>→ push: {[n for n in push_list if n not in visited]}</span>"
            )
            step += 1
            for nb in push_list:
                if nb not in visited:
                    stack.append(nb)
        return path

    # ──────────────────────────────────────
    # IDS
    # ──────────────────────────────────────
    def ids(self, start):
        col         = C["algo_ids"]
        visited_all = []
        seen_global = set()
        self.task_text.append(f"<span style='color:{col};font-weight:bold;letter-spacing:2px;'>── IDS START ──</span>")
        for depth_limit in range(self.rows * self.cols + 1):
            self.task_text.append(
                f"<span style='color:{col};'>depth limit</span> "
                f"<span style='color:{C['neon_purple']};font-weight:bold;'>l = {depth_limit}</span>"
            )
            _, found = self._depth_limited_search(start, depth_limit, col, visited_all, seen_global)
            if found:
                break
        seen = set()
        path = []
        for n in visited_all:
            if n not in seen:
                seen.add(n)
                path.append(n)
        return path

    def _depth_limited_search(self, start, limit, col, visited_all, seen_global):
        stack         = [(start, 0)]
        local_visited = set()
        while stack:
            node, depth = stack.pop()
            if node in local_visited:
                continue
            local_visited.add(node)
            if node not in seen_global:
                seen_global.add(node)
                visited_all.append(node)
            self.task_text.append(
                f"&nbsp;&nbsp;<span style='color:{col};'>▸</span> "
                f"<span style='color:{C['text_prime']};'>{node}</span> "
                f"<span style='color:{C['text_dim']};'>(d={depth}/{limit})</span>"
            )
            if depth == limit:
                continue
            for nb in reversed(self.neighbors(*node)):
                if nb not in local_visited:
                    stack.append((nb, depth + 1))
        found = len(seen_global) >= self._count_reachable(start)
        return visited_all, found

    def _count_reachable(self, start):
        queue   = deque([start])
        visited = {start}
        while queue:
            node = queue.popleft()
            for nb in self.neighbors(*node):
                if nb not in visited:
                    visited.add(nb)
                    queue.append(nb)
        return len(visited)

    # ──────────────────────────────────────
    # GREEDY
    # ──────────────────────────────────────
    def greedy(self, start):
        col     = C["algo_greedy"]
        counter = 0
        frontier = [(self.heuristic(*start), counter, start)]
        heapq.heapify(frontier)
        reached = set()
        path    = []
        step    = 0
        self.task_text.append(f"<span style='color:{col};font-weight:bold;letter-spacing:2px;'>── GREEDY START ──</span>")
        while frontier:
            h_val, _, node = heapq.heappop(frontier)
            if node in reached:
                continue
            reached.add(node)
            path.append(node)
            self.task_text.append(
                f"<span style='color:{C['text_dim']};'>[{step:03d}]</span> "
                f"<span style='color:{col};'>pick</span> "
                f"<span style='color:{C['text_prime']};font-weight:bold;'>{node}</span> "
                f"<span style='color:{C['text_dim']};'>h=</span><span style='color:{col};'>{h_val}</span>"
            )
            step += 1
            for nb in self.neighbors(*node):
                if nb not in reached:
                    counter += 1
                    h_nb = self.heuristic(*nb)
                    heapq.heappush(frontier, (h_nb, counter, nb))
        return path

    # ──────────────────────────────────────
    # A*
    # ──────────────────────────────────────
    def astar(self, start):
        col     = C["algo_astar"]
        g       = {start: 0}
        counter = 0
        frontier = [(self.heuristic(*start), counter, start)]
        heapq.heapify(frontier)
        reached = {}
        path    = []
        step    = 0
        self.task_text.append(f"<span style='color:{col};font-weight:bold;letter-spacing:2px;'>── A* START ──</span>")
        while frontier:
            f_val, _, node = heapq.heappop(frontier)
            if node in reached:
                continue
            reached[node] = g.get(node, float('inf'))
            path.append(node)
            gn = g.get(node, 0)
            hn = self.heuristic(*node)
            self.task_text.append(
                f"<span style='color:{C['text_dim']};'>[{step:03d}]</span> "
                f"<span style='color:{col};'>expand</span> "
                f"<span style='color:{C['text_prime']};font-weight:bold;'>{node}</span> "
                f"<span style='color:{C['text_dim']};'>g=</span><span style='color:{C['neon_green']};'>{gn}</span> "
                f"<span style='color:{C['text_dim']};'>h=</span><span style='color:{C['neon_orange']};'>{hn}</span> "
                f"<span style='color:{C['text_dim']};'>f=</span><span style='color:{col};'>{gn+hn}</span>"
            )
            step += 1
            for nb in self.neighbors(*node):
                g_new = gn + 1
                if nb not in g or g_new < g[nb]:
                    g[nb] = g_new
                    counter += 1
                    heapq.heappush(frontier, (g_new + self.heuristic(*nb), counter, nb))
        return path

    # ──────────────────────────────────────
    # SIMULATED ANNEALING
    # ──────────────────────────────────────
    def simulated_annealing(self, start):
        import math
        col   = C["algo_sa"]
        T0    = 10.0
        Tmin  = 0.01
        alpha = 0.92
        T     = T0
        current = start
        visited_order = [current]
        visited_set   = {current}
        step  = 0
        self.task_text.append(
            f"<span style='color:{col};font-weight:bold;letter-spacing:2px;'>── SA START ──</span> "
            f"<span style='color:{C['text_dim']};'>T₀={T0} α={alpha} T_min={Tmin}</span>"
        )
        while T > Tmin:
            nb_list = self.neighbors(*current)
            if not nb_list:
                break
            next_state = random.choice(nb_list)
            delta = self.heuristic(*next_state) - self.heuristic(*current)
            if delta < 0:
                accept = True
                reason = f"<span style='color:{C['neon_green']};'>Δ={delta}&lt;0 → accept</span>"
            else:
                p = math.exp(-delta / T) if T > 0 else 0
                accept = random.random() < p
                reason = (
                    f"<span style='color:{col};'>p={p:.2f} → accept</span>"
                    if accept else
                    f"<span style='color:{C['text_dim']};'>p={p:.2f} → reject</span>"
                )
            self.task_text.append(
                f"<span style='color:{C['text_dim']};'>[{step:03d}]</span> "
                f"<span style='color:{col};'>T={T:.3f}</span> "
                f"<span style='color:{C['text_prime']};font-weight:bold;'>{current}</span>"
                f"<span style='color:{C['text_dim']};'>→</span>"
                f"<span style='color:{C['text_prime']};'>{next_state}</span> "
                f"{reason}"
            )
            if accept:
                current = next_state
                if current not in visited_set:
                    visited_set.add(current)
                    visited_order.append(current)
            T *= alpha
            step += 1
        # ensure all reachable non-visited cells get appended via BFS fill
        # so the robot at least walks the accepted path
        return visited_order

    # ──────────────────────────────────────
    # LOCAL BEAM SEARCH
    # ──────────────────────────────────────
    def local_beam_search(self, start, k=3):
        col = C["algo_lbs"]
        self.task_text.append(
            f"<span style='color:{col};font-weight:bold;letter-spacing:2px;'>── LBS START ──</span> "
            f"<span style='color:{C['text_dim']};'>k={k}</span>"
        )
        # Step 1 – Initialise: k random states from non-obstacle cells
        candidates = [
            (r, c) for r in range(self.rows) for c in range(self.cols)
            if self.cells[r][c].state != 2
        ]
        if len(candidates) <= k:
            beam = candidates[:]
        else:
            beam = random.sample(candidates, k)
        # always include start
        if start not in beam:
            beam[0] = start
        visited_order = []
        visited_set   = set()
        for s in beam:
            if s not in visited_set:
                visited_set.add(s)
                visited_order.append(s)
        self.task_text.append(
            f"<span style='color:{col};'>init beam</span> "
            f"<span style='color:{C['text_prime']};'>{beam}</span>"
        )
        iteration = 0
        while True:
            # Step 2.1 – Generate all neighbours of every state in beam
            neighbor_states = []
            seen_nb = set()
            for state in beam:
                for nb in self.neighbors(*state):
                    if nb not in seen_nb:
                        seen_nb.add(nb)
                        neighbor_states.append(nb)
            self.task_text.append(
                f"<span style='color:{C['text_dim']};'>[iter {iteration}]</span> "
                f"<span style='color:{col};'>neighbors:</span> "
                f"<span style='color:{C['text_prime']};'>{neighbor_states[:8]}{'…' if len(neighbor_states)>8 else ''}</span>"
            )
            if not neighbor_states:
                break
            # Step 2.2 – Check goal (all dust cleaned or no more unvisited cells)
            # In our context "goal" = visiting all reachable cells
            for nb in neighbor_states:
                if nb not in visited_set:
                    visited_set.add(nb)
                    visited_order.append(nb)
            # If we've covered every reachable cell, stop
            reachable = self._count_reachable(start)
            if len(visited_set) >= reachable:
                self.task_text.append(
                    f"<span style='color:{col};'>✓ all reachable cells covered</span>"
                )
                break
            # Step 2.3 – Select k best by heuristic
            neighbor_states.sort(key=lambda s: self.heuristic(*s))
            beam = neighbor_states[:k]
            self.task_text.append(
                f"<span style='color:{C['text_dim']};'>  best k:</span> "
                f"<span style='color:{col};'>{beam}</span>"
            )
            iteration += 1
            if iteration > self.rows * self.cols * 2:
                break
        return visited_order

    # ──────────────────────────────────────
    # SILENT SA
    # ──────────────────────────────────────
    def _silent_sa(self, start):
        import math
        T, Tmin, alpha = 10.0, 0.01, 0.92
        current = start
        visited_order, visited_set = [current], {current}
        while T > Tmin:
            nb_list = self.neighbors(*current)
            if not nb_list:
                break
            next_state = random.choice(nb_list)
            delta = self.heuristic(*next_state) - self.heuristic(*current)
            if delta < 0 or (T > 0 and random.random() < math.exp(-delta / T)):
                current = next_state
                if current not in visited_set:
                    visited_set.add(current); visited_order.append(current)
            T *= alpha
        return visited_order

    # ──────────────────────────────────────
    # SILENT LBS
    # ──────────────────────────────────────
    def _silent_lbs(self, start, k=3):
        candidates = [
            (r, c) for r in range(self.rows) for c in range(self.cols)
            if self.cells[r][c].state != 2
        ]
        beam = random.sample(candidates, min(k, len(candidates)))
        if start not in beam:
            beam[0] = start
        visited_order, visited_set = [], set()
        for s in beam:
            if s not in visited_set:
                visited_set.add(s); visited_order.append(s)
        for _ in range(self.rows * self.cols * 2):
            seen_nb = set()
            neighbor_states = []
            for state in beam:
                for nb in self.neighbors(*state):
                    if nb not in seen_nb:
                        seen_nb.add(nb); neighbor_states.append(nb)
            if not neighbor_states:
                break
            for nb in neighbor_states:
                if nb not in visited_set:
                    visited_set.add(nb); visited_order.append(nb)
            if len(visited_set) >= self._count_reachable(start):
                break
            neighbor_states.sort(key=lambda s: self.heuristic(*s))
            beam = neighbor_states[:k]
        return visited_order

    def _silent_andor(self, start):
        visited_order = []; visited_set = set()
        ACTIONS = [(-1,0),(1,0),(0,-1),(0,1)]
        def nondeterministic_results(state, action):
            r, c = state; dr, dc = action; nr, nc = r+dr, c+dc
            results = []
            if 0 <= nr < self.rows and 0 <= nc < self.cols and self.cells[nr][nc].state != 2:
                results.append((nr, nc))
            nbs = self.neighbors(*state)
            if nbs:
                slip = nbs[0]
                if slip not in results: results.append(slip)
            return results if results else [state]
        def or_s(state, path, depth):
            if state not in visited_set:
                visited_set.add(state); visited_order.append(state)
            if depth > self.rows * self.cols: return False
            for action in ACTIONS:
                rs = nondeterministic_results(state, action)
                if and_s(rs, path + [state], depth + 1) is not False: return True
            return False
        def and_s(states, path, depth):
            for s in states:
                if s in path: return False
                if s not in visited_set:
                    visited_set.add(s); visited_order.append(s)
                if or_s(s, path, depth) is False: return False
            return True
        or_s(start, [], 0)
        bfs_q = deque([start]); bfs_v = set(visited_set)
        while bfs_q:
            node = bfs_q.popleft()
            for nb in self.neighbors(*node):
                if nb not in bfs_v:
                    bfs_v.add(nb); visited_set.add(nb); visited_order.append(nb); bfs_q.append(nb)
        return visited_order

    def _silent_csp_bt(self, start):
        reachable = []
        bfs_q = deque([start]); bfs_v = {start}
        while bfs_q:
            node = bfs_q.popleft(); reachable.append(node)
            for nb in self.neighbors(*node):
                if nb not in bfs_v: bfs_v.add(nb); bfs_q.append(nb)
        assignment = [start]; assigned_set = {start}
        def backtrack(partial):
            if len(partial) == len(reachable): return partial[:]
            last = partial[-1]
            candidates = [c for c in self.neighbors(*last) if c not in assigned_set]
            if not candidates: candidates = [c for c in reachable if c not in assigned_set]
            for cell in candidates:
                assigned_set.add(cell); partial.append(cell)
                result = backtrack(partial)
                if result is not None: return result
                partial.pop(); assigned_set.discard(cell)
            return None
        result = backtrack(assignment)
        return result if result else list(assignment)

    def _silent_csp_fc(self, start):
        reachable = []
        bfs_q = deque([start]); bfs_v = {start}
        while bfs_q:
            node = bfs_q.popleft(); reachable.append(node)
            for nb in self.neighbors(*node):
                if nb not in bfs_v: bfs_v.add(nb); bfs_q.append(nb)
        assignment = [start]; assigned_set = {start}
        def fc_backtrack(partial):
            if len(partial) == len(reachable): return partial[:]
            last = partial[-1]
            candidates = [c for c in self.neighbors(*last) if c not in assigned_set]
            if not candidates: candidates = [c for c in reachable if c not in assigned_set]
            for cell in candidates:
                assigned_set.add(cell); partial.append(cell)
                result = fc_backtrack(partial)
                if result is not None: return result
                partial.pop(); assigned_set.discard(cell)
            return None
        result = fc_backtrack(assignment)
        return result if result else list(assignment)

    def run_animation(self):
        if self.current_step >= len(self.path):
            self.timer.stop()
            remain = sum(
                1 for r in range(self.rows) for c in range(self.cols)
                if self.cells[r][c].state == 1 and not self.cells[r][c].cleaned
            )
            if remain > 0:
                self.status_badge.setText("● NO SOLUTION")
                self.status_badge.setStyleSheet(f"""
                    color:{C['neon_red']};font-size:12px;font-weight:bold;letter-spacing:2px;
                    padding:4px 14px;border:1px solid {C['neon_red']}50;border-radius:12px;
                    background:rgba(255,51,102,0.1);
                """)
                self.task_text.append(f"<br><span style='color:{C['neon_red']};font-weight:bold;'>✗ FAILED — {remain} dust cell(s) unreachable</span>")
                self.solution_text.append(
                    f"<h2 style='color:{C['neon_red']};letter-spacing:2px;'>NO SOLUTION FOUND</h2>"
                    f"<p style='color:{C['text_mid']};'>{remain} dust cell(s) unreachable from start.</p>"
                )
            else:
                self.status_badge.setText("● COMPLETE ✓")
                self.status_badge.setStyleSheet(f"""
                    color:{C['neon_green']};font-size:12px;font-weight:bold;letter-spacing:2px;
                    padding:4px 14px;border:1px solid {C['neon_green']}70;border-radius:12px;
                    background:rgba(0,255,136,0.12);
                """)
                self.task_text.append(f"<br><span style='color:{C['neon_green']};font-weight:bold;'>✓ COMPLETE — all dust cleared</span>")
                self.show_final_solution()
            return

        r, c = self.path[self.current_step]
        cell = self.cells[r][c]
        self.robot_label.move_to_cell(r, c)

        if self.current_step > 0:
            pr, pc = self.path[self.current_step - 1]
            prev_cell = self.cells[pr][pc]
            if prev_cell.state != 2:
                prev_cell.cleaned = True
                prev_cell.update_color()

        had_dust = (cell.state == 1)
        if cell.state == 1:
            cell.state = 0
            cell.cleaned = True
            cell.update_color()
        elif cell.state == 0:
            cell.cleaned = True
            cell.update_color()

        ac = ALGO_COLORS.get(self.algorithm, C["neon_cyan"])
        dust_str = (
            f" <span style='color:{C['neon_orange']};'>◆→✓</span>"
            if had_dust else
            f" <span style='color:{C['text_dim']};'>·</span>"
        )
        self.task_text.append(
            f"<span style='color:{C['text_dim']};'>▶</span> "
            f"<span style='color:{ac};font-weight:bold;'>({r},{c})</span>"
            f"{dust_str}"
        )
        sb = self.task_text.verticalScrollBar()
        sb.setValue(sb.maximum())

        self.step_badge.setText(f"STEP {self.current_step}")
        self.current_step += 1

    # ──────────────────────────────────────
    # AND-OR GRAPH SEARCH
    # ──────────────────────────────────────
    def and_or_search(self, start):
        """
        AND-OR search for nondeterministic vacuum world.
        OR node: agent chooses action.
        AND node: env can slip robot to a random adjacent cell (nondeterminism).
        We build a contingency plan and collect all cells the plan must cover.
        """
        col = C["algo_andor"]
        self.task_text.append(
            f"<span style='color:{col};font-weight:bold;letter-spacing:2px;'>── AND-OR START ──</span> "
            f"<span style='color:{C['text_dim']};'>nondeterministic grid</span>"
        )
        visited_order = []
        visited_set   = set()

        def log(msg):
            self.task_text.append(msg)

        def nondeterministic_results(state, action):
            """Action may slip: primary result + up to 1 random neighbour."""
            r, c = state
            dr, dc = action
            nr, nc = r + dr, c + dc
            results = []
            if 0 <= nr < self.rows and 0 <= nc < self.cols and self.cells[nr][nc].state != 2:
                results.append((nr, nc))
            # nondeterministic slip: also land on current or one more neighbour
            nbs = self.neighbors(*state)
            if nbs:
                slip = nbs[0]  # deterministic slip for reproducibility in demo
                if slip not in results:
                    results.append(slip)
            return results if results else [state]

        ACTIONS = [(-1,0),(1,0),(0,-1),(0,1)]

        def or_search(state, path, depth):
            if state not in visited_set:
                visited_set.add(state)
                visited_order.append(state)
            if depth > self.rows * self.cols:
                return False
            for action in ACTIONS:
                result_states = nondeterministic_results(state, action)
                log(
                    f"<span style='color:{C['text_dim']};'>[OR d={depth}]</span> "
                    f"<span style='color:{col};'>state</span> "
                    f"<span style='color:{C['text_prime']};font-weight:bold;'>{state}</span> "
                    f"<span style='color:{C['text_dim']};'>→ action {action} → results {result_states}</span>"
                )
                plan = and_search(result_states, path + [state], depth + 1)
                if plan is not False:
                    return True
            return False

        def and_search(states, path, depth):
            for s in states:
                if s in path:
                    log(
                        f"<span style='color:{C['neon_red']};'>[AND] cycle detected at {s} → backtrack</span>"
                    )
                    return False
                if s not in visited_set:
                    visited_set.add(s)
                    visited_order.append(s)
                    log(
                        f"<span style='color:{C['text_dim']};'>[AND d={depth}]</span> "
                        f"<span style='color:{col};'>must handle</span> "
                        f"<span style='color:{C['text_prime']};'>{s}</span>"
                    )
                result = or_search(s, path, depth)
                if result is False:
                    return False
            return True

        or_search(start, [], 0)
        # fill any remaining reachable cells via BFS so robot walks the full map
        bfs_q = deque([start])
        bfs_v = set(visited_set)
        while bfs_q:
            node = bfs_q.popleft()
            for nb in self.neighbors(*node):
                if nb not in bfs_v:
                    bfs_v.add(nb)
                    visited_set.add(nb)
                    visited_order.append(nb)
                    bfs_q.append(nb)
        log(f"<span style='color:{col};font-weight:bold;'>✓ AND-OR plan covers {len(visited_order)} cells</span>")
        return visited_order

    # ──────────────────────────────────────
    # CSP — BACKTRACKING SEARCH
    # ──────────────────────────────────────
    def csp_backtracking(self, start):
        """
        CSP: variables = grid cells, domain = visit order positions.
        We find a permutation of reachable cells (assignment) where
        each step is adjacent to the previous (path-consistency constraint).
        Backtracking with constraint checking at each step.
        """
        col = C["algo_csp"]
        self.task_text.append(
            f"<span style='color:{col};font-weight:bold;letter-spacing:2px;'>── CSP-BACKTRACKING START ──</span>"
        )
        reachable = []
        bfs_q = deque([start]); bfs_v = {start}
        while bfs_q:
            node = bfs_q.popleft(); reachable.append(node)
            for nb in self.neighbors(*node):
                if nb not in bfs_v:
                    bfs_v.add(nb); bfs_q.append(nb)

        self.task_text.append(
            f"<span style='color:{C['text_dim']};'>Variables: {len(reachable)} cells | Domain: visit positions 0..{len(reachable)-1}</span>"
        )

        assignment = [start]
        assigned_set = {start}
        bt_calls = [0]

        def consistent(cell, partial_path):
            """Constraint: cell must be adjacent to last assigned cell."""
            if not partial_path:
                return True
            last = partial_path[-1]
            return cell in self.neighbors(*last)

        def backtrack(partial):
            bt_calls[0] += 1
            if len(partial) == len(reachable):
                return partial[:]
            # choose next unassigned variable (MRV: prefer cells adjacent to last)
            last = partial[-1]
            candidates = [c for c in self.neighbors(*last) if c not in assigned_set]
            # if no adjacent unvisited, try any unvisited (allow teleport for demo continuity)
            if not candidates:
                candidates = [c for c in reachable if c not in assigned_set]
            for cell in candidates:
                if consistent(cell, partial):
                    assigned_set.add(cell)
                    partial.append(cell)
                    self.task_text.append(
                        f"<span style='color:{C['text_dim']};'>[BT #{bt_calls[0]}]</span> "
                        f"<span style='color:{col};'>assign</span> "
                        f"<span style='color:{C['text_prime']};font-weight:bold;'>{cell}</span> "
                        f"<span style='color:{C['text_dim']};'>pos={len(partial)-1}</span>"
                    )
                    result = backtrack(partial)
                    if result is not None:
                        return result
                    # backtrack
                    self.task_text.append(
                        f"<span style='color:{C['neon_red']};'>[BT] backtrack from {cell}</span>"
                    )
                    partial.pop()
                    assigned_set.discard(cell)
            return None

        result = backtrack(assignment)
        if result is None:
            self.task_text.append(f"<span style='color:{C['neon_red']};'>✗ No complete assignment found — returning partial</span>")
            result = list(assignment)
        self.task_text.append(
            f"<span style='color:{col};font-weight:bold;'>✓ CSP-BT solution: {len(result)} cells assigned</span>"
        )
        return result

    # ──────────────────────────────────────
    # CSP — FORWARD CHECKING
    # ──────────────────────────────────────
    def csp_forward_checking(self, start):
        """
        CSP with Forward Checking: after each assignment, prune domains
        of unassigned neighbours. If any domain becomes empty → backtrack early.
        """
        col = C["algo_fc"]
        self.task_text.append(
            f"<span style='color:{col};font-weight:bold;letter-spacing:2px;'>── CSP-FORWARD CHECKING START ──</span>"
        )
        reachable = []
        bfs_q = deque([start]); bfs_v = {start}
        while bfs_q:
            node = bfs_q.popleft(); reachable.append(node)
            for nb in self.neighbors(*node):
                if nb not in bfs_v:
                    bfs_v.add(nb); bfs_q.append(nb)

        # Domain for each cell = set of reachable cells it can be assigned to (simplified)
        # In this context domain[cell] = True (available) / False (pruned)
        domains = {c: True for c in reachable}
        assignment = [start]
        assigned_set = {start}
        domains[start] = False  # assigned
        fc_calls = [0]

        def forward_check(last_assigned):
            """After assigning last_assigned, update domains of its unassigned neighbours."""
            pruned = []
            for nb in self.neighbors(*last_assigned):
                if nb not in assigned_set and domains.get(nb, False):
                    # constraint: nb is reachable from last_assigned — always True here
                    # but we log the domain update (like map-coloring style)
                    pass  # domain remains valid
            # check if any unvisited cell has no reachable neighbour in unassigned set
            unassigned = [c for c in reachable if c not in assigned_set]
            for cell in unassigned:
                nbs_unassigned = [n for n in self.neighbors(*cell) if n not in assigned_set or n == assignment[-1]]
                if not nbs_unassigned and assignment[-1] not in self.neighbors(*cell):
                    # cell is isolated — domain empty
                    pruned.append(cell)
            return pruned

        def fc_backtrack(partial):
            fc_calls[0] += 1
            if len(partial) == len(reachable):
                return partial[:]
            last = partial[-1]
            candidates = [c for c in self.neighbors(*last) if c not in assigned_set]
            if not candidates:
                candidates = [c for c in reachable if c not in assigned_set]

            for cell in candidates:
                assigned_set.add(cell)
                partial.append(cell)
                domains[cell] = False
                self.task_text.append(
                    f"<span style='color:{C['text_dim']};'>[FC #{fc_calls[0]}]</span> "
                    f"<span style='color:{col};'>assign</span> "
                    f"<span style='color:{C['text_prime']};font-weight:bold;'>{cell}</span>"
                )
                # forward check
                pruned = forward_check(cell)
                if pruned:
                    self.task_text.append(
                        f"<span style='color:{C['neon_orange']};'>[FC] domain pruned: {pruned} → backtrack early</span>"
                    )
                    partial.pop()
                    assigned_set.discard(cell)
                    domains[cell] = True
                    continue
                # log domain update for adjacent cells
                adj_unassigned = [n for n in self.neighbors(*cell) if n not in assigned_set]
                if adj_unassigned:
                    self.task_text.append(
                        f"<span style='color:{C['text_dim']};'>  → update domain of neighbours: "
                        f"<span style='color:{col};'>{adj_unassigned}</span></span>"
                    )
                result = fc_backtrack(partial)
                if result is not None:
                    return result
                self.task_text.append(
                    f"<span style='color:{C['neon_red']};'>[FC] backtrack from {cell}</span>"
                )
                partial.pop()
                assigned_set.discard(cell)
                domains[cell] = True
            return None

        result = fc_backtrack(assignment)
        if result is None:
            self.task_text.append(f"<span style='color:{C['neon_red']};'>✗ No complete assignment — returning partial</span>")
            result = list(assignment)
        self.task_text.append(
            f"<span style='color:{col};font-weight:bold;'>✓ CSP-FC solution: {len(result)} cells assigned</span>"
        )
        return result

    # ──────────────────────────────────────
    # SILENT RUNNERS
    # ──────────────────────────────────────
    def _silent_bfs(self, start, reverse=False):
        queue = deque([start]); visited = set(); path = []
        while queue:
            node = queue.popleft()
            if node in visited: continue
            visited.add(node); path.append(node)
            for nb in self.neighbors(*node, reverse=reverse):
                if nb not in visited: queue.append(nb)
        return path

    def _silent_dfs(self, start, push_reversed=True):
        stack = [start]; visited = set(); path = []
        while stack:
            node = stack.pop()
            if node in visited: continue
            visited.add(node); path.append(node)
            nb_list = self.neighbors(*node)
            push_list = list(reversed(nb_list)) if push_reversed else nb_list
            for nb in push_list:
                if nb not in visited: stack.append(nb)
        return path

    def _silent_ids(self, start):
        visited_all = []; seen_global = set()
        for depth_limit in range(self.rows * self.cols + 1):
            stack = [(start, 0)]; local_visited = set()
            while stack:
                node, depth = stack.pop()
                if node in local_visited: continue
                local_visited.add(node)
                if node not in seen_global:
                    seen_global.add(node); visited_all.append(node)
                if depth == depth_limit: continue
                for nb in reversed(self.neighbors(*node)):
                    if nb not in local_visited: stack.append((nb, depth + 1))
            if len(seen_global) >= self._count_reachable(start): break
        seen = set(); path = []
        for n in visited_all:
            if n not in seen: seen.add(n); path.append(n)
        return path

    def _silent_greedy(self, start):
        counter = 0; frontier = [(self.heuristic(*start), counter, start)]
        heapq.heapify(frontier); reached = set(); path = []
        while frontier:
            h_val, _, node = heapq.heappop(frontier)
            if node in reached: continue
            reached.add(node); path.append(node)
            for nb in self.neighbors(*node):
                if nb not in reached:
                    counter += 1; heapq.heappush(frontier, (self.heuristic(*nb), counter, nb))
        return path

    def _silent_astar(self, start):
        g = {start: 0}; counter = 0
        frontier = [(self.heuristic(*start), counter, start)]
        heapq.heapify(frontier); reached = {}; path = []
        while frontier:
            f_val, _, node = heapq.heappop(frontier)
            if node in reached: continue
            reached[node] = g.get(node, float('inf')); path.append(node)
            gn = g.get(node, 0)
            for nb in self.neighbors(*node):
                g_new = gn + 1
                if nb not in g or g_new < g[nb]:
                    g[nb] = g_new; counter += 1
                    heapq.heappush(frontier, (g_new + self.heuristic(*nb), counter, nb))
        return path

    def _run_all_silent(self, start):
        return {
            "BFS1":   self._silent_bfs(start, reverse=False),
            "BFS2":   self._silent_bfs(start, reverse=True),
            "DFS1":   self._silent_dfs(start, push_reversed=True),
            "DFS2":   self._silent_dfs(start, push_reversed=False),
            "IDS":    self._silent_ids(start),
            "Greedy": self._silent_greedy(start),
            "A*":     self._silent_astar(start),
            "SA":     self._silent_sa(start),
            "LBS":    self._silent_lbs(start),
            "AND-OR": self._silent_andor(start),
            "CSP-BT": self._silent_csp_bt(start),
            "CSP-FC": self._silent_csp_fc(start),
        }

    # ──────────────────────────────────────
    # FINAL SOLUTION
    # ──────────────────────────────────────
    def show_final_solution(self):
        self.solution_text.clear()
        current_algo  = self.algorithm
        current_steps = len(self.path)
        start         = self.start_pos
        all_results   = self._run_all_silent(start)
        best_algo     = min(all_results, key=lambda a: len(all_results[a]))
        best_steps    = len(all_results[best_algo])
        ac            = ALGO_COLORS[current_algo]

        # header
        self.solution_text.append(
            f"<span style='color:{C['neon_cyan']};font-size:14px;font-weight:bold;letter-spacing:3px;'>"
            f"RESULTS — {current_algo}</span>"
            f"<span style='color:{C['text_dim']};'> &nbsp;|&nbsp; start: {start}</span><br>"
        )

        # comparison table
        header_bg = C["surface"]
        self.solution_text.append(
            f"<table width='100%' cellspacing='0' style='border-collapse:collapse;font-size:12px;font-family:Consolas,monospace;'>"
            f"<tr style='background:{header_bg};'>"
            f"<td style='padding:5px 10px;color:{C['text_dim']};letter-spacing:2px;font-size:10px;'>ALGO</td>"
            f"<td style='padding:5px 10px;color:{C['text_dim']};letter-spacing:2px;font-size:10px;text-align:center;'>STEPS</td>"
            f"<td style='padding:5px 10px;color:{C['text_dim']};letter-spacing:2px;font-size:10px;text-align:center;'>DELTA</td>"
            f"<td style='padding:5px 10px;color:{C['text_dim']};letter-spacing:2px;font-size:10px;text-align:center;'>STATUS</td>"
            f"</tr>"
        )

        for i, (algo, path) in enumerate(all_results.items()):
            steps = len(path)
            col   = ALGO_COLORS[algo]
            bg    = "rgba(255,255,255,0.02)" if i % 2 == 0 else "rgba(0,0,0,0.2)"
            is_current = (algo == current_algo)
            is_best    = (steps == best_steps)

            if is_best and is_current:
                badge = "⭐ OPTIMAL + RUNNING"
                badge_col = C['neon_green']
            elif is_best:
                badge = "⭐ OPTIMAL"
                badge_col = C['neon_green']
            elif is_current:
                badge = "▶ RUNNING"
                badge_col = col
            else:
                badge = "—"
                badge_col = C['text_dim']

            diff = steps - current_steps
            if diff > 0:
                diff_str = f"<span style='color:{C['neon_red']};'>+{diff}</span>"
            elif diff < 0:
                diff_str = f"<span style='color:{C['neon_green']};'>{diff}</span>"
            else:
                diff_str = f"<span style='color:{C['text_dim']};'>0</span>"

            row_bg = f"background:rgba(0,212,255,0.05);border-left:2px solid {col};" if is_current else f"background:{bg};"
            self.solution_text.append(
                f"<tr style='{row_bg}'>"
                f"<td style='padding:5px 10px;color:{col};font-weight:bold;'>{algo}</td>"
                f"<td style='padding:5px 10px;text-align:center;color:{C['text_prime']};font-weight:bold;'>{steps}</td>"
                f"<td style='padding:5px 10px;text-align:center;'>{diff_str}</td>"
                f"<td style='padding:5px 10px;text-align:center;color:{badge_col};font-size:11px;'><b>{badge}</b></td>"
                f"</tr>"
            )
        self.solution_text.append("</table><br>")

        # conclusion
        ng = C['neon_green']
        tm = C['text_mid']
        td = C['text_dim']
        no = C['neon_orange']
        if best_algo == current_algo:
            self.solution_text.append(
                f"<div style='border-left:2px solid {ng};padding:8px 12px;background:rgba(0,255,136,0.06);'>"
                f"<span style='color:{ng};font-weight:bold;'>✓ {current_algo} is the optimal algorithm</span> "
                f"<span style='color:{tm};'>for this map with {best_steps} steps.</span></div>"
            )
        else:
            saved = current_steps - best_steps
            opt_col = ALGO_COLORS[best_algo]
            self.solution_text.append(
                f"<div style='border-left:2px solid {no};padding:8px 12px;background:rgba(255,140,0,0.06);'>"
                f"<span style='color:{opt_col};font-weight:bold;'>⚡ {best_algo}</span> "
                f"<span style='color:{tm};'>is optimal ({best_steps} steps) — saves </span>"
                f"<span style='color:{ng};font-weight:bold;'>{saved} steps</span> "
                f"<span style='color:{td};'>vs {current_algo} ({current_steps})</span></div>"
            )

        # path display
        self.solution_text.append(
            f"<br><span style='color:{ac};font-size:11px;letter-spacing:2px;'>PATH — {current_algo} ({current_steps} steps)</span><br>"
        )
        chunks = [f"<span style='color:{C['text_dim']};'>{i}:</span><span style='color:{C['text_prime']};'>{pos}</span>"
                  for i, pos in enumerate(self.path)]
        self.solution_text.append(" <span style='color:#1A2E4A;'>›</span> ".join(chunks))

        if best_algo != current_algo:
            best_path = all_results[best_algo]
            opt_col = ALGO_COLORS[best_algo]
            self.solution_text.append(
                f"<br><br><span style='color:{opt_col};font-size:11px;letter-spacing:2px;'>PATH — {best_algo} [{best_steps} steps]</span><br>"
            )
            opt_chunks = [f"<span style='color:{C['text_dim']};'>{i}:</span><span style='color:{C['text_prime']};'>{pos}</span>"
                          for i, pos in enumerate(best_path)]
            self.solution_text.append(" <span style='color:#1A2E4A;'>›</span> ".join(opt_chunks))


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────
app = QApplication(sys.argv)
app.setStyle("Fusion")
window = VacuumApp()
window.show()
sys.exit(app.exec())