import panel as pn
from datafed_app import DataFedApp

app = DataFedApp()
app.login_button.button_type = 'success'
app.logout_button.button_type = 'danger'
app.update_button.button_type = 'primary'
app.login_button.icon = 'sign-in'
app.logout_button.icon = 'sign-out'
app.update_button.icon = 'edit'
app.start_auto_button.icon = 'play'
app.stop_auto_button.icon = 'stop'

# Material Design CSS
pn.config.raw_css.append("""
:root {
    --md-primary-color: #1976d2;
    --md-secondary-color: #dc004e;
    --md-background-color: #fafafa;
    --md-surface-color: #ffffff;
    --md-error-color: #b00020;
    --md-text-primary: rgba(0, 0, 0, 0.87);
    --md-text-secondary: rgba(0, 0, 0, 0.6);
    --md-divider-color: rgba(0, 0, 0, 0.12);
}

body {
    background-color: var(--md-background-color);
    color: var(--md-text-primary);
    font-family: 'Roboto', sans-serif;
}

.bk-btn {
    text-transform: uppercase;
    font-weight: 500;
    letter-spacing: 0.0892857143em;
    padding: 0 16px;
    transition: box-shadow 0.2s;
}

.bk-btn:hover {
    box-shadow: 0px 2px 4px -1px rgba(0,0,0,0.2), 0px 4px 5px 0px rgba(0,0,0,0.14), 0px 1px 10px 0px rgba(0,0,0,0.12);
}

.bk-btn-primary {
    background-color: var(--md-primary-color) !important;
    color: white !important;
}

.bk-btn-danger {
    background-color: var(--md-error-color) !important;
    color: white !important;
}

.bk-btn-success {
    background-color: #4caf50 !important;
    color: white !important;
}

select {
    background-color: var(--md-surface-color);
    border: 1px solid var(--md-divider-color);
    padding: 8px 12px;
    border-radius: 4px;
    font-size: 14px;
    color: var(--md-text-primary);
    transition: border-color 0.2s;
}

select:focus {
    border-color: var(--md-primary-color);
    outline: none;
}

.pn-loading-spinner {
    display: none !important;
}

.bk-panel-models-markdown {
    background-color: var(--md-surface-color);
    padding: 16px;
    border-radius: 4px;
    box-shadow: 0px 2px 1px -1px rgba(0,0,0,0.2), 0px 1px 1px 0px rgba(0,0,0,0.14), 0px 1px 3px 0px rgba(0,0,0,0.12);
}

.bk-panel-models-markdown h3 {
    color: var(--md-primary-color);
    margin-top: 0;
}

.progress-container {
    background-color: var(--md-surface-color);
    padding: 16px;
    border-radius: 4px;
    box-shadow: 0px 2px 1px -1px rgba(0,0,0,0.2), 0px 1px 1px 0px rgba(0,0,0,0.14), 0px 1px 3px 0px rgba(0,0,0,0.12);
}

.file-tracking-pane {
    background-color: var(--md-surface-color);
    padding: 16px;
    border-radius: 4px;
    box-shadow: 0px 2px 1px -1px rgba(0,0,0,0.2), 0px 1px 1px 0px rgba(0,0,0,0.14), 0px 1px 3px 0px rgba(0,0,0,0.12);
    margin: 8px;
}

.bk-tabs-header {
    background-color: var(--md-surface-color);
    border-bottom: 1px solid var(--md-divider-color);
    padding: 0 16px;
}

.bk-tab {
    color: var(--md-text-secondary);
    padding: 16px 24px;
    transition: all 0.2s ease;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-size: 0.875rem;
    position: relative;
    margin: 0 4px;
}

.bk-tab:hover {
    color: var(--md-primary-color);
    background-color: rgba(25, 118, 210, 0.04);
}

.bk-tab.active {
    color: var(--md-primary-color);
    background-color: rgba(25, 118, 210, 0.08);
}

.bk-tab.active::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 2px;
    background-color: var(--md-primary-color);
    transform: scaleX(1);
    transition: transform 0.2s ease;
}

.bk-tab:not(.active)::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 2px;
    background-color: var(--md-primary-color);
    transform: scaleX(0);
    transition: transform 0.2s ease;
}

.bk-tab:hover::after {
    transform: scaleX(1);
}

.bk-tabs-content {
    padding: 24px;
    background-color: var(--md-surface-color);
    border-radius: 0 0 4px 4px;
    box-shadow: 0px 2px 1px -1px rgba(0,0,0,0.2), 0px 1px 1px 0px rgba(0,0,0,0.14), 0px 1px 3px 0px rgba(0,0,0,0.12);
}


.bk-header .bk-btn {
    color: white !important;
}

.bk-header .bk-btn:hover {
    background-color: rgba(255, 255, 255, 0.1) !important;
}
""")

@pn.depends(app.param.current_user)
def login_logout_button(current_user):
    if current_user == "Not Logged In":
        return app.login_button
    else:
        return app.logout_button

@pn.depends(app.metadata_json_editor.param.value)
def update_button_visibility(metadata_json_editor_value):
    if metadata_json_editor_value:
        return app.update_button
    else:
        return pn.pane.Markdown("")

def on_update_button_click(event):
    app.update_record()
    pn.state.notifications.success('Record updated successfully!', duration=2000)

app.update_button.on_click(on_update_button_click)

# Define the header with Material Design styling
header = pn.Row(
    pn.layout.HSpacer(),
    pn.pane.Markdown("**User:**", css_classes=['md-text']),
    pn.bind(lambda current_user: pn.pane.Markdown(f"**{current_user}**", css_classes=['md-text']), app.param.current_user),
    pn.layout.Spacer(width=20),
    app.logout_button,
    pn.layout.Spacer(width=20),
    pn.layout.HSpacer()
)

@pn.depends(app.param.record_alert_message)
def record_alert(record_alert_message):
    return pn.Column(
        pn.pane.Markdown(f"### {record_alert_message}", css_classes=['md-text']),
        pn.widgets.Button(name='Close', button_type='danger', on_click=lambda event: app.clear_alert_message())
    ) if record_alert_message else None

# Define the login pane with Material Design styling
login_pane = pn.Column(
    pn.pane.Markdown("### Login", css_classes=['md-text']),
    pn.Param(app.param.username, css_classes=['md-input']),
    pn.Param(app.param.password, widgets={'password': pn.widgets.PasswordInput}, css_classes=['md-input']),
    pn.widgets.Button(name='Submit Login', button_type='primary', on_click=app.check_login),
    pn.Param(app.param.login_status, css_classes=['md-text']),
    css_classes=['md-card']
)

# Automated processing panel with Material Design styling
@pn.depends(app.param.progress, app.param.processing_status, app.param.current_file, app.param.task_id)
def auto_processing_panel(progress, status, current_file, task_id):
    progress_bar = pn.widgets.Progress(name="Progress", value=progress, width=400)
    
    return pn.Column(
        pn.pane.Markdown("## Automated Data Processing", css_classes=['md-text']),
        pn.Row(app.start_auto_button, app.stop_auto_button),
        pn.Row(
            pn.Column(
                pn.pane.Markdown("### Directory Configuration", css_classes=['md-text']),
                pn.pane.Markdown("**Current Auto Processing Directory:**", css_classes=['md-text']),
                pn.pane.Markdown(f"`{app.file_path}`", css_classes=['md-text']),
                pn.pane.Markdown("**Change Directory:**", css_classes=['md-text']),
                app.auto_processing_dir_selector,
                css_classes=['progress-container']
            ),
            pn.Column(
                pn.pane.Markdown(f"**Status:** {status}", css_classes=['md-text']),
                pn.pane.Markdown(f"**Current File:** {current_file}", css_classes=['md-text']),
                pn.pane.Markdown(f"**Task ID:** {task_id}", css_classes=['md-text']),
                progress_bar,
                pn.pane.Markdown(f"**Progress:** {progress}%", css_classes=['md-text']),
                css_classes=['progress-container']
            )
        ),
        pn.Row(
            pn.Column(
                app.current_file_pane,
                width=400,
                css_classes=['file-tracking-pane']
            ),
            pn.Column(
                app.processed_files_pane,
                width=400,
                css_classes=['file-tracking-pane']
            ),
            pn.Column(
                app.unprocessed_files_pane,
                width=400,
                css_classes=['file-tracking-pane']
            )
        ),
        pn.Row(app.record_output_pane)
    )

# Define the record management pane with Material Design styling
record_pane = pn.Column(
    pn.Param(app.param.selected_context, widgets={'selected_context': pn.widgets.Select}, css_classes=['md-select']),
    pn.Param(app.param.selected_collection, widgets={'selected_collection': pn.widgets.Select}, css_classes=['md-select']),
    pn.Tabs(
        ("Create Record", pn.Column(
            pn.Row(pn.Param(app.param.title, css_classes=['md-input']), app.file_selector, app.metadata_json_editor),
            app.create_button,
            app.record_output_pane,
            css_classes=['md-card']
        )),
        ("Read Record", pn.Column(
            pn.Param(app.param.record_id, css_classes=['md-select']),
            pn.Column(app.read_button, app.update_button, app.delete_button),
            app.record_output_pane,
            app.metadata_json_editor,
            css_classes=['md-card']
        )),
        ("Auto Processing", auto_processing_panel)
    )
)

@pn.depends(app.param.current_user)
def main_content(current_user):
    if current_user == "Not Logged In":
        return login_pane
    else:
        return record_pane

# Use BootstrapTemplate with Material Design styling
template = pn.template.BootstrapTemplate(
    title='DataFed Management',
    theme='default',
    header_background='#1976d2',
    header_color='white'
)

template.header.append(header)
template.main.append(main_content)
template.modal.append(record_alert)
template.modal.append(pn.bind(lambda show: login_pane if show else None, app.param.show_login_panel))

pn.state.onload(lambda: app.toggle_login_panel(None))

template.servable()
