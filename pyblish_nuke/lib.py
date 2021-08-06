# Standard library
import os
import sys

# Pyblish libraries
import pyblish
from pyblish import api, util

# Host libraries
import nuke
import nukescripts

# Local libraries
from . import plugins
from .vendor.Qt import QtWidgets, QtGui, QtCore


cached_process = None


self = sys.modules[__name__]
self._has_been_setup = False
self._has_menu = False
self._registered_gui = None
self._dock = None


def setup(console=False, port=None, menu=True):
    """Setup integration

    Registers Pyblish for Maya plug-ins and appends an item to the File-menu

    Arguments:
        console (bool): Display console with GUI
        port (int, optional): Port from which to start looking for an
            available port to connect with Pyblish QML, default
            provided by Pyblish Integration.

    """

    if self._has_been_setup:
        teardown()

    register_plugins()
    register_host()

    if menu:
        add_to_filemenu()
        self._has_menu = True

    self._has_been_setup = True
    print("pyblish: Loaded successfully.")


def show():
    """Try showing the most desirable GUI

    This function cycles through the currently registered
    graphical user interfaces, if any, and presents it to
    the user.

    """

    parent = None
    current = QtWidgets.QApplication.activeWindow()
    while current:
        parent = current
        current = parent.parent()

    window = (_discover_gui() or _show_no_gui)(parent)

    return window


def _discover_gui():
    """Return the most desirable of the currently registered GUIs"""

    # Prefer last registered
    guis = reversed(api.registered_guis())

    for gui in guis:
        try:
            gui = __import__(gui).show
        except (ImportError, AttributeError):
            continue
        else:
            return gui


def teardown():
    """Remove integration"""
    if not self._has_been_setup:
        return

    deregister_plugins()
    deregister_host()

    if self._has_menu:
        remove_from_filemenu()
        self._has_menu = False

    self._has_been_setup = False
    print("pyblish: Integration torn down successfully")


def remove_from_filemenu():
    menubar = nuke.menu("Nuke")
    menu = menubar.menu("File")

    menu.removeItem("Publish")


def deregister_plugins():
    # De-register accompanying plugins
    plugin_path = os.path.dirname(plugins.__file__)
    api.deregister_plugin_path(plugin_path)
    print("pyblish: Deregistered %s" % plugin_path)


def register_host():
    """Register supported hosts"""
    api.register_host("nuke")


def deregister_host():
    """De-register supported hosts"""
    api.deregister_host("nuke")


def register_plugins():
    # Register accompanying plugins
    plugin_path = os.path.dirname(plugins.__file__)
    api.register_plugin_path(plugin_path)


def add_to_filemenu():
    menubar = nuke.menu("Nuke")
    menu = menubar.menu("File")

    menu.addSeparator(index=8)

    shortcut = os.environ.get("PYBLISH_HOTKEY", "")

    # cmd = "import pyblish_nuke;pyblish_nuke.publish()"
    # menu.addCommand("Publish", cmd, shortcut, index=9)
    cmd = "import pyblish_nuke;pyblish_nuke.show()"
    menu.addCommand("Publish", cmd, shortcut, index=10)

    menu.addSeparator(index=11)


class Splash(QtWidgets.QWidget):
    """Splash screen for publishing."""

    def __init__(self, parent=None):
        super(Splash, self).__init__(parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setWindowFlags(
            QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint
        )

        pixmap = QtGui.QPixmap(os.path.join(os.path.dirname(__file__), "splash.png"))
        image = QtWidgets.QLabel()
        image.setPixmap(pixmap)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(image)

        self.bar = QtGui.QProgressBar()
        layout.addWidget(self.bar)

        # Center widget on screen
        self.resize(100, 100)


def publish():

    splash = Splash()
    splash.show()

    def on_published(context):
        api.deregister_callback(*callback)

        try:
            splash.close()
        except RuntimeError:
            # Splash already closed
            pass

        errors = False
        for r in context.data["results"]:
            if r["error"]:
                errors = True

        messagebox = QtWidgets.QMessageBox()

        pixmap_path = os.path.join(os.path.dirname(__file__), "success.png")
        messagebox_text = "Publish successfull."
        if errors:
            pixmap_path = os.path.join(os.path.dirname(__file__), "failed.png")
            messagebox_text = "Publish failed.\n\nSee script editor for details."

        messagebox.setIconPixmap(QtGui.QPixmap(pixmap_path))

        messagebox.setWindowTitle("Publish")
        messagebox.setText(messagebox_text)
        messagebox.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

        messagebox.exec_()

    callback = "published", on_published
    api.register_callback(*callback)

    def publish_iter():

        for result in util.publish_iter():
            splash.bar.setValue(result["progress"] * 100)

    QtCore.QTimer.singleShot(10, publish_iter)


def _show_no_gui():
    """Popup with information about how to register a new GUI

    In the event of no GUI being registered or available,
    this information dialog will appear to guide the user
    through how to get set up with one.

    """

    messagebox = QtWidgets.QMessageBox()
    messagebox.setIcon(messagebox.Warning)
    messagebox.setWindowIcon(
        QtGui.QIcon(
            os.path.join(os.path.dirname(pyblish.__file__), "icons", "logo-32x32.svg")
        )
    )

    spacer = QtWidgets.QWidget()
    spacer.setMinimumSize(400, 0)
    spacer.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)

    layout = messagebox.layout()
    layout.addWidget(spacer, layout.rowCount(), 0, 1, layout.columnCount())

    messagebox.setWindowTitle("Uh oh")
    messagebox.setText("No registered GUI found.")

    if not api.registered_guis():
        messagebox.setInformativeText(
            "In order to show you a GUI, one must first be registered. "
            'Press "Show details..." below for information on how to '
            "do that."
        )

        messagebox.setDetailedText(
            "Pyblish supports one or more graphical user interfaces "
            "to be registered at once, the next acting as a fallback to "
            "the previous."
            "\n"
            "\n"
            "For example, to use Pyblish Lite, first install it:"
            "\n"
            "\n"
            "$ pip install pyblish-lite"
            "\n"
            "\n"
            "Then register it, like so:"
            "\n"
            "\n"
            ">>> from pyblish import api\n"
            '>>> api.register_gui("pyblish_lite")'
            "\n"
            "\n"
            "The next time you try running this, Lite will appear."
            "\n"
            "See http://api.pyblish.com/register_gui.html for "
            "more information."
        )

    else:
        messagebox.setInformativeText(
            "None of the registered graphical user interfaces "
            "could be found."
            "\n"
            "\n"
            'Press "Show details" for more information.'
        )

        messagebox.setDetailedText(
            "These interfaces are currently registered."
            "\n"
            "%s" % "\n".join(api.registered_guis())
        )

    messagebox.setStandardButtons(messagebox.Ok)
    messagebox.exec_()


def _nuke_set_zero_margins(widget_object):
    """Remove Nuke margins when docked UI
    .. _More info:
        https://gist.github.com/maty974/4739917
    """
    parentApp = QtWidgets.QApplication.allWidgets()
    parentWidgetList = []
    for parent in parentApp:
        for child in parent.children():
            if widget_object.__class__.__name__ == child.__class__.__name__:
                parentWidgetList.append(parent.parentWidget())
                parentWidgetList.append(parent.parentWidget().parentWidget())
                parentWidgetList.append(
                    parent.parentWidget().parentWidget().parentWidget()
                )

                for sub in parentWidgetList:
                    for tinychild in sub.children():
                        try:
                            tinychild.setContentsMargins(0, 0, 0, 0)
                        except Exception:
                            pass


class pyblish_nuke_dockwidget(QtWidgets.QWidget):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        QtWidgets.QVBoxLayout(self)
        self.setObjectName("pyblish_nuke.dock")


def dock(window):
    """Expecting a window to parent into a Nuke panel, that is dockable."""

    # Deleting existing dock
    # There is a bug where existing docks are kept in-memory when closed via UI
    if self._dock:
        print("Deleting existing dock...")
        parent = self._dock
        dialog = None
        stacked_widget = None
        main_windows = []

        # Getting dock parents
        while parent:
            if isinstance(parent, QtWidgets.QDialog):
                dialog = parent
            if isinstance(parent, QtWidgets.QStackedWidget):
                stacked_widget = parent
            if isinstance(parent, QtWidgets.QMainWindow):
                main_windows.append(parent)
            parent = parent.parent()

        dialog.deleteLater()

        if len(main_windows) > 1:
            # Then it's a floating window
            if stacked_widget.count() == 1:
                # Then it's empty and we can close it,
                # as is native Nuke UI behaviour
                main_windows[0].deleteLater()

    # Creating new dock
    pane = nuke.getPaneFor("Properties.1")
    widget_path = "pyblish_nuke.lib.pyblish_nuke_dockwidget"
    panel = nukescripts.panels.registerWidgetAsPanel(
        widget_path, window.windowTitle(), "pyblish_nuke.dock", True
    ).addToPane(pane)

    panel_widget = panel.customKnob.getObject().widget
    panel_widget.layout().addWidget(window)
    _nuke_set_zero_margins(panel_widget)
    self._dock = panel_widget

    return self._dock
