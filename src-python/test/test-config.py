"""
Tests that the configuration parser generates proper outputs.
"""
import configparser
import os
import random
import sys
import syslog
import unittest

# Ensure we can import smallwm
sys.path.append(os.path.join(*os.path.split(sys.path[0])[:-1]))

from Xlib import XK
import smallwm.config
from smallwm import actions, keyboard

# The location of the configuratio file to write to when generating test data
FILENAME = '/tmp/_smallwm_test_data'

# Generate some kind of non-useful key or value
SHORT_ALLOWED_CHARS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
def generate_short_noise():
    return ''.join(random.choice(SHORT_ALLOWED_CHARS) for _ in range(10))

LONG_ALLOWED_CHARS = SHORT_ALLOWED_CHARS + '\n'
def generate_long_noise():
    return ''.join(random.choice(LONG_ALLOWED_CHARS) for _ in range(500))

# Don't actually log to syslog - just record that there was a problem
syslog_recorded_error = False
def fake_syslog(level, text):
    global syslog_recorded_error
    syslog_recorded_error = True

smallwm.config.syslog.syslog = fake_syslog

def did_syslog_log_error():
    global syslog_recorded_error
    tmp = syslog_recorded_error
    syslog_recorded_error = False
    return tmp

class SmallWMConfigTester(smallwm.config.SmallWMConfig):
    """
    A subclass of smallwm.config.SmallWMConfig which finds its configuration
    file in a different location.
    """
    def get_config_filename(self):
        "Returns the path to the test filename."
        return FILENAME

def generate_config_file(section, items):
    """
    Generates a configuration file, which contains the data from the given
    dictionary. Returns a SmallWMConfigTester which has already parsed the values.
    """
    return generate_extended_config_file((section, items))

def generate_extended_config_file(*section_items):
    """
    Generates a configuration file which has multiple sections.
    """
    parser = configparser.ConfigParser()
    for section, items in section_items:
        parser.add_section(section)
        for key, value in items.items():
            parser.set(section, key, value)

    with open(FILENAME, 'w') as fp:
        parser.write(fp)

    tester = SmallWMConfigTester()
    tester.parse()
    return tester

class TestMalformedConfig(unittest.TestCase):
    """
    Tests a number of errors in the configuration file, and makes sure that
    they all throw errors.
    """
    def test_nonexistent_sections(self):
        """
        Ensures nonexistent section headings log errors.
        """
        generate_config_file(generate_short_noise(), {'test': 'test'})
        self.assertTrue(did_syslog_log_error())

    # Spell this out since configparser won't let us have duplicate sections
    DUPLICATE_SECTIONS = """
[smallwm]
show-pixmaps = true
[smallwm]
icon-width = 10
"""
    def test_duplicate_sections(self):
        """
        Ensures that duplicate sections log errors.
        """
        with open(FILENAME, 'w') as fp:
            fp.write(self.DUPLICATE_SECTIONS)

        parser = SmallWMConfigTester()
        parser.parse()
        self.assertTrue(did_syslog_log_error())
    
    # Spell this out since configparser won't let us have duplicate options
    DUPLICATE_OPTIONS = """
[smallwm]
show-pixmaps = true
show-pixmaps = false
"""
    def test_duplicate_options(self):
        """
        Ensure that duplicate options log errors.
        """
        with open(FILENAME, 'w') as fp:
            fp.write(self.DUPLICATE_OPTIONS)

        parser = SmallWMConfigTester()
        parser.parse()
        self.assertTrue(did_syslog_log_error())

    def test_noise(self):
        """
        Ensure that a randomly generated file (i.e. a file with syntax errors)
        causes an error.
        """
        with open(FILENAME, 'w') as fp:
            fp.write(generate_long_noise())

        parser = SmallWMConfigTester()
        parser.parse()
        self.assertTrue(did_syslog_log_error())

class TestSmallWMSection(unittest.TestCase):
    """
    Check that all of the numeric attributes in [smallwm] accept only positive
    integers.
    """
    INT_OPTIONS = {'desktops': 'num_desktops',
        'icon-width': 'icon_width', 
        'icon-height': 'icon_height', 
        'border-width': 'border_width'}
    VALID_INT_VALUES = {
        '12': 12,
        # It seems odd to store configuration values in hex, but why not?
        '0x12': 0x12,
    }
    INVALID_INT_VALUES = {'not-a-number', '-12', '1.27', '1e2', generate_short_noise()}
    def test_int_values(self):
        """
        Check that all of the numeric attributes accept only positive integers.
        """
        for key, attrib in self.INT_OPTIONS.items():
            for value, expected in self.VALID_INT_VALUES.items():
                result = generate_config_file('smallwm', {key: value})
                actual_value = getattr(result, attrib)
                self.assertFalse(did_syslog_log_error())
                self.assertEqual(actual_value, expected)
    
            for value in self.INVALID_INT_VALUES:
                generate_config_file('smallwm', {key: value})
                self.assertTrue(did_syslog_log_error())

    LOGLEVEL_VALID_VALUES = {'EMERG', 'ALERT', 'CRIT', 'ERR', 'WARNING', 'NOTICE', 'INFO', 'DEBUG'}

    # Make sure there are some nonsense values, plus some which are from syslog
    # but which are not log levels
    LOGLEVEL_INVALID_VALUES = {'MAIL', 'CONS', 'not-a-log-level', '42',
        generate_short_noise()}
    def test_log_levels(self):
        """
        Make sure that valid log levels are parsed properly, and invalid ones
        are rejected.
        """
        for level in self.LOGLEVEL_VALID_VALUES:
            result = generate_config_file('smallwm', {'log-level': level})
            self.assertFalse(did_syslog_log_error())
            self.assertEqual(result.log_mask, getattr(syslog, 'LOG_' + level))

        for value in self.LOGLEVEL_INVALID_VALUES:
            generate_config_file('smallwm', {'log-level': value})
            self.assertTrue(did_syslog_log_error())

    PIXMAP_VALID_VALUES = {'tRue': True, 'FAlSe': False,
        'true': True, 'false': False,
        'TRUE': True, 'FALSE': False}
    PIXMAP_INVALID_VALUES = {'ture', 'flase', 'not-a-bool', '42', generate_short_noise()}
    def test_pixmaps(self):
        """
        Ensures that case-variations of 'true' and 'false' are interpreted
        correctly.
        """
        for value, expected in self.PIXMAP_VALID_VALUES.items():
            result = generate_config_file('smallwm', {'icon-pixmaps': value})
            self.assertFalse(did_syslog_log_error())
            self.assertEqual(result.show_pixmaps, expected)

        for value in self.PIXMAP_INVALID_VALUES:
            generate_config_file('smallwm', {'icon-pixmaps': value})
            self.assertTrue(did_syslog_log_error())

class TestClassActions(unittest.TestCase):
    """
    Tests some values for class actions, to make sure that they work as expected.
    """
    def test_nonexistant_Value(self):
        """
        Ensures that actions which are not actually actions log errors.
        """
        gibberish = generate_short_noise()
        result = generate_config_file('actions', {'class': gibberish})
        self.assertTrue(did_syslog_log_error())

    ATOMIC_VALUES = {'stick': actions.Stick,
        'maximize': actions.Maximize}
    def test_atomic(self):
        """
        Make sure that the actions which lack parameters produce the proper
        kind of values in the actions list.
        """
        for action, atom_type in self.ATOMIC_VALUES.items():
            result = generate_config_file('actions', {'class': action})
            self.assertFalse(did_syslog_log_error())
            atom = result.class_actions['class'][0]
            self.assertIsInstance(atom, atom_type)

    def do_parameterized_test(self, allowed, not_allowed):
        """
        Does a parameterized test on a particular set of values.
        """
        for value, expected in allowed.items():
            result = generate_config_file('actions', {'class': value})
            self.assertFalse(did_syslog_log_error())
            actual = result.class_actions['class'][0]
            self.assertEqual(actual, expected)
        
        for value in not_allowed:
            generate_config_file('actions', {'class': value})
            self.assertTrue(did_syslog_log_error())

    VALID_LAYERS = {'layer:67': actions.SetLayer(67)}
    INVALID_LAYERS = {'layer:-182', 'layer:60.273', generate_short_noise()}
    def test_layer(self):
        """
        Ensure that the layer action accepts correct values and rejects
        invalid values.
        """
        self.do_parameterized_test(self.VALID_LAYERS, self.INVALID_LAYERS)

    VALID_SNAPS = {'snap:left': actions.Snap(actions.LEFT),
        'snap:right': actions.Snap(actions.RIGHT),
        'snap:top': actions.Snap(actions.TOP),
        'snap:bottom': actions.Snap(actions.BOTTOM)}
    INVALID_SNAPS = {'not-a-snap', '42', generate_short_noise()}
    def test_snaps(self):
        """
        Ensure that the snap action accepts correct values and rejects
        invalid values.
        """
        self.do_parameterized_test(self.VALID_SNAPS, self.INVALID_SNAPS)

class TestKeyboardShortcuts(unittest.TestCase):
    """
    Test some values for keyboard shortcuts.
    """
    VALID_SHORTCUT_NAMES = {name: action
        for action, name, _ in smallwm.config.DEFAULT_SHORTCUTS}
    INVALID_SHORTCUT_NAMES = {'not-a-shortcut', '42', generate_short_noise()}

    # Just _some_ used bindings, mind you, _not_ all of them
    USED_KEY_BINDINGS = {'bracketright', 'backslash', 'h'}
    UNUSED_KEY_BINDINGS = {'asciitilde', 'Return', 'F1'}
    INVALID_KEY_BINDINGS = {'not-a-binding', '42', generate_short_noise()}

    def test_unused_bindings(self):
        """
        Make sure non-overlapping bindings work.
        """
        for shortcut, action in self.VALID_SHORTCUT_NAMES.items():
            for binding in self.UNUSED_KEY_BINDINGS:
                binding_value = getattr(XK, 'XK_' + binding)
                result = generate_config_file('keyboard', {shortcut: binding})

                self.assertFalse(did_syslog_log_error())
                self.assertEqual(result.command_keys[action], binding_value)
                self.assertEqual(result.key_commands[binding_value], action)

    def test_used_bindings(self):
        """
        Ensures that bindings which overlap are not allowed by default, but
        which are allowed when prefixed with a '!'
        """
        for shortcut in self.VALID_SHORTCUT_NAMES:
            for binding in self.USED_KEY_BINDINGS:
                generate_config_file('keyboard', {shortcut: binding})
                self.assertTrue(did_syslog_log_error())
        
        for shortcut, action in self.VALID_SHORTCUT_NAMES.items():
            for binding in self.USED_KEY_BINDINGS:
                binding_value = getattr(XK, 'XK_' + binding)
                result = generate_config_file('keyboard', 
                        {shortcut: '!' + binding})

                self.assertFalse(did_syslog_log_error())
                self.assertEqual(result.command_keys[action], binding_value)
                self.assertEqual(result.key_commands[binding_value], action)

    def test_invalid_bindings(self):
        """
        Ensures that nonexistent actions, and nonexistent keys, log errors.
        """
        for shortcut in self.VALID_SHORTCUT_NAMES:
            for binding in self.INVALID_KEY_BINDINGS:
                generate_config_file('keyboard', {shortcut: binding})
                self.assertTrue(did_syslog_log_error())

        for shortcut in self.INVALID_SHORTCUT_NAMES:
            for binding in self.UNUSED_KEY_BINDINGS:
                generate_config_file('keyboard', {shortcut: binding})
                self.assertTrue(did_syslog_log_error())

if __name__ == '__main__':
    unittest.main()
