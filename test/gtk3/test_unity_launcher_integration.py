#!/usr/bin/python

from gi.repository import Gtk
import time
import unittest

from testutils import setup_test_env
from mock import Mock, patch

setup_test_env()

# overwrite early
import softwarecenter.utils

from softwarecenter.enums import TransactionTypes
from softwarecenter.utils import convert_desktop_file_to_installed_location
from softwarecenter.db.application import Application
from softwarecenter.ui.gtk3.panes.availablepane import get_test_window
from softwarecenter.backend.unitylauncher import UnityLauncherInfo

# Tests for Ubuntu Software Center's integration with the Unity launcher,
# see https://wiki.ubuntu.com/SoftwareCenter#Learning%20how%20to%20launch%20an%20application

# we can only have one instance of availablepane, so create it here
win = get_test_window()
available_pane = win.get_data("pane")

class TestUnityLauncherIntegration(unittest.TestCase):

    def setUp(self):
        # monkey patch is_unity_running
        softwarecenter.utils.is_unity_running = lambda: True
        
    def _zzz(self):
        for i in range(10):
            time.sleep(0.1)
            self._p()

    def _p(self):
        while Gtk.events_pending():
            Gtk.main_iteration()

    def _simulate_install_events(self, app):
        # pretend we started an install
        available_pane.backend.emit("transaction-started",
                                    app.pkgname, app.appname,
                                    "testid101",
                                    TransactionTypes.INSTALL)
        self._zzz()
        # send the signal to complete the install
        mock_result = Mock()
        mock_result.pkgname = app.pkgname
        available_pane.backend.emit("transaction-finished",
                                    mock_result)
        self._zzz()

    def _install_from_list_view(self, pkgname):
        from softwarecenter.ui.gtk3.panes.availablepane import AvailablePane
        available_pane.notebook.set_current_page(AvailablePane.Pages.LIST)
        self._p()
        available_pane.on_search_terms_changed(None,
                                               "ark,artha,software-center")
        self._p()
        # select the first item in the list
        available_pane.app_view.tree_view.set_cursor(Gtk.TreePath(0),
                                                            None, False)
        # ok to just use the test app here                                            
        app = Application("", pkgname)
        self._p()
        self._simulate_install_events(app)

    def _navigate_to_appdetails_and_install(self, pkgname):
        app = Application("", pkgname)
        available_pane.app_view.emit("application-activated",
                                     app)
        self._p()
        self._simulate_install_events(app)

    def _check_send_application_to_launcher_args(self,
                                                 pkgname, launcher_info):
        self.assertEqual(pkgname, self.expected_pkgname)
        self.assertEqual(launcher_info.name, self.expected_launcher_info.name)
        self.assertEqual(launcher_info.icon_name,
                         self.expected_launcher_info.icon_name)
        self.assertTrue(launcher_info.icon_x > 5)
        self.assertTrue(launcher_info.icon_y > 5)
        # check that the icon size is one of either 32 pixels (for the
        # list view case) or 96 pixels (for the details view case)
        self.assertTrue(launcher_info.icon_size == 32 or
                        launcher_info.icon_size == 96)
        self.assertEqual(launcher_info.installed_desktop_file_path,
                self.expected_launcher_info.installed_desktop_file_path)
        self.assertEqual(launcher_info.trans_id,
                self.expected_launcher_info.trans_id)

    @patch('softwarecenter.ui.gtk3.panes.availablepane.UnityLauncher'
           '.send_application_to_launcher')
    def test_unity_launcher_integration_list_view(self,
                                         mock_send_application_to_launcher):
        # test the automatic add to launcher enabled functionality when
        # installing an app from the list view
        available_pane.add_to_launcher_enabled = True
        test_pkgname = "software-center"
        self.expected_pkgname = test_pkgname
        self.expected_launcher_info = UnityLauncherInfo("software-center",
                "softwarecenter",
                0, 0, 0, 0, # these values are set in availablepane
                "/usr/share/applications/ubuntu-software-center.desktop",
                "")
        self._install_from_list_view(test_pkgname)
        self.assertTrue(mock_send_application_to_launcher.called)
        args, kwargs = mock_send_application_to_launcher.call_args
        self._check_send_application_to_launcher_args(*args, **kwargs)

    @patch('softwarecenter.ui.gtk3.panes.availablepane.UnityLauncher'
           '.send_application_to_launcher')
    def test_unity_launcher_integration_details_view(self,
                                         mock_send_application_to_launcher):
        # test the automatic add to launcher enabled functionality when
        # installing an app from the details view
        available_pane.add_to_launcher_enabled = True
        test_pkgname = "software-center"
        self.expected_pkgname = test_pkgname
        self.expected_launcher_info = UnityLauncherInfo("software-center",
                "softwarecenter",
                0, 0, 0, 0, # these values are set in availablepane
                "/usr/share/applications/ubuntu-software-center.desktop",
                "")
        self._navigate_to_appdetails_and_install(test_pkgname)
        self.assertTrue(mock_send_application_to_launcher.called)
        args, kwargs = mock_send_application_to_launcher.call_args
        self._check_send_application_to_launcher_args(*args, **kwargs)
        
    @patch('softwarecenter.ui.gtk3.panes.availablepane.UnityLauncher'
           '.send_application_to_launcher')
    def test_unity_launcher_integration_disabled(self,
                                         mock_send_application_to_launcher):
        # test the case where automatic add to launcher is disabled
        available_pane.add_to_launcher_enabled = False
        test_pkgname = "software-center"
        self._navigate_to_appdetails_and_install(test_pkgname)
        self.assertFalse(mock_send_application_to_launcher.called)
       
    @patch('softwarecenter.ui.gtk3.panes.availablepane'
           '.convert_desktop_file_to_installed_location')
    @patch('softwarecenter.ui.gtk3.panes.availablepane.UnityLauncher'
           '.send_application_to_launcher')
    # NOTE: the order of attributes in the method call appears reversed, this
    # is because the patch decorators above are executed from innermost to
    # outermost
    def test_unity_launcher_integration_launcher(self,
                mock_send_application_to_launcher,
                mock_convert_desktop_file_to_installed_location):
        # this is a 3-tuple of (pkgname, desktop-file, expected_result)
        TEST_CASES = (
            # normal app
            ("software-center", "/usr/share/app-install/desktop/"\
                 "software-center:ubuntu-software-center.desktop", True),
            # NoDisplay=True line
            ("wine", "/usr/share/app-install/desktop/"\
                 "wine1.4:wine.desktop", False),
            # No Exec= line
            ("bzr", "/usr/share/app-install/desktop/"\
                 "bzr.desktop", False)
            )
        # run the test over all test-cases
        available_pane.add_to_launcher_enabled = True
        for test_pkgname, app_install_desktop_file_path, res in TEST_CASES:
            # setup the mock
            mock_convert_desktop_file_to_installed_location.return_value = (
                app_install_desktop_file_path)
            # this is the tofu of the test
            self._navigate_to_appdetails_and_install(test_pkgname)
            # verify
            self.assertEqual(mock_send_application_to_launcher.called, res)
            # and reset again to ensure we don't get the call info from
            # the previous call(s)
            mock_send_application_to_launcher.reset_mock()


class DesktopFilepathConversionTestCase(unittest.TestCase):
        
    def test_normal(self):
        # test 'normal' case
        app_install_desktop_path = ("./data/app-install/desktop/" +
                                    "deja-dup:deja-dup.desktop")
        installed_desktop_path = convert_desktop_file_to_installed_location(
                app_install_desktop_path, "deja-dup")
        self.assertEqual(installed_desktop_path,
                         "./data/applications/deja-dup.desktop")

    def test_encoded_subdir(self):
        # test encoded subdirectory case, e.g. e.g. kde4_soundkonverter.desktop
        app_install_desktop_path = ("./data/app-install/desktop/" +
                                    "soundkonverter:" +
                                    "kde4__soundkonverter.desktop")
        installed_desktop_path = convert_desktop_file_to_installed_location(
                app_install_desktop_path, "soundkonverter")
        self.assertEqual(installed_desktop_path,
                         "./data/applications/kde4/soundkonverter.desktop")

    def test_purchase_via_software_center_agent(self):
        # test the for-purchase case (uses "software-center-agent" as its
        # appdetails.desktop_file value)
        # FIXME: this will only work if update-manager is installed
        app_install_desktop_path = "software-center-agent"
        installed_desktop_path = convert_desktop_file_to_installed_location(
                app_install_desktop_path, "update-manager")
        self.assertEqual(installed_desktop_path,
                         "/usr/share/applications/update-manager.desktop")

    def test_no_value(self):
        # test case where we don't have a value for app_install_desktop_path
        # (e.g. for a local .deb install, see bug LP: #768158)
        installed_desktop_path = convert_desktop_file_to_installed_location(
                None, "update-manager")
        # FIXME: this will only work if update-manager is installed
        self.assertEqual(installed_desktop_path,
                         "/usr/share/applications/update-manager.desktop")
    

if __name__ == "__main__":
    unittest.main()
