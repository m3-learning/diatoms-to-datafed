from __future__ import annotations
import os
import json
from typing import ClassVar
import param
import panel as pn
from panel.viewable import Layoutable
from panel.widgets.base import CompositeWidget
from panel.widgets.select import CrossSelector
from panel.layout import Column, Row, Divider
from panel.widgets.button import Button
from panel.widgets.input import TextInput
from panel.io import PeriodicCallback
from panel.util import fullpath
from fnmatch import fnmatch

pn.extension('material')

class FileSelector(CompositeWidget):
    directory = param.String(default=os.getcwd(), doc="The directory to explore.")
    file_pattern = param.String(default='*', doc="A glob-like pattern to filter the files.")
    only_files = param.Boolean(default=False, doc="Whether to only allow selecting files.")
    show_hidden = param.Boolean(default=False, doc="Whether to show hidden files and directories (starting with a period).")
    size = param.Integer(default=10, doc="The number of options shown at once (note this is the only way to control the height of this widget)")
    refresh_period = param.Integer(default=None, doc="If set to non-None value indicates how frequently to refresh the directory contents in milliseconds.")
    root_directory = param.String(default=None, doc="If set, overrides directory parameter as the root directory beyond which users cannot navigate.")
    value = param.List(default=[], doc="List of selected files.")
    _composite_type: ClassVar[type[Column]] = Column

    def __init__(self, directory=None, **params):
        if directory is not None:
            params['directory'] = fullpath(directory)
        if 'root_directory' in params:
            root = params['root_directory']
            params['root_directory'] = fullpath(root)
        if params.get('width') and params.get('height') and 'sizing_mode' not in params:
            params['sizing_mode'] = None

        super().__init__(**params)

        layout = {p: getattr(self, p) for p in Layoutable.param if p not in ('name', 'height', 'margin') and getattr(self, p) is not None}
        sel_layout = dict(layout, sizing_mode='stretch_width', height=300, margin=0)
        self._selector = CrossSelector(
            filter_fn=lambda p, f: fnmatch(f, p), size=self.size, **sel_layout, value=[]
        )

        self._back = Button(name='◀', width=40, height=40, margin=(5, 10, 0, 0), disabled=True, align='center')
        self._forward = Button(name='▶', width=40, height=40, margin=(5, 10, 0, 0), disabled=True, align='center')
        self._up = Button(name='⬆', width=40, height=40, margin=(5, 10, 0, 0), disabled=True, align='center')
        self._directory = TextInput(value=self.directory, margin=(5, 10, 0, 0), width_policy='max', height_policy='max')
        self._go = Button(name='⬇', disabled=True, width=40, height=40, margin=(5, 5, 0, 0), align='center')
        self._reload = Button(name='↻', width=40, height=40, margin=(5, 0, 0, 10), align='center')
        self._nav_bar = Row(
            self._back, self._forward, self._up, self._directory, self._go, self._reload,
            **dict(layout, width=None, margin=0, width_policy='max')
        )
        self._composite[:] = [self._nav_bar, Divider(margin=0), self._selector]

        self._stack = []
        self._cwd = None
        self._position = -1
        self._update_files(True)

        self._selector._lists[False].on_double_click(self._select_and_go)
        self.link(self._directory, directory='value')
        self._selector.param.watch(self._update_value, 'value')
        self._go.on_click(self._update_files)
        self._reload.on_click(self._update_files)
        self._up.on_click(self._go_up)
        self._back.on_click(self._go_back)
        self._forward.on_click(self._go_forward)
        self._directory.param.watch(self._dir_change, 'value')
        self._selector._lists[False].param.watch(self._select, 'value')
        self._selector._lists[False].param.watch(self._filter_denylist, 'options')
        self._periodic = PeriodicCallback(callback=self._refresh, period=self.refresh_period or 0)
        self.param.watch(self._update_periodic, 'refresh_period')
        if self.refresh_period:
            self._periodic.start()

        self._message = pn.pane.Markdown("", width_policy='max', height_policy='max')
        self._selected_file_display = pn.pane.Markdown("", width_policy='max', height_policy='max')
        self._output = pn.Column(self._selected_file_display, self._message)

        self._composite.append(self._output)

    def _select_and_go(self, event):
        relpath = event.option.replace('📁', '').replace('⬆ ', '')
        if relpath == 'panel.':
            return self._go_up()
        sel = fullpath(os.path.join(self._cwd, relpath))
        if os.path.isdir(sel):
            self._directory.value = sel
        else:
            self._directory.value = self._cwd
        self._update_files()

    def _update_periodic(self, event):
        if event.new:
            self._periodic.period = event.new
            if not self._periodic.running:
                self._periodic.start()
        elif self._periodic.running:
            self._periodic.stop()

    @property
    def _root_directory(self):
        return self.root_directory or self.directory

    def _update_value(self, event):
        # Allow only one file to be selected
        if len(event.new) > 1:
            self._selector.value = [event.new[-1]]
        else:
            self._selector.value = event.new

        self.value = self._selector.value
        self._update_output(self.value)

    def _dir_change(self, event):
        path = fullpath(self._directory.value)
        if not path.startswith(self._root_directory):
            self._directory.value = self._root_directory
            return
        elif path != self._directory.value:
            self._directory.value = path
        self._go.disabled = path == self._cwd

    def _refresh(self):
        self._update_files(refresh=True)

    def _update_files(self, event=None, refresh=False):
        path = fullpath(self._directory.value)
        refresh = refresh or (event and getattr(event, 'obj', None) is self._reload)
        if refresh:
            path = self._cwd
        elif not os.path.isdir(path):
            self._selector.options = ['Entered path is not valid']
            self._selector.disabled = True
            return
        elif event is not None and (not self._stack or path != self._stack[-1]):
            self._stack.append(path)
            self._position += 1

        self._cwd = path
        if not refresh:
            self._go.disabled = True
        self._up.disabled = path == self._root_directory
        if self._position == len(self._stack)-1:
            self._forward.disabled = True
        if 0 <= self._position and len(self._stack) > 1:
            self._back.disabled = False

        selected = self.value
        dirs, files = self._scan_path(path, self.file_pattern)
        for s in selected:
            check = os.path.realpath(s) if os.path.islink(s) else s
            if os.path.isdir(check):
                dirs.append(s)
            elif os.path.isfile(check):
                files.append(s)

        paths = [
            p for p in sorted(dirs) + sorted(files)
            if self.show_hidden or not os.path.basename(p).startswith('.')
        ]
        abbreviated = [
            ('📁' if f in dirs else '') + os.path.relpath(f, self._cwd)
            for f in paths
        ]
        if not self._up.disabled:
            paths.insert(0, 'panel.')
            abbreviated.insert(0, '⬆ panel.')

        options = dict(zip(abbreviated, paths))
        self._selector.options = options
        self._selector.value = selected

    def _filter_denylist(self, event):
        dirs, files = self._scan_path(self._cwd, self.file_pattern)
        paths = [('📁' if p in dirs else '') + os.path.relpath(p, self._cwd) for p in dirs + files]
        denylist = self._selector._lists[False]
        options = dict(self._selector._items)
        self._selector.options.clear()
        prefix = [] if self._up.disabled else [('⬆ panel.', 'panel.')]
        self._selector.options.update(prefix + [
            (k, v) for k, v in options.items() if k in paths or v in self.value
        ])
        options = [o for o in denylist.options if o in paths]
        if not self._up.disabled:
            options.insert(0, '⬆ panel.')
        denylist.options = options

    def _select(self, event):
        if len(event.new) != 1:
            self._directory.value = self._cwd
            return

        relpath = event.new[0].replace('📁', '').replace('⬆ ', '')
        sel = fullpath(os.path.join(self._cwd, relpath))
        if os.path.isdir(sel):
            self._directory.value = sel
        else:
            self._directory.value = self._cwd

    def _go_back(self, event):
        self._position -= 1
        self._directory.value = self._stack[self._position]
        self._update_files()
        self._forward.disabled = False
        if self._position == 0:
            self._back.disabled = True

    def _go_forward(self, event):
        self._position += 1
        self._directory.value = self._stack[self._position]
        self._update_files()

    def _go_up(self, event=None):
        path = self._cwd.split(os.path.sep)
        self._directory.value = os.path.sep.join(path[:-1]) or os.path.sep
        self._update_files(True)

    def _update_output(self, selected_files):
        if not selected_files:
            self._selected_file_display.object = ""
            self._output[1:] = [self._message]  # Ensures only one item is assigned
            return None

        selected_file = selected_files[0]
        self._selected_file_display.object = f""

        if selected_file.endswith('.json'):
            with open(selected_file, 'r') as f:
                json_data = json.load(f)
            # Update the Column to display the selected file and JSON viewer
            self._output[:] = [self._selected_file_display]  # Replace with selected file display
            return json_data  # Return JSON data for processing in DataFedApp
        else:
            # Show message if the selected file is not a JSON
            self._output[:] = [self._selected_file_display, self._message]  # Replace with message
            return None

    def _scan_path(self, path, file_pattern):
        paths = [os.path.join(path, p) for p in os.listdir(path)]
        dirs = [p for p in paths if os.path.isdir(p)]
        files = [p for p in paths if os.path.isfile(p) and fnmatch(os.path.basename(p), file_pattern)]
        for p in paths:
            if not os.path.islink(p):
                continue
            path = os.path.realpath(p)
            if os.path.isdir(path):
                dirs.append(p)
            elif os.path.isfile(path):
                files.append(p)
        return dirs, files
