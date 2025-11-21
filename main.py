from nicegui import ui, app
from database import Database
from typing import Optional, Dict, Any
from datetime import datetime
import os

# Initialize database
db = Database()

# Table configuration mapping display names to table names
TABLE_CONFIG = {
    'Devices': 'devices',
    'Employees': 'employees',
    'Departments': 'departments',
    'Manufacturers': 'manufacturer',
    'Device Types': 'device_types',
    'Devices Issued': 'devices_issued'
}


def format_value(value: Any) -> str:
    """Format values for display"""
    if value is None:
        return ''
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    return str(value)


def format_field_label(field_name: str) -> str:
    """Format field name for display, removing '_id' suffix"""
    label = field_name.replace('_', ' ').title()
    # Remove " Id" suffix from foreign key fields
    if label.endswith(' Id') and field_name != 'id':
        label = label[:-3]  # Remove the last 3 characters (" Id")
    return label


def get_foreign_key_display(table_name: str, column_name: str, value: Any) -> str:
    """Get display value for foreign keys"""
    if value is None:
        return ''

    try:
        if column_name == 'manufacturer_id':
            manufacturers = db.get_manufacturers()
            for m in manufacturers:
                if m['id'] == value:
                    return m['name']
        elif column_name == 'device_type_id':
            types = db.get_device_types()
            for t in types:
                if t['id'] == value:
                    return t['device_type']
        elif column_name == 'department_id':
            departments = db.get_departments()
            for d in departments:
                if d['id'] == value:
                    return d['name']
        elif column_name == 'employee_id':
            employees = db.get_employees()
            for e in employees:
                if e['id'] == value:
                    return f"{e['first_name']} {e['last_name']}"
        elif column_name == 'device_id':
            devices = db.get_devices()
            for d in devices:
                if d['id'] == value:
                    return f"{d['model']} ({d['serial_number']})"
    except:
        pass

    return str(value)


def create_form_field(column_info: Dict[str, Any], initial_value: Any = None, table_name: str = None, is_new: bool = True):
    """Create appropriate form field based on column type"""
    field_name = column_info['Field']
    field_type = column_info['Type']
    is_nullable = column_info['Null'] == 'YES'

    # Skip ID field for new entries
    if field_name == 'id' and initial_value is None:
        return None

    # Skip date_of_issue for new devices_issued entries (will be set by database)
    if table_name == 'devices_issued' and field_name == 'date_of_issue' and is_new:
        return None

    label = format_field_label(field_name)

    # Handle foreign keys with dropdowns
    if field_name == 'manufacturer_id':
        manufacturers = db.get_manufacturers()
        if not manufacturers:
            return ui.label(f'{label}: No manufacturers available').classes('text-orange-600 w-full')
        options = {m['id']: m['name'] for m in manufacturers}
        return ui.select(options=options, label=label, value=initial_value).classes('w-full')

    elif field_name == 'device_type_id':
        types = db.get_device_types()
        if not types:
            return ui.label(f'{label}: No device types available').classes('text-orange-600 w-full')
        options = {t['id']: t['device_type'] for t in types}
        return ui.select(options=options, label=label, value=initial_value).classes('w-full')

    elif field_name == 'department_id':
        departments = db.get_departments()
        if not departments:
            return ui.label(f'{label}: No departments available').classes('text-orange-600 w-full')
        options = {d['id']: d['name'] for d in departments}
        return ui.select(options=options, label=label, value=initial_value).classes('w-full')

    elif field_name == 'employee_id':
        employees = db.get_employees()
        if not employees and not is_nullable:
            return ui.label(f'{label}: No employees available').classes('text-orange-600 w-full')
        options = {e['id']: f"{e['first_name']} {e['last_name']}" for e in employees}
        if is_nullable:
            options[None] = '(None)'
        return ui.select(options=options, label=label, value=initial_value).classes('w-full')

    elif field_name == 'device_id':
        # For new devices_issued entries, only show available devices
        if table_name == 'devices_issued' and is_new:
            devices = db.get_available_devices()
            if not devices:
                return ui.label(f'{label}: No available devices to issue').classes('text-orange-600 w-full')
        else:
            devices = db.get_devices()
            if not devices:
                return ui.label(f'{label}: No devices available').classes('text-orange-600 w-full')
        options = {d['id']: f"{d['model']} ({d['serial_number']})" for d in devices}
        return ui.select(options=options, label=label, value=initial_value).classes('w-full')

    # Handle timestamps
    elif 'timestamp' in field_type or 'datetime' in field_type:
        value_str = initial_value.strftime('%Y-%m-%dT%H:%M') if initial_value else ''
        return ui.input(label=label, value=value_str).props('type=datetime-local').classes('w-full')

    # Handle integers
    elif 'int' in field_type:
        return ui.number(label=label, value=initial_value if initial_value is not None else 0).classes('w-full')

    # Handle text fields
    else:
        return ui.input(label=label, value=initial_value if initial_value else '').classes('w-full')


async def show_new_entry_dialog(table_display_name: str):
    """Show dialog for creating a new entry"""
    table_name = TABLE_CONFIG[table_display_name]
    columns = db.get_table_columns(table_name)

    form_fields = {}

    with ui.dialog() as dialog, ui.card().classes('w-full max-w-2xl'):
        ui.label(f'New {table_display_name} Entry').classes('text-xl font-bold mb-4')

        with ui.column().classes('w-full gap-2'):
            for col in columns:
                if col['Field'] == 'id':
                    continue
                field = create_form_field(col, table_name=table_name, is_new=True)
                if field:
                    form_fields[col['Field']] = field

        with ui.row().classes('w-full justify-end gap-2 mt-4'):
            ui.button('Cancel', on_click=dialog.close).props('flat')
            ui.button('Create', on_click=lambda: save_new_entry(dialog, table_name, form_fields))

    dialog.open()


async def save_new_entry(dialog, table_name: str, form_fields: Dict):
    """Save a new entry to the database"""
    try:
        data = {}
        for field_name, field_widget in form_fields.items():
            value = field_widget.value
            # Handle empty strings for nullable fields
            if value == '' or value is None:
                # Check if field allows NULL
                columns = db.get_table_columns(table_name)
                col_info = next((c for c in columns if c['Field'] == field_name), None)
                if col_info and col_info['Null'] == 'YES':
                    data[field_name] = None
                else:
                    data[field_name] = value
            else:
                data[field_name] = value

        db.insert_row(table_name, data)
        ui.notify('Entry created successfully!', type='positive')
        dialog.close()
        # Refresh the page
        ui.navigate.reload()
    except Exception as e:
        ui.notify(f'Error creating entry: {str(e)}', type='negative')


async def show_edit_dialog(table_display_name: str, row_id: int):
    """Show dialog for editing an entry"""
    table_name = TABLE_CONFIG[table_display_name]
    row_data = db.get_row_by_id(table_name, row_id)
    columns = db.get_table_columns(table_name)

    if not row_data:
        ui.notify('Entry not found', type='negative')
        return

    form_fields = {}

    with ui.dialog() as dialog, ui.card().classes('w-full max-w-2xl'):
        ui.label(f'Edit {table_display_name} Entry (ID: {row_id})').classes('text-xl font-bold mb-4')

        with ui.column().classes('w-full gap-2'):
            for col in columns:
                if col['Field'] == 'id':
                    continue
                field = create_form_field(col, row_data.get(col['Field']), table_name=table_name, is_new=False)
                if field:
                    form_fields[col['Field']] = field

        with ui.row().classes('w-full justify-end gap-2 mt-4'):
            ui.button('Cancel', on_click=dialog.close).props('flat')
            ui.button('Save', on_click=lambda: save_edit(dialog, table_name, row_id, form_fields))

    dialog.open()


async def save_edit(dialog, table_name: str, row_id: int, form_fields: Dict):
    """Save edited entry to the database"""
    try:
        data = {}
        for field_name, field_widget in form_fields.items():
            value = field_widget.value
            # Handle empty strings for nullable fields
            if value == '' or value is None:
                columns = db.get_table_columns(table_name)
                col_info = next((c for c in columns if c['Field'] == field_name), None)
                if col_info and col_info['Null'] == 'YES':
                    data[field_name] = None
                else:
                    data[field_name] = value
            else:
                data[field_name] = value

        db.update_row(table_name, row_id, data)
        ui.notify('Entry updated successfully!', type='positive')
        dialog.close()
        # Refresh the page
        ui.navigate.reload()
    except Exception as e:
        ui.notify(f'Error updating entry: {str(e)}', type='negative')


async def show_delete_dialog(table_display_name: str, row_id: int):
    """Show confirmation dialog for deleting an entry"""
    table_name = TABLE_CONFIG[table_display_name]

    with ui.dialog() as dialog, ui.card():
        ui.label(f'Delete Entry?').classes('text-xl font-bold mb-4')
        ui.label(f'Are you sure you want to delete this {table_display_name} entry (ID: {row_id})?').classes('mb-4')
        ui.label('This action cannot be undone.').classes('text-red-600 mb-4')

        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancel', on_click=dialog.close).props('flat')
            ui.button('Delete', on_click=lambda: confirm_delete(dialog, table_name, row_id)).props('color=negative')

    dialog.open()


async def confirm_delete(dialog, table_name: str, row_id: int):
    """Delete the entry from the database"""
    try:
        success = db.delete_row(table_name, row_id)
        if success:
            ui.notify('Entry deleted successfully!', type='positive')
        else:
            ui.notify('Entry not found or already deleted', type='warning')
        dialog.close()
        # Refresh the page
        ui.navigate.reload()
    except Exception as e:
        ui.notify(f'Error deleting entry: {str(e)}', type='negative')


def render_table_page(table_display_name: str, items_per_page: int, current_page: int):
    """Render the table display page"""
    table_name = TABLE_CONFIG[table_display_name]

    # Calculate offset
    offset = (current_page - 1) * items_per_page

    # Get data
    data, total_count = db.get_table_data(table_name, limit=items_per_page, offset=offset)
    total_pages = max(1, (total_count + items_per_page - 1) // items_per_page)

    # Header with New Entry button
    with ui.row().classes('w-full justify-between items-center mb-4'):
        ui.label(table_display_name).classes('text-2xl font-bold')
        ui.button('New Entry', icon='add', on_click=lambda: show_new_entry_dialog(table_display_name)).props('color=primary')

    # Pagination controls at top
    with ui.row().classes('w-full items-center gap-4 mb-4'):
        ui.label(f'Total: {total_count} entries')

        # Items per page selector
        def change_items_per_page(e):
            if e.value == 'custom':
                return  # Will handle custom input separately
            new_per_page = int(e.value)
            ui.navigate.to(f'/?table={table_display_name}&page=1&per_page={new_per_page}')

        ui.select(
            options={'25': '25 per page', '50': '50 per page', '100': '100 per page'},
            value=str(items_per_page) if items_per_page in [25, 50, 100] else '25',
            on_change=change_items_per_page
        ).classes('w-40')

        # Page navigation
        ui.label(f'Page {current_page} of {total_pages}')

        def prev_page():
            if current_page > 1:
                ui.navigate.to(f'/?table={table_display_name}&page={current_page - 1}&per_page={items_per_page}')

        def next_page():
            if current_page < total_pages:
                ui.navigate.to(f'/?table={table_display_name}&page={current_page + 1}&per_page={items_per_page}')

        ui.button(icon='chevron_left', on_click=prev_page).props('flat').set_enabled(current_page > 1)
        ui.button(icon='chevron_right', on_click=next_page).props('flat').set_enabled(current_page < total_pages)

    # Table display
    if data:
        columns_info = db.get_table_columns(table_name)
        column_names = [col['Field'] for col in columns_info]

        # Create table headers with Edit column
        headers = [{'name': col, 'label': format_field_label(col), 'field': col, 'sortable': True, 'align': 'left'} for col in column_names]
        headers.append({'name': 'actions', 'label': 'Actions', 'field': 'actions', 'sortable': False})

        # Prepare rows with formatted values
        rows = []
        for row in data:
            formatted_row = {}
            for col in column_names:
                value = row.get(col)
                # Show foreign key display values
                if col.endswith('_id') and col != 'id':
                    formatted_row[col] = get_foreign_key_display(table_name, col, value)
                else:
                    formatted_row[col] = format_value(value)
            formatted_row['_id'] = row['id']  # Store actual ID for edit
            rows.append(formatted_row)

        table = ui.table(columns=headers, rows=rows, row_key='_id').classes('w-full')

        # Add edit and delete buttons to each row
        table.add_slot('body-cell-actions', '''
            <q-td :props="props">
                <q-btn flat dense icon="edit" @click="$parent.$emit('edit', props.row)" />
                <q-btn flat dense icon="delete" color="negative" @click="$parent.$emit('delete', props.row)" />
            </q-td>
        ''')

        table.on('edit', lambda e: show_edit_dialog(table_display_name, e.args['_id']))
        table.on('delete', lambda e: show_delete_dialog(table_display_name, e.args['_id']))

    else:
        ui.label('No entries found').classes('text-gray-500')


@ui.page('/')
def main_page(table: str = 'Devices', page: int = 1, per_page: int = 25):
    """Main page with navigation and content"""

    # Validate table name
    if table not in TABLE_CONFIG:
        table = 'Devices'

    # Validate pagination
    page = max(1, page)
    per_page = max(1, min(1000, per_page))  # Cap at 1000

    # Dark mode toggle with persistence
    dark = ui.dark_mode(value=app.storage.user.get('dark_mode', False))

    def save_dark_mode():
        app.storage.user['dark_mode'] = dark.value

    with ui.left_drawer(fixed=True).classes('bg-gray-100 dark:bg-gray-900').style('width: 250px'):
        ui.label('Scooteq Database').classes('text-xl font-bold p-4')

        with ui.column().classes('w-full'):
            for table_name in TABLE_CONFIG.keys():
                ui.button(
                    table_name,
                    on_click=lambda t=table_name: ui.navigate.to(f'/?table={t}&page=1&per_page={per_page}')
                ).props('flat align=left').classes('w-full')

        # Dark mode toggle at bottom of sidebar
        ui.separator().classes('my-4')
        with ui.row().classes('w-full px-4'):
            ui.switch('Dark mode').bind_value(dark).on('update:model-value', save_dark_mode)

    # Main content area
    with ui.column().classes('w-full p-6'):
        render_table_page(table, per_page, page)


ui.run(
    host='0.0.0.0',
    port=int(os.getenv('APP_PORT', '8081')),
    reload=False,
    storage_secret=os.getenv('STORAGE_SECRET', 'scooteq_secret_key_change_in_production')
)
