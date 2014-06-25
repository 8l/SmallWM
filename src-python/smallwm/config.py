"""
Parses the configuration file, building the proper data structures to store
configuration information.

.. py:data DEFAULT_SHORTCUTS

    A list of all of the default key shortcuts, with each element containing
    the keyboard action (what, logically, happens when the key is pressed)
    along with the configuration descriptor (what name does that action have
    in the configuration file) and the X key symbol (the physical key that X
    tells us was pressed).

.. py:data SYSLOG_LEVEL
    
    A mapping between textual names found in the configuration file, and the
    actual log levels given by syslog.

.. py:data SNAP_DIRS

    A mapping between textual names found in the configuration file, and the
    direction in which a window is snapped.
"""

import configparser
import os
import syslog

from smallwm import actions, keyboard, utils
from Xlib import XK

# The members from XK are dynamically generated, and thus we should tell pylint
# to ignore any errors as a result of trying to analyze Xlib.XK statically

# pylint: disable=E1101
DEFAULT_SHORTCUTS = [
    (keyboard.CLIENT_NEXT_DESKTOP, "client-next-desktop", XK.XK_bracketright),
    (keyboard.CLIENT_PREV_DESKTOP, "client-prev-desktop", XK.XK_bracketleft),
    (keyboard.NEXT_DESKTOP, "next-desktop", XK.XK_period),
    (keyboard.PREV_DESKTOP, "prev-desktop", XK.XK_comma),
    (keyboard.TOGGLE_STICK, "toggle-stick", XK.XK_backslash),
    (keyboard.ICONIFY, "iconify", XK.XK_h),
    (keyboard.MAXIMIZE, "maximize", XK.XK_m),
    (keyboard.REQUEST_CLOSE, "request-close", XK.XK_c),
    (keyboard.FORCE_CLOSE, "force-close", XK.XK_x),
    (keyboard.SNAP_TOP, "snap-top", XK.XK_Up),
    (keyboard.SNAP_BOTTOM, "snap-bottom", XK.XK_Down),
    (keyboard.SNAP_LEFT, "snap-left", XK.XK_Left),
    (keyboard.SNAP_RIGHT, "snap-right", XK.XK_Right),
    (keyboard.LAYER_ABOVE, "layer-above", XK.XK_Page_Up),
    (keyboard.LAYER_BELOW, "layer-below", XK.XK_Page_Down),
    (keyboard.LAYER_TOP, "layer-top", XK.XK_Home),
    (keyboard.LAYER_BOTTOM, "layer-bottom", XK.XK_End),
    (keyboard.LAYER_1, "layer-1", XK.XK_1),
    (keyboard.LAYER_2, "layer-2", XK.XK_2),
    (keyboard.LAYER_3, "layer-3", XK.XK_3),
    (keyboard.LAYER_4, "layer-4", XK.XK_4),
    (keyboard.LAYER_5, "layer-5", XK.XK_5),
    (keyboard.LAYER_6, "layer-6", XK.XK_6),
    (keyboard.LAYER_7, "layer-7", XK.XK_7),
    (keyboard.LAYER_8, "layer-8", XK.XK_8),
    (keyboard.LAYER_9, "layer-9", XK.XK_9),
    (keyboard.EXIT_WM, "exit", XK.XK_Escape)
]
# pylint: enable=E1101

SYSLOG_LEVEL = {
    name: getattr(syslog, 'LOG_' + name) for name in
    ['EMERG', 'ALERT', 'CRIT', 'ERR', 'WARNING', 'NOTICE', 'INFO', 'DEBUG']
}

SNAP_DIRS = {
    'left': actions.LEFT,
    'right': actions.RIGHT,
    'top': actions.TOP,
    'bottom': actions.BOTTOM,
}

class SmallWMConfig:
    """
    Loads and parses the configuration file, and then stores the configuration
    values.

    .. py:attribute log_mask
    
        The minimum level of messages to send to syslog.

    .. py:attribute shell

        The shell to run on ``Super + LeftButton``.

    .. py:attribute key_commands

        A mapping from X key symbols to keyboard actions.

    .. py:attribute command_keys

        The reverse mapping of :attr:`key_commands`.

    .. py:attribute num_desktops

        The total number of desktops available to users.

    .. py:attribute icon_width
    
        The width of icon windows.

    .. py:attribute icon_height

        The height of icon windows.

    .. py:attribute border_width

        The width of the border applied to windows.

    .. py:attribute class_actions

        A mapping from X11 classes to the list of actions applied to each
        window of that class.

    .. py:attribute show_pixmaps

        Whether or not to show application icons inside icon windows.
    """
    def __init__(self):
        self.log_mask = syslog.LOG_UPTO(syslog.LOG_WARNING)
        self.shell = "/usr/bin/xterm"

        self.key_commands = {}
        self.command_keys = {}
        self._config_actions = {} # Maps configuration keys to keyboard actions
        for action, config_name, key_binding in DEFAULT_SHORTCUTS:
            self.key_commands[key_binding] = action
            self.command_keys[action] = key_binding
            self._config_actions[config_name] = action

        self.num_desktops = 5
        self.icon_width = 75
        self.icon_height = 20
        self.border_width = 2
        self.class_actions = {}
        self.show_pixmaps = True

        # Maps configuration file sections to the
        self._section_mapping = {
            'smallwm': self.parse_smallwm_body,
            'actions': self.parse_class_action,
            'keyboard': self.parse_key_binding,
        }

    def get_config_filename(self):
        """
        :return: The path to the configuration file.
        """
        return os.path.join(os.environ["HOME"], '.config', 'smallwm')

    def nonexistent_section(self, section):
        """
        Prints an error to syslog about a nonexistent section.
        """
        syslog.syslog(syslog.LOG_WARNING,
            'Nonexistent section {}'.format(section))

    def nonexistent_key(self, section, key):
        """
        Prints an error to syslog about a nonexistent key.
        """
        syslog.syslog(syslog.LOG_WARNING,
            'Nonexistant key {}.{}'.format(section, key))

    def parse(self):
        """
        Parses the configuration file, and dispatches each configuration option
        to the appropriate handler.
        """
        try:
            parser = configparser.ConfigParser()
            parser.read(self.get_config_filename())

            for section_name in parser.sections():
                if section_name in self._section_mapping:
                    section = parser[section_name]
                    for key, value in section.items():
                        self._section_mapping[section_name](key, value)
                else:
                    self.nonexistent_section(section_name)
        except configparser.Error as ex:
            syslog.syslog(syslog.LOG_ERR,
                'Parsing configuration file failed - "{}"'.format(ex))

    def parse_smallwm_body(self, key, value):
        """
        Parses the SmallWM core options.

        - ``log-level``
        - ``shell``
        - ``desktops``
        - ``icon-width``
        - ``icon-height``
        - ``icon-pixmaps``
        - ``border-width``
        """
        if key == 'log-level':
            try:
                self.log_mask = SYSLOG_LEVEL[value]
            except KeyError:
                syslog.syslog(syslog.LOG_WARNING,
                    'Invalid log level "{}"'.format(value))
        elif key == 'shell':
            self.shell = value
        elif key == 'desktops':
            try:
                self.num_desktops = utils.positive_int(value)
            except ValueError:
                syslog.syslog(syslog.LOG_WARNING,
                    'Invalid cardinal "{}"'.format(value))
        elif key == 'icon-width':
            try:
                self.icon_width = utils.positive_int(value)
            except ValueError:
                syslog.syslog(syslog.LOG_WARNING,
                    'Invalid cardinal "{}"'.format(value))
        elif key == 'icon-height':
            try:
                self.icon_height = utils.positive_int(value)
            except ValueError:
                syslog.syslog(syslog.LOG_WARNING,
                    'Invalid cardinal "{}"'.format(value))
        elif key == 'border-width':
            try:
                self.border_width = utils.positive_int(value)
            except ValueError:
                syslog.syslog(syslog.LOG_WARNING,
                    'Invalid cardinal "{}"'.format(value))
        elif key == 'icon-pixmaps':
            try:
                if value.lower() == 'true':
                    self.show_pixmaps = True
                elif value.lower() == 'false':
                    self.show_pixmaps = False
                else:
                    raise ValueError
            except ValueError:
                syslog.syslog(syslog.LOG_WARNING,
                    'Invalid boolean "{}"'.format(value))
        else:
            self.nonexistent_key('smallwm', 'key')

    def parse_class_action(self, key, value):
        """
        Parses the class action syntax into actions. A small grammar of the action
        syntax is given below. The gist is that it is a list of comma-separated
        actions.::

            <actions> := {<action> {"," <action>}+}?

            <action> := "stick"
                    |   "maximize"
                    |   "snap:" <snapdir>
                    |   "layer:" <int>

            <snapdir> := "left"
                    |   "right"
                    |   "top"
                    |   "bottom"
        """
        action_list = []
        self.class_actions[key] = action_list

        action_values = value.split(',')
        for action in action_values:
            # Whitespace is allowed, but we don't have any use for it
            action = action.strip()

            if action == 'stick':
                action_list.append(actions.Stick())
            elif action == 'maximize':
                action_list.append(actions.Maximize())
            elif action.startswith('layer:'):
                try:
                    layer_offset = len('layer:')
                    layer = utils.positive_int(action[layer_offset:])
                    if layer > utils.MAX_LAYER:
                        raise ValueError

                    action_list.append(actions.SetLayer(layer))
                except ValueError:
                    syslog.syslog(syslog.LOG_WARNING,
                        'Invalid action: "{}"'.format(action))
            elif action.startswith('snap:'):
                try:
                    direction_offset = len('snap:')
                    direction = SNAP_DIRS[action[direction_offset:]]
                    action_list.append(actions.Snap(direction))
                except KeyError:
                    syslog.syslog(syslog.LOG_WARNING,
                        'Invalid action: "{}"'.format(action))
            else:
                syslog.syslog(syslog.LOG_WARNING,
                    'Invalid action: "{}"'.format(action))

    def parse_key_binding(self, key, value):
        """
        Parses key bindings, and assigns them to actions.
        """
        # If the user wants to use an existing key binding, they have to use
        # an '!' before the value of the key to let us know that they're not
        # accidentally trying to double-bind a key
        if value[0] == '!':
            force_overwrite = True
            value = value[1:]
        else:
            force_overwrite = False

        try:
            action = self._config_actions[key]
        except KeyError:
            syslog.syslog(syslog.LOG_WARNING,
                'Invalid keyboard binding: "{}"'.format(key))
            return

        try:
            key_binding = getattr(XK, 'XK_' + value)
        except AttributeError:
            syslog.syslog(syslog.LOG_WARNING,
                'Invalid keyboard shortcut: "{}"'.format(value))
            return

        # If there is already a key binding, then log an error, but only if
        # the user hasn't already asked us to ignore this check
        if not force_overwrite and key_binding in self.key_commands:
            syslog.syslog(syslog.LOG_WARNING,
                'Key binding collision: "{}"'.format(value))
            return

        # If an old binding exists for this action, then remove it
        if action in self.command_keys:
            existing_key = self.command_keys[action]
            del self.command_keys[action]
            del self.key_commands[existing_key]

        self.key_commands[key_binding] = action
        self.command_keys[action] = key_binding
