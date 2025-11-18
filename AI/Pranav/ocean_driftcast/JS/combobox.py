"""
Synthetic demo for presentation, not scientific output.

Custom combobox widget for Matplotlib with dropdown, type-ahead, and keyboard navigation.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.widgets import TextBox
from difflib import get_close_matches
from typing import List, Callable, Optional


class ComboBox:
    """
    A combobox widget combining a textbox with a dropdown list.
    Supports type-ahead filtering, keyboard navigation, and fuzzy matching.
    """

    def __init__(self, ax_textbox, ax_dropdown_btn, options: List[str],
                 on_select: Callable[[str], None], initial_text: str = ""):
        """
        Initialize combobox.

        Args:
            ax_textbox: Matplotlib axes for the text input
            ax_dropdown_btn: Matplotlib axes for the dropdown button
            options: List of all available options
            on_select: Callback function when option is selected
            initial_text: Initial text in textbox
        """
        self.all_options = sorted(options)
        self.filtered_options = self.all_options.copy()
        self.on_select = on_select
        self.selected_index = 0
        self.is_dropdown_open = False

        # Colors
        self.bg_color = '#0f3548'
        self.text_color = 'white'
        self.highlight_color = '#00d9ff'
        self.border_color = '#00d9ff'

        # Create textbox
        self.textbox = TextBox(
            ax_textbox, '',
            initial=initial_text,
            color=self.bg_color,
            hovercolor='#1a4a5f',
            label_pad=0.01
        )
        self.textbox.text_disp.set_color(self.text_color)
        self.textbox.on_submit(self._on_textbox_submit)
        self.textbox.on_text_change(self._on_text_change)

        # Create dropdown button
        self.dropdown_btn_ax = ax_dropdown_btn
        self.dropdown_btn_ax.set_facecolor(self.bg_color)
        self.dropdown_btn_ax.set_xlim(0, 1)
        self.dropdown_btn_ax.set_ylim(0, 1)
        self.dropdown_btn_ax.axis('off')

        # Draw dropdown arrow
        arrow = mpatches.FancyBboxPatch(
            (0.1, 0.3), 0.8, 0.4,
            boxstyle="round,pad=0.05",
            facecolor=self.bg_color,
            edgecolor=self.border_color,
            linewidth=1
        )
        self.dropdown_btn_ax.add_patch(arrow)

        # Arrow symbol
        self.dropdown_btn_ax.text(
            0.5, 0.5, '▼',
            ha='center', va='center',
            color=self.text_color,
            fontsize=10,
            weight='bold'
        )

        # Connect button click
        self.dropdown_btn_ax.figure.canvas.mpl_connect(
            'button_press_event', self._on_dropdown_click
        )

        # Dropdown list (created on demand)
        self.dropdown_ax = None
        self.dropdown_items = []
        self.dropdown_patches = []

        # Keyboard handler
        self.key_conn = None

    def _on_textbox_submit(self, text):
        """Handle Enter key in textbox."""
        # Select current filtered option or first match
        if self.filtered_options:
            if self.is_dropdown_open and 0 <= self.selected_index < len(self.filtered_options):
                selected = self.filtered_options[self.selected_index]
            else:
                # Fuzzy match
                matches = get_close_matches(text, self.all_options, n=1, cutoff=0.3)
                selected = matches[0] if matches else self.filtered_options[0]

            self.textbox.set_val(selected)
            self._close_dropdown()
            self.on_select(selected)

    def _on_text_change(self, text):
        """Handle text changes for type-ahead filtering."""
        if not text.strip():
            self.filtered_options = self.all_options.copy()
        else:
            # Fuzzy matching
            text_lower = text.lower()

            # Exact matches first
            exact = [opt for opt in self.all_options if text_lower in opt.lower()]

            # Then fuzzy matches
            fuzzy = get_close_matches(text, self.all_options, n=10, cutoff=0.4)

            # Combine, removing duplicates
            self.filtered_options = exact + [f for f in fuzzy if f not in exact]

            # If nothing found, show all
            if not self.filtered_options:
                self.filtered_options = self.all_options.copy()

        # Reset selection
        self.selected_index = 0

        # Update dropdown if open
        if self.is_dropdown_open:
            self._update_dropdown_list()

    def _on_dropdown_click(self, event):
        """Handle dropdown button click."""
        if event.inaxes == self.dropdown_btn_ax:
            if self.is_dropdown_open:
                self._close_dropdown()
            else:
                self._open_dropdown()

    def _open_dropdown(self):
        """Open the dropdown list."""
        if self.is_dropdown_open:
            return

        self.is_dropdown_open = True

        # Create dropdown axes below textbox
        fig = self.textbox.ax.figure

        # Position below textbox
        textbox_pos = self.textbox.ax.get_position()

        # Calculate dropdown size
        max_items = min(10, len(self.filtered_options))
        item_height = 0.03
        dropdown_height = max_items * item_height

        self.dropdown_ax = fig.add_axes([
            textbox_pos.x0,
            textbox_pos.y0 - dropdown_height - 0.01,
            textbox_pos.width,
            dropdown_height
        ])

        self.dropdown_ax.set_facecolor(self.bg_color)
        self.dropdown_ax.set_xlim(0, 1)
        self.dropdown_ax.set_ylim(0, max_items)
        self.dropdown_ax.axis('off')

        # Add border
        border = mpatches.Rectangle(
            (0, 0), 1, max_items,
            fill=False,
            edgecolor=self.border_color,
            linewidth=2,
            transform=self.dropdown_ax.transData
        )
        self.dropdown_ax.add_patch(border)

        # Populate list
        self._update_dropdown_list()

        # Connect keyboard
        self.key_conn = fig.canvas.mpl_connect('key_press_event', self._on_key_press)

        # Connect click on items
        self.click_conn = fig.canvas.mpl_connect('button_press_event', self._on_item_click)

        fig.canvas.draw_idle()

    def _update_dropdown_list(self):
        """Update dropdown list items."""
        if not self.dropdown_ax:
            return

        # Clear existing items
        for patch in self.dropdown_patches:
            patch.remove()
        for text in self.dropdown_items:
            text.remove()

        self.dropdown_patches = []
        self.dropdown_items = []

        # Show up to 10 items
        max_items = min(10, len(self.filtered_options))

        for i in range(max_items):
            option = self.filtered_options[i]
            y_pos = max_items - i - 1

            # Background patch
            is_selected = (i == self.selected_index)
            bg_color = self.highlight_color if is_selected else self.bg_color
            fg_color = '#000000' if is_selected else self.text_color

            patch = mpatches.Rectangle(
                (0, y_pos), 1, 1,
                facecolor=bg_color,
                edgecolor='none',
                transform=self.dropdown_ax.transData
            )
            self.dropdown_ax.add_patch(patch)
            self.dropdown_patches.append(patch)

            # Text
            text = self.dropdown_ax.text(
                0.02, y_pos + 0.5,
                option,
                ha='left', va='center',
                color=fg_color,
                fontsize=8,
                transform=self.dropdown_ax.transData
            )
            self.dropdown_items.append(text)

        self.dropdown_ax.figure.canvas.draw_idle()

    def _close_dropdown(self):
        """Close the dropdown list."""
        if not self.is_dropdown_open:
            return

        self.is_dropdown_open = False

        if self.dropdown_ax:
            self.dropdown_ax.remove()
            self.dropdown_ax = None

        self.dropdown_items = []
        self.dropdown_patches = []

        if self.key_conn:
            self.textbox.ax.figure.canvas.mpl_disconnect(self.key_conn)
            self.key_conn = None

        if hasattr(self, 'click_conn') and self.click_conn:
            self.textbox.ax.figure.canvas.mpl_disconnect(self.click_conn)
            self.click_conn = None

        self.textbox.ax.figure.canvas.draw_idle()

    def _on_key_press(self, event):
        """Handle keyboard navigation."""
        if not self.is_dropdown_open:
            return

        if event.key == 'down':
            # Move down
            self.selected_index = min(self.selected_index + 1, len(self.filtered_options) - 1)
            self._update_dropdown_list()

        elif event.key == 'up':
            # Move up
            self.selected_index = max(self.selected_index - 1, 0)
            self._update_dropdown_list()

        elif event.key == 'enter':
            # Select current item
            if self.filtered_options:
                selected = self.filtered_options[self.selected_index]
                self.textbox.set_val(selected)
                self._close_dropdown()
                self.on_select(selected)

        elif event.key == 'escape':
            # Close dropdown
            self._close_dropdown()

    def _on_item_click(self, event):
        """Handle click on dropdown item."""
        if not self.is_dropdown_open or not self.dropdown_ax:
            return

        if event.inaxes == self.dropdown_ax:
            # Determine which item was clicked
            max_items = min(10, len(self.filtered_options))
            y = event.ydata

            if y is not None:
                item_index = int(max_items - y - 1)

                if 0 <= item_index < len(self.filtered_options):
                    selected = self.filtered_options[item_index]
                    self.textbox.set_val(selected)
                    self._close_dropdown()
                    self.on_select(selected)

    def set_options(self, options: List[str]):
        """Update the list of available options."""
        self.all_options = sorted(options)
        self.filtered_options = self.all_options.copy()
        self.selected_index = 0

        if self.is_dropdown_open:
            self._update_dropdown_list()

    def get_value(self) -> str:
        """Get current textbox value."""
        return self.textbox.text

    def set_value(self, value: str):
        """Set textbox value."""
        self.textbox.set_val(value)
