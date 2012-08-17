#!/usr/bin/python

import unittest

from gi.repository import Gtk
from mock import Mock

from testutils import setup_test_env
setup_test_env()

from softwarecenter.ui.gtk3.panes import availablepane, softwarepane
from softwarecenter.ui.gtk3.session.viewmanager import (
    ViewManager,
    get_viewmanager
)


class TestViewManager(unittest.TestCase):
    """Test suite for the viewmanager."""

    def setUp(self):
        # create it once, it becomes global instance
        self.vm = get_viewmanager()
        if self.vm is None:
            self.vm = ViewManager(Gtk.Notebook())

        self.addCleanup(self.vm.destroy)

    def test_get_viewmanager(self):
        view_manager = get_viewmanager()
        self.assertNotEqual(view_manager, None)
        # is a singleton singleton
        view_manager2 = get_viewmanager()
        self.assertIs(view_manager, view_manager2)
        # test creating it twice raises a error
        self.assertRaises(ValueError, ViewManager, Gtk.Notebook())

    def test_display_page_stops_video(self):
        called = []
        # navigate to an app details view with video
        pane = Mock()
        pane.pane_name = 'MockPane'
        pane.is_applist_view_showing = lambda: False
        pane.app_details_view.videoplayer.stop = lambda: called.append('stop')
        self.vm.display_page(
            pane, page=availablepane.AvailablePane.Pages.DETAILS,
            view_state=softwarepane.DisplayState())

        other_pane = Mock()
        other_pane.pane_name = 'MockPane'
        self.vm.display_page(
            other_pane, page=availablepane.AvailablePane.Pages.DETAILS,
            view_state=softwarepane.DisplayState())

        self.assertEqual(called, ['stop'])


if __name__ == "__main__":
    unittest.main()
