# -*- coding: utf-8 -*-
"""
qt_compat.py
Compatibilité QGIS 3 / QGIS 4 -> Qt5 / Qt6

Objectifs :
- Utiliser exclusivement qgis.PyQt
- Fournir des alias stables pour les enums Qt souvent cassés en Qt6
- Fournir quelques helpers simples pour éviter les if/else partout
"""

from __future__ import annotations

from qgis.PyQt import QtCore, QtGui, QtWidgets
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QPalette
from qgis.PyQt.QtWidgets import QComboBox
from qgis.PyQt.QtNetwork import QNetworkReply, QNetworkRequest, QNetworkAccessManager

import platform

IS_WINDOWS = platform.system().lower() == "windows"

# ---------------------------------------------------------
# Version info
# ---------------------------------------------------------
IS_QT6 = hasattr(Qt, "AlignmentFlag")
IS_QT5 = not IS_QT6


# ---------------------------------------------------------
# Helpers internes
# ---------------------------------------------------------
def _get_enum(container, name, fallback=None):
    return getattr(container, name, fallback)


def _resolve(root, qt6_chain: str, qt5_attr: str, default=None):
    """
    Résout un enum/attribut Qt6 via une chaîne imbriquée,
    avec fallback Qt5 direct.
    """
    try:
        cur = root
        for part in qt6_chain.split("."):
            cur = getattr(cur, part)
        return cur
    except Exception:
        try:
            return getattr(root, qt5_attr)
        except Exception:
            return default


def _resolve_any(root, qt6_chains: list[str], qt5_attrs: list[str], default=None):
    """
    Essaie plusieurs chemins Qt6 puis plusieurs noms Qt5.
    """
    for chain in qt6_chains:
        try:
            cur = root
            for part in chain.split("."):
                cur = getattr(cur, part)
            return cur
        except Exception:
            pass

    for attr in qt5_attrs:
        try:
            return getattr(root, attr)
        except Exception:
            pass

    return default


# ---------------------------------------------------------
# Read/Write state
# ---------------------------------------------------------
try:
    from qgis.PyQt.QtCore import QIODeviceBase
    FILE_READ_ONLY = QIODeviceBase.OpenModeFlag.ReadOnly
    FILE_WRITE_ONLY = QIODeviceBase.OpenModeFlag.WriteOnly
    FILE_READ_WRITE = QIODeviceBase.OpenModeFlag.ReadWrite
except Exception:
    from qgis.PyQt.QtCore import QFile
    FILE_READ_ONLY = QFile.ReadOnly
    FILE_WRITE_ONLY = QFile.WriteOnly
    FILE_READ_WRITE = QFile.ReadWrite


# ---------------------------------------------------------
# QIcon
# ---------------------------------------------------------
QIcon = QtGui.QIcon
if hasattr(QIcon, "Mode"):
    QICON_NORMAL = QIcon.Mode.Normal
    QICON_DISABLED = QIcon.Mode.Disabled
    QICON_ACTIVE = QIcon.Mode.Active
    QICON_SELECTED = QIcon.Mode.Selected

    QICON_ON = QIcon.State.On
    QICON_OFF = QIcon.State.Off
else:
    QICON_NORMAL = QIcon.Normal
    QICON_DISABLED = QIcon.Disabled
    QICON_ACTIVE = QIcon.Active
    QICON_SELECTED = QIcon.Selected

    QICON_ON = QIcon.On
    QICON_OFF = QIcon.Off


# ---------------------------------------------------------
# QComboBox
# ---------------------------------------------------------
try:
    COMBO_INSERT_AT_TOP = QComboBox.InsertPolicy.InsertAtTop
    COMBO_INSERT_AT_BOTTOM = QComboBox.InsertPolicy.InsertAtBottom
    COMBO_INSERT_AT_CURRENT = QComboBox.InsertPolicy.InsertAtCurrent
    COMBO_INSERT_AFTER_CURRENT = QComboBox.InsertPolicy.InsertAfterCurrent
    COMBO_INSERT_BEFORE_CURRENT = QComboBox.InsertPolicy.InsertBeforeCurrent
    COMBO_INSERT_ALPHABETICALLY = QComboBox.InsertPolicy.InsertAlphabetically
    COMBO_NO_INSERT = QComboBox.InsertPolicy.NoInsert
except AttributeError:
    COMBO_INSERT_AT_TOP = QComboBox.InsertAtTop
    COMBO_INSERT_AT_BOTTOM = QComboBox.InsertAtBottom
    COMBO_INSERT_AT_CURRENT = QComboBox.InsertAtCurrent
    COMBO_INSERT_AFTER_CURRENT = QComboBox.InsertAfterCurrent
    COMBO_INSERT_BEFORE_CURRENT = QComboBox.InsertBeforeCurrent
    COMBO_INSERT_ALPHABETICALLY = QComboBox.InsertAlphabetically
    COMBO_NO_INSERT = QComboBox.NoInsert


# ---------------------------------------------------------
# QFont style
# ---------------------------------------------------------
QFont = QtGui.QFont
if hasattr(QFont, "Style"):
    FONTSTYLE_NORMAL = QFont.Style.StyleNormal
    FONTSTYLE_ITALIC = QFont.Style.StyleItalic
    FONTSTYLE_OBLIQUE = QFont.Style.StyleOblique

    FONTSTYLE_MIXED = getattr(QFont.Style, "StyleMixed", None)
    FONTSTYLE_ANY = getattr(QFont.Style, "StyleAny", None)
else:
    FONTSTYLE_NORMAL = QFont.StyleNormal
    FONTSTYLE_ITALIC = QFont.StyleItalic
    FONTSTYLE_OBLIQUE = QFont.StyleOblique

    FONTSTYLE_MIXED = getattr(QFont, "StyleMixed", None)
    FONTSTYLE_ANY = getattr(QFont, "StyleAny", None)


# ---------------------------------------------------------
# Alignment flags
# ---------------------------------------------------------
if hasattr(Qt, "AlignmentFlag"):
    ALIGN_LEFT = Qt.AlignmentFlag.AlignLeft
    ALIGN_RIGHT = Qt.AlignmentFlag.AlignRight
    ALIGN_HCENTER = Qt.AlignmentFlag.AlignHCenter
    ALIGN_JUSTIFY = Qt.AlignmentFlag.AlignJustify
    ALIGN_TOP = Qt.AlignmentFlag.AlignTop
    ALIGN_BOTTOM = Qt.AlignmentFlag.AlignBottom
    ALIGN_VCENTER = Qt.AlignmentFlag.AlignVCenter
    ALIGN_CENTER = Qt.AlignmentFlag.AlignCenter

    ALIGN_LEADING = getattr(Qt.AlignmentFlag, "AlignLeading", ALIGN_LEFT)
    ALIGN_TRAILING = getattr(Qt.AlignmentFlag, "AlignTrailing", ALIGN_RIGHT)
    ALIGN_ABSOLUTE = getattr(Qt.AlignmentFlag, "AlignAbsolute", 0)
    ALIGN_HORIZONTAL_MASK = getattr(Qt.AlignmentFlag, "AlignHorizontal_Mask", 0)
    ALIGN_VERTICAL_MASK = getattr(Qt.AlignmentFlag, "AlignVertical_Mask", 0)
    ALIGN_BASELINE = getattr(Qt.AlignmentFlag, "AlignBaseline", 0)
else:
    ALIGN_LEFT = Qt.AlignLeft
    ALIGN_RIGHT = Qt.AlignRight
    ALIGN_HCENTER = Qt.AlignHCenter
    ALIGN_JUSTIFY = Qt.AlignJustify
    ALIGN_TOP = Qt.AlignTop
    ALIGN_BOTTOM = Qt.AlignBottom
    ALIGN_VCENTER = Qt.AlignVCenter
    ALIGN_CENTER = Qt.AlignCenter

    ALIGN_LEADING = getattr(Qt, "AlignLeading", ALIGN_LEFT)
    ALIGN_TRAILING = getattr(Qt, "AlignTrailing", ALIGN_RIGHT)
    ALIGN_ABSOLUTE = getattr(Qt, "AlignAbsolute", 0)
    ALIGN_HORIZONTAL_MASK = getattr(Qt, "AlignHorizontal_Mask", 0)
    ALIGN_VERTICAL_MASK = getattr(Qt, "AlignVertical_Mask", 0)
    ALIGN_BASELINE = getattr(Qt, "AlignBaseline", 0)

# ---------------------------------------------------------
# Global colors
# ---------------------------------------------------------
if hasattr(Qt, "GlobalColor"):
    COLOR_BLACK = Qt.GlobalColor.black
    COLOR_WHITE = Qt.GlobalColor.white
    COLOR_RED = Qt.GlobalColor.red
    COLOR_GREEN = Qt.GlobalColor.green
    COLOR_BLUE = Qt.GlobalColor.blue
    COLOR_CYAN = Qt.GlobalColor.cyan
    COLOR_MAGENTA = Qt.GlobalColor.magenta
    COLOR_YELLOW = Qt.GlobalColor.yellow
    COLOR_GRAY = Qt.GlobalColor.gray
    COLOR_DARKGRAY = Qt.GlobalColor.darkGray
    COLOR_LIGHTGRAY = Qt.GlobalColor.lightGray
    COLOR_TRANSPARENT = Qt.GlobalColor.transparent
    COLOR_DARKRED = Qt.GlobalColor.darkRed
    COLOR_DARKGREEN = Qt.GlobalColor.darkGreen
    COLOR_DARKBLUE = Qt.GlobalColor.darkBlue
    COLOR_DARKYELLOW = Qt.GlobalColor.darkYellow
    COLOR_DARKCYAN = Qt.GlobalColor.darkCyan
    COLOR_DARKMAGENTA = Qt.GlobalColor.darkMagenta
else:
    COLOR_BLACK = Qt.black
    COLOR_WHITE = Qt.white
    COLOR_RED = Qt.red
    COLOR_GREEN = Qt.green
    COLOR_BLUE = Qt.blue
    COLOR_CYAN = Qt.cyan
    COLOR_MAGENTA = Qt.magenta
    COLOR_YELLOW = Qt.yellow
    COLOR_GRAY = Qt.gray
    COLOR_DARKGRAY = Qt.darkGray
    COLOR_LIGHTGRAY = Qt.lightGray
    COLOR_TRANSPARENT = Qt.transparent
    COLOR_DARKRED = Qt.darkRed
    COLOR_DARKGREEN = Qt.darkGreen
    COLOR_DARKBLUE = Qt.darkBlue
    COLOR_DARKYELLOW = Qt.darkYellow
    COLOR_DARKCYAN = Qt.darkCyan
    COLOR_DARKMAGENTA = Qt.darkMagenta

# ---------------------------------------------------------
# QPalette
# ---------------------------------------------------------
PALETTE_ACTIVE = _resolve(QPalette, "ColorGroup.Active", "Active")
PALETTE_INACTIVE = _resolve(QPalette, "ColorGroup.Inactive", "Inactive")
PALETTE_DISABLED = _resolve(QPalette, "ColorGroup.Disabled", "Disabled")

PALETTE_WINDOW_TEXT = _resolve(QPalette, "ColorRole.WindowText", "WindowText")
PALETTE_BUTTON = _resolve(QPalette, "ColorRole.Button", "Button")
PALETTE_LIGHT = _resolve(QPalette, "ColorRole.Light", "Light")
PALETTE_MIDLIGHT = _resolve(QPalette, "ColorRole.Midlight", "Midlight")
PALETTE_DARK = _resolve(QPalette, "ColorRole.Dark", "Dark")
PALETTE_MID = _resolve(QPalette, "ColorRole.Mid", "Mid")
PALETTE_TEXT = _resolve(QPalette, "ColorRole.Text", "Text")
PALETTE_BRIGHT_TEXT = _resolve(QPalette, "ColorRole.BrightText", "BrightText")
PALETTE_BUTTON_TEXT = _resolve(QPalette, "ColorRole.ButtonText", "ButtonText")
PALETTE_BASE = _resolve(QPalette, "ColorRole.Base", "Base")
PALETTE_WINDOW = _resolve(QPalette, "ColorRole.Window", "Window")
PALETTE_SHADOW = _resolve(QPalette, "ColorRole.Shadow", "Shadow")
PALETTE_HIGHLIGHT = _resolve(QPalette, "ColorRole.Highlight", "Highlight")
PALETTE_HIGHLIGHTED_TEXT = _resolve(QPalette, "ColorRole.HighlightedText", "HighlightedText")
PALETTE_LINK = _resolve(QPalette, "ColorRole.Link", "Link")
PALETTE_LINK_VISITED = _resolve(QPalette, "ColorRole.LinkVisited", "LinkVisited")
PALETTE_ALTERNATE_BASE = _resolve(QPalette, "ColorRole.AlternateBase", "AlternateBase")
PALETTE_TOOLTIP_BASE = _resolve(QPalette, "ColorRole.ToolTipBase", "ToolTipBase")
PALETTE_TOOLTIP_TEXT = _resolve(QPalette, "ColorRole.ToolTipText", "ToolTipText")
PALETTE_PLACEHOLDER_TEXT = _resolve(QPalette, "ColorRole.PlaceholderText", "PlaceholderText")


# ---------------------------------------------------------
# Orientation
# ---------------------------------------------------------
if hasattr(Qt, "Orientation"):
    ORIENTATION_HORIZONTAL = Qt.Orientation.Horizontal
    ORIENTATION_VERTICAL = Qt.Orientation.Vertical
else:
    ORIENTATION_HORIZONTAL = Qt.Horizontal
    ORIENTATION_VERTICAL = Qt.Vertical


# ---------------------------------------------------------
# Sort order
# ---------------------------------------------------------
if hasattr(Qt, "SortOrder"):
    SORT_ASCENDING = Qt.SortOrder.AscendingOrder
    SORT_DESCENDING = Qt.SortOrder.DescendingOrder
else:
    SORT_ASCENDING = Qt.AscendingOrder
    SORT_DESCENDING = Qt.DescendingOrder


# ---------------------------------------------------------
# Check state
# ---------------------------------------------------------
if hasattr(Qt, "CheckState"):
    CHECKED = Qt.CheckState.Checked
    UNCHECKED = Qt.CheckState.Unchecked
    PARTIALLY_CHECKED = Qt.CheckState.PartiallyChecked
else:
    CHECKED = Qt.Checked
    UNCHECKED = Qt.Unchecked
    PARTIALLY_CHECKED = Qt.PartiallyChecked


# ---------------------------------------------------------
# QItemSelectionModel
# ---------------------------------------------------------
QItemSelectionModel = QtCore.QItemSelectionModel
if hasattr(QItemSelectionModel, "SelectionFlag"):
    SELECTION_CLEAR = QItemSelectionModel.SelectionFlag.Clear
    SELECTION_SELECT = QItemSelectionModel.SelectionFlag.Select
    SELECTION_DESELECT = QItemSelectionModel.SelectionFlag.Deselect
    SELECTION_TOGGLE = QItemSelectionModel.SelectionFlag.Toggle
    SELECTION_CURRENT = QItemSelectionModel.SelectionFlag.Current
    SELECTION_ROWS = QItemSelectionModel.SelectionFlag.Rows
    SELECTION_COLUMNS = QItemSelectionModel.SelectionFlag.Columns
    SELECTION_CLEAR_AND_SELECT = QItemSelectionModel.SelectionFlag.ClearAndSelect
else:
    SELECTION_CLEAR = QItemSelectionModel.Clear
    SELECTION_SELECT = QItemSelectionModel.Select
    SELECTION_DESELECT = QItemSelectionModel.Deselect
    SELECTION_TOGGLE = QItemSelectionModel.Toggle
    SELECTION_CURRENT = QItemSelectionModel.Current
    SELECTION_ROWS = QItemSelectionModel.Rows
    SELECTION_COLUMNS = QItemSelectionModel.Columns
    SELECTION_CLEAR_AND_SELECT = QItemSelectionModel.ClearAndSelect


# ---------------------------------------------------------
# ItemDataRole
# ---------------------------------------------------------
if hasattr(Qt, "ItemDataRole"):
    DISPLAY_ROLE = Qt.ItemDataRole.DisplayRole
    DECORATION_ROLE = Qt.ItemDataRole.DecorationRole
    EDIT_ROLE = Qt.ItemDataRole.EditRole
    TOOLTIP_ROLE = Qt.ItemDataRole.ToolTipRole
    STATUS_TIP_ROLE = Qt.ItemDataRole.StatusTipRole
    WHATS_THIS_ROLE = Qt.ItemDataRole.WhatsThisRole
    FONT_ROLE = Qt.ItemDataRole.FontRole
    TEXT_ALIGNMENT_ROLE = Qt.ItemDataRole.TextAlignmentRole
    BACKGROUND_ROLE = Qt.ItemDataRole.BackgroundRole
    FOREGROUND_ROLE = Qt.ItemDataRole.ForegroundRole
    CHECK_STATE_ROLE = Qt.ItemDataRole.CheckStateRole
    USER_ROLE = Qt.ItemDataRole.UserRole
else:
    DISPLAY_ROLE = Qt.DisplayRole
    DECORATION_ROLE = Qt.DecorationRole
    EDIT_ROLE = Qt.EditRole
    TOOLTIP_ROLE = Qt.ToolTipRole
    STATUS_TIP_ROLE = Qt.StatusTipRole
    WHATS_THIS_ROLE = Qt.WhatsThisRole
    FONT_ROLE = Qt.FontRole
    TEXT_ALIGNMENT_ROLE = Qt.TextAlignmentRole
    BACKGROUND_ROLE = Qt.BackgroundRole
    FOREGROUND_ROLE = Qt.ForegroundRole
    CHECK_STATE_ROLE = Qt.CheckStateRole
    USER_ROLE = Qt.UserRole


# ---------------------------------------------------------
# Text flags
# ---------------------------------------------------------
if hasattr(Qt, "TextFlag"):
    TEXTFLAG_SINGLELINE = Qt.TextFlag.TextSingleLine
    TEXTFLAG_DONTCLIP = getattr(Qt.TextFlag, "TextDontClip", None)
    TEXTFLAG_EXPANDTABS = getattr(Qt.TextFlag, "TextExpandTabs", None)
    TEXTFLAG_SHOWMNEMONIC = getattr(Qt.TextFlag, "TextShowMnemonic", None)
    TEXTFLAG_WORDWRAP = getattr(Qt.TextFlag, "TextWordWrap", None)
else:
    TEXTFLAG_SINGLELINE = Qt.TextSingleLine
    TEXTFLAG_DONTCLIP = getattr(Qt, "TextDontClip", None)
    TEXTFLAG_EXPANDTABS = getattr(Qt, "TextExpandTabs", None)
    TEXTFLAG_SHOWMNEMONIC = getattr(Qt, "TextShowMnemonic", None)
    TEXTFLAG_WORDWRAP = getattr(Qt, "TextWordWrap", None)


# ---------------------------------------------------------
# Item flags
# ---------------------------------------------------------
if hasattr(Qt, "ItemFlag"):
    ITEM_IS_SELECTABLE = Qt.ItemFlag.ItemIsSelectable
    ITEM_IS_EDITABLE = Qt.ItemFlag.ItemIsEditable
    ITEM_IS_DRAG_ENABLED = Qt.ItemFlag.ItemIsDragEnabled
    ITEM_IS_DROP_ENABLED = Qt.ItemFlag.ItemIsDropEnabled
    ITEM_IS_USER_CHECKABLE = Qt.ItemFlag.ItemIsUserCheckable
    ITEM_IS_ENABLED = Qt.ItemFlag.ItemIsEnabled
    ITEM_IS_AUTO_TRISTATE = Qt.ItemFlag.ItemIsAutoTristate
    ITEM_NEVER_HAS_CHILDREN = Qt.ItemFlag.ItemNeverHasChildren
    ITEM_IS_USER_TRISTATE = getattr(Qt.ItemFlag, "ItemIsUserTristate", None)
else:
    ITEM_IS_SELECTABLE = Qt.ItemIsSelectable
    ITEM_IS_EDITABLE = Qt.ItemIsEditable
    ITEM_IS_DRAG_ENABLED = Qt.ItemIsDragEnabled
    ITEM_IS_DROP_ENABLED = Qt.ItemIsDropEnabled
    ITEM_IS_USER_CHECKABLE = Qt.ItemIsUserCheckable
    ITEM_IS_ENABLED = Qt.ItemIsEnabled
    ITEM_IS_AUTO_TRISTATE = Qt.ItemIsAutoTristate
    ITEM_NEVER_HAS_CHILDREN = Qt.ItemNeverHasChildren
    ITEM_IS_USER_TRISTATE = getattr(Qt, "ItemIsUserTristate", None)


# ---------------------------------------------------------
# Window modality
# ---------------------------------------------------------
if hasattr(Qt, "WindowModality"):
    WINDOW_MODAL = Qt.WindowModality.WindowModal
    APPLICATION_MODAL = Qt.WindowModality.ApplicationModal
    NON_MODAL = Qt.WindowModality.NonModal
else:
    WINDOW_MODAL = Qt.WindowModal
    APPLICATION_MODAL = Qt.ApplicationModal
    NON_MODAL = Qt.NonModal


# ---------------------------------------------------------
# Context menu policy
# ---------------------------------------------------------
if hasattr(Qt, "ContextMenuPolicy"):
    CUSTOM_CONTEXT_MENU = Qt.ContextMenuPolicy.CustomContextMenu
    DEFAULT_CONTEXT_MENU = Qt.ContextMenuPolicy.DefaultContextMenu
    NO_CONTEXT_MENU = Qt.ContextMenuPolicy.NoContextMenu
else:
    CUSTOM_CONTEXT_MENU = Qt.CustomContextMenu
    DEFAULT_CONTEXT_MENU = Qt.DefaultContextMenu
    NO_CONTEXT_MENU = Qt.NoContextMenu


# ---------------------------------------------------------
# Pen style
# ---------------------------------------------------------
if hasattr(Qt, "PenStyle"):
    PEN_NO_PEN = Qt.PenStyle.NoPen
    PEN_SOLID_LINE = Qt.PenStyle.SolidLine
    PEN_DASH_LINE = Qt.PenStyle.DashLine
    PEN_DOT_LINE = Qt.PenStyle.DotLine
else:
    PEN_NO_PEN = Qt.NoPen
    PEN_SOLID_LINE = Qt.SolidLine
    PEN_DASH_LINE = Qt.DashLine
    PEN_DOT_LINE = Qt.DotLine


# ---------------------------------------------------------
# Brush style
# ---------------------------------------------------------
if hasattr(Qt, "BrushStyle"):
    BRUSH_NO_BRUSH = Qt.BrushStyle.NoBrush
    BRUSH_SOLID_PATTERN = Qt.BrushStyle.SolidPattern
else:
    BRUSH_NO_BRUSH = Qt.NoBrush
    BRUSH_SOLID_PATTERN = Qt.SolidPattern


# ---------------------------------------------------------
# Cursor shape
# ---------------------------------------------------------
if hasattr(Qt, "CursorShape"):
    CURSOR_ARROW = Qt.CursorShape.ArrowCursor
    CURSOR_WAIT = Qt.CursorShape.WaitCursor
    CURSOR_POINTING_HAND = Qt.CursorShape.PointingHandCursor
    CURSOR_CROSS = Qt.CursorShape.CrossCursor
else:
    CURSOR_ARROW = Qt.ArrowCursor
    CURSOR_WAIT = Qt.WaitCursor
    CURSOR_POINTING_HAND = Qt.PointingHandCursor
    CURSOR_CROSS = Qt.CrossCursor


# ---------------------------------------------------------
# Focus policy
# ---------------------------------------------------------
if hasattr(Qt, "FocusPolicy"):
    FOCUS_NO = Qt.FocusPolicy.NoFocus
    FOCUS_TAB = Qt.FocusPolicy.TabFocus
    FOCUS_CLICK = Qt.FocusPolicy.ClickFocus
    FOCUS_STRONG = Qt.FocusPolicy.StrongFocus
else:
    FOCUS_NO = Qt.NoFocus
    FOCUS_TAB = Qt.TabFocus
    FOCUS_CLICK = Qt.ClickFocus
    FOCUS_STRONG = Qt.StrongFocus


# ---------------------------------------------------------
# Focus reasons
# ---------------------------------------------------------
try:
    FOCUS_MOUSE = Qt.FocusReason.MouseFocusReason
    FOCUS_REASON_TAB = Qt.FocusReason.TabFocusReason
    FOCUS_BACKTAB = Qt.FocusReason.BacktabFocusReason
    FOCUS_ACTIVE_WINDOW = Qt.FocusReason.ActiveWindowFocusReason
    FOCUS_POPUP = Qt.FocusReason.PopupFocusReason
    FOCUS_SHORTCUT = Qt.FocusReason.ShortcutFocusReason
    FOCUS_MENU_BAR = Qt.FocusReason.MenuBarFocusReason
    FOCUS_OTHER = Qt.FocusReason.OtherFocusReason
    FOCUS_REASON_NO = Qt.FocusReason.NoFocusReason
except AttributeError:
    FOCUS_MOUSE = Qt.MouseFocusReason
    FOCUS_REASON_TAB = Qt.TabFocusReason
    FOCUS_BACKTAB = Qt.BacktabFocusReason
    FOCUS_ACTIVE_WINDOW = Qt.ActiveWindowFocusReason
    FOCUS_POPUP = Qt.PopupFocusReason
    FOCUS_SHORTCUT = Qt.ShortcutFocusReason
    FOCUS_MENU_BAR = Qt.MenuBarFocusReason
    FOCUS_OTHER = Qt.OtherFocusReason
    FOCUS_REASON_NO = Qt.NoFocusReason


# ---------------------------------------------------------
# Text interaction flags
# ---------------------------------------------------------
if hasattr(Qt, "TextInteractionFlag"):
    TEXT_NO_INTERACTION = Qt.TextInteractionFlag.NoTextInteraction
    TEXT_SELECTABLE_BY_MOUSE = Qt.TextInteractionFlag.TextSelectableByMouse
    TEXT_SELECTABLE_BY_KEYBOARD = Qt.TextInteractionFlag.TextSelectableByKeyboard
    LINKS_ACCESSIBLE_BY_MOUSE = Qt.TextInteractionFlag.LinksAccessibleByMouse
    LINKS_ACCESSIBLE_BY_KEYBOARD = Qt.TextInteractionFlag.LinksAccessibleByKeyboard
    TEXT_EDITABLE = Qt.TextInteractionFlag.TextEditable
    TEXT_EDITOR_INTERACTION = Qt.TextInteractionFlag.TextEditorInteraction
    TEXT_BROWSER_INTERACTION = Qt.TextInteractionFlag.TextBrowserInteraction
else:
    TEXT_NO_INTERACTION = Qt.NoTextInteraction
    TEXT_SELECTABLE_BY_MOUSE = Qt.TextSelectableByMouse
    TEXT_SELECTABLE_BY_KEYBOARD = Qt.TextSelectableByKeyboard
    LINKS_ACCESSIBLE_BY_MOUSE = Qt.LinksAccessibleByMouse
    LINKS_ACCESSIBLE_BY_KEYBOARD = Qt.LinksAccessibleByKeyboard
    TEXT_EDITABLE = Qt.TextEditable
    TEXT_EDITOR_INTERACTION = Qt.TextEditorInteraction
    TEXT_BROWSER_INTERACTION = Qt.TextBrowserInteraction


# ---------------------------------------------------------
# Keyboard modifiers
# ---------------------------------------------------------
if hasattr(Qt, "KeyboardModifier"):
    SHIFT_MODIFIER = Qt.KeyboardModifier.ShiftModifier
    CTRL_MODIFIER = Qt.KeyboardModifier.ControlModifier
    ALT_MODIFIER = Qt.KeyboardModifier.AltModifier
    META_MODIFIER = Qt.KeyboardModifier.MetaModifier
    NO_MODIFIER = Qt.KeyboardModifier.NoModifier
else:
    SHIFT_MODIFIER = Qt.ShiftModifier
    CTRL_MODIFIER = Qt.ControlModifier
    ALT_MODIFIER = Qt.AltModifier
    META_MODIFIER = Qt.MetaModifier
    NO_MODIFIER = Qt.NoModifier


# ---------------------------------------------------------
# Aspect ratio / transformation
# ---------------------------------------------------------
if hasattr(Qt, "AspectRatioMode"):
    KEEP_ASPECT_RATIO = Qt.AspectRatioMode.KeepAspectRatio
    KEEP_ASPECT_RATIO_BY_EXPANDING = Qt.AspectRatioMode.KeepAspectRatioByExpanding
    IGNORE_ASPECT_RATIO = Qt.AspectRatioMode.IgnoreAspectRatio
else:
    KEEP_ASPECT_RATIO = Qt.KeepAspectRatio
    KEEP_ASPECT_RATIO_BY_EXPANDING = Qt.KeepAspectRatioByExpanding
    IGNORE_ASPECT_RATIO = Qt.IgnoreAspectRatio

if hasattr(Qt, "TransformationMode"):
    FAST_TRANSFORMATION = Qt.TransformationMode.FastTransformation
    SMOOTH_TRANSFORMATION = Qt.TransformationMode.SmoothTransformation
else:
    FAST_TRANSFORMATION = Qt.FastTransformation
    SMOOTH_TRANSFORMATION = Qt.SmoothTransformation


# ---------------------------------------------------------
# Case sensitivity / match flags
# ---------------------------------------------------------
if hasattr(Qt, "CaseSensitivity"):
    CASE_SENSITIVE = Qt.CaseSensitivity.CaseSensitive
    CASE_INSENSITIVE = Qt.CaseSensitivity.CaseInsensitive
else:
    CASE_SENSITIVE = Qt.CaseSensitive
    CASE_INSENSITIVE = Qt.CaseInsensitive

if hasattr(Qt, "MatchFlag"):
    MATCH_EXACT = Qt.MatchFlag.MatchExactly
    MATCH_CONTAINS = Qt.MatchFlag.MatchContains
    MATCH_STARTS_WITH = Qt.MatchFlag.MatchStartsWith
    MATCH_ENDS_WITH = Qt.MatchFlag.MatchEndsWith
    MATCH_RECURSIVE = Qt.MatchFlag.MatchRecursive
    MATCH_WRAP = Qt.MatchFlag.MatchWrap
    MATCH_FIXED_STRING = Qt.MatchFlag.MatchFixedString
    MATCH_CASE_SENSITIVE = Qt.MatchFlag.MatchCaseSensitive
else:
    MATCH_EXACT = Qt.MatchExactly
    MATCH_CONTAINS = Qt.MatchContains
    MATCH_STARTS_WITH = Qt.MatchStartsWith
    MATCH_ENDS_WITH = Qt.MatchEndsWith
    MATCH_RECURSIVE = Qt.MatchRecursive
    MATCH_WRAP = Qt.MatchWrap
    MATCH_FIXED_STRING = Qt.MatchFixedString
    MATCH_CASE_SENSITIVE = Qt.MatchCaseSensitive


# ---------------------------------------------------------
# Tool button style / arrows
# ---------------------------------------------------------
if hasattr(Qt, "ToolButtonStyle"):
    TOOLBUTTON_ICON_ONLY = Qt.ToolButtonStyle.ToolButtonIconOnly
    TOOLBUTTON_TEXT_ONLY = Qt.ToolButtonStyle.ToolButtonTextOnly
    TOOLBUTTON_TEXT_BESIDE_ICON = Qt.ToolButtonStyle.ToolButtonTextBesideIcon
    TOOLBUTTON_TEXT_UNDER_ICON = Qt.ToolButtonStyle.ToolButtonTextUnderIcon
else:
    TOOLBUTTON_ICON_ONLY = Qt.ToolButtonIconOnly
    TOOLBUTTON_TEXT_ONLY = Qt.ToolButtonTextOnly
    TOOLBUTTON_TEXT_BESIDE_ICON = Qt.ToolButtonTextBesideIcon
    TOOLBUTTON_TEXT_UNDER_ICON = Qt.ToolButtonTextUnderIcon

if hasattr(Qt, "ArrowType"):
    ARROW_UP = Qt.ArrowType.UpArrow
    ARROW_DOWN = Qt.ArrowType.DownArrow
    ARROW_LEFT = Qt.ArrowType.LeftArrow
    ARROW_RIGHT = Qt.ArrowType.RightArrow
    ARROW_NONE = Qt.ArrowType.NoArrow
else:
    ARROW_UP = Qt.UpArrow
    ARROW_DOWN = Qt.DownArrow
    ARROW_LEFT = Qt.LeftArrow
    ARROW_RIGHT = Qt.RightArrow
    ARROW_NONE = Qt.NoArrow


# ---------------------------------------------------------
# QEvent types
# ---------------------------------------------------------
QEvent = QtCore.QEvent
if hasattr(QEvent, "Type"):
    EVENT_CLOSE = QEvent.Type.Close
    EVENT_SHOW = QEvent.Type.Show
    EVENT_HIDE = QEvent.Type.Hide
    EVENT_RESIZE = QEvent.Type.Resize
    EVENT_MOVE = QEvent.Type.Move

    EVENT_FOCUS_IN = QEvent.Type.FocusIn
    EVENT_FOCUS_OUT = QEvent.Type.FocusOut

    EVENT_MOUSE_BUTTON_PRESS = QEvent.Type.MouseButtonPress
    EVENT_MOUSE_BUTTON_RELEASE = QEvent.Type.MouseButtonRelease
    EVENT_MOUSE_BUTTON_DBLCLICK = QEvent.Type.MouseButtonDblClick
    EVENT_MOUSE_MOVE = QEvent.Type.MouseMove

    EVENT_KEY_PRESS = QEvent.Type.KeyPress
    EVENT_KEY_RELEASE = QEvent.Type.KeyRelease

    EVENT_LANGUAGE_CHANGE = QEvent.Type.LanguageChange
    EVENT_ENABLED_CHANGE = QEvent.Type.EnabledChange
    EVENT_WINDOW_STATE_CHANGE = QEvent.Type.WindowStateChange
else:
    EVENT_CLOSE = QEvent.Close
    EVENT_SHOW = QEvent.Show
    EVENT_HIDE = QEvent.Hide
    EVENT_RESIZE = QEvent.Resize
    EVENT_MOVE = QEvent.Move

    EVENT_FOCUS_IN = QEvent.FocusIn
    EVENT_FOCUS_OUT = QEvent.FocusOut

    EVENT_MOUSE_BUTTON_PRESS = QEvent.MouseButtonPress
    EVENT_MOUSE_BUTTON_RELEASE = QEvent.MouseButtonRelease
    EVENT_MOUSE_BUTTON_DBLCLICK = QEvent.MouseButtonDblClick
    EVENT_MOUSE_MOVE = QEvent.MouseMove

    EVENT_KEY_PRESS = QEvent.KeyPress
    EVENT_KEY_RELEASE = QEvent.KeyRelease

    EVENT_LANGUAGE_CHANGE = QEvent.LanguageChange
    EVENT_ENABLED_CHANGE = QEvent.EnabledChange
    EVENT_WINDOW_STATE_CHANGE = QEvent.WindowStateChange

# ---------------------------------------------------------
# QHeaderView resize modes
# ---------------------------------------------------------
QHeaderView = QtWidgets.QHeaderView
if hasattr(QHeaderView, "ResizeMode"):
    HEADER_INTERACTIVE = QHeaderView.ResizeMode.Interactive
    HEADER_STRETCH = QHeaderView.ResizeMode.Stretch
    HEADER_FIXED = QHeaderView.ResizeMode.Fixed
    HEADER_RESIZE_TO_CONTENTS = QHeaderView.ResizeMode.ResizeToContents
else:
    HEADER_INTERACTIVE = QHeaderView.Interactive
    HEADER_STRETCH = QHeaderView.Stretch
    HEADER_FIXED = QHeaderView.Fixed
    HEADER_RESIZE_TO_CONTENTS = QHeaderView.ResizeToContents


# ---------------------------------------------------------
# QDialogButtonBox standard buttons
# ---------------------------------------------------------
QDialogButtonBox = QtWidgets.QDialogButtonBox
if hasattr(QDialogButtonBox, "StandardButton"):
    BUTTONBOX_OK = QDialogButtonBox.StandardButton.Ok
    BUTTONBOX_CANCEL = QDialogButtonBox.StandardButton.Cancel
    BUTTONBOX_YES = QDialogButtonBox.StandardButton.Yes
    BUTTONBOX_NO = QDialogButtonBox.StandardButton.No
    BUTTONBOX_APPLY = QDialogButtonBox.StandardButton.Apply
    BUTTONBOX_CLOSE = QDialogButtonBox.StandardButton.Close
    BUTTONBOX_SAVE = QDialogButtonBox.StandardButton.Save
    BUTTONBOX_OPEN = QDialogButtonBox.StandardButton.Open
    BUTTONBOX_RESET = QDialogButtonBox.StandardButton.Reset
    BUTTONBOX_HELP = QDialogButtonBox.StandardButton.Help
    BUTTONBOX_DISCARD = getattr(QDialogButtonBox.StandardButton, "Discard", None)
    BUTTONBOX_RESTORE_DEFAULTS = getattr(QDialogButtonBox.StandardButton, "RestoreDefaults", None)
else:
    BUTTONBOX_OK = QDialogButtonBox.Ok
    BUTTONBOX_CANCEL = QDialogButtonBox.Cancel
    BUTTONBOX_YES = QDialogButtonBox.Yes
    BUTTONBOX_NO = QDialogButtonBox.No
    BUTTONBOX_APPLY = QDialogButtonBox.Apply
    BUTTONBOX_CLOSE = QDialogButtonBox.Close
    BUTTONBOX_SAVE = QDialogButtonBox.Save
    BUTTONBOX_OPEN = QDialogButtonBox.Open
    BUTTONBOX_RESET = QDialogButtonBox.Reset
    BUTTONBOX_HELP = QDialogButtonBox.Help
    BUTTONBOX_DISCARD = getattr(QDialogButtonBox, "Discard", None)
    BUTTONBOX_RESTORE_DEFAULTS = getattr(QDialogButtonBox, "RestoreDefaults", None)


# ---------------------------------------------------------
# QMessageBox standard buttons and icons
# ---------------------------------------------------------
QMessageBox = QtWidgets.QMessageBox
if hasattr(QMessageBox, "StandardButton"):
    MSGBOX_OK = QMessageBox.StandardButton.Ok
    MSGBOX_CANCEL = QMessageBox.StandardButton.Cancel
    MSGBOX_YES = QMessageBox.StandardButton.Yes
    MSGBOX_NO = QMessageBox.StandardButton.No
    MSGBOX_CLOSE = QMessageBox.StandardButton.Close

    MSGBOX_NO_ICON = QMessageBox.Icon.NoIcon
    MSGBOX_INFORMATION = QMessageBox.Icon.Information
    MSGBOX_WARNING = QMessageBox.Icon.Warning
    MSGBOX_CRITICAL = QMessageBox.Icon.Critical
    MSGBOX_QUESTION = QMessageBox.Icon.Question
else:
    MSGBOX_OK = QMessageBox.Ok
    MSGBOX_CANCEL = QMessageBox.Cancel
    MSGBOX_YES = QMessageBox.Yes
    MSGBOX_NO = QMessageBox.No
    MSGBOX_CLOSE = QMessageBox.Close

    MSGBOX_NO_ICON = QMessageBox.NoIcon
    MSGBOX_INFORMATION = QMessageBox.Information
    MSGBOX_WARNING = QMessageBox.Warning
    MSGBOX_CRITICAL = QMessageBox.Critical
    MSGBOX_QUESTION = QMessageBox.Question


# ---------------------------------------------------------
# QMessageBox button roles (Qt5 / Qt6)
# ---------------------------------------------------------
QMessageBox = QtWidgets.QMessageBox

if hasattr(QMessageBox, "ButtonRole"):
    # Qt6
    MSGBOX_ACCEPT_ROLE = QMessageBox.ButtonRole.AcceptRole
    MSGBOX_ACTION_ROLE = QMessageBox.ButtonRole.ActionRole
    MSGBOX_REJECT_ROLE = QMessageBox.ButtonRole.RejectRole
else:
    # Qt5
    MSGBOX_ACCEPT_ROLE = QMessageBox.AcceptRole
    MSGBOX_ACTION_ROLE = QMessageBox.ActionRole
    MSGBOX_REJECT_ROLE = QMessageBox.RejectRole


# ---------------------------------------------------------
# QFileDialog
# ---------------------------------------------------------
QFileDialog = QtWidgets.QFileDialog
if hasattr(QFileDialog, "FileMode"):
    FILEMODE_ANY_FILE = QFileDialog.FileMode.AnyFile
    FILEMODE_EXISTING_FILE = QFileDialog.FileMode.ExistingFile
    FILEMODE_EXISTING_FILES = QFileDialog.FileMode.ExistingFiles
    FILEMODE_DIRECTORY = QFileDialog.FileMode.Directory

    ACCEPT_OPEN = QFileDialog.AcceptMode.AcceptOpen
    ACCEPT_SAVE = QFileDialog.AcceptMode.AcceptSave

    OPTION_SHOW_DIRS_ONLY = QFileDialog.Option.ShowDirsOnly
    OPTION_DONT_USE_NATIVE_DIALOG = QFileDialog.Option.DontUseNativeDialog
    OPTION_DONT_RESOLVE_SYMLINKS = QFileDialog.Option.DontResolveSymlinks
else:
    FILEMODE_ANY_FILE = QFileDialog.AnyFile
    FILEMODE_EXISTING_FILE = QFileDialog.ExistingFile
    FILEMODE_EXISTING_FILES = QFileDialog.ExistingFiles
    FILEMODE_DIRECTORY = QFileDialog.Directory

    ACCEPT_OPEN = QFileDialog.AcceptOpen
    ACCEPT_SAVE = QFileDialog.AcceptSave

    OPTION_SHOW_DIRS_ONLY = QFileDialog.ShowDirsOnly
    OPTION_DONT_USE_NATIVE_DIALOG = QFileDialog.DontUseNativeDialog
    OPTION_DONT_RESOLVE_SYMLINKS = QFileDialog.DontResolveSymlinks


# ---------------------------------------------------------
# QSizePolicy
# ---------------------------------------------------------
QSizePolicy = QtWidgets.QSizePolicy
if hasattr(QSizePolicy, "Policy"):
    SIZEPOLICY_FIXED = QSizePolicy.Policy.Fixed
    SIZEPOLICY_MINIMUM = QSizePolicy.Policy.Minimum
    SIZEPOLICY_MAXIMUM = QSizePolicy.Policy.Maximum
    SIZEPOLICY_PREFERRED = QSizePolicy.Policy.Preferred
    SIZEPOLICY_EXPANDING = QSizePolicy.Policy.Expanding
    SIZEPOLICY_MINIMUM_EXPANDING = QSizePolicy.Policy.MinimumExpanding
    SIZEPOLICY_IGNORED = QSizePolicy.Policy.Ignored
else:
    SIZEPOLICY_FIXED = QSizePolicy.Fixed
    SIZEPOLICY_MINIMUM = QSizePolicy.Minimum
    SIZEPOLICY_MAXIMUM = QSizePolicy.Maximum
    SIZEPOLICY_PREFERRED = QSizePolicy.Preferred
    SIZEPOLICY_EXPANDING = QSizePolicy.Expanding
    SIZEPOLICY_MINIMUM_EXPANDING = QSizePolicy.MinimumExpanding
    SIZEPOLICY_IGNORED = QSizePolicy.Ignored


# ---------------------------------------------------------
# QAbstractItemView
# ---------------------------------------------------------
QAbstractItemView = QtWidgets.QAbstractItemView
if hasattr(QAbstractItemView, "SelectionBehavior"):
    # SelectionBehavior
    SELECT_ITEMS = QAbstractItemView.SelectionBehavior.SelectItems
    SELECT_ROWS = QAbstractItemView.SelectionBehavior.SelectRows
    SELECT_COLUMNS = QAbstractItemView.SelectionBehavior.SelectColumns

    # SelectionMode
    SINGLE_SELECTION = QAbstractItemView.SelectionMode.SingleSelection
    MULTI_SELECTION = QAbstractItemView.SelectionMode.MultiSelection
    EXTENDED_SELECTION = QAbstractItemView.SelectionMode.ExtendedSelection
    NO_SELECTION = QAbstractItemView.SelectionMode.NoSelection

    # EditTrigger
    EDIT_NO_EDIT_TRIGGERS = QAbstractItemView.EditTrigger.NoEditTriggers
    EDIT_CURRENT_CHANGED = QAbstractItemView.EditTrigger.CurrentChanged
    EDIT_DOUBLE_CLICKED = QAbstractItemView.EditTrigger.DoubleClicked
    EDIT_SELECTED_CLICKED = QAbstractItemView.EditTrigger.SelectedClicked
    EDIT_EDIT_KEY_PRESSED = QAbstractItemView.EditTrigger.EditKeyPressed
    EDIT_ANY_KEY_PRESSED = QAbstractItemView.EditTrigger.AnyKeyPressed
    EDIT_ALL_EDIT_TRIGGERS = QAbstractItemView.EditTrigger.AllEditTriggers

    # DragDropMode
    DRAGDROP_NO = QAbstractItemView.DragDropMode.NoDragDrop
    DRAGDROP_DRAG_ONLY = QAbstractItemView.DragDropMode.DragOnly
    DRAGDROP_DROP_ONLY = QAbstractItemView.DragDropMode.DropOnly
    DRAGDROP_DRAG_DROP = QAbstractItemView.DragDropMode.DragDrop
    DRAGDROP_INTERNAL_MOVE = QAbstractItemView.DragDropMode.InternalMove

else:
    # SelectionBehavior
    SELECT_ITEMS = QAbstractItemView.SelectItems
    SELECT_ROWS = QAbstractItemView.SelectRows
    SELECT_COLUMNS = QAbstractItemView.SelectColumns

    # SelectionMode
    SINGLE_SELECTION = QAbstractItemView.SingleSelection
    MULTI_SELECTION = QAbstractItemView.MultiSelection
    EXTENDED_SELECTION = QAbstractItemView.ExtendedSelection
    NO_SELECTION = QAbstractItemView.NoSelection

    # EditTrigger
    EDIT_NO_EDIT_TRIGGERS = QAbstractItemView.NoEditTriggers
    EDIT_CURRENT_CHANGED = QAbstractItemView.CurrentChanged
    EDIT_DOUBLE_CLICKED = QAbstractItemView.DoubleClicked
    EDIT_SELECTED_CLICKED = QAbstractItemView.SelectedClicked
    EDIT_EDIT_KEY_PRESSED = QAbstractItemView.EditKeyPressed
    EDIT_ANY_KEY_PRESSED = QAbstractItemView.AnyKeyPressed
    EDIT_ALL_EDIT_TRIGGERS = QAbstractItemView.AllEditTriggers

    # DragDropMode
    DRAGDROP_NO = QAbstractItemView.NoDragDrop
    DRAGDROP_DRAG_ONLY = QAbstractItemView.DragOnly
    DRAGDROP_DROP_ONLY = QAbstractItemView.DropOnly
    DRAGDROP_DRAG_DROP = QAbstractItemView.DragDrop
    DRAGDROP_INTERNAL_MOVE = QAbstractItemView.InternalMove

# ---------------------------------------------------------
# QFrame
# ---------------------------------------------------------
QFrame = QtWidgets.QFrame
if hasattr(QFrame, "Shape"):
    FRAME_NOFRAME = QFrame.Shape.NoFrame
    FRAME_BOX = QFrame.Shape.Box
    FRAME_PANEL = QFrame.Shape.Panel
    FRAME_STYLED_PANEL = QFrame.Shape.StyledPanel
    FRAME_HLINE = QFrame.Shape.HLine
    FRAME_VLINE = QFrame.Shape.VLine
    FRAME_WIN_PANEL = QFrame.Shape.WinPanel

    FRAME_PLAIN = QFrame.Shadow.Plain
    FRAME_RAISED = QFrame.Shadow.Raised
    FRAME_SUNKEN = QFrame.Shadow.Sunken
else:
    FRAME_NOFRAME = QFrame.NoFrame
    FRAME_BOX = QFrame.Box
    FRAME_PANEL = QFrame.Panel
    FRAME_STYLED_PANEL = QFrame.StyledPanel
    FRAME_HLINE = QFrame.HLine
    FRAME_VLINE = QFrame.VLine
    FRAME_WIN_PANEL = QFrame.WinPanel

    FRAME_PLAIN = QFrame.Plain
    FRAME_RAISED = QFrame.Raised
    FRAME_SUNKEN = QFrame.Sunken


# ---------------------------------------------------------
# QStyle standard pixmaps / icons
# ---------------------------------------------------------
QStyle = QtWidgets.QStyle
if hasattr(QStyle, "StandardPixmap"):
    STYLE_SP_DIR_ICON = QStyle.StandardPixmap.SP_DirIcon
    STYLE_SP_FILE_ICON = QStyle.StandardPixmap.SP_FileIcon
    STYLE_SP_DESKTOP_ICON = QStyle.StandardPixmap.SP_DesktopIcon
    STYLE_SP_TRASH_ICON = QStyle.StandardPixmap.SP_TrashIcon
    STYLE_SP_COMPUTER_ICON = QStyle.StandardPixmap.SP_ComputerIcon
    STYLE_SP_DRIVEHD_ICON = QStyle.StandardPixmap.SP_DriveHDIcon
    STYLE_SP_DIALOG_OK = QStyle.StandardPixmap.SP_DialogOkButton
    STYLE_SP_DIALOG_CANCEL = QStyle.StandardPixmap.SP_DialogCancelButton
    STYLE_SP_MESSAGEBOX_INFORMATION = QStyle.StandardPixmap.SP_MessageBoxInformation
    STYLE_SP_MESSAGEBOX_WARNING = QStyle.StandardPixmap.SP_MessageBoxWarning
    STYLE_SP_MESSAGEBOX_CRITICAL = QStyle.StandardPixmap.SP_MessageBoxCritical
else:
    STYLE_SP_DIR_ICON = QStyle.SP_DirIcon
    STYLE_SP_FILE_ICON = QStyle.SP_FileIcon
    STYLE_SP_DESKTOP_ICON = QStyle.SP_DesktopIcon
    STYLE_SP_TRASH_ICON = QStyle.SP_TrashIcon
    STYLE_SP_COMPUTER_ICON = QStyle.SP_ComputerIcon
    STYLE_SP_DRIVEHD_ICON = QStyle.SP_DriveHDIcon
    STYLE_SP_DIALOG_OK = QStyle.SP_DialogOkButton
    STYLE_SP_DIALOG_CANCEL = QStyle.SP_DialogCancelButton
    STYLE_SP_MESSAGEBOX_INFORMATION = QStyle.SP_MessageBoxInformation
    STYLE_SP_MESSAGEBOX_WARNING = QStyle.SP_MessageBoxWarning
    STYLE_SP_MESSAGEBOX_CRITICAL = QStyle.SP_MessageBoxCritical


# ---------------------------------------------------------
# QTabWidget
# ---------------------------------------------------------
QTabWidget = QtWidgets.QTabWidget
if hasattr(QTabWidget, "TabPosition"):
    TAB_NORTH = QTabWidget.TabPosition.North
    TAB_SOUTH = QTabWidget.TabPosition.South
    TAB_WEST = QTabWidget.TabPosition.West
    TAB_EAST = QTabWidget.TabPosition.East

    TAB_ROUNDED = QTabWidget.TabShape.Rounded
    TAB_TRIANGULAR = QTabWidget.TabShape.Triangular
else:
    TAB_NORTH = QTabWidget.North
    TAB_SOUTH = QTabWidget.South
    TAB_WEST = QTabWidget.West
    TAB_EAST = QTabWidget.East

    TAB_ROUNDED = QTabWidget.Rounded
    TAB_TRIANGULAR = QTabWidget.Triangular


# ---------------------------------------------------------
# QDockWidget
# ---------------------------------------------------------
QDockWidget = QtWidgets.QDockWidget
if hasattr(QDockWidget, "DockWidgetFeature"):
    DOCK_CLOSABLE = QDockWidget.DockWidgetFeature.DockWidgetClosable
    DOCK_MOVABLE = QDockWidget.DockWidgetFeature.DockWidgetMovable
    DOCK_FLOATABLE = QDockWidget.DockWidgetFeature.DockWidgetFloatable
    DOCK_VERTICAL_TITLEBAR = QDockWidget.DockWidgetFeature.DockWidgetVerticalTitleBar
    DOCK_NO_FEATURES = QDockWidget.DockWidgetFeature.NoDockWidgetFeatures
else:
    DOCK_CLOSABLE = QDockWidget.DockWidgetClosable
    DOCK_MOVABLE = QDockWidget.DockWidgetMovable
    DOCK_FLOATABLE = QDockWidget.DockWidgetFloatable
    DOCK_VERTICAL_TITLEBAR = QDockWidget.DockWidgetVerticalTitleBar
    DOCK_NO_FEATURES = QDockWidget.NoDockWidgetFeatures


# ---------------------------------------------------------
# Dock widget areas
# ---------------------------------------------------------
if hasattr(Qt, "DockWidgetArea"):
    DOCKAREA_LEFT = Qt.DockWidgetArea.LeftDockWidgetArea
    DOCKAREA_RIGHT = Qt.DockWidgetArea.RightDockWidgetArea
    DOCKAREA_TOP = Qt.DockWidgetArea.TopDockWidgetArea
    DOCKAREA_BOTTOM = Qt.DockWidgetArea.BottomDockWidgetArea
    DOCKAREA_ALL = Qt.DockWidgetArea.AllDockWidgetAreas
    DOCKAREA_NONE = Qt.DockWidgetArea.NoDockWidgetArea
else:
    DOCKAREA_LEFT = Qt.LeftDockWidgetArea
    DOCKAREA_RIGHT = Qt.RightDockWidgetArea
    DOCKAREA_TOP = Qt.TopDockWidgetArea
    DOCKAREA_BOTTOM = Qt.BottomDockWidgetArea
    DOCKAREA_ALL = Qt.AllDockWidgetAreas
    DOCKAREA_NONE = Qt.NoDockWidgetArea


# ---------------------------------------------------------
# QToolButton popup mode
# ---------------------------------------------------------
QToolButton = QtWidgets.QToolButton
if hasattr(QToolButton, "ToolButtonPopupMode"):
    TOOLBUTTON_POPUP_DELAYED = QToolButton.ToolButtonPopupMode.DelayedPopup
    TOOLBUTTON_POPUP_MENU_BUTTON = QToolButton.ToolButtonPopupMode.MenuButtonPopup
    TOOLBUTTON_POPUP_INSTANT = QToolButton.ToolButtonPopupMode.InstantPopup
else:
    TOOLBUTTON_POPUP_DELAYED = QToolButton.DelayedPopup
    TOOLBUTTON_POPUP_MENU_BUTTON = QToolButton.MenuButtonPopup
    TOOLBUTTON_POPUP_INSTANT = QToolButton.InstantPopup

# ---------------------------------------------------------
# QWizard
# ---------------------------------------------------------
QWizard = QtWidgets.QWizard
if hasattr(QWizard, "WizardStyle"):
    WIZARD_CLASSIC_STYLE = QWizard.WizardStyle.ClassicStyle
    WIZARD_MODERN_STYLE = QWizard.WizardStyle.ModernStyle
    WIZARD_MAC_STYLE = QWizard.WizardStyle.MacStyle
    WIZARD_AERO_STYLE = getattr(QWizard.WizardStyle, "AeroStyle", None)
else:
    WIZARD_CLASSIC_STYLE = QWizard.ClassicStyle
    WIZARD_MODERN_STYLE = QWizard.ModernStyle
    WIZARD_MAC_STYLE = QWizard.MacStyle
    WIZARD_AERO_STYLE = getattr(QWizard, "AeroStyle", None)


# ---------------------------------------------------------
# QPainter
# ---------------------------------------------------------
QPainter = QtGui.QPainter
if hasattr(QPainter, "RenderHint"):
    PAINTER_ANTIALIASING = QPainter.RenderHint.Antialiasing
    PAINTER_TEXT_ANTIALIASING = QPainter.RenderHint.TextAntialiasing
    PAINTER_SMOOTH_PIXMAP_TRANSFORM = QPainter.RenderHint.SmoothPixmapTransform
else:
    PAINTER_ANTIALIASING = QPainter.Antialiasing
    PAINTER_TEXT_ANTIALIASING = QPainter.TextAntialiasing
    PAINTER_SMOOTH_PIXMAP_TRANSFORM = QPainter.SmoothPixmapTransform


# ---------------------------------------------------------
# Key shortcuts
# ---------------------------------------------------------
if hasattr(Qt, "Key"):
    KEY_ESCAPE = Qt.Key.Key_Escape
    KEY_ENTER = Qt.Key.Key_Enter
    KEY_RETURN = Qt.Key.Key_Return
    KEY_DELETE = Qt.Key.Key_Delete
    KEY_BACKSPACE = Qt.Key.Key_Backspace
    KEY_SPACE = Qt.Key.Key_Space
    KEY_TAB = Qt.Key.Key_Tab
else:
    KEY_ESCAPE = Qt.Key_Escape
    KEY_ENTER = Qt.Key_Enter
    KEY_RETURN = Qt.Key_Return
    KEY_DELETE = Qt.Key_Delete
    KEY_BACKSPACE = Qt.Key_Backspace
    KEY_SPACE = Qt.Key_Space
    KEY_TAB = Qt.Key_Tab


# ---------------------------------------------------------
# Mouse buttons
# ---------------------------------------------------------
if hasattr(Qt, "MouseButton"):
    LEFT_BUTTON = Qt.MouseButton.LeftButton
    RIGHT_BUTTON = Qt.MouseButton.RightButton
    MIDDLE_BUTTON = Qt.MouseButton.MiddleButton

else:
    LEFT_BUTTON = Qt.LeftButton
    RIGHT_BUTTON = Qt.RightButton
    MIDDLE_BUTTON = getattr(Qt, "MiddleButton", getattr(Qt, "MidButton", None))

MID_BUTTON = MIDDLE_BUTTON

# ---------------------------------------------------------
# Window flags
# ---------------------------------------------------------
if hasattr(Qt, "WindowType"):
    WINDOW = Qt.WindowType.Window
    DIALOG = Qt.WindowType.Dialog
    SHEET = Qt.WindowType.Sheet
    DRAWER = Qt.WindowType.Drawer
    POPUP = Qt.WindowType.Popup
    TOOL = Qt.WindowType.Tool
    TOOL_TIP = Qt.WindowType.ToolTip
    SPLASH_SCREEN = Qt.WindowType.SplashScreen
    DESKTOP = getattr(Qt.WindowType, "Desktop", None)
    SUB_WINDOW = Qt.WindowType.SubWindow
    FOREIGN_WINDOW = getattr(Qt.WindowType, "ForeignWindow", None)
    COVER_WINDOW = getattr(Qt.WindowType, "CoverWindow", None)

    WINDOW_TYPE_MASK = getattr(Qt.WindowType, "WindowType_Mask", None)

    MS_WINDOWS_FIXED_SIZE_DIALOG_HINT = getattr(
        Qt.WindowType, "MSWindowsFixedSizeDialogHint", None
    )
    MS_WINDOWS_OWN_DC = getattr(Qt.WindowType, "MSWindowsOwnDC", None)
    BYPASS_WINDOW_MANAGER_HINT = getattr(
        Qt.WindowType, "BypassWindowManagerHint", None
    )
    X11_BYPASS_WINDOW_MANAGER_HINT = getattr(
        Qt.WindowType, "X11BypassWindowManagerHint", BYPASS_WINDOW_MANAGER_HINT
    )
    FRAMELESS_WINDOW_HINT = getattr(Qt.WindowType, "FramelessWindowHint", None)
    WINDOW_TITLE_HINT = getattr(Qt.WindowType, "WindowTitleHint", None)
    WINDOW_SYSTEM_MENU_HINT = getattr(Qt.WindowType, "WindowSystemMenuHint", None)
    WINDOW_MINIMIZE_BUTTON_HINT = getattr(
        Qt.WindowType, "WindowMinimizeButtonHint", None
    )
    WINDOW_MAXIMIZE_BUTTON_HINT = getattr(
        Qt.WindowType, "WindowMaximizeButtonHint", None
    )
    WINDOW_MIN_MAX_BUTTONS_HINT = getattr(
        Qt.WindowType, "WindowMinMaxButtonsHint", None
    )
    WINDOW_CLOSE_BUTTON_HINT = getattr(
        Qt.WindowType, "WindowCloseButtonHint", None
    )
    WINDOW_CONTEXT_HELP_BUTTON_HINT = getattr(
        Qt.WindowType, "WindowContextHelpButtonHint", None
    )
    WINDOW_SHADE_BUTTON_HINT = getattr(
        Qt.WindowType, "WindowShadeButtonHint", None
    )
    WINDOW_STAYS_ON_TOP_HINT = getattr(
        Qt.WindowType, "WindowStaysOnTopHint", None
    )
    WINDOW_STAYS_ON_BOTTOM_HINT = getattr(
        Qt.WindowType, "WindowStaysOnBottomHint", None
    )
    WINDOW_TRANSPARENT_FOR_INPUT = getattr(
        Qt.WindowType, "WindowTransparentForInput", None
    )
    WINDOW_OVERRIDES_SYSTEM_GESTURE = getattr(
        Qt.WindowType, "WindowOverridesSystemGestures", None
    )
    WINDOW_DOES_NOT_ACCEPT_FOCUS = getattr(
        Qt.WindowType, "WindowDoesNotAcceptFocus", None
    )
    MAXIMIZE_USING_FULLSCREEN_GEOMETRY_HINT = getattr(
        Qt.WindowType, "MaximizeUsingFullscreenGeometryHint", None
    )

    CUSTOMIZE_WINDOW_HINT = getattr(Qt.WindowType, "CustomizeWindowHint", None)
    WINDOW_FULLSCREEN_BUTTON_HINT = getattr(
        Qt.WindowType, "WindowFullscreenButtonHint", None
    )
    NO_DROP_SHADOW_WINDOW_HINT = getattr(
        Qt.WindowType, "NoDropShadowWindowHint", None
    )

else:
    WINDOW = Qt.Window
    DIALOG = Qt.Dialog
    SHEET = getattr(Qt, "Sheet", None)
    DRAWER = getattr(Qt, "Drawer", None)
    POPUP = Qt.Popup
    TOOL = Qt.Tool
    TOOL_TIP = Qt.ToolTip
    SPLASH_SCREEN = Qt.SplashScreen
    DESKTOP = getattr(Qt, "Desktop", None)
    SUB_WINDOW = Qt.SubWindow
    FOREIGN_WINDOW = getattr(Qt, "ForeignWindow", None)
    COVER_WINDOW = getattr(Qt, "CoverWindow", None)

    WINDOW_TYPE_MASK = getattr(Qt, "WindowType_Mask", None)

    MS_WINDOWS_FIXED_SIZE_DIALOG_HINT = getattr(
        Qt, "MSWindowsFixedSizeDialogHint", None
    )
    MS_WINDOWS_OWN_DC = getattr(Qt, "MSWindowsOwnDC", None)
    BYPASS_WINDOW_MANAGER_HINT = getattr(
        Qt, "BypassWindowManagerHint", None
    )
    X11_BYPASS_WINDOW_MANAGER_HINT = getattr(
        Qt, "X11BypassWindowManagerHint", BYPASS_WINDOW_MANAGER_HINT
    )
    FRAMELESS_WINDOW_HINT = getattr(Qt, "FramelessWindowHint", None)
    WINDOW_TITLE_HINT = getattr(Qt, "WindowTitleHint", None)
    WINDOW_SYSTEM_MENU_HINT = getattr(Qt, "WindowSystemMenuHint", None)
    WINDOW_MINIMIZE_BUTTON_HINT = getattr(
        Qt, "WindowMinimizeButtonHint", None
    )
    WINDOW_MAXIMIZE_BUTTON_HINT = getattr(
        Qt, "WindowMaximizeButtonHint", None
    )
    WINDOW_MIN_MAX_BUTTONS_HINT = getattr(
        Qt, "WindowMinMaxButtonsHint", None
    )
    WINDOW_CLOSE_BUTTON_HINT = getattr(
        Qt, "WindowCloseButtonHint", None
    )
    WINDOW_CONTEXT_HELP_BUTTON_HINT = getattr(
        Qt, "WindowContextHelpButtonHint", None
    )
    WINDOW_SHADE_BUTTON_HINT = getattr(
        Qt, "WindowShadeButtonHint", None
    )
    WINDOW_STAYS_ON_TOP_HINT = getattr(
        Qt, "WindowStaysOnTopHint", None
    )
    WINDOW_STAYS_ON_BOTTOM_HINT = getattr(
        Qt, "WindowStaysOnBottomHint", None
    )
    WINDOW_TRANSPARENT_FOR_INPUT = getattr(
        Qt, "WindowTransparentForInput", None
    )
    WINDOW_OVERRIDES_SYSTEM_GESTURE = getattr(
        Qt, "WindowOverridesSystemGestures", None
    )
    WINDOW_DOES_NOT_ACCEPT_FOCUS = getattr(
        Qt, "WindowDoesNotAcceptFocus", None
    )
    MAXIMIZE_USING_FULLSCREEN_GEOMETRY_HINT = getattr(
        Qt, "MaximizeUsingFullscreenGeometryHint", None
    )

    CUSTOMIZE_WINDOW_HINT = getattr(Qt, "CustomizeWindowHint", None)
    WINDOW_FULLSCREEN_BUTTON_HINT = getattr(
        Qt, "WindowFullscreenButtonHint", None
    )
    NO_DROP_SHADOW_WINDOW_HINT = getattr(
        Qt, "NoDropShadowWindowHint", None
    )


# ---------------------------------------------------------
# Regular expressions
# ---------------------------------------------------------
try:
    from qgis.PyQt.QtCore import QRegularExpression
except Exception:
    QRegularExpression = None

try:
    from qgis.PyQt.QtGui import QRegularExpressionValidator
    REGEX_VALIDATOR_CLASS = QRegularExpressionValidator
    IS_MODERN_REGEX = True
except Exception:
    from qgis.PyQt.QtGui import QRegExpValidator
    from qgis.PyQt.QtCore import QRegExp

    REGEX_VALIDATOR_CLASS = QRegExpValidator
    IS_MODERN_REGEX = False

    if QRegularExpression is None:
        QRegularExpression = QRegExp


def make_regex(pattern: str, case_sensitivity=None, legacy_pattern_syntax=None):
    """
    Fabrique l'objet regex compatible Qt5 / Qt6.

    Qt6 :
        retourne QRegularExpression
    Qt5 :
        retourne QRegExp

    Les paramètres supplémentaires sont acceptés pour compatibilité
    avec les anciens appels make_regex(text, CASE_INSENSITIVE, QRegExp.RegExp).
    """
    pattern = "" if pattern is None else str(pattern)

    if IS_MODERN_REGEX:
        rx = QRegularExpression(pattern)
        try:
            if case_sensitivity == CASE_INSENSITIVE:
                opts = rx.patternOptions() | QRegularExpression.PatternOption.CaseInsensitiveOption
                rx.setPatternOptions(opts)
        except Exception:
            pass
        return rx

    try:
        from qgis.PyQt.QtCore import QRegExp
        syntax = legacy_pattern_syntax if legacy_pattern_syntax is not None else QRegExp.RegExp
        cs = case_sensitivity if case_sensitivity is not None else CASE_SENSITIVE
        return QRegExp(pattern, cs, syntax)
    except Exception:
        return QRegularExpression(pattern)

def regex_pattern(rx):
    """Retourne le pattern texte d'un regex Qt5/Qt6."""
    if rx is None:
        return ""
    try:
        return rx.pattern()
    except Exception:
        return str(rx)

def regex_is_empty(rx):
    """True si le regex est vide ou non exploitable."""
    return regex_pattern(rx) == ""


def regex_has_match(rx, text):
    """Teste si rx matche text, en Qt5/Qt6."""
    text = "" if text is None else str(text)

    if rx is None:
        return True

    if IS_MODERN_REGEX:
        try:
            return rx.match(text).hasMatch()
        except Exception:
            return False

    try:
        return rx.indexIn(text) >= 0
    except Exception:
        return False


def regex_index_in(rx, text):
    """Equivalent Qt5-like de indexIn pour Qt5/Qt6."""
    text = "" if text is None else str(text)

    if rx is None:
        return -1

    if IS_MODERN_REGEX:
        try:
            m = rx.match(text)
            if m.hasMatch():
                return m.capturedStart(0)
            return -1
        except Exception:
            return -1

    try:
        return rx.indexIn(text)
    except Exception:
        return -1


def regex_exact_match(rx, text):
    """Compat Qt5/Qt6 pour exactMatch."""
    text = "" if text is None else str(text)

    if rx is None:
        return False

    if IS_MODERN_REGEX:
        try:
            pattern = regex_pattern(rx)
            anchored = make_regex(r"^(?:%s)$" % pattern)
            return anchored.match(text).hasMatch()
        except Exception:
            return False

    try:
        return rx.exactMatch(text)
    except Exception:
        return False

def filter_proxy_regex(proxy):
    """Retourne le regex du proxy en Qt5/Qt6."""
    if proxy is None:
        return None
    if hasattr(proxy, "filterRegularExpression"):
        try:
            return proxy.filterRegularExpression()
        except Exception:
            pass
    if hasattr(proxy, "filterRegExp"):
        try:
            return proxy.filterRegExp()
        except Exception:
            pass
    return None


def filter_proxy_regex_has_match(proxy, text):
    return regex_has_match(filter_proxy_regex(proxy), text)


def filter_proxy_regex_index_in(proxy, text):
    return regex_index_in(filter_proxy_regex(proxy), text)



# ---------------------------------------------------------
# Dialog codes
# ---------------------------------------------------------
QDialog = QtWidgets.QDialog
if hasattr(QDialog, "DialogCode"):
    DIALOG_ACCEPTED = QDialog.DialogCode.Accepted
    DIALOG_REJECTED = QDialog.DialogCode.Rejected
else:
    DIALOG_ACCEPTED = QDialog.Accepted
    DIALOG_REJECTED = QDialog.Rejected

# ---------------------------------------------------------
# Window attribute
# ---------------------------------------------------------
try:
    WA_DELETE_ON_CLOSE = Qt.WidgetAttribute.WA_DeleteOnClose
except AttributeError:
    WA_DELETE_ON_CLOSE = Qt.WA_DeleteOnClose


# ---------------------------------------------------------
# Application attributes (High DPI)
# ---------------------------------------------------------
try:
    QT_AA_ENABLE_HIGH_DPI_SCALING = Qt.ApplicationAttribute.AA_EnableHighDpiScaling
except AttributeError:
    QT_AA_ENABLE_HIGH_DPI_SCALING = getattr(Qt, "AA_EnableHighDpiScaling", None)

try:
    QT_AA_USE_HIGH_DPI_PIXMAPS = Qt.ApplicationAttribute.AA_UseHighDpiPixmaps
except AttributeError:
    QT_AA_USE_HIGH_DPI_PIXMAPS = getattr(Qt, "AA_UseHighDpiPixmaps", None)


# ---------------------------------------------------------
# Text format
# ---------------------------------------------------------
if hasattr(Qt, "TextFormat"):
    TEXTFORMAT_PLAINTEXT = Qt.TextFormat.PlainText
    TEXTFORMAT_RICHTEXT = Qt.TextFormat.RichText
    TEXTFORMAT_AUTOTEXT = Qt.TextFormat.AutoText
    TEXTFORMAT_MARKDOWNTEXT = getattr(Qt.TextFormat, "MarkdownText", None)
    TEXTFORMAT_LOGTEXT = getattr(Qt.TextFormat, "LogText", None)
else:
    TEXTFORMAT_PLAINTEXT = Qt.PlainText
    TEXTFORMAT_RICHTEXT = Qt.RichText
    TEXTFORMAT_AUTOTEXT = Qt.AutoText
    TEXTFORMAT_MARKDOWNTEXT = getattr(Qt, "MarkdownText", None)
    TEXTFORMAT_LOGTEXT = getattr(Qt, "LogText", None)


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------
def set_tab_stop_compat(widget, value):
    if hasattr(widget, "setTabStopDistance"):
        widget.setTabStopDistance(value)
    else:
        widget.setTabStopWidth(value)

def primary_screen_geometry(available=True):
    screen = QtGui.QGuiApplication.primaryScreen()
    if screen is None:
        return QtCore.QRect(0, 0, 1920, 1080)
    return screen.availableGeometry() if available else screen.geometry()

def qt_exec(dialog) -> int:
    if hasattr(dialog, "exec"):
        return dialog.exec()
    return dialog.exec_()


def single_shot(msec: int, callback) -> None:
    QtCore.QTimer.singleShot(msec, callback)


def set_alignment(widget, alignment) -> None:
    widget.setAlignment(alignment)


def header_resize_to_contents(header) -> None:
    if hasattr(header, "setSectionResizeMode"):
        header.setSectionResizeMode(HEADER_RESIZE_TO_CONTENTS)
    else:
        header.setResizeMode(HEADER_RESIZE_TO_CONTENTS)


def header_stretch(header) -> None:
    if hasattr(header, "setSectionResizeMode"):
        header.setSectionResizeMode(HEADER_STRETCH)
    else:
        header.setResizeMode(HEADER_STRETCH)


def header_interactive(header) -> None:
    if hasattr(header, "setSectionResizeMode"):
        header.setSectionResizeMode(HEADER_INTERACTIVE)
    else:
        header.setResizeMode(HEADER_INTERACTIVE)


def standard_icon(widget, standard_pixmap):
    style = widget.style() if widget is not None else QtWidgets.QApplication.style()
    return style.standardIcon(standard_pixmap)


def combine_flags(*flags):
    valid = [f for f in flags if f is not None]
    if not valid:
        return 0
    result = valid[0]
    for flag in valid[1:]:
        result = result | flag
    return result

# ---------------------------------------------------------
# Network / QNetworkReply / QNetworkRequest / QNetworkAccessManager
# ---------------------------------------------------------
from qgis.PyQt.QtNetwork import QNetworkAccessManager

QNETWORK_REPLY = QNetworkReply
QNETWORK_REQUEST = QNetworkRequest
QNETWORK_ACCESS_MANAGER = QNetworkAccessManager

# --- QNetworkReply.NetworkError
try:
    # Qt6 / bindings récents
    _QNR_ERR = QNetworkReply.NetworkError

    NETWORK_REPLY_NO_ERROR = _QNR_ERR.NoError

    NETWORK_REPLY_CONNECTION_REFUSED = getattr(_QNR_ERR, "ConnectionRefusedError", None)
    NETWORK_REPLY_REMOTE_HOST_CLOSED = getattr(_QNR_ERR, "RemoteHostClosedError", None)
    NETWORK_REPLY_HOST_NOT_FOUND = getattr(_QNR_ERR, "HostNotFoundError", None)
    NETWORK_REPLY_TIMEOUT = getattr(_QNR_ERR, "TimeoutError", None)
    NETWORK_REPLY_OPERATION_CANCELED = getattr(_QNR_ERR, "OperationCanceledError", None)
    NETWORK_REPLY_SSL_HANDSHAKE_FAILED = getattr(_QNR_ERR, "SslHandshakeFailedError", None)
    NETWORK_REPLY_TEMPORARY_NETWORK_FAILURE = getattr(_QNR_ERR, "TemporaryNetworkFailureError", None)
    NETWORK_REPLY_NETWORK_SESSION_FAILED = getattr(_QNR_ERR, "NetworkSessionFailedError", None)
    NETWORK_REPLY_BACKGROUND_REQUEST_NOT_ALLOWED = getattr(_QNR_ERR, "BackgroundRequestNotAllowedError", None)
    NETWORK_REPLY_TOO_MANY_REDIRECTS = getattr(_QNR_ERR, "TooManyRedirectsError", None)
    NETWORK_REPLY_INSECURE_REDIRECT = getattr(_QNR_ERR, "InsecureRedirectError", None)

    NETWORK_REPLY_PROXY_CONNECTION_REFUSED = getattr(_QNR_ERR, "ProxyConnectionRefusedError", None)
    NETWORK_REPLY_PROXY_CONNECTION_CLOSED = getattr(_QNR_ERR, "ProxyConnectionClosedError", None)
    NETWORK_REPLY_PROXY_NOT_FOUND = getattr(_QNR_ERR, "ProxyNotFoundError", None)
    NETWORK_REPLY_PROXY_TIMEOUT = getattr(_QNR_ERR, "ProxyTimeoutError", None)
    NETWORK_REPLY_PROXY_AUTHENTICATION_REQUIRED = getattr(_QNR_ERR, "ProxyAuthenticationRequiredError", None)

    NETWORK_REPLY_CONTENT_ACCESS_DENIED = getattr(_QNR_ERR, "ContentAccessDenied", None)
    NETWORK_REPLY_CONTENT_OPERATION_NOT_PERMITTED = getattr(_QNR_ERR, "ContentOperationNotPermittedError", None)
    NETWORK_REPLY_CONTENT_NOT_FOUND = getattr(_QNR_ERR, "ContentNotFoundError", None)
    NETWORK_REPLY_AUTHENTICATION_REQUIRED = getattr(_QNR_ERR, "AuthenticationRequiredError", None)
    NETWORK_REPLY_CONTENT_RE_SEND_ERROR = getattr(_QNR_ERR, "ContentReSendError", None)

    NETWORK_REPLY_PROTOCOL_UNKNOWN = getattr(_QNR_ERR, "ProtocolUnknownError", None)
    NETWORK_REPLY_PROTOCOL_INVALID_OPERATION = getattr(_QNR_ERR, "ProtocolInvalidOperationError", None)
    NETWORK_REPLY_UNKNOWN_NETWORK_ERROR = getattr(_QNR_ERR, "UnknownNetworkError", None)
    NETWORK_REPLY_UNKNOWN_PROXY_ERROR = getattr(_QNR_ERR, "UnknownProxyError", None)
    NETWORK_REPLY_UNKNOWN_CONTENT_ERROR = getattr(_QNR_ERR, "UnknownContentError", None)
    NETWORK_REPLY_PROTOCOL_FAILURE = getattr(_QNR_ERR, "ProtocolFailure", None)

    NETWORK_REPLY_INTERNAL_SERVER_ERROR = getattr(_QNR_ERR, "InternalServerError", None)
    NETWORK_REPLY_OPERATION_NOT_IMPLEMENTED = getattr(_QNR_ERR, "OperationNotImplementedError", None)
    NETWORK_REPLY_SERVICE_UNAVAILABLE = getattr(_QNR_ERR, "ServiceUnavailableError", None)
    NETWORK_REPLY_UNKNOWN_SERVER_ERROR = getattr(_QNR_ERR, "UnknownServerError", None)

except AttributeError:
    # Qt5 / anciens bindings
    NETWORK_REPLY_NO_ERROR = getattr(QNetworkReply, "NoError", None)

    NETWORK_REPLY_CONNECTION_REFUSED = getattr(QNetworkReply, "ConnectionRefusedError", None)
    NETWORK_REPLY_REMOTE_HOST_CLOSED = getattr(QNetworkReply, "RemoteHostClosedError", None)
    NETWORK_REPLY_HOST_NOT_FOUND = getattr(QNetworkReply, "HostNotFoundError", None)
    NETWORK_REPLY_TIMEOUT = getattr(QNetworkReply, "TimeoutError", None)
    NETWORK_REPLY_OPERATION_CANCELED = getattr(QNetworkReply, "OperationCanceledError", None)
    NETWORK_REPLY_SSL_HANDSHAKE_FAILED = getattr(QNetworkReply, "SslHandshakeFailedError", None)
    NETWORK_REPLY_TEMPORARY_NETWORK_FAILURE = getattr(QNetworkReply, "TemporaryNetworkFailureError", None)
    NETWORK_REPLY_NETWORK_SESSION_FAILED = getattr(QNetworkReply, "NetworkSessionFailedError", None)
    NETWORK_REPLY_BACKGROUND_REQUEST_NOT_ALLOWED = getattr(QNetworkReply, "BackgroundRequestNotAllowedError", None)
    NETWORK_REPLY_TOO_MANY_REDIRECTS = getattr(QNetworkReply, "TooManyRedirectsError", None)
    NETWORK_REPLY_INSECURE_REDIRECT = getattr(QNetworkReply, "InsecureRedirectError", None)

    NETWORK_REPLY_PROXY_CONNECTION_REFUSED = getattr(QNetworkReply, "ProxyConnectionRefusedError", None)
    NETWORK_REPLY_PROXY_CONNECTION_CLOSED = getattr(QNetworkReply, "ProxyConnectionClosedError", None)
    NETWORK_REPLY_PROXY_NOT_FOUND = getattr(QNetworkReply, "ProxyNotFoundError", None)
    NETWORK_REPLY_PROXY_TIMEOUT = getattr(QNetworkReply, "ProxyTimeoutError", None)
    NETWORK_REPLY_PROXY_AUTHENTICATION_REQUIRED = getattr(QNetworkReply, "ProxyAuthenticationRequiredError", None)

    NETWORK_REPLY_CONTENT_ACCESS_DENIED = getattr(QNetworkReply, "ContentAccessDenied", None)
    NETWORK_REPLY_CONTENT_OPERATION_NOT_PERMITTED = getattr(QNetworkReply, "ContentOperationNotPermittedError", None)
    NETWORK_REPLY_CONTENT_NOT_FOUND = getattr(QNetworkReply, "ContentNotFoundError", None)
    NETWORK_REPLY_AUTHENTICATION_REQUIRED = getattr(QNetworkReply, "AuthenticationRequiredError", None)
    NETWORK_REPLY_CONTENT_RE_SEND_ERROR = getattr(QNetworkReply, "ContentReSendError", None)

    NETWORK_REPLY_PROTOCOL_UNKNOWN = getattr(QNetworkReply, "ProtocolUnknownError", None)
    NETWORK_REPLY_PROTOCOL_INVALID_OPERATION = getattr(QNetworkReply, "ProtocolInvalidOperationError", None)
    NETWORK_REPLY_UNKNOWN_NETWORK_ERROR = getattr(QNetworkReply, "UnknownNetworkError", None)
    NETWORK_REPLY_UNKNOWN_PROXY_ERROR = getattr(QNetworkReply, "UnknownProxyError", None)
    NETWORK_REPLY_UNKNOWN_CONTENT_ERROR = getattr(QNetworkReply, "UnknownContentError", None)
    NETWORK_REPLY_PROTOCOL_FAILURE = getattr(QNetworkReply, "ProtocolFailure", None)

    NETWORK_REPLY_INTERNAL_SERVER_ERROR = getattr(QNetworkReply, "InternalServerError", None)
    NETWORK_REPLY_OPERATION_NOT_IMPLEMENTED = getattr(QNetworkReply, "OperationNotImplementedError", None)
    NETWORK_REPLY_SERVICE_UNAVAILABLE = getattr(QNetworkReply, "ServiceUnavailableError", None)
    NETWORK_REPLY_UNKNOWN_SERVER_ERROR = getattr(QNetworkReply, "UnknownServerError", None)

# --- QNetworkRequest.Attribute
try:
    _QNR_ATTR = QNetworkRequest.Attribute

    NETWORKREQUEST_HTTP_STATUS_CODE = getattr(_QNR_ATTR, "HttpStatusCodeAttribute", None)
    NETWORKREQUEST_HTTP_REASON_PHRASE = getattr(_QNR_ATTR, "HttpReasonPhraseAttribute", None)
    NETWORKREQUEST_REDIRECTION_TARGET = getattr(_QNR_ATTR, "RedirectionTargetAttribute", None)
    NETWORKREQUEST_CONNECTION_ENCRYPTED = getattr(_QNR_ATTR, "ConnectionEncryptedAttribute", None)

    NETWORKREQUEST_CACHE_LOAD_CONTROL = getattr(_QNR_ATTR, "CacheLoadControlAttribute", None)
    NETWORKREQUEST_CACHE_SAVE_CONTROL = getattr(_QNR_ATTR, "CacheSaveControlAttribute", None)
    NETWORKREQUEST_SOURCE_IS_FROM_CACHE = getattr(_QNR_ATTR, "SourceIsFromCacheAttribute", None)
    NETWORKREQUEST_DO_NOT_BUFFER_UPLOAD_DATA = getattr(_QNR_ATTR, "DoNotBufferUploadDataAttribute", None)

    NETWORKREQUEST_HTTP_PIPLINING_ALLOWED = getattr(_QNR_ATTR, "HttpPipeliningAllowedAttribute", None)
    NETWORKREQUEST_HTTP_PIPLINING_WAS_USED = getattr(_QNR_ATTR, "HttpPipeliningWasUsedAttribute", None)
    NETWORKREQUEST_CUSTOM_VERB = getattr(_QNR_ATTR, "CustomVerbAttribute", None)

    NETWORKREQUEST_COOKIE_LOAD_CONTROL = getattr(_QNR_ATTR, "CookieLoadControlAttribute", None)
    NETWORKREQUEST_COOKIE_SAVE_CONTROL = getattr(_QNR_ATTR, "CookieSaveControlAttribute", None)
    NETWORKREQUEST_AUTHENTICATION_REUSE = getattr(_QNR_ATTR, "AuthenticationReuseAttribute", None)

    NETWORKREQUEST_BACKGROUND_REQUEST = getattr(_QNR_ATTR, "BackgroundRequestAttribute", None)
    NETWORKREQUEST_EMIT_ALL_UPLOAD_PROGRESS_SIGNALS = getattr(
        _QNR_ATTR, "EmitAllUploadProgressSignalsAttribute", None
    )
    NETWORKREQUEST_ORIGINAL_CONTENT_LENGTH = getattr(
        _QNR_ATTR, "OriginalContentLengthAttribute", None
    )
    NETWORKREQUEST_REDIRECT_POLICY = getattr(_QNR_ATTR, "RedirectPolicyAttribute", None)
    NETWORKREQUEST_HTTP2_WAS_USED = getattr(_QNR_ATTR, "Http2WasUsedAttribute", None)

except AttributeError:
    NETWORKREQUEST_HTTP_STATUS_CODE = getattr(QNetworkRequest, "HttpStatusCodeAttribute", None)
    NETWORKREQUEST_HTTP_REASON_PHRASE = getattr(QNetworkRequest, "HttpReasonPhraseAttribute", None)
    NETWORKREQUEST_REDIRECTION_TARGET = getattr(QNetworkRequest, "RedirectionTargetAttribute", None)
    NETWORKREQUEST_CONNECTION_ENCRYPTED = getattr(QNetworkRequest, "ConnectionEncryptedAttribute", None)

    NETWORKREQUEST_CACHE_LOAD_CONTROL = getattr(QNetworkRequest, "CacheLoadControlAttribute", None)
    NETWORKREQUEST_CACHE_SAVE_CONTROL = getattr(QNetworkRequest, "CacheSaveControlAttribute", None)
    NETWORKREQUEST_SOURCE_IS_FROM_CACHE = getattr(QNetworkRequest, "SourceIsFromCacheAttribute", None)
    NETWORKREQUEST_DO_NOT_BUFFER_UPLOAD_DATA = getattr(QNetworkRequest, "DoNotBufferUploadDataAttribute", None)

    NETWORKREQUEST_HTTP_PIPLINING_ALLOWED = getattr(QNetworkRequest, "HttpPipeliningAllowedAttribute", None)
    NETWORKREQUEST_HTTP_PIPLINING_WAS_USED = getattr(QNetworkRequest, "HttpPipeliningWasUsedAttribute", None)
    NETWORKREQUEST_CUSTOM_VERB = getattr(QNetworkRequest, "CustomVerbAttribute", None)

    NETWORKREQUEST_COOKIE_LOAD_CONTROL = getattr(QNetworkRequest, "CookieLoadControlAttribute", None)
    NETWORKREQUEST_COOKIE_SAVE_CONTROL = getattr(QNetworkRequest, "CookieSaveControlAttribute", None)
    NETWORKREQUEST_AUTHENTICATION_REUSE = getattr(QNetworkRequest, "AuthenticationReuseAttribute", None)

    NETWORKREQUEST_BACKGROUND_REQUEST = getattr(QNetworkRequest, "BackgroundRequestAttribute", None)
    NETWORKREQUEST_EMIT_ALL_UPLOAD_PROGRESS_SIGNALS = getattr(
        QNetworkRequest, "EmitAllUploadProgressSignalsAttribute", None
    )
    NETWORKREQUEST_ORIGINAL_CONTENT_LENGTH = getattr(
        QNetworkRequest, "OriginalContentLengthAttribute", None
    )
    NETWORKREQUEST_REDIRECT_POLICY = getattr(QNetworkRequest, "RedirectPolicyAttribute", None)
    NETWORKREQUEST_HTTP2_WAS_USED = getattr(QNetworkRequest, "Http2WasUsedAttribute", None)

# --- QNetworkRequest.CacheLoadControl
try:
    _QNR_CACHE = QNetworkRequest.CacheLoadControl
    NETWORKREQUEST_ALWAYS_NETWORK = getattr(_QNR_CACHE, "AlwaysNetwork", None)
    NETWORKREQUEST_PREFER_NETWORK = getattr(_QNR_CACHE, "PreferNetwork", None)
    NETWORKREQUEST_PREFER_CACHE = getattr(_QNR_CACHE, "PreferCache", None)
    NETWORKREQUEST_ALWAYS_CACHE = getattr(_QNR_CACHE, "AlwaysCache", None)
except AttributeError:
    NETWORKREQUEST_ALWAYS_NETWORK = getattr(QNetworkRequest, "AlwaysNetwork", None)
    NETWORKREQUEST_PREFER_NETWORK = getattr(QNetworkRequest, "PreferNetwork", None)
    NETWORKREQUEST_PREFER_CACHE = getattr(QNetworkRequest, "PreferCache", None)
    NETWORKREQUEST_ALWAYS_CACHE = getattr(QNetworkRequest, "AlwaysCache", None)

# --- QNetworkRequest.RedirectPolicy
try:
    _QNR_REDIRECT = QNetworkRequest.RedirectPolicy
    NETWORKREQUEST_MANUAL_REDIRECT_POLICY = getattr(_QNR_REDIRECT, "ManualRedirectPolicy", None)
    NETWORKREQUEST_NO_LESS_SAFE_REDIRECT_POLICY = getattr(
        _QNR_REDIRECT, "NoLessSafeRedirectPolicy", None
    )
    NETWORKREQUEST_SAME_ORIGIN_REDIRECT_POLICY = getattr(
        _QNR_REDIRECT, "SameOriginRedirectPolicy", None
    )
    NETWORKREQUEST_USER_VERIFIED_REDIRECT_POLICY = getattr(
        _QNR_REDIRECT, "UserVerifiedRedirectPolicy", None
    )
except AttributeError:
    NETWORKREQUEST_MANUAL_REDIRECT_POLICY = getattr(QNetworkRequest, "ManualRedirectPolicy", None)
    NETWORKREQUEST_NO_LESS_SAFE_REDIRECT_POLICY = getattr(
        QNetworkRequest, "NoLessSafeRedirectPolicy", None
    )
    NETWORKREQUEST_SAME_ORIGIN_REDIRECT_POLICY = getattr(
        QNetworkRequest, "SameOriginRedirectPolicy", None
    )
    NETWORKREQUEST_USER_VERIFIED_REDIRECT_POLICY = getattr(
        QNetworkRequest, "UserVerifiedRedirectPolicy", None
    )

# --- QNetworkRequest.Priority
try:
    _QNR_PRIORITY = QNetworkRequest.Priority
    NETWORKREQUEST_HIGH_PRIORITY = getattr(_QNR_PRIORITY, "HighPriority", None)
    NETWORKREQUEST_NORMAL_PRIORITY = getattr(_QNR_PRIORITY, "NormalPriority", None)
    NETWORKREQUEST_LOW_PRIORITY = getattr(_QNR_PRIORITY, "LowPriority", None)
except AttributeError:
    NETWORKREQUEST_HIGH_PRIORITY = getattr(QNetworkRequest, "HighPriority", None)
    NETWORKREQUEST_NORMAL_PRIORITY = getattr(QNetworkRequest, "NormalPriority", None)
    NETWORKREQUEST_LOW_PRIORITY = getattr(QNetworkRequest, "LowPriority", None)

# --- QNetworkAccessManager.Operation
try:
    _QNAM_OP = QNetworkAccessManager.Operation
    NETWORKOP_HEAD = getattr(_QNAM_OP, "HeadOperation", None)
    NETWORKOP_GET = getattr(_QNAM_OP, "GetOperation", None)
    NETWORKOP_PUT = getattr(_QNAM_OP, "PutOperation", None)
    NETWORKOP_POST = getattr(_QNAM_OP, "PostOperation", None)
    NETWORKOP_DELETE = getattr(_QNAM_OP, "DeleteOperation", None)
    NETWORKOP_CUSTOM = getattr(_QNAM_OP, "CustomOperation", None)
except AttributeError:
    NETWORKOP_HEAD = getattr(QNetworkAccessManager, "HeadOperation", None)
    NETWORKOP_GET = getattr(QNetworkAccessManager, "GetOperation", None)
    NETWORKOP_PUT = getattr(QNetworkAccessManager, "PutOperation", None)
    NETWORKOP_POST = getattr(QNetworkAccessManager, "PostOperation", None)
    NETWORKOP_DELETE = getattr(QNetworkAccessManager, "DeleteOperation", None)
    NETWORKOP_CUSTOM = getattr(QNetworkAccessManager, "CustomOperation", None)

# --- helpers lecture reply
def network_reply_error(reply):
    """
    Retourne le code erreur de reply.error() ou None si indisponible.
    """
    try:
        return reply.error()
    except Exception:
        return None


def network_reply_ok(reply) -> bool:
    """
    True si la réponse réseau est sans erreur.
    """
    return network_reply_error(reply) == NETWORK_REPLY_NO_ERROR


def network_reply_error_string(reply) -> str:
    """
    Retourne errorString() de manière sûre.
    """
    try:
        return reply.errorString() or ""
    except Exception:
        return ""


def network_reply_status_code(reply):
    """
    Retourne le code HTTP si disponible.
    """
    try:
        if NETWORKREQUEST_HTTP_STATUS_CODE is None:
            return None
        return reply.attribute(NETWORKREQUEST_HTTP_STATUS_CODE)
    except Exception:
        return None


def network_reply_reason(reply):
    """
    Retourne la raison HTTP si disponible.
    """
    try:
        if NETWORKREQUEST_HTTP_REASON_PHRASE is None:
            return None
        return reply.attribute(NETWORKREQUEST_HTTP_REASON_PHRASE)
    except Exception:
        return None


def network_reply_redirect_target(reply):
    """
    Retourne la cible de redirection si présente.
    """
    try:
        if NETWORKREQUEST_REDIRECTION_TARGET is None:
            return None
        return reply.attribute(NETWORKREQUEST_REDIRECTION_TARGET)
    except Exception:
        return None


def network_reply_debug_dict(reply) -> dict:
    """
    Petit résumé utile pour logs/debug.
    """
    return {
        "error_code": network_reply_error(reply),
        "error_string": network_reply_error_string(reply),
        "http_status": network_reply_status_code(reply),
        "http_reason": network_reply_reason(reply),
        "redirect_target": network_reply_redirect_target(reply),
    }

# --- helpers request
def network_request_set_cache_control(request, cache_control):
    """
    Applique request.setAttribute(CacheLoadControlAttribute, cache_control)
    si les enums nécessaires sont disponibles.
    """
    try:
        if (
            request is None
            or NETWORKREQUEST_CACHE_LOAD_CONTROL is None
            or cache_control is None
        ):
            return False
        request.setAttribute(NETWORKREQUEST_CACHE_LOAD_CONTROL, cache_control)
        return True
    except Exception:
        return False


def network_request_set_always_network(request):
    return network_request_set_cache_control(request, NETWORKREQUEST_ALWAYS_NETWORK)


def network_request_set_prefer_network(request):
    return network_request_set_cache_control(request, NETWORKREQUEST_PREFER_NETWORK)


def network_request_set_prefer_cache(request):
    return network_request_set_cache_control(request, NETWORKREQUEST_PREFER_CACHE)


def network_request_set_always_cache(request):
    return network_request_set_cache_control(request, NETWORKREQUEST_ALWAYS_CACHE)


def network_request_set_redirect_policy(request, policy):
    """
    Applique request.setAttribute(RedirectPolicyAttribute, policy)
    si disponible.
    """
    try:
        if (
            request is None
            or NETWORKREQUEST_REDIRECT_POLICY is None
            or policy is None
        ):
            return False
        request.setAttribute(NETWORKREQUEST_REDIRECT_POLICY, policy)
        return True
    except Exception:
        return False


def network_reply_is_redirect(reply) -> bool:
    target = network_reply_redirect_target(reply)
    if target is None:
        return False
    try:
        if isinstance(target, QtCore.QUrl):
            return target.isValid() and not target.isEmpty()
    except Exception:
        pass
    return bool(target)


def network_operation_name(operation) -> str:
    mapping = {
        NETWORKOP_HEAD: "HEAD",
        NETWORKOP_GET: "GET",
        NETWORKOP_PUT: "PUT",
        NETWORKOP_POST: "POST",
        NETWORKOP_DELETE: "DELETE",
        NETWORKOP_CUSTOM: "CUSTOM",
    }
    return mapping.get(operation, str(operation))

# ---------------------------------------------------------
# subprocess / Windows helpers
# ---------------------------------------------------------
def subprocess_no_window_kwargs() -> dict:
    """
    Retourne des kwargs subprocess compatibles Windows/Qt5/Qt6
    pour éviter la console noire.
    """
    import subprocess
    import platform

    kwargs = {}

    if platform.system().lower() == "windows":
        if hasattr(subprocess, "CREATE_NO_WINDOW"):
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

        if hasattr(subprocess, "STARTUPINFO") and hasattr(subprocess, "STARTF_USESHOWWINDOW"):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            kwargs["startupinfo"] = startupinfo

    return kwargs


__all__ = [
    "Qt", "QtCore", "QtGui", "QtWidgets",
    "IS_QT5", "IS_QT6", "IS_WINDOWS",

    "ALIGN_LEFT", "ALIGN_RIGHT", "ALIGN_HCENTER", "ALIGN_JUSTIFY",
    "ALIGN_TOP", "ALIGN_BOTTOM", "ALIGN_VCENTER", "ALIGN_CENTER",
    "ALIGN_LEADING", "ALIGN_TRAILING", "ALIGN_ABSOLUTE",
    "ALIGN_HORIZONTAL_MASK", "ALIGN_VERTICAL_MASK", "ALIGN_BASELINE",

    "primary_screen_geometry", "set_tab_stop_compat",

    "QRegularExpression",
    "REGEX_VALIDATOR_CLASS",
    "make_regex",
    "IS_MODERN_REGEX",
    "regex_pattern",
    "regex_is_empty",
    "regex_has_match",
    "regex_index_in",
    "regex_exact_match",
    "filter_proxy_regex",
    "filter_proxy_regex_has_match",
    "filter_proxy_regex_index_in",

    "SELECTION_CLEAR",
    "SELECTION_SELECT",
    "SELECTION_DESELECT",
    "SELECTION_TOGGLE",
    "SELECTION_CURRENT",
    "SELECTION_ROWS",
    "SELECTION_COLUMNS",
    "SELECTION_CLEAR_AND_SELECT",

    "COLOR_BLACK", "COLOR_WHITE", "COLOR_RED", "COLOR_GREEN", "COLOR_BLUE",
    "COLOR_CYAN", "COLOR_MAGENTA", "COLOR_YELLOW",
    "COLOR_GRAY", "COLOR_DARKGRAY", "COLOR_LIGHTGRAY", "COLOR_TRANSPARENT",
    "COLOR_DARKRED", "COLOR_DARKGREEN", "COLOR_DARKBLUE",
    "COLOR_DARKYELLOW", "COLOR_DARKCYAN", "COLOR_DARKMAGENTA",

    "PALETTE_ACTIVE", "PALETTE_INACTIVE", "PALETTE_DISABLED",
    "PALETTE_WINDOW_TEXT", "PALETTE_BUTTON", "PALETTE_LIGHT",
    "PALETTE_MIDLIGHT", "PALETTE_DARK", "PALETTE_MID",
    "PALETTE_TEXT", "PALETTE_BRIGHT_TEXT", "PALETTE_BUTTON_TEXT",
    "PALETTE_BASE", "PALETTE_WINDOW", "PALETTE_SHADOW",
    "PALETTE_HIGHLIGHT", "PALETTE_HIGHLIGHTED_TEXT",
    "PALETTE_LINK", "PALETTE_LINK_VISITED",
    "PALETTE_ALTERNATE_BASE", "PALETTE_TOOLTIP_BASE",
    "PALETTE_TOOLTIP_TEXT", "PALETTE_PLACEHOLDER_TEXT",

    "ORIENTATION_HORIZONTAL", "ORIENTATION_VERTICAL",
    "SORT_ASCENDING", "SORT_DESCENDING",
    "CHECKED", "UNCHECKED", "PARTIALLY_CHECKED",

    "DISPLAY_ROLE", "DECORATION_ROLE", "EDIT_ROLE", "TOOLTIP_ROLE",
    "STATUS_TIP_ROLE", "WHATS_THIS_ROLE", "FONT_ROLE",
    "TEXT_ALIGNMENT_ROLE", "BACKGROUND_ROLE", "FOREGROUND_ROLE",
    "CHECK_STATE_ROLE", "USER_ROLE",

    "TEXTFLAG_SINGLELINE", "TEXTFLAG_DONTCLIP", "TEXTFLAG_EXPANDTABS",
    "TEXTFLAG_SHOWMNEMONIC", "TEXTFLAG_WORDWRAP",

    "TEXTFORMAT_PLAINTEXT", "TEXTFORMAT_RICHTEXT", "TEXTFORMAT_AUTOTEXT",
    "TEXTFORMAT_MARKDOWNTEXT", "TEXTFORMAT_LOGTEXT",

    "ITEM_IS_SELECTABLE", "ITEM_IS_EDITABLE", "ITEM_IS_DRAG_ENABLED",
    "ITEM_IS_DROP_ENABLED", "ITEM_IS_USER_CHECKABLE", "ITEM_IS_ENABLED",
    "ITEM_IS_AUTO_TRISTATE", "ITEM_NEVER_HAS_CHILDREN",
    "ITEM_IS_USER_TRISTATE",

    "WINDOW_MODAL", "APPLICATION_MODAL", "NON_MODAL",
    "CUSTOM_CONTEXT_MENU", "DEFAULT_CONTEXT_MENU", "NO_CONTEXT_MENU",

    "QT_AA_ENABLE_HIGH_DPI_SCALING", "QT_AA_USE_HIGH_DPI_PIXMAPS",

    "PEN_NO_PEN", "PEN_SOLID_LINE", "PEN_DASH_LINE", "PEN_DOT_LINE",
    "BRUSH_NO_BRUSH", "BRUSH_SOLID_PATTERN",

    "CURSOR_ARROW", "CURSOR_WAIT", "CURSOR_POINTING_HAND", "CURSOR_CROSS",
    "FOCUS_NO", "FOCUS_TAB", "FOCUS_CLICK", "FOCUS_STRONG",
    "FOCUS_MOUSE", "FOCUS_BACKTAB", "FOCUS_ACTIVE_WINDOW",
    "FOCUS_POPUP", "FOCUS_SHORTCUT", "FOCUS_MENU_BAR", "FOCUS_OTHER",
    "FOCUS_REASON_TAB", "FOCUS_REASON_NO",

    "TEXT_NO_INTERACTION",
    "TEXT_SELECTABLE_BY_MOUSE", "TEXT_SELECTABLE_BY_KEYBOARD",
    "LINKS_ACCESSIBLE_BY_MOUSE", "LINKS_ACCESSIBLE_BY_KEYBOARD",
    "TEXT_EDITABLE", "TEXT_EDITOR_INTERACTION", "TEXT_BROWSER_INTERACTION",

    "SHIFT_MODIFIER", "CTRL_MODIFIER", "ALT_MODIFIER", "META_MODIFIER", "NO_MODIFIER",
    "KEEP_ASPECT_RATIO", "KEEP_ASPECT_RATIO_BY_EXPANDING", "IGNORE_ASPECT_RATIO",
    "FAST_TRANSFORMATION", "SMOOTH_TRANSFORMATION",
    "CASE_SENSITIVE", "CASE_INSENSITIVE",
    "MATCH_EXACT", "MATCH_CONTAINS", "MATCH_STARTS_WITH", "MATCH_ENDS_WITH",
    "MATCH_RECURSIVE", "MATCH_WRAP", "MATCH_FIXED_STRING", "MATCH_CASE_SENSITIVE",

    "TOOLBUTTON_ICON_ONLY", "TOOLBUTTON_TEXT_ONLY",
    "TOOLBUTTON_TEXT_BESIDE_ICON", "TOOLBUTTON_TEXT_UNDER_ICON",

    "TOOLBUTTON_POPUP_DELAYED",
    "TOOLBUTTON_POPUP_MENU_BUTTON",
    "TOOLBUTTON_POPUP_INSTANT",

    "ARROW_UP", "ARROW_DOWN", "ARROW_LEFT", "ARROW_RIGHT", "ARROW_NONE",

    "EVENT_CLOSE", "EVENT_SHOW", "EVENT_HIDE", "EVENT_RESIZE", "EVENT_MOVE",
    "EVENT_MOUSE_BUTTON_PRESS", "EVENT_MOUSE_BUTTON_RELEASE",
    "EVENT_MOUSE_MOVE", "EVENT_KEY_PRESS", "EVENT_KEY_RELEASE",
    "EVENT_LANGUAGE_CHANGE", "EVENT_ENABLED_CHANGE", "EVENT_WINDOW_STATE_CHANGE",

    "EVENT_FOCUS_IN", "EVENT_FOCUS_OUT",
    "EVENT_MOUSE_BUTTON_DBLCLICK",

    "HEADER_INTERACTIVE", "HEADER_STRETCH", "HEADER_FIXED",
    "HEADER_RESIZE_TO_CONTENTS",

    "BUTTONBOX_OK", "BUTTONBOX_CANCEL", "BUTTONBOX_YES", "BUTTONBOX_NO",
    "BUTTONBOX_APPLY", "BUTTONBOX_CLOSE", "BUTTONBOX_SAVE",
    "BUTTONBOX_OPEN", "BUTTONBOX_RESET", "BUTTONBOX_HELP",
    "BUTTONBOX_DISCARD", "BUTTONBOX_RESTORE_DEFAULTS",

    "MSGBOX_OK", "MSGBOX_CANCEL", "MSGBOX_YES", "MSGBOX_NO", "MSGBOX_CLOSE",
    "MSGBOX_NO_ICON", "MSGBOX_INFORMATION", "MSGBOX_WARNING",
    "MSGBOX_CRITICAL", "MSGBOX_QUESTION", "MSGBOX_ACCEPT_ROLE", "MSGBOX_ACTION_ROLE", "MSGBOX_REJECT_ROLE",

    "FILEMODE_ANY_FILE", "FILEMODE_EXISTING_FILE", "FILEMODE_EXISTING_FILES",
    "FILEMODE_DIRECTORY", "ACCEPT_OPEN", "ACCEPT_SAVE",
    "OPTION_SHOW_DIRS_ONLY", "OPTION_DONT_USE_NATIVE_DIALOG", "OPTION_DONT_RESOLVE_SYMLINKS",

    "SIZEPOLICY_FIXED", "SIZEPOLICY_MINIMUM", "SIZEPOLICY_MAXIMUM",
    "SIZEPOLICY_PREFERRED", "SIZEPOLICY_EXPANDING",
    "SIZEPOLICY_MINIMUM_EXPANDING", "SIZEPOLICY_IGNORED",

    "FONTSTYLE_NORMAL",
    "FONTSTYLE_ITALIC",
    "FONTSTYLE_OBLIQUE",
    "FONTSTYLE_MIXED",
    "FONTSTYLE_ANY",

    "SELECT_ITEMS", "SELECT_ROWS", "SELECT_COLUMNS",
    "SINGLE_SELECTION", "MULTI_SELECTION", "EXTENDED_SELECTION", "NO_SELECTION",
    "EDIT_NO_EDIT_TRIGGERS", "EDIT_CURRENT_CHANGED", "EDIT_DOUBLE_CLICKED",
    "EDIT_SELECTED_CLICKED", "EDIT_EDIT_KEY_PRESSED",
    "EDIT_ANY_KEY_PRESSED", "EDIT_ALL_EDIT_TRIGGERS",

    "DRAGDROP_NO", "DRAGDROP_DRAG_ONLY", "DRAGDROP_DROP_ONLY",
    "DRAGDROP_DRAG_DROP", "DRAGDROP_INTERNAL_MOVE",

    "FRAME_NOFRAME", "FRAME_BOX", "FRAME_PANEL", "FRAME_STYLED_PANEL",
    "FRAME_HLINE", "FRAME_VLINE", "FRAME_WIN_PANEL",
    "FRAME_PLAIN", "FRAME_RAISED", "FRAME_SUNKEN",

    "STYLE_SP_DIR_ICON", "STYLE_SP_FILE_ICON", "STYLE_SP_DESKTOP_ICON",
    "STYLE_SP_TRASH_ICON", "STYLE_SP_COMPUTER_ICON", "STYLE_SP_DRIVEHD_ICON",
    "STYLE_SP_DIALOG_OK", "STYLE_SP_DIALOG_CANCEL",
    "STYLE_SP_MESSAGEBOX_INFORMATION", "STYLE_SP_MESSAGEBOX_WARNING",
    "STYLE_SP_MESSAGEBOX_CRITICAL",

    "TAB_NORTH", "TAB_SOUTH", "TAB_WEST", "TAB_EAST",
    "TAB_ROUNDED", "TAB_TRIANGULAR",

    "DOCK_CLOSABLE", "DOCK_MOVABLE", "DOCK_FLOATABLE",
    "DOCK_VERTICAL_TITLEBAR", "DOCK_NO_FEATURES",

    "DOCKAREA_LEFT", "DOCKAREA_RIGHT", "DOCKAREA_TOP",
    "DOCKAREA_BOTTOM", "DOCKAREA_ALL", "DOCKAREA_NONE",

    "WIZARD_CLASSIC_STYLE", "WIZARD_MODERN_STYLE",
    "WIZARD_MAC_STYLE", "WIZARD_AERO_STYLE",

    "PAINTER_ANTIALIASING", "PAINTER_TEXT_ANTIALIASING",
    "PAINTER_SMOOTH_PIXMAP_TRANSFORM",

    "KEY_ESCAPE", "KEY_ENTER", "KEY_RETURN", "KEY_DELETE",
    "KEY_BACKSPACE", "KEY_SPACE", "KEY_TAB",

    "LEFT_BUTTON", "RIGHT_BUTTON", "MIDDLE_BUTTON", "MID_BUTTON",

    "WINDOW", "DIALOG", "SHEET", "DRAWER", "POPUP",
    "TOOL", "TOOL_TIP", "SPLASH_SCREEN", "DESKTOP", "SUB_WINDOW",
    "FOREIGN_WINDOW", "COVER_WINDOW",

    "WINDOW_TYPE_MASK",

    "CUSTOMIZE_WINDOW_HINT",
    "WINDOW_TITLE_HINT", "WINDOW_SYSTEM_MENU_HINT",
    "WINDOW_MINIMIZE_BUTTON_HINT", "WINDOW_MAXIMIZE_BUTTON_HINT",
    "WINDOW_MIN_MAX_BUTTONS_HINT",
    "WINDOW_CLOSE_BUTTON_HINT",
    "WINDOW_CONTEXT_HELP_BUTTON_HINT",
    "WINDOW_SHADE_BUTTON_HINT",

    "WINDOW_STAYS_ON_TOP_HINT", "WINDOW_STAYS_ON_BOTTOM_HINT",
    "WINDOW_TRANSPARENT_FOR_INPUT",
    "WINDOW_OVERRIDES_SYSTEM_GESTURE",
    "WINDOW_DOES_NOT_ACCEPT_FOCUS",

    "FRAMELESS_WINDOW_HINT",
    "BYPASS_WINDOW_MANAGER_HINT", "X11_BYPASS_WINDOW_MANAGER_HINT",

    "MS_WINDOWS_FIXED_SIZE_DIALOG_HINT", "MS_WINDOWS_OWN_DC",

    "MAXIMIZE_USING_FULLSCREEN_GEOMETRY_HINT",
    "WINDOW_FULLSCREEN_BUTTON_HINT",
    "NO_DROP_SHADOW_WINDOW_HINT",

    "qt_exec", "single_shot", "set_alignment",
    "header_resize_to_contents", "header_stretch", "header_interactive",
    "standard_icon", "combine_flags",

    "QICON_NORMAL", "QICON_DISABLED", "QICON_ACTIVE", "QICON_SELECTED",
    "QICON_ON", "QICON_OFF",

    "FILE_READ_ONLY", "FILE_WRITE_ONLY", "FILE_READ_WRITE",

    "WA_DELETE_ON_CLOSE",

    "COMBO_INSERT_AT_TOP", "COMBO_INSERT_AT_BOTTOM", "COMBO_INSERT_AT_CURRENT",
    "COMBO_INSERT_AFTER_CURRENT", "COMBO_INSERT_BEFORE_CURRENT", "COMBO_INSERT_ALPHABETICALLY",
    "COMBO_NO_INSERT",

    "DIALOG_ACCEPTED", "DIALOG_REJECTED",

    "QNETWORK_REPLY", "QNETWORK_REQUEST", "QNETWORK_ACCESS_MANAGER",

    "NETWORK_REPLY_NO_ERROR",
    "NETWORK_REPLY_CONNECTION_REFUSED",
    "NETWORK_REPLY_REMOTE_HOST_CLOSED",
    "NETWORK_REPLY_HOST_NOT_FOUND",
    "NETWORK_REPLY_TIMEOUT",
    "NETWORK_REPLY_OPERATION_CANCELED",
    "NETWORK_REPLY_SSL_HANDSHAKE_FAILED",
    "NETWORK_REPLY_TEMPORARY_NETWORK_FAILURE",
    "NETWORK_REPLY_NETWORK_SESSION_FAILED",
    "NETWORK_REPLY_BACKGROUND_REQUEST_NOT_ALLOWED",
    "NETWORK_REPLY_TOO_MANY_REDIRECTS",
    "NETWORK_REPLY_INSECURE_REDIRECT",
    "NETWORK_REPLY_PROXY_CONNECTION_REFUSED",
    "NETWORK_REPLY_PROXY_CONNECTION_CLOSED",
    "NETWORK_REPLY_PROXY_NOT_FOUND",
    "NETWORK_REPLY_PROXY_TIMEOUT",
    "NETWORK_REPLY_PROXY_AUTHENTICATION_REQUIRED",
    "NETWORK_REPLY_CONTENT_ACCESS_DENIED",
    "NETWORK_REPLY_CONTENT_OPERATION_NOT_PERMITTED",
    "NETWORK_REPLY_CONTENT_NOT_FOUND",
    "NETWORK_REPLY_AUTHENTICATION_REQUIRED",
    "NETWORK_REPLY_CONTENT_RE_SEND_ERROR",
    "NETWORK_REPLY_PROTOCOL_UNKNOWN",
    "NETWORK_REPLY_PROTOCOL_INVALID_OPERATION",
    "NETWORK_REPLY_UNKNOWN_NETWORK_ERROR",
    "NETWORK_REPLY_UNKNOWN_PROXY_ERROR",
    "NETWORK_REPLY_UNKNOWN_CONTENT_ERROR",
    "NETWORK_REPLY_PROTOCOL_FAILURE",
    "NETWORK_REPLY_INTERNAL_SERVER_ERROR",
    "NETWORK_REPLY_OPERATION_NOT_IMPLEMENTED",
    "NETWORK_REPLY_SERVICE_UNAVAILABLE",
    "NETWORK_REPLY_UNKNOWN_SERVER_ERROR",

    "NETWORKREQUEST_HTTP_STATUS_CODE",
    "NETWORKREQUEST_HTTP_REASON_PHRASE",
    "NETWORKREQUEST_REDIRECTION_TARGET",
    "NETWORKREQUEST_CONNECTION_ENCRYPTED",
    "NETWORKREQUEST_CACHE_LOAD_CONTROL",
    "NETWORKREQUEST_CACHE_SAVE_CONTROL",
    "NETWORKREQUEST_SOURCE_IS_FROM_CACHE",
    "NETWORKREQUEST_DO_NOT_BUFFER_UPLOAD_DATA",
    "NETWORKREQUEST_HTTP_PIPLINING_ALLOWED",
    "NETWORKREQUEST_HTTP_PIPLINING_WAS_USED",
    "NETWORKREQUEST_CUSTOM_VERB",
    "NETWORKREQUEST_COOKIE_LOAD_CONTROL",
    "NETWORKREQUEST_COOKIE_SAVE_CONTROL",
    "NETWORKREQUEST_AUTHENTICATION_REUSE",
    "NETWORKREQUEST_BACKGROUND_REQUEST",
    "NETWORKREQUEST_EMIT_ALL_UPLOAD_PROGRESS_SIGNALS",
    "NETWORKREQUEST_ORIGINAL_CONTENT_LENGTH",
    "NETWORKREQUEST_REDIRECT_POLICY",
    "NETWORKREQUEST_HTTP2_WAS_USED",

    "NETWORKREQUEST_ALWAYS_NETWORK",
    "NETWORKREQUEST_PREFER_NETWORK",
    "NETWORKREQUEST_PREFER_CACHE",
    "NETWORKREQUEST_ALWAYS_CACHE",

    "NETWORKREQUEST_MANUAL_REDIRECT_POLICY",
    "NETWORKREQUEST_NO_LESS_SAFE_REDIRECT_POLICY",
    "NETWORKREQUEST_SAME_ORIGIN_REDIRECT_POLICY",
    "NETWORKREQUEST_USER_VERIFIED_REDIRECT_POLICY",

    "NETWORKREQUEST_HIGH_PRIORITY",
    "NETWORKREQUEST_NORMAL_PRIORITY",
    "NETWORKREQUEST_LOW_PRIORITY",

    "NETWORKOP_HEAD",
    "NETWORKOP_GET",
    "NETWORKOP_PUT",
    "NETWORKOP_POST",
    "NETWORKOP_DELETE",
    "NETWORKOP_CUSTOM",

    "network_reply_error",
    "network_reply_ok",
    "network_reply_error_string",
    "network_reply_status_code",
    "network_reply_reason",
    "network_reply_redirect_target",
    "network_reply_debug_dict",

    "network_request_set_cache_control",
    "network_request_set_always_network",
    "network_request_set_prefer_network",
    "network_request_set_prefer_cache",
    "network_request_set_always_cache",
    "network_request_set_redirect_policy",
    "network_reply_is_redirect",
    "network_operation_name",

    "subprocess_no_window_kwargs",

]