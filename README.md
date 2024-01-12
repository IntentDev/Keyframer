# Keyframer

Keyframer is a keyframe editor component for use with animationCOMP in TD. It's designed as a replacement for the existing animation editor in TD, offering enhanced functionality and user experience.

## Key Features

- **Template Creation**: Utilize an internal template animationCOMP to generate multiple animationCOMPs with identical initial channels.
- **Channel Creation**: Easily create new channels by dropping Pars, CHOP channels, CHOPs, and DATs into Keyframer. Includes a standard append channels function with custom names.
- **AnimationCOMP Editing**: Directly edit any dropped animationCOMP within Keyframer.
- **Undo/Redo**: Full support for undoing and redoing actions.
- **Keyframe Management**:
  - Insert Keys using Alt-Left Click or Alt-Ctrl Left Click.
  - Delete Keys with the Delete button.
  - Translate Keys by selecting and dragging with the mouse. Use Shift for horizontal locking and Shift-Ctrl for vertical locking.
  - Scale Keys by selecting multiple keys, then pressing D, F, or both, and moving the mouse to scale along the X, Y, or XY axis.
- **Clipboard Operations**: Copy, cut, and paste selected keys at the current mouse position (within the edit view).
- **Bezier Handles**: Handles represent the actual length of acceleration for precise control.
- **Handle Locking**: Toggle lock/unlock on handles with the T key.
- **Channel Organization**: Reorder channels via middle-click and drag in the Channel List.
- **Advanced Features**:
  - Auto limiting handle lengths.
  - New `EaseAdjust()` segment type with adjustable ease in/out handles.
  - Nudge selected items (keys or handles) using arrow keys (Shift, Ctrl, and Alt modify step size).
  - Tab selection of adjacent items - use Tab and Shift+Tab to navigate.
  - Marquee and Shift select for multi-item selection.
- **View Controls**:
  - Translate View with a middle-click and drag.
  - Zoom View with Shift-Middle Click and drag.
  - Fit View to screen with the H key.
  - Auto Vert Slider Widgets for smooth, fine adjustments of values for selected items.

## Installation

To use Keyframer, only the `Keyframer.*.tox` file is required (external modules and files do not need to be downloaded).
